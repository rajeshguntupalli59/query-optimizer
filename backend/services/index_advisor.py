"""
Index advisor.

PostgreSQL  — pg_indexes, pg_stat_user_indexes, information_schema
MSSQL       — sys.dm_db_missing_index_details, sys.indexes,
              sys.foreign_keys, sys.foreign_key_columns
"""
from __future__ import annotations
import re
from services.connection_manager import open_connection


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def recommend_indexes(conn_id: str, sql: str) -> list[dict]:
    conn, adapter, cfg = open_connection(conn_id)
    try:
        if cfg["db_type"] == "postgres":
            return _pg_recommend(conn, sql)
        else:
            return _mssql_recommend(conn, sql)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Shared SQL parsing helpers
# ---------------------------------------------------------------------------
def _extract_tables(sql: str) -> list[str]:
    pattern = re.compile(r'(?:FROM|JOIN)\s+([\w.\[\]]+)', re.IGNORECASE)
    tables = []
    for m in pattern.finditer(sql):
        tables.append(m.group(1).strip("[]"))
    return list(dict.fromkeys(tables))


def _split_schema_pg(table: str):
    parts = table.split(".")
    return (parts[0], parts[1]) if len(parts) == 2 else ("public", parts[0])


def _split_schema_mssql(table: str):
    parts = table.split(".")
    return (parts[0], parts[1]) if len(parts) == 2 else ("dbo", parts[0])


def _deduplicate(recs: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in recs:
        key = (r["table"], tuple(r["columns"]))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
def _pg_recommend(conn, sql: str) -> list[dict]:
    from psycopg2.extras import RealDictCursor
    recs = []
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        recs.extend(_pg_unindexed_tables(cur, sql))
        recs.extend(_pg_fk_without_index(cur, sql))
        recs.extend(_pg_infer_from_sql(cur, sql))
    return _deduplicate(recs)


def _pg_unindexed_tables(cur, sql: str) -> list[dict]:
    recs = []
    for table in _extract_tables(sql):
        schema, tname = _split_schema_pg(table)
        cur.execute(
            "SELECT indexrelname FROM pg_stat_user_indexes WHERE schemaname=%s AND relname=%s",
            (schema, tname),
        )
        if not cur.fetchall():
            cur.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, tname),
            )
            if cur.fetchone():
                recs.append({
                    "table": f"{schema}.{tname}", "columns": [],
                    "reason": "Table has no indexes at all",
                    "ddl": f"-- Add indexes based on your query predicates on {schema}.{tname}",
                    "estimated_benefit": "High",
                })
    return recs


def _pg_fk_without_index(cur, sql: str) -> list[dict]:
    cur.execute("""
        SELECT tc.table_schema, tc.table_name, kcu.column_name, ccu.table_name AS ftable
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name=tc.constraint_name
        WHERE tc.constraint_type='FOREIGN KEY'
          AND NOT EXISTS (
              SELECT 1 FROM pg_indexes
              WHERE schemaname=tc.table_schema AND tablename=tc.table_name
                AND indexdef ILIKE '%' || kcu.column_name || '%'
          )
    """)
    tables_in_sql = {t.lower() for t in _extract_tables(sql)}
    recs = []
    for row in cur.fetchall():
        schema = row["table_schema"]
        tname  = row["table_name"]
        col    = row["column_name"]
        ftable = row["ftable"]
        if tname.lower() in tables_in_sql or ftable.lower() in tables_in_sql:
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col],
                "reason": f"FK column '{col}' has no index — can cause slow joins",
                "ddl": f"CREATE INDEX ON {schema}.{tname} ({col});",
                "estimated_benefit": "Medium-High",
            })
    return recs


def _pg_infer_from_sql(cur, sql: str) -> list[dict]:
    recs = []
    upper = sql.upper()
    where_cols = re.findall(r'WHERE\s+\w+\.(\w+)\s*[=<>!]', upper)
    order_cols  = re.findall(r'ORDER\s+BY\s+\w+\.(\w+)', upper)
    tables = _extract_tables(sql)
    if not tables:
        return recs
    schema, tname = _split_schema_pg(tables[0])
    for col in set(where_cols):
        if not _pg_index_exists(cur, schema, tname, col.lower()):
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col.lower()],
                "reason": f"WHERE column '{col.lower()}' has no index",
                "ddl": f"CREATE INDEX ON {schema}.{tname} ({col.lower()});",
                "estimated_benefit": "High",
            })
    for col in set(order_cols):
        if not _pg_index_exists(cur, schema, tname, col.lower()):
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col.lower()],
                "reason": f"ORDER BY column '{col.lower()}' has no index",
                "ddl": f"CREATE INDEX ON {schema}.{tname} ({col.lower()});",
                "estimated_benefit": "Medium",
            })
    return recs


def _pg_index_exists(cur, schema: str, table: str, column: str) -> bool:
    cur.execute(
        "SELECT 1 FROM pg_indexes WHERE schemaname=%s AND tablename=%s AND indexdef ILIKE %s LIMIT 1",
        (schema, table, f"%({column})%"),
    )
    return cur.fetchone() is not None


# ---------------------------------------------------------------------------
# MSSQL
# ---------------------------------------------------------------------------
def _mssql_recommend(conn, sql: str) -> list[dict]:
    recs = []
    cursor = conn.cursor()
    recs.extend(_mssql_missing_index_dmv(cursor, sql))
    recs.extend(_mssql_fk_without_index(cursor, sql))
    recs.extend(_mssql_infer_from_sql(cursor, sql))
    return _deduplicate(recs)


def _mssql_missing_index_dmv(cursor, sql: str) -> list[dict]:
    """
    sys.dm_db_missing_index_details is populated by the query optimiser
    whenever it detects a missing index during compilation/execution.
    We surface the top entries for tables referenced in the user's SQL.
    """
    tables_in_sql = {t.lower().lstrip("[").rstrip("]") for t in _extract_tables(sql)}
    cursor.execute("""
        SELECT TOP 20
            d.statement                         AS full_table,
            d.equality_columns,
            d.inequality_columns,
            d.included_columns,
            gs.avg_total_user_cost * gs.avg_user_impact * (gs.user_seeks + gs.user_scans)
                                                AS score
        FROM sys.dm_db_missing_index_details d
        JOIN sys.dm_db_missing_index_groups g
            ON d.index_handle = g.index_handle
        JOIN sys.dm_db_missing_index_group_stats gs
            ON g.index_group_handle = gs.group_handle
        ORDER BY score DESC
    """)
    cols = [d[0] for d in cursor.description]
    recs = []
    for row in cursor.fetchall():
        r = dict(zip(cols, row))
        full_table = (r["full_table"] or "").strip("[]").replace("].[", ".").replace("[", "")
        tname = full_table.split(".")[-1].lower()
        if tables_in_sql and tname not in tables_in_sql:
            continue
        eq_cols   = [c.strip().strip("[]") for c in (r["equality_columns"]   or "").split(",") if c.strip()]
        ineq_cols = [c.strip().strip("[]") for c in (r["inequality_columns"] or "").split(",") if c.strip()]
        inc_cols  = [c.strip().strip("[]") for c in (r["included_columns"]   or "").split(",") if c.strip()]
        all_key   = eq_cols + ineq_cols
        if not all_key:
            continue
        key_part = ", ".join(f"[{c}]" for c in all_key)
        inc_part = (f" INCLUDE ({', '.join(f'[{c}]' for c in inc_cols)})" if inc_cols else "")
        table_part = full_table.replace(".", "].[").join(["[", "]"]) if "." in full_table else f"[{full_table}]"
        ddl = f"CREATE INDEX IX_{tname}_{'_'.join(all_key[:3])} ON {table_part} ({key_part}){inc_part};"
        recs.append({
            "table":    full_table,
            "columns":  all_key,
            "reason":   f"Query optimiser identified a missing index (impact score {r['score']:.0f})",
            "ddl":      ddl,
            "estimated_benefit": "High — recommended directly by SQL Server's missing index DMV",
        })
    return recs


def _mssql_fk_without_index(cursor, sql: str) -> list[dict]:
    tables_in_sql = {t.lower().lstrip("[").rstrip("]") for t in _extract_tables(sql)}
    cursor.execute("""
        SELECT
            OBJECT_SCHEMA_NAME(fk.parent_object_id)    AS schema_name,
            OBJECT_NAME(fk.parent_object_id)           AS table_name,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS column_name
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc
            ON fk.object_id = fkc.constraint_object_id
        WHERE NOT EXISTS (
            SELECT 1 FROM sys.index_columns ic
            JOIN sys.indexes i ON ic.object_id=i.object_id AND ic.index_id=i.index_id
            WHERE ic.object_id = fkc.parent_object_id
              AND ic.column_id = fkc.parent_column_id
              AND ic.index_column_id = 1
        )
    """)
    recs = []
    for schema, tname, col in cursor.fetchall():
        if tables_in_sql and tname.lower() not in tables_in_sql:
            continue
        recs.append({
            "table":    f"{schema}.{tname}",
            "columns":  [col],
            "reason":   f"FK column '[{col}]' has no supporting index — slow joins likely",
            "ddl":      f"CREATE INDEX IX_{tname}_{col} ON [{schema}].[{tname}] ([{col}]);",
            "estimated_benefit": "Medium-High",
        })
    return recs


def _mssql_infer_from_sql(cursor, sql: str) -> list[dict]:
    recs = []
    upper = sql.upper()
    where_cols = re.findall(r'WHERE\s+(?:\w+\.)?(\w+)\s*[=<>!]', upper)
    order_cols  = re.findall(r'ORDER\s+BY\s+(?:\w+\.)?(\w+)', upper)
    tables = _extract_tables(sql)
    if not tables:
        return recs
    schema, tname = _split_schema_mssql(tables[0])
    for col in set(where_cols):
        if not _mssql_index_exists(cursor, schema, tname, col):
            recs.append({
                "table":    f"{schema}.{tname}",
                "columns":  [col.lower()],
                "reason":   f"WHERE column '[{col.lower()}]' has no index",
                "ddl":      f"CREATE INDEX IX_{tname}_{col.lower()} ON [{schema}].[{tname}] ([{col.lower()}]);",
                "estimated_benefit": "High",
            })
    for col in set(order_cols):
        if not _mssql_index_exists(cursor, schema, tname, col):
            recs.append({
                "table":    f"{schema}.{tname}",
                "columns":  [col.lower()],
                "reason":   f"ORDER BY column '[{col.lower()}]' has no index",
                "ddl":      f"CREATE INDEX IX_{tname}_{col.lower()} ON [{schema}].[{tname}] ([{col.lower()}]);",
                "estimated_benefit": "Medium",
            })
    return recs


def _mssql_index_exists(cursor, schema: str, table: str, column: str) -> bool:
    cursor.execute("""
        SELECT 1
        FROM sys.indexes i
        JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id
        JOIN sys.columns c        ON ic.object_id=c.object_id AND ic.column_id=c.column_id
        WHERE OBJECT_SCHEMA_NAME(i.object_id) = ?
          AND OBJECT_NAME(i.object_id) = ?
          AND c.name = ?
    """, (schema, table, column))
    return cursor.fetchone() is not None
