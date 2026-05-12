"""
License validation via Lemon Squeezy API.

Flow:
  1. Buyer enters their key (from purchase receipt email).
  2. We call LS /licenses/activate — consumes one activation slot.
  3. On success, key is stored in SQLite.
  4. Every subsequent app start reads from SQLite only — no internet needed.
"""
import os
import socket
import requests
from database import get_conn

_LS_ACTIVATE = "https://api.lemonsqueezy.com/v1/licenses/activate"


def _call_ls_activate(key: str) -> tuple[bool, str, str]:
    """
    Returns (success, instance_id_or_empty, error_message).
    """
    try:
        hostname = socket.gethostname() or "queryoptimizer"
        resp = requests.post(
            _LS_ACTIVATE,
            data={"license_key": key, "instance_name": hostname},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        data = resp.json()
        if data.get("activated"):
            instance_id = (data.get("instance") or {}).get("id", "")
            return True, instance_id, ""
        error = data.get("error") or "Key is invalid or has already reached its activation limit."
        return False, "", error
    except requests.Timeout:
        return False, "", "Connection timed out. Check your internet and try again."
    except Exception:
        return False, "", "Could not reach the license server. Please try again in a few minutes."


def get_license_status() -> dict:
    # Env var allows pre-activated / headless deployments
    env_key = os.getenv("LICENSE_KEY", "").strip()
    if env_key:
        return {"activated": True, "key": env_key}
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key='license_key'"
        ).fetchone()
    stored = row["value"] if row else ""
    return {"activated": bool(stored), "key": stored}


def activate(key: str) -> dict:
    key = key.upper().strip()
    if not key:
        return {"activated": False, "error": "Please enter your license key."}

    success, instance_id, error = _call_ls_activate(key)
    if not success:
        return {"activated": False, "error": error}

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO app_settings(key,value) VALUES('license_key',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key,),
        )
        if instance_id:
            conn.execute(
                "INSERT INTO app_settings(key,value) VALUES('license_instance_id',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (instance_id,),
            )
    return {"activated": True, "key": key}
