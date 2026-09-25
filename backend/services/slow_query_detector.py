"""
Slow query detection.

PostgreSQL  — pg_stat_statements (requires extension)
MSSQL       — sys.dm_exec_query_stats + sys.dm_exec_sql_text (built-in DMVs)
"""
from __future__ import annotations
from services.connection_manager import open_connection


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def get_slow_queries(conn_id: str, limit: int = 20, min_calls: int = 1) -> list[dict]:
    conn, adapter, cfg = open_connection(conn_id)
    try:
        if cfg["db_type"] == "postgres":
            return _pg_slow_queries(conn, limit, min_calls)
        elif cfg["db_type"] == "mysql":
            return _mysql_slow_queries(conn, limit, min_calls)
        else:
            return _mssql_slow_queries(conn, limit, min_calls)
    finally:
        conn.close()


def reset_stats(conn_id: str) -> dict:
    conn, adapter, cfg = open_connection(conn_id)
    try:
        if cfg["db_type"] == "postgres":
            return _pg_reset(conn)
        elif cfg["db_type"] == "mysql":
            return _mysql_reset(conn)
        else:
            return _mssql_reset(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
def _pg_slow_queries(conn, limit: int, min_calls: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_available_extensions WHERE name='pg_stat_statements'")
        if not cur.fetchone():
            return [{"error": "pg_stat_statements extension is not available on this server"}]

        cur.execute("SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements'")
        if not cur.fetchone():
            return [{"error": "pg_stat_statements is not enabled. Run: CREATE EXTENSION pg_stat_statements;"}]

        cur.execute("SHOW server_version_num")
        version = int(cur.fetchone()[0])
        time_col = "total_exec_time" if version >= 130000 else "total_time"
        mean_col = "mean_exec_time"  if version >= 130000 else "mean_time"
        min_col  = "min_exec_time"   if version >= 130000 else "min_time"
        max_col  = "max_exec_time"   if version >= 130000 else "max_time"

        cur.execute(
            f"""
            SELECT
                query,
                calls,
                {time_col}  AS total_time_ms,
                {mean_col}  AS mean_time_ms,
                {min_col}   AS min_time_ms,
                {max_col}   AS max_time_ms,
                rows,
                100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            WHERE calls >= %s
            ORDER BY {mean_col} DESC
            LIMIT %s
            """,
            (min_calls, limit),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _pg_reset(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_stat_statements_reset()")
        conn.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
def _mysql_slow_queries(conn, limit: int, min_calls: int) -> list[dict]:
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            SELECT
                DIGEST_TEXT                                AS query,
                COUNT_STAR                                 AS calls,
                SUM_TIMER_WAIT   / 1000000000.0            AS total_time_ms,
                AVG_TIMER_WAIT   / 1000000000.0            AS mean_time_ms,
                MIN_TIMER_WAIT   / 1000000000.0            AS min_time_ms,
                MAX_TIMER_WAIT   / 1000000000.0            AS max_time_ms,
                SUM_ROWS_SENT                              AS rows,
                NULL                                       AS hit_percent
            FROM performance_schema.events_statements_summary_by_digest
            WHERE DIGEST_TEXT IS NOT NULL
              AND COUNT_STAR >= {min_calls}
            ORDER BY SUM_TIMER_WAIT DESC
            LIMIT {limit}
        """)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception as e:
        return [{"error": f"performance_schema not available: {e}"}]


def _mysql_reset(conn) -> dict:
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE performance_schema.events_statements_summary_by_digest")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# MSSQL
# ---------------------------------------------------------------------------
def _mssql_slow_queries(conn, limit: int, min_calls: int) -> list[dict]:
    """
    Uses sys.dm_exec_query_stats (built-in, no extension needed).
    Times are in microseconds in the DMV; we convert to milliseconds.
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP ({limit})
            SUBSTRING(
                qt.text,
                (qs.statement_start_offset / 2) + 1,
                ((CASE qs.statement_end_offset
                    WHEN -1 THEN DATALENGTH(qt.text)
                    ELSE qs.statement_end_offset
                  END - qs.statement_start_offset) / 2) + 1
            )                                                    AS query,
            qs.execution_count                                   AS calls,
            qs.total_elapsed_time / 1000.0                       AS total_time_ms,
            qs.total_elapsed_time / qs.execution_count / 1000.0  AS mean_time_ms,
            qs.min_elapsed_time  / 1000.0                        AS min_time_ms,
            qs.max_elapsed_time  / 1000.0                        AS max_time_ms,
            qs.total_rows / qs.execution_count                   AS rows,
            (qs.total_logical_reads - qs.total_physical_reads) * 100.0
                / NULLIF(qs.total_logical_reads, 0)              AS hit_percent
        FROM sys.dm_exec_query_stats qs
        CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
        WHERE qs.execution_count >= {min_calls}
          AND qt.text NOT LIKE '%dm_exec_query_stats%'
        ORDER BY mean_time_ms DESC
    """)
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _mssql_reset(conn) -> dict:
    """
    DBCC FREEPROCCACHE clears the plan cache, which also resets DMV counters.
    Requires ALTER SERVER STATE permission.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("DBCC FREEPROCCACHE")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
