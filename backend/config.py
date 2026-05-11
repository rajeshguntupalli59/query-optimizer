import os
import secrets
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "queryoptimizer.db"

# Fernet key for encrypting saved passwords.
# Priority: SECRET_KEY env var → persisted key file → auto-generate + persist.
_KEY_FILE = DATA_DIR / ".secret_key"

def _load_or_create_key() -> bytes:
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key.encode()
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    _KEY_FILE.chmod(0o600)
    return key

FERNET_KEY: bytes = _load_or_create_key()

# AI integration (BYOE — Bring Your Own Endpoint)
AI_ENDPOINT: str  = os.getenv("AI_ENDPOINT", "")
AI_API_KEY:  str  = os.getenv("AI_API_KEY",  "")
AI_MODEL:    str  = os.getenv("AI_MODEL",     "gpt-4o")
AI_PROVIDER: str  = os.getenv("AI_PROVIDER",  "openai")   # openai | anthropic | ollama | generic
AI_TIMEOUT:  int  = int(os.getenv("AI_TIMEOUT", "30"))
