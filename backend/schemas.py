from pydantic import BaseModel
from typing import Optional, Any, Literal


class ConnectionCreate(BaseModel):
    name: str
    db_type: Literal['postgres', 'mssql', 'mysql'] = 'postgres'
    host: str
    port: int = 5432
    database: str
    username: str
    password: str


class ConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str


class QueryRequest(BaseModel):
    connection_id: str
    sql: str


class ExplainRequest(BaseModel):
    connection_id: str
    sql: str
    analyze: bool = False
    buffers: bool = False
    verbose: bool = False


class ExplainResponse(BaseModel):
    plan: list[dict[str, Any]]
    summary: dict[str, Any]
    raw_text: str


class IndexRecommendation(BaseModel):
    table: str
    columns: list[str]
    reason: str
    ddl: str
    estimated_benefit: str


class SlowQuery(BaseModel):
    query: str
    calls: int
    total_time_ms: float
    mean_time_ms: float
    min_time_ms: float
    max_time_ms: float
    rows: int
    hit_percent: float


class RewriteSuggestion(BaseModel):
    issue: str
    severity: str          # high | medium | low
    original: str
    suggestion: str
    rewritten_sql: Optional[str] = None
