from fastapi import APIRouter
from pydantic import BaseModel
from services.query_rewriter import rewrite_query

router = APIRouter(prefix="/rewrite", tags=["rewrite"])


class RewriteRequest(BaseModel):
    sql: str


@router.post("")
@router.post("/", include_in_schema=False)
def rewrite(body: RewriteRequest):
    return rewrite_query(body.sql)
