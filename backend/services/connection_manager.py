"""
Connection manager — persists to SQLite, encrypts passwords with Fernet.
"""
import uuid
from typing import Optional

from cryptography.fernet import Fernet

from config import FERNET_KEY
from database import get_conn
from schemas import ConnectionCreate, ConnectionResponse
from services.db_adapter import get_adapter

_fernet = Fernet(FERNET_KEY)


# ── Encryption helpers ──────────────────────────────────────────────────────

def _encrypt(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()

def _decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()


# ── CRUD ────────────────────────────────────────────────────────────────────

def add_connection(data: ConnectionCreate) -> ConnectionResponse:
    conn_id = str(uuid.uuid4())
    enc_pw  = _encrypt(data.password)
    with get_conn() as db:
        db.execute(
            "INSERT INTO connections (id,name,db_type,host,port,database,username,password_enc) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (conn_id, data.name, data.db_type, data.host, data.port,
             data.database, data.username, enc_pw),
        )
    return _to_response(dict(id=conn_id, name=data.name, db_type=data.db_type,
                             host=data.host, port=data.port, database=data.database,
                             username=data.username))


def list_connections() -> list[ConnectionResponse]:
    with get_conn() as db:
        rows = db.execute(
            "SELECT id,name,db_type,host,port,database,username FROM connections ORDER BY created_at"
        ).fetchall()
    return [_to_response(dict(r)) for r in rows]


def get_connection(conn_id: str) -> Optional[dict]:
    with get_conn() as db:
        row = db.execute(
            "SELECT id,name,db_type,host,port,database,username,password_enc "
            "FROM connections WHERE id=?", (conn_id,)
        ).fetchone()
    if not row:
        return None
    cfg = dict(row)
    cfg["password"] = _decrypt(cfg.pop("password_enc"))
    return cfg


def delete_connection(conn_id: str) -> bool:
    with get_conn() as db:
        cur = db.execute("DELETE FROM connections WHERE id=?", (conn_id,))
    return cur.rowcount > 0


def test_connection(conn_id: str) -> dict:
    cfg = get_connection(conn_id)
    if not cfg:
        return {"success": False, "error": "Connection not found"}
    try:
        adapter = get_adapter(cfg["db_type"])
        conn = adapter.open(cfg)
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def open_connection(conn_id: str):
    cfg = get_connection(conn_id)
    if not cfg:
        raise ValueError("Connection not found")
    adapter = get_adapter(cfg["db_type"])
    return adapter.open(cfg), adapter, cfg


# ── Internal ─────────────────────────────────────────────────────────────────

def _to_response(c: dict) -> ConnectionResponse:
    return ConnectionResponse(
        id=c["id"], name=c["name"], db_type=c["db_type"],
        host=c["host"], port=c["port"], database=c["database"],
        username=c["username"],
    )
