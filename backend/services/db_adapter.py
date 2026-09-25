"""
Database adapter layer.
Each adapter exposes open(cfg) -> connection and is the single place
where driver-specific code lives. Services import get_adapter() and
never import psycopg2 / pyodbc directly.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class DBAdapter(ABC):
    @abstractmethod
    def open(self, cfg: dict):
        """Return an open DBAPI-2 connection."""

    @abstractmethod
    def cursor_fetchall_dicts(self, conn, sql: str, params: tuple = ()) -> list[dict]:
        """Execute sql, return rows as list-of-dicts."""

    @abstractmethod
    def server_version(self, conn) -> int:
        """Return a comparable integer (e.g. 150002 for MSSQL 2019, 140005 for PG 14.0.5)."""

    @property
    @abstractmethod
    def default_port(self) -> int: ...

    @property
    @abstractmethod
    def placeholder(self) -> str:
        """Positional placeholder: %s (psycopg2) or ? (pyodbc)."""


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------
class PostgreSQLAdapter(DBAdapter):
    default_port  = 5432
    placeholder   = "%s"

    def open(self, cfg: dict):
        import psycopg2
        return psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["database"],
            user=cfg["username"],
            password=cfg["password"],
            connect_timeout=10,
        )

    def cursor_fetchall_dicts(self, conn, sql: str, params: tuple = ()) -> list[dict]:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or None)
            return [dict(r) for r in cur.fetchall()]

    def server_version(self, conn) -> int:
        with conn.cursor() as cur:
            cur.execute("SHOW server_version_num")
            return int(cur.fetchone()[0])


# ---------------------------------------------------------------------------
# Microsoft SQL Server
# ---------------------------------------------------------------------------
class MSSQLAdapter(DBAdapter):
    default_port  = 1433
    placeholder   = "?"

    # Ordered preference list of ODBC drivers (latest first)
    _DRIVERS = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ]

    def _driver(self) -> str:
        try:
            import pyodbc
            available = [d for d in pyodbc.drivers() if "SQL Server" in d]
            for preferred in self._DRIVERS:
                if preferred in available:
                    return preferred
            if available:
                return available[0]
        except Exception:
            pass
        return "ODBC Driver 17 for SQL Server"

    def open(self, cfg: dict):
        import pyodbc
        driver = self._driver()
        host = cfg["host"]
        # Named instances (host\INSTANCE) must not have port appended
        server = host if "\\" in host else f"{host},{cfg['port']}"
        auth = (
            "Trusted_Connection=yes;"
            if not cfg.get("username")
            else f"UID={cfg['username']};PWD={cfg['password']};"
        )
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={cfg['database']};"
            + auth +
            "TrustServerCertificate=yes;"
            "Connection Timeout=10;"
        )
        return pyodbc.connect(conn_str, autocommit=True)

    def cursor_fetchall_dicts(self, conn, sql: str, params: tuple = ()) -> list[dict]:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def server_version(self, conn) -> int:
        cursor = conn.cursor()
        cursor.execute("SELECT SERVERPROPERTY('ProductVersion')")
        ver_str = cursor.fetchone()[0]          # e.g. "15.0.2000.5"
        parts = ver_str.split(".")
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major * 10000 + minor * 100 + patch   # e.g. 150000


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
class MySQLAdapter(DBAdapter):
    default_port  = 3306
    placeholder   = "%s"

    def open(self, cfg: dict):
        import pymysql
        return pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["username"],
            password=cfg["password"],
            connect_timeout=10,
            autocommit=True,
        )

    def cursor_fetchall_dicts(self, conn, sql: str, params: tuple = ()) -> list[dict]:
        cursor = conn.cursor(pymysql.cursors.DictCursor) if hasattr(conn, 'cursor') else conn.cursor()
        cursor.execute(sql, params or None)
        return [dict(r) for r in cursor.fetchall()]

    def server_version(self, conn) -> int:
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        ver_str = cursor.fetchone()[0]  # e.g. "8.4.9"
        parts = ver_str.split(".")
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int((parts[2] or "0").split("-")[0]) if len(parts) > 2 else 0
        return major * 10000 + minor * 100 + patch


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_ADAPTERS: dict[str, DBAdapter] = {
    "postgres": PostgreSQLAdapter(),
    "mssql":    MSSQLAdapter(),
    "mysql":    MySQLAdapter(),
}


def get_adapter(db_type: str) -> DBAdapter:
    adapter = _ADAPTERS.get(db_type)
    if not adapter:
        raise ValueError(f"Unsupported db_type '{db_type}'. Choose 'postgres', 'mssql', or 'mysql'.")
    return adapter
