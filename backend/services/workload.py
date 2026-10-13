"""Workload capture + replay, folded in from the standalone WorkloadReplayer.

Capture: top-N queries by total time from pg_stat_statements / dm_exec_query_stats.
Replay:  run a captured workload against a target connection with configurable
         iterations × concurrency, then compare against baseline timings.
"""
import json
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from database import get_conn
from services.connection_manager import get_connection, open_connection
from services.db_adapter import get_adapter

WRITE_RE = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)
WRITE_BLOCK_MSG = "blocked by safe mode (write/DDL statement)"


def _is_write(sql: str) -> bool:
    return bool(WRITE_RE.match(sql))


# ── Capture ──────────────────────────────────────────────────────────────────

def capture_workload(source_conn_id: str, name: str, limit: int = 50) -> dict:
    conn, adapter, cfg = open_connection(source_conn_id)
    db_type = cfg["db_type"]
    ph = adapter.placeholder
    try:
        if db_type == "postgres":
            exists = adapter.cursor_fetchall_dicts(
                conn, "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements') AS ok")
            if not exists[0]["ok"]:
                raise RuntimeError(
                    "pg_stat_statements is not enabled on this database. Run "
                    "CREATE EXTENSION pg_stat_statements; and add it to "
                    "shared_preload_libraries, then restart PostgreSQL.")
            rows = adapter.cursor_fetchall_dicts(conn, f"""
                SELECT query AS sql, calls, mean_exec_time AS mean_ms,
                       total_exec_time AS total_ms
                FROM pg_stat_statements
                WHERE query NOT ILIKE '%%pg_stat_statements%%'
                  AND query NOT ILIKE '%%pg_stat_activity%%'
                ORDER BY total_exec_time DESC
                LIMIT {ph}
            """, (limit,))
        else:
            rows = adapter.cursor_fetchall_dicts(conn, f"""
                SELECT TOP ({limit})
                    SUBSTRING(qt.text, (qs.statement_start_offset/2)+1,
                        ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(qt.text)
                          ELSE qs.statement_end_offset END - qs.statement_start_offset)/2)+1) AS sql,
                    qs.execution_count AS calls,
                    (qs.total_elapsed_time / 1000.0) / NULLIF(qs.execution_count, 0) AS mean_ms,
                    qs.total_elapsed_time / 1000.0 AS total_ms
                FROM sys.dm_exec_query_stats qs
                CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
                WHERE qt.text NOT LIKE '%%dm_exec_query_stats%%'
                ORDER BY qs.total_elapsed_time DESC
            """)
    finally:
        conn.close()

    queries = [
        {"sql": (r.get("sql") or "").strip(),
         "calls": int(r.get("calls") or 0),
         "mean_ms": float(r.get("mean_ms") or 0),
         "total_ms": float(r.get("total_ms") or 0)}
        for r in rows if (r.get("sql") or "").strip()
    ]
    wid = uuid.uuid4().hex[:12]
    with get_conn() as db:
        db.execute(
            "INSERT INTO workloads (id, name, db_type, source_name, query_count, captured_at, queries_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (wid, name, db_type, cfg["name"], len(queries),
             datetime.now(timezone.utc).isoformat(), json.dumps(queries)),
        )
    return {"id": wid, "name": name, "db_type": db_type,
            "query_count": len(queries), "queries": queries}


def list_workloads() -> list[dict]:
    with get_conn() as db:
        rows = db.execute(
            "SELECT id, name, db_type, source_name, query_count, captured_at"
            " FROM workloads ORDER BY captured_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_workload(wid: str) -> dict | None:
    with get_conn() as db:
        row = db.execute("SELECT * FROM workloads WHERE id=?", (wid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["queries"] = json.loads(d.pop("queries_json"))
    return d


def delete_workload(wid: str):
    with get_conn() as db:
        db.execute("DELETE FROM workloads WHERE id=?", (wid,))


# ── Replay ───────────────────────────────────────────────────────────────────

def _run_once(adapter, cfg: dict, sql: str) -> dict:
    conn = adapter.open(cfg)
    try:
        cur = conn.cursor()
        start = time.perf_counter()
        try:
            cur.execute(sql)
            try:
                while True:
                    if cur.description is None:
                        break
                    cur.fetchall()
                    if not cur.nextset():
                        break
            except Exception:
                pass
            return {"ms": (time.perf_counter() - start) * 1000, "error": None}
        except Exception as e:  # noqa: BLE001
            return {"ms": (time.perf_counter() - start) * 1000, "error": str(e)[:300]}
        finally:
            try:
                cur.close()
            except Exception:
                pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def replay_workload(workload: dict, target_conn_id: str, iterations: int = 3,
                    concurrency: int = 4, safe_mode: bool = True) -> dict:
    target_cfg = get_connection(target_conn_id)
    if not target_cfg:
        raise ValueError("Target connection not found")
    if target_cfg["db_type"] != workload["db_type"]:
        raise ValueError(
            f"Engine mismatch: workload is {workload['db_type']}, "
            f"target is {target_cfg['db_type']}")
    adapter = get_adapter(target_cfg["db_type"])

    # connectivity check
    _run_once(adapter, target_cfg, "SELECT 1")

    queries = workload["queries"]
    tasks = [(qi, q) for qi, q in enumerate(queries)
             for _ in range(max(1, iterations))]

    def work(item):
        qi, q = item
        sql = q["sql"]
        if safe_mode and _is_write(sql):
            return qi, {"ms": 0.0, "error": WRITE_BLOCK_MSG, "blocked": True}
        r = _run_once(adapter, target_cfg, sql)
        r["blocked"] = False
        return qi, r

    per_query: dict[int, list] = {i: [] for i in range(len(queries))}
    with ThreadPoolExecutor(max_workers=max(1, min(concurrency, 32))) as ex:
        for qi, r in ex.map(work, tasks):
            per_query[qi].append(r)

    results = []
    for qi, q in enumerate(queries):
        runs = per_query[qi]
        ok = [r for r in runs if not r["error"]]
        errs = [r for r in runs if r["error"] and not r.get("blocked")]
        blocked = [r for r in runs if r.get("blocked")]
        ms_vals = [r["ms"] for r in ok]
        base = q.get("mean_ms") or 0
        mean = sum(ms_vals) / len(ms_vals) if ms_vals else 0.0
        delta = (mean - base) / base * 100 if base > 0 and mean > 0 else None
        if errs and not ok:
            status = "failed"
        elif blocked and not ok:
            status = "blocked"
        elif delta is not None and delta >= 50:
            status = "slower"
        elif errs:
            status = "errors"
        else:
            status = "ok"
        results.append({
            "sql": q["sql"][:500],
            "baseline_mean_ms": round(base, 3),
            "baseline_calls": q.get("calls", 0),
            "runs": len(ok), "errors": len(errs), "blocked": len(blocked),
            "replay_mean_ms": round(mean, 3),
            "replay_min_ms": round(min(ms_vals), 3) if ms_vals else 0,
            "replay_max_ms": round(max(ms_vals), 3) if ms_vals else 0,
            "delta_pct": round(delta, 1) if delta is not None else None,
            "status": status,
            "first_error": errs[0]["error"] if errs else None,
        })

    summary = {k: sum(1 for r in results if r["status"] == k)
               for k in ("ok", "slower", "failed", "errors", "blocked")}
    summary["total"] = len(results)
    return {"summary": summary, "results": results,
            "target": target_cfg["name"], "iterations": iterations,
            "concurrency": concurrency, "safe_mode": safe_mode}
