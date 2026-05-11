import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, DML


RULES: list[dict] = []


def _rule(severity: str, issue: str):
    def decorator(fn):
        RULES.append({"fn": fn, "severity": severity, "issue": issue})
        return fn
    return decorator


@_rule("high", "SELECT * used")
def check_select_star(sql: str, parsed) -> list[dict]:
    if re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
        return [{
            "issue": "SELECT * fetches all columns — specify only needed columns",
            "severity": "high",
            "original": "SELECT *",
            "suggestion": "List only the columns your application needs",
            "rewritten_sql": re.sub(r'SELECT\s+\*', 'SELECT col1, col2 /* specify columns */', sql, flags=re.IGNORECASE, count=1),
        }]
    return []


@_rule("high", "OR in WHERE clause can prevent index use")
def check_or_clause(sql: str, parsed) -> list[dict]:
    if re.search(r'\bOR\b', sql, re.IGNORECASE) and re.search(r'\bWHERE\b', sql, re.IGNORECASE):
        return [{
            "issue": "OR in WHERE can prevent index use — consider UNION ALL",
            "severity": "high",
            "original": "WHERE ... OR ...",
            "suggestion": "Replace OR with UNION ALL to allow each branch to use its own index",
            "rewritten_sql": None,
        }]
    return []


@_rule("high", "Function on indexed column disables index")
def check_function_on_column(sql: str, parsed) -> list[dict]:
    pattern = re.compile(r'WHERE\s+\w+\s*\(\s*(\w+\.\w+|\w+)\s*\)', re.IGNORECASE)
    matches = pattern.findall(sql)
    results = []
    for m in matches:
        results.append({
            "issue": f"Function applied to column '{m}' in WHERE — index on that column cannot be used",
            "severity": "high",
            "original": f"WHERE func({m}) = ...",
            "suggestion": f"Rewrite to apply the function to the literal side, or use a function-based index",
            "rewritten_sql": None,
        })
    return results


@_rule("medium", "LIKE with leading wildcard prevents index")
def check_leading_wildcard(sql: str, parsed) -> list[dict]:
    if re.search(r"LIKE\s+'%", sql, re.IGNORECASE):
        return [{
            "issue": "LIKE '%...' with a leading wildcard cannot use a B-tree index",
            "severity": "medium",
            "original": "LIKE '%value'",
            "suggestion": "Use a full-text index (GIN + tsvector) or reverse the string and use LIKE 'eulav%'",
            "rewritten_sql": None,
        }]
    return []


@_rule("medium", "DISTINCT may indicate missing GROUP BY or duplicate rows")
def check_distinct(sql: str, parsed) -> list[dict]:
    if re.search(r'\bSELECT\s+DISTINCT\b', sql, re.IGNORECASE):
        return [{
            "issue": "SELECT DISTINCT forces a sort/hash operation — verify duplicates are expected",
            "severity": "medium",
            "original": "SELECT DISTINCT",
            "suggestion": "If duplicates come from a JOIN, fix the join condition. If intentional, consider GROUP BY for clarity.",
            "rewritten_sql": None,
        }]
    return []


@_rule("medium", "NOT IN with subquery is slow on NULLs")
def check_not_in(sql: str, parsed) -> list[dict]:
    if re.search(r'\bNOT\s+IN\s*\(SELECT\b', sql, re.IGNORECASE):
        return [{
            "issue": "NOT IN (SELECT ...) behaves incorrectly when the subquery contains NULLs",
            "severity": "medium",
            "original": "NOT IN (SELECT ...)",
            "suggestion": "Replace with NOT EXISTS or a LEFT JOIN ... WHERE right.id IS NULL",
            "rewritten_sql": re.sub(
                r'WHERE\s+(\w+(?:\.\w+)?)\s+NOT\s+IN\s*\(SELECT\s+(\w+(?:\.\w+)?)\s+FROM\s+(\w+(?:\.\w+)?)',
                r'WHERE NOT EXISTS (SELECT 1 FROM \3 WHERE \2 = \1',
                sql, flags=re.IGNORECASE, count=1
            ),
        }]
    return []


@_rule("medium", "Implicit cross join (comma-separated tables)")
def check_cross_join(sql: str, parsed) -> list[dict]:
    if re.search(r'FROM\s+\w+\s*,\s*\w+', sql, re.IGNORECASE):
        return [{
            "issue": "Comma-separated table list creates an implicit CROSS JOIN",
            "severity": "medium",
            "original": "FROM table1, table2",
            "suggestion": "Use explicit JOIN ... ON syntax to make the join condition clear",
            "rewritten_sql": None,
        }]
    return []


@_rule("low", "IN list with many literals — consider a temp table")
def check_large_in_list(sql: str, parsed) -> list[dict]:
    matches = re.findall(r'\bIN\s*\(([^)]+)\)', sql, re.IGNORECASE)
    results = []
    for m in matches:
        items = [x.strip() for x in m.split(",")]
        if len(items) > 50:
            results.append({
                "issue": f"IN list has {len(items)} literals — may cause plan instability",
                "severity": "low",
                "original": f"IN ({m[:60]}...)",
                "suggestion": "Load values into a temp table and JOIN against it",
                "rewritten_sql": None,
            })
    return results


@_rule("low", "OFFSET pagination is slow on large tables")
def check_offset(sql: str, parsed) -> list[dict]:
    if re.search(r'\bOFFSET\s+\d{4,}\b', sql, re.IGNORECASE):
        return [{
            "issue": "Large OFFSET causes the database to scan and discard many rows",
            "severity": "low",
            "original": "LIMIT n OFFSET large_number",
            "suggestion": "Use keyset (cursor) pagination: WHERE id > last_seen_id ORDER BY id LIMIT n",
            "rewritten_sql": None,
        }]
    return []


def rewrite_query(sql: str) -> list[dict]:
    parsed = sqlparse.parse(sql.strip())
    suggestions = []
    for rule in RULES:
        try:
            results = rule["fn"](sql, parsed)
            suggestions.extend(results)
        except Exception:
            pass
    return suggestions
