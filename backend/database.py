"""
SQLite bootstrap — creates tables on first run.
Import and call init_db() from main.py startup.
"""
import sqlite3
from config import DB_PATH


DDL = """
CREATE TABLE IF NOT EXISTS connections (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    db_type     TEXT NOT NULL DEFAULT 'postgres',
    host        TEXT NOT NULL,
    port        INTEGER NOT NULL,
    database    TEXT NOT NULL,
    username    TEXT NOT NULL,
    password_enc TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(DDL)
