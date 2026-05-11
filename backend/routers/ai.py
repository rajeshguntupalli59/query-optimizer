from fastapi import APIRouter
from pydantic import BaseModel
from services.ai_assistant import analyze_with_ai, get_ai_config, save_ai_config

router = APIRouter(prefix="/ai", tags=["ai"])


class AiAnalyzeRequest(BaseModel):
    sql: str
    db_type: str = "postgres"
    context: str = ""


class AiConfigUpdate(BaseModel):
    endpoint: str
    api_key: str
    model: str
    provider: str


@router.post("/analyze")
def analyze(body: AiAnalyzeRequest):
    return analyze_with_ai(body.sql, body.db_type, body.context)


@router.get("/config")
def get_config():
    cfg = get_ai_config()
    cfg["api_key"] = "••••••••" if cfg["api_key"] else ""
    return cfg


@router.put("/config")
def update_config(body: AiConfigUpdate):
    existing_key = get_ai_config()["api_key"] if body.api_key == "••••••••" else body.api_key
    save_ai_config(body.endpoint, existing_key or "", body.model, body.provider)
    return {"success": True}
