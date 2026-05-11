"""
BYOE (Bring Your Own Endpoint) AI assistant.

Supports OpenAI-compatible APIs, Anthropic, Ollama, and any generic
JSON endpoint. Client configures via .env or the Settings UI.
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from database import get_conn
import config as _cfg


# ── Config helpers ───────────────────────────────────────────────────────────

def _get_setting(key: str, fallback: str = "") -> str:
    """DB settings override env defaults."""
    with get_conn() as db:
        row = db.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row and row["value"] else fallback


def get_ai_config() -> dict:
    return {
        "endpoint": _get_setting("AI_ENDPOINT", _cfg.AI_ENDPOINT),
        "api_key":  _get_setting("AI_API_KEY",  _cfg.AI_API_KEY),
        "model":    _get_setting("AI_MODEL",     _cfg.AI_MODEL),
        "provider": _get_setting("AI_PROVIDER",  _cfg.AI_PROVIDER),
        "enabled":  bool(_get_setting("AI_ENDPOINT", _cfg.AI_ENDPOINT)),
    }


def save_ai_config(endpoint: str, api_key: str, model: str, provider: str):
    pairs = [
        ("AI_ENDPOINT", endpoint),
        ("AI_API_KEY",  api_key),
        ("AI_MODEL",    model),
        ("AI_PROVIDER", provider),
    ]
    with get_conn() as db:
        for k, v in pairs:
            db.execute(
                "INSERT INTO app_settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, v),
            )


# ── Prompt builder ───────────────────────────────────────────────────────────

_SYSTEM = (
    "You are an expert DBA and SQL performance engineer. "
    "Analyze the SQL query and return a JSON object with these keys:\n"
    "  rewritten_sql: string — an optimised version of the query (preserve semantics)\n"
    "  explanation:   string — what you changed and why\n"
    "  warnings:      array of strings — potential issues found\n"
    "  tips:          array of strings — additional tuning advice\n"
    "Return ONLY valid JSON, no markdown fences."
)

def _build_prompt(sql: str, db_type: str, context: str = "") -> str:
    parts = [f"Database: {db_type.upper()}"]
    if context:
        parts.append(f"Additional context: {context}")
    parts.append(f"SQL Query:\n{sql}")
    return "\n\n".join(parts)


# ── Provider-specific request builders ───────────────────────────────────────

def _openai_request(prompt: str, cfg: dict) -> tuple[dict, dict]:
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system",  "content": _SYSTEM},
            {"role": "user",    "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    return payload, headers


def _anthropic_request(prompt: str, cfg: dict) -> tuple[dict, dict]:
    payload = {
        "model": cfg["model"],
        "max_tokens": 2048,
        "system": _SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key":    cfg["api_key"],
        "anthropic-version": "2023-06-01",
    }
    return payload, headers


def _ollama_request(prompt: str, cfg: dict) -> tuple[dict, dict]:
    payload = {
        "model":  cfg["model"],
        "prompt": f"{_SYSTEM}\n\n{prompt}",
        "stream": False,
        "format": "json",
    }
    headers = {"Content-Type": "application/json"}
    return payload, headers


def _generic_request(prompt: str, cfg: dict) -> tuple[dict, dict]:
    payload = {
        "model":    cfg["model"],
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    return payload, headers


_BUILDERS = {
    "openai":    _openai_request,
    "anthropic": _anthropic_request,
    "ollama":    _ollama_request,
    "generic":   _generic_request,
}


# ── Response parsers ──────────────────────────────────────────────────────────

def _parse_response(raw: dict, provider: str) -> dict:
    try:
        if provider == "anthropic":
            text = raw["content"][0]["text"]
        elif provider == "ollama":
            text = raw.get("response", raw.get("message", {}).get("content", "{}"))
        else:
            text = raw["choices"][0]["message"]["content"]
        return json.loads(text)
    except Exception as e:
        return {"error": f"Could not parse AI response: {e}", "raw": str(raw)[:500]}


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_with_ai(sql: str, db_type: str = "postgres", context: str = "") -> dict:
    cfg = get_ai_config()
    if not cfg["enabled"]:
        return {"error": "AI is not configured. Set AI_ENDPOINT in Settings or .env"}

    prompt   = _build_prompt(sql, db_type, context)
    builder  = _BUILDERS.get(cfg["provider"], _generic_request)
    payload, headers = builder(prompt, cfg)

    data = json.dumps(payload).encode()
    req  = urllib.request.Request(cfg["endpoint"], data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_cfg.AI_TIMEOUT) as resp:
            raw = json.loads(resp.read())
        return _parse_response(raw, cfg["provider"])
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        return {"error": f"AI endpoint returned {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}
