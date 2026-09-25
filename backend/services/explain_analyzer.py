"""
EXPLAIN / execution-plan runner.

PostgreSQL  — EXPLAIN (FORMAT JSON, [ANALYZE], [BUFFERS])
MSSQL       — SET SHOWPLAN_ALL ON  (estimated)
              SET STATISTICS PROFILE ON (actual, runs the query)
"""
from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from services.connection_manager import open_connection


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_explain(conn_id: str, sql: str, analyze: bool, buffers: bool, verbose: bool) -> dict:
    conn, adapter, cfg = open_connection(conn_id)
    try:
        if cfg["db_type"] == "postgres":
            return _pg_explain(conn, sql, analyze, buffers, verbose)
        elif cfg["db_type"] == "mysql":
            return _mysql_explain(conn, sql, analyze)
        else:
            return _mssql_explain(conn, sql, analyze)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
def _pg_explain(conn, sql: str, analyze: bool, buffers: bool, verbose: bool) -> dict:
    options = ["FORMAT JSON"]
    if analyze:
        options.append("ANALYZE")
    if buffers and analyze:
        options.append("BUFFERS")
    if verbose:
        options.append("VERBOSE")

    explain_sql = f"EXPLAIN ({', '.join(options)}) {sql}"
    with conn.cursor() as cur:
        cur.execute(explain_sql)
        plan_json = cur.fetchone()[0]

    if isinstance(plan_json, str):
        plan_json = json.loads(plan_json)

    summary = _pg_summarize(plan_json)
    return {"plan": plan_json, "summary": summary, "dialect": "postgres"}


def _pg_summarize(plan: list) -> dict:
    root = plan[0].get("Plan", {})
    warnings: list = []
    _pg_walk(root, warnings)
    return {
        "total_cost":        root.get("Total Cost"),
        "startup_cost":      root.get("Startup Cost"),
        "plan_rows":         root.get("Plan Rows"),
        "node_type":         root.get("Node Type"),
        "actual_total_time": root.get("Actual Total Time"),
        "actual_rows":       root.get("Actual Rows"),
        "warnings":          warnings,
    }


def _pg_walk(node: dict, warnings: list):
    node_type      = node.get("Node Type", "")
    rows_estimate  = node.get("Plan Rows", 1)
    rows_actual    = node.get("Actual Rows")

    if rows_actual is not None and rows_estimate > 0:
        ratio = rows_actual / rows_estimate
        if ratio > 10 or ratio < 0.1:
            warnings.append({
                "type":      "row_estimate_off",
                "node":      node_type,
                "estimated": rows_estimate,
                "actual":    rows_actual,
                "message":   f"{node_type}: row estimate off by {ratio:.1f}x — run ANALYZE to refresh statistics",
            })

    if node_type == "Seq Scan":
        relation = node.get("Relation Name", "?")
        warnings.append({
            "type":     "seq_scan",
            "node":     node_type,
            "relation": relation,
            "message":  f"Sequential scan on '{relation}' — consider an index if this table is large",
        })

    if node_type in ("Hash Join", "Nested Loop") and node.get("Total Cost", 0) > 10_000:
        warnings.append({
            "type":    "expensive_join",
            "node":    node_type,
            "cost":    node.get("Total Cost"),
            "message": f"Expensive {node_type} (cost {node.get('Total Cost'):.0f}) — verify join columns are indexed",
        })

    for child_key in ("Plans", "InitPlan", "SubPlan"):
        for child in node.get(child_key, []):
            _pg_walk(child, warnings)


# ---------------------------------------------------------------------------
# MSSQL
# ---------------------------------------------------------------------------
def _mssql_explain(conn, sql: str, analyze: bool) -> dict:
    """
    Estimated plan  → SET SHOWPLAN_ALL ON   (does NOT execute the query)
    Actual plan     → SET STATISTICS PROFILE ON (DOES execute the query)
    Both return tabular rows that we convert to a unified tree structure.
    """
    cursor = conn.cursor()

    if analyze:
        cursor.execute("SET STATISTICS PROFILE ON")
    else:
        cursor.execute("SET SHOWPLAN_ALL ON")

    cursor.execute(sql)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

    # Turn off after reading — separate statement
    if analyze:
        # STATISTICS PROFILE returns two result sets: the data, then the profile
        while cursor.nextset():
            profile_rows = cursor.fetchall()
            profile_cols = [d[0] for d in cursor.description]
            rows = profile_rows
            cols = profile_cols
        cursor.execute("SET STATISTICS PROFILE OFF")
    else:
        cursor.execute("SET SHOWPLAN_ALL OFF")

    plan_rows = [dict(zip(cols, r)) for r in rows]
    tree, summary = _mssql_build_tree(plan_rows, analyze)
    return {"plan": tree, "summary": summary, "dialect": "mssql"}


def _mssql_build_tree(rows: list[dict], actual: bool) -> tuple[list, dict]:
    """
    SHOWPLAN_ALL / STATISTICS PROFILE rows have NodeId + Parent columns.
    Build a nested tree similar to PostgreSQL's JSON plan.
    """
    nodes: dict[int, dict] = {}
    for r in rows:
        node_id = r.get("NodeId") or r.get("Nodeid") or 0
        node = {
            "Node Type":    (r.get("PhysicalOp") or r.get("LogicalOp") or "").strip(),
            "Logical Op":   (r.get("LogicalOp") or "").strip(),
            "Total Cost":   _safe_float(r.get("TotalSubtreeCost")),
            "Estimate CPU": _safe_float(r.get("EstimateCPU")),
            "Estimate IO":  _safe_float(r.get("EstimateIO")),
            "Plan Rows":    _safe_float(r.get("EstimateRows")),
            "Parallel":     r.get("Parallel", 0),
            "Description":  (r.get("Argument") or r.get("StmtText") or "").strip(),
            "Plans":        [],
            "_parent":      r.get("Parent"),
            "_id":          node_id,
        }
        if actual:
            node["Actual Rows"]       = _safe_float(r.get("Rows"))
            node["Actual Executions"] = _safe_float(r.get("Executes"))
        nodes[node_id] = node

    roots = []
    for node in nodes.values():
        parent_id = node.pop("_parent")
        node.pop("_id")
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id]["Plans"].append(node)
        else:
            roots.append(node)

    warnings = _mssql_warnings(roots[0] if roots else {})
    root = roots[0] if roots else {}
    summary = {
        "total_cost":        root.get("Total Cost"),
        "startup_cost":      None,
        "plan_rows":         root.get("Plan Rows"),
        "node_type":         root.get("Node Type"),
        "actual_total_time": None,
        "actual_rows":       root.get("Actual Rows"),
        "warnings":          warnings,
    }
    return [{"Plan": root}], summary


def _mssql_warnings(node: dict) -> list[dict]:
    warnings = []
    _mssql_walk(node, warnings)
    return warnings


def _mssql_walk(node: dict, warnings: list):
    node_type = node.get("Node Type", "")
    desc      = node.get("Description", "")

    if "Table Scan" in node_type or "Clustered Index Scan" in node_type:
        warnings.append({
            "type":    "table_scan",
            "node":    node_type,
            "message": f"{node_type}: full scan detected — consider a covering index",
        })

    est  = node.get("Plan Rows", 1) or 1
    act  = node.get("Actual Rows")
    if act is not None and est > 0:
        ratio = act / est
        if ratio > 10 or ratio < 0.1:
            warnings.append({
                "type":      "row_estimate_off",
                "node":      node_type,
                "estimated": est,
                "actual":    act,
                "message":   f"{node_type}: row estimate off by {ratio:.1f}x — update statistics",
            })

    if node_type in ("Hash Match", "Nested Loops") and (node.get("Total Cost") or 0) > 10_000:
        warnings.append({
            "type":    "expensive_join",
            "node":    node_type,
            "message": f"Expensive {node_type} join (cost {node.get('Total Cost'):.0f})",
        })

    if "KEY LOOKUP" in node_type.upper():
        warnings.append({
            "type":    "key_lookup",
            "node":    node_type,
            "message": "Key Lookup detected — the non-clustered index doesn't cover all selected columns; add INCLUDE columns",
        })

    for child in node.get("Plans", []):
        _mssql_walk(child, warnings)


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
def _mysql_explain(conn, sql: str, analyze: bool) -> dict:
    cursor = conn.cursor()
    if analyze:
        try:
            cursor.execute(f"EXPLAIN ANALYZE {sql}")
            rows = cursor.fetchall()
            analyze_text = "\n".join(str(r[0]) for r in rows)
            warnings = []
            if "Full table scan" in analyze_text or "ALL" in analyze_text:
                warnings.append({"type": "table_scan", "node": "MySQL", "message": "Full table scan detected — consider adding an index"})
            return {
                "plan": [{"Plan": {"Node Type": "MySQL Query", "Description": analyze_text, "Plans": []}}],
                "summary": {"total_cost": None, "startup_cost": None, "plan_rows": None,
                            "node_type": "MySQL", "actual_total_time": None, "actual_rows": None, "warnings": warnings},
                "dialect": "mysql",
            }
        except Exception:
            pass
    cursor.execute(f"EXPLAIN FORMAT=JSON {sql}")
    row = cursor.fetchone()
    plan_json = json.loads(row[0])
    tree = _mysql_json_to_tree(plan_json)
    warnings = _mysql_warnings(plan_json)
    cost = _mysql_extract_cost(plan_json)
    return {
        "plan": [{"Plan": tree}],
        "summary": {"total_cost": cost, "startup_cost": None, "plan_rows": None,
                    "node_type": "MySQL", "actual_total_time": None, "actual_rows": None, "warnings": warnings},
        "dialect": "mysql",
    }


def _mysql_extract_cost(plan: dict) -> float | None:
    try:
        return float(plan["query_block"]["cost_info"]["query_cost"])
    except Exception:
        return None


def _mysql_json_to_tree(plan: dict) -> dict:
    block = plan.get("query_block", {})
    cost = block.get("cost_info", {}).get("query_cost")
    children = []
    for key in ("table", "nested_loop", "union_result", "ordering_operation", "grouping_operation"):
        val = block.get(key)
        if val:
            if isinstance(val, list):
                for item in val:
                    tbl = item.get("table") or item
                    children.append(_mysql_table_to_node(tbl))
            else:
                children.append(_mysql_table_to_node(val))
    return {
        "Node Type": "MySQL Query",
        "Total Cost": float(cost) if cost else None,
        "Plans": children,
    }


def _mysql_table_to_node(tbl: dict) -> dict:
    cost_info = tbl.get("cost_info", {})
    read_cost = cost_info.get("read_cost") or cost_info.get("prefix_cost")
    return {
        "Node Type": tbl.get("access_type", "table").upper(),
        "Relation Name": tbl.get("table_name", "?"),
        "Total Cost": float(read_cost) if read_cost else None,
        "Plan Rows": tbl.get("rows_examined_per_scan"),
        "Key": tbl.get("key"),
        "Possible Keys": tbl.get("possible_keys"),
        "Plans": [],
    }


def _mysql_warnings(plan: dict) -> list[dict]:
    warnings = []
    block = plan.get("query_block", {})
    for key in ("table", "nested_loop"):
        val = block.get(key)
        if not val:
            continue
        tables = val if isinstance(val, list) else [{"table": val}]
        for item in tables:
            tbl = item.get("table") or item
            access = tbl.get("access_type", "")
            tname = tbl.get("table_name", "?")
            if access == "ALL":
                warnings.append({"type": "seq_scan", "node": "Full Scan", "relation": tname,
                                  "message": f"Full table scan on '{tname}' — add an index on filter/join columns"})
    return warnings


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
