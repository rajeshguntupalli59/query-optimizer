"""Free version: no license key required. Kept for API compatibility."""

def get_license_status() -> dict:
    return {"activated": True, "key": "free"}


def activate(key: str = "") -> dict:
    return {"activated": True, "key": "free"}
