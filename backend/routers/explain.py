from fastapi import APIRouter, HTTPException
from schemas import ExplainRequest
from services.explain_analyzer import run_explain

router = APIRouter(prefix="/explain", tags=["explain"])


@router.post("")
@router.post("/", include_in_schema=False)
def explain_query(body: ExplainRequest):
    try:
        return run_explain(body.connection_id, body.sql, body.analyze, body.buffers, body.verbose)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))
