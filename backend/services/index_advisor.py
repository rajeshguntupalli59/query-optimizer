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
        elif cfg["db_type"] == "mysql":
            return _mysql_recommend(conn, sql)
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


def _tables_bare(sql: str) -> set[str]:
    """Bare lowercased table names from SQL — 'shop.orders' and '[dbo].[orders]'
    both become 'orders'. Used to match catalog (bare) names against whatever
    qualification style the user's SQL uses."""
    return {t.lower().replace("[", "").replace("]", "").split(".")[-1]
            for t in _extract_tables(sql)}


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
        recs.extend(_pg_index_hygiene(cur, sql))
    return _deduplicate(recs)


def _pg_index_hygiene(cur, sql: str) -> list[dict]:
    """Find unused and duplicate indexes on tables referenced by the SQL."""
    tables_bare = _tables_bare(sql)
    recs = []
    # Unused: non-PK, non-unique indexes with zero scans
    cur.execute("""
        SELECT s.schemaname, s.relname AS tablename, s.indexrelname AS indexname,
               pg_relation_size(s.indexrelid) AS bytes
        FROM pg_stat_user_indexes s
        JOIN pg_index i ON i.indexrelid = s.indexrelid
        WHERE s.idx_scan = 0 AND NOT i.indisunique AND NOT i.indisprimary
    """)
    for r in cur.fetchall():
        if tables_bare and r["tablename"].lower() not in tables_bare:
            continue
        kb = (r["bytes"] or 0) // 1024
        recs.append({
            "table": f"{r['schemaname']}.{r['tablename']}",
            "columns": [r["indexname"]],
            "reason": f"Index '{r['indexname']}' has never been scanned — dead weight on writes"
                      + (f" ({kb} KB reclaimable)" if kb else ""),
            "ddl": f"DROP INDEX {r['schemaname']}.{r['indexname']};",
            "estimated_benefit": "Medium — faster writes, less disk",
        })
    # Duplicates: same table + same leading column list, different names
    cur.execute("""
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    """)
    seen: dict[tuple, list] = {}
    for r in cur.fetchall():
        indexdef = r["indexdef"] or ""
        if "((" in indexdef:
            continue  # expression index — leave alone
        m = re.search(r"\(\s*([^()]+?)\s*\)", indexdef)
        if not m:
            continue
        cols = ",".join(c.strip().strip('"').split()[0] for c in m.group(1).split(","))
        inc = re.search(r"INCLUDE\s*\(([^)]+)\)", indexdef, re.I)
        key_cols = cols + ("+inc:" + inc.group(1) if inc else "")
        key = (r["schemaname"], r["tablename"], key_cols)
        seen.setdefault(key, []).append(r["indexname"])
    for (schema, table, key_cols), names in seen.items():
        if len(names) < 2:
            continue
        if tables_bare and table.lower() not in tables_bare:
            continue
        cols = key_cols.split("+inc:")[0]
        keep, *dupes = sorted(names)
        for d in dupes:
            recs.append({
                "table": f"{schema}.{table}",
                "columns": [d],
                "reason": f"Duplicate of '{keep}' on ({cols}) — same columns, extra write cost",
                "ddl": f"DROP INDEX {schema}.{d};",
                "estimated_benefit": "Medium — faster writes, less disk",
            })
    return recs


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
    tables_bare = _tables_bare(sql)
    recs = []
    for row in cur.fetchall():
        schema = row["table_schema"]
        tname  = row["table_name"]
        col    = row["column_name"]
        ftable = row["ftable"]
        if tname.lower() in tables_bare or ftable.lower() in tables_bare:
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col],
                "reason": f"FK column '{col}' has no index — can cause slow joins",
                "ddl": f"CREATE INDEX {_pg_index_name(tname, col)} ON {schema}.{tname} ({col});",
                "estimated_benefit": "Medium-High",
            })
    return recs


# Tokens that look like columns to the naive regexes below but are actually
# SQL keywords or literals — never recommend indexes on these.
_SQL_KEYWORDS = frozenset({
    "AND", "OR", "NOT", "NULL", "TRUE", "FALSE", "EXISTS", "BETWEEN", "LIKE",
    "IN", "IS", "AS", "ON", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END",
    "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
    "CROSS", "UNION", "ALL", "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
})


def _is_real_column(col: str) -> bool:
    return bool(col) and not col.isdigit() and col not in _SQL_KEYWORDS


def _pg_index_name(tname: str, col: str) -> str:
    """Deterministic, safe index name for advisor-generated DDL."""
    safe = re.sub(r"\W", "_", f"ix_{tname}_{col}".lower())
    return safe[:60]


def _pg_infer_from_sql(cur, sql: str) -> list[dict]:
    recs = []
    upper = sql.upper()
    where_cols = re.findall(r'WHERE\s+(?:\w+\.)?(\w+)\s*[=<>!]', upper)
    order_cols  = re.findall(r'ORDER\s+BY\s+(?:\w+\.)?(\w+)', upper)
    tables = _extract_tables(sql)
    if not tables:
        return recs
    schema, tname = _split_schema_pg(tables[0])
    for col in set(where_cols):
        if not _is_real_column(col):
            continue
        if not _pg_index_exists(cur, schema, tname, col.lower()):
            idx = _pg_index_name(tname, col.lower())
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col.lower()],
                "reason": f"WHERE column '{col.lower()}' has no index",
                "ddl": f"CREATE INDEX {idx} ON {schema}.{tname} ({col.lower()});",
                "estimated_benefit": "High",
            })
    for col in set(order_cols):
        if not _is_real_column(col):
            continue
        if not _pg_index_exists(cur, schema, tname, col.lower()):
            idx = _pg_index_name(tname, col.lower())
            recs.append({
                "table": f"{schema}.{tname}", "columns": [col.lower()],
                "reason": f"ORDER BY column '{col.lower()}' has no index",
                "ddl": f"CREATE INDEX {idx} ON {schema}.{tname} ({col.lower()});",
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
# MySQL
# ---------------------------------------------------------------------------
def _mysql_recommend(conn, sql: str) -> list[dict]:
    recs = []
    cursor = conn.cursor()
    recs.extend(_mysql_fk_without_index(cursor, sql, conn))
    recs.extend(_mysql_infer_from_sql(cursor, sql, conn))
    return _deduplicate(recs)


def _mysql_fk_without_index(cursor, sql: str, conn) -> list[dict]:
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    cursor.execute("""
        SELECT kcu.TABLE_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME
        FROM information_schema.KEY_COLUMN_USAGE kcu
        WHERE kcu.TABLE_SCHEMA = %s
          AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM information_schema.STATISTICS s
              WHERE s.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                AND s.TABLE_NAME = kcu.TABLE_NAME
                AND s.COLUMN_NAME = kcu.COLUMN_NAME
                AND s.SEQ_IN_INDEX = 1
          )
    """, (db_name,))
    tables_bare = _tables_bare(sql)
    recs = []
    for row in cursor.fetchall():
        tname, col, ref = row[0], row[1], row[2]
        if tables_bare and tname.lower() not in tables_bare and ref.lower() not in tables_bare:
            continue
        recs.append({
            "table": f"{db_name}.{tname}", "columns": [col],
            "reason": f"FK column '{col}' references '{ref}' but has no supporting index",
            "ddl": f"CREATE INDEX idx_{tname}_{col} ON `{tname}` (`{col}`);",
            "estimated_benefit": "Medium-High",
        })
    return recs


def _mysql_infer_from_sql(cursor, sql: str, conn) -> list[dict]:
    recs = []
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    upper = sql.upper()
    where_cols = re.findall(r'WHERE\s+(?:\w+\.)?(\w+)\s*[=<>!]', upper)
    order_cols  = re.findall(r'ORDER\s+BY\s+(?:\w+\.)?(\w+)', upper)
    tables = _extract_tables(sql)
    if not tables:
        return recs
    tname = tables[0].split(".")[-1]
    for col in set(where_cols):
        if not _mysql_index_exists(cursor, db_name, tname, col.lower()):
            recs.append({
                "table": f"{db_name}.{tname}", "columns": [col.lower()],
                "reason": f"WHERE column `{col.lower()}` has no index",
                "ddl": f"CREATE INDEX idx_{tname}_{col.lower()} ON `{tname}` (`{col.lower()}`);",
                "estimated_benefit": "High",
            })
    for col in set(order_cols):
        if not _mysql_index_exists(cursor, db_name, tname, col.lower()):
            recs.append({
                "table": f"{db_name}.{tname}", "columns": [col.lower()],
                "reason": f"ORDER BY column `{col.lower()}` has no index",
                "ddl": f"CREATE INDEX idx_{tname}_{col.lower()} ON `{tname}` (`{col.lower()}`);",
                "estimated_benefit": "Medium",
            })
    return recs


def _mysql_index_exists(cursor, db_name: str, table: str, column: str) -> bool:
    cursor.execute("""
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s LIMIT 1
    """, (db_name, table, column))
    return cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# MSSQL
# ---------------------------------------------------------------------------
def _mssql_recommend(conn, sql: str) -> list[dict]:
    recs = []
    cursor = conn.cursor()
    recs.extend(_mssql_missing_index_dmv(cursor, sql))
    recs.extend(_mssql_fk_without_index(cursor, sql))
    recs.extend(_mssql_infer_from_sql(cursor, sql))
    recs.extend(_mssql_index_hygiene(cursor, sql))
    return _deduplicate(recs)


def _mssql_index_hygiene(cursor, sql: str) -> list[dict]:
    """Unused and duplicate indexes on tables referenced by the SQL."""
    tables_bare = _tables_bare(sql)
    recs = []
    # Unused: no user seeks/scans/lookups, not PK/unique
    cursor.execute("""
        SELECT OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
               OBJECT_NAME(i.object_id) AS table_name,
               i.name AS index_name
        FROM sys.indexes i
        LEFT JOIN sys.dm_db_index_usage_stats u
          ON u.object_id = i.object_id AND u.index_id = i.index_id
         AND u.database_id = DB_ID()
        WHERE i.type_desc IN ('NONCLUSTERED', 'CLUSTERED')
          AND i.is_primary_key = 0 AND i.is_unique = 0
          AND COALESCE(u.user_seeks, 0) + COALESCE(u.user_scans, 0)
              + COALESCE(u.user_lookups, 0) = 0
    """)
    cols = [d[0] for d in cursor.description]
    for row in cursor.fetchall():
        r = dict(zip(cols, row))
        if not r["index_name"]:
            continue
        if tables_bare and r["table_name"].lower() not in tables_bare:
            continue
        recs.append({
            "table": f"{r['schema_name']}.{r['table_name']}",
            "columns": [r["index_name"]],
            "reason": f"Index '{r['index_name']}' has no user seeks/scans — dead weight on writes",
            "ddl": f"DROP INDEX [{r['index_name']}] ON [{r['schema_name']}].[{r['table_name']}];",
            "estimated_benefit": "Medium — faster writes, less disk",
        })
    # Duplicates: same key columns, different names
    cursor.execute("""
        SELECT OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
               OBJECT_NAME(i.object_id) AS table_name,
               i.name AS index_name,
               STRING_AGG(COL_NAME(ic.object_id, ic.column_id), ',')
                   WITHIN GROUP (ORDER BY ic.key_ordinal) AS cols
        FROM sys.indexes i
        JOIN sys.index_columns ic
          ON ic.object_id = i.object_id AND ic.index_id = i.index_id
         AND ic.is_included_column = 0
        WHERE i.name IS NOT NULL
        GROUP BY OBJECT_SCHEMA_NAME(i.object_id), OBJECT_NAME(i.object_id),
                 i.name, i.object_id, i.index_id
    """)
    cols = [d[0] for d in cursor.description]
    seen: dict[tuple, list] = {}
    for row in cursor.fetchall():
        r = dict(zip(cols, row))
        key = (r["schema_name"], r["table_name"], r["cols"])
        seen.setdefault(key, []).append(r["index_name"])
    for (schema, table, collist), names in seen.items():
        if len(names) < 2:
            continue
        if tables_bare and table.lower() not in tables_bare:
            continue
        keep, *dupes = sorted(names)
        for d in dupes:
            recs.append({
                "table": f"{schema}.{table}",
                "columns": [d],
                "reason": f"Duplicate of '{keep}' on ({collist}) — same columns, extra write cost",
                "ddl": f"DROP INDEX [{d}] ON [{schema}].[{table}];",
                "estimated_benefit": "Medium — faster writes, less disk",
            })
    return recs


def _mssql_missing_index_dmv(cursor, sql: str) -> list[dict]:
    """
    sys.dm_db_missing_index_details is populated by the query optimiser
    whenever it detects a missing index during compilation/execution.
    We surface the top entries for tables referenced in the user's SQL.
    """
    tables_bare = _tables_bare(sql)
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
        if tables_bare and tname not in tables_bare:
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
    tables_bare = _tables_bare(sql)
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
        if tables_bare and tname.lower() not in tables_bare:
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
        if not _is_real_column(col):
            continue
        if not _mssql_index_exists(cursor, schema, tname, col):
            recs.append({
                "table":    f"{schema}.{tname}",
                "columns":  [col.lower()],
                "reason":   f"WHERE column '[{col.lower()}]' has no index",
                "ddl":      f"CREATE INDEX IX_{tname}_{col.lower()} ON [{schema}].[{tname}] ([{col.lower()}]);",
                "estimated_benefit": "High",
            })
    for col in set(order_cols):
        if not _is_real_column(col):
            continue
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


# ---------------------------------------------------------------------------
# Index impact test — create the recommended index, measure before/after,
# then drop it again. PostgreSQL only for now.
# ---------------------------------------------------------------------------

_INDEX_NAME_RE = re.compile(
    r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?'
    r'["\']?([\w$]+)["\']?\s+ON',
    re.IGNORECASE,
)


def _pg_explain_stats(conn, sql: str) -> dict:
    """Return execution time (ms) and total cost for a SELECT via EXPLAIN ANALYZE."""
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
        plan = cur.fetchone()[0]
    if isinstance(plan, str):
        import json as _json
        plan = _json.loads(plan)
    root = plan[0].get("Plan", {})
    return {
        "execution_ms": root.get("Actual Total Time"),
        "total_cost":   root.get("Total Cost"),
        "node_type":    root.get("Node Type"),
    }


def test_index_impact(conn_id: str, ddl: str, sql: str) -> dict:
    """
    Measure a query before and after creating the recommended index,
    then drop the index. Returns the comparison.
    """
    first_word = (sql or "").strip().split(None, 1)
    if not first_word or first_word[0].upper() not in ("SELECT", "WITH"):
        raise ValueError("Impact test only runs SELECT/WITH queries (it executes them).")
    if not (ddl or "").strip().upper().startswith("CREATE"):
        raise ValueError("No CREATE INDEX statement to test.")

    m = _INDEX_NAME_RE.search(ddl)
    if m:
        index_name = m.group(1)
    else:
        # DDL without an explicit name (e.g. "CREATE INDEX ON t (c)") —
        # generate one so we can drop it afterwards.
        import secrets as _secrets
        index_name = f"qo_impact_{_secrets.token_hex(4)}"
        ddl = re.sub(r"CREATE(\s+UNIQUE)?\s+INDEX\s+",
                     rf"CREATE\1 INDEX {index_name} ", ddl,
                     count=1, flags=re.IGNORECASE)

    # Schema-qualify the DROP: the index lives in the table's schema, which is
    # usually not on the search_path, so an unqualified DROP would miss it.
    on_m = re.search(r"\bON\s+(?:\"?([\w$]+)\"?\.)?\"?([\w$]+)\"?", ddl, re.IGNORECASE)
    idx_schema = on_m.group(1) if on_m else None
    drop_target = f'"{idx_schema}"."{index_name}"' if idx_schema else f'"{index_name}"'

    conn, adapter, cfg = open_connection(conn_id)
    try:
        if cfg["db_type"] != "postgres":
            raise ValueError("Impact test is currently supported for PostgreSQL only.")
        conn.autocommit = True
        before = _pg_explain_stats(conn, sql)
        with conn.cursor() as cur:
            cur.execute(ddl)
        try:
            after = _pg_explain_stats(conn, sql)
        finally:
            with conn.cursor() as cur:
                cur.execute(f"DROP INDEX IF EXISTS {drop_target}")
    finally:
        conn.close()

    b_ms, a_ms = before["execution_ms"], after["execution_ms"]
    improvement = None
    if isinstance(b_ms, (int, float)) and isinstance(a_ms, (int, float)) and b_ms > 0:
        improvement = round((b_ms - a_ms) / b_ms * 100, 1)

    return {
        "index": index_name,
        "before": before,
        "after": after,
        "improvement_pct": improvement,
        "plan_changed": before["node_type"] != after["node_type"],
        "verdict": (
            "faster" if improvement is not None and improvement > 10 else
            "no meaningful change" if improvement is not None else
            "could not measure"
        ),
    }
