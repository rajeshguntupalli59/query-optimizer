from fastapi import APIRouter, HTTPException, Query
from services.slow_query_detector import get_slow_queries, reset_stats

router = APIRouter(prefix="/slow-queries", tags=["slow-queries"])


@router.get("/{conn_id}")
def slow_queries(
    conn_id: str,
    limit: int = Query(20, ge=1, le=100),
    min_calls: int = Query(1, ge=1),
):
    try:
        return get_slow_queries(conn_id, limit, min_calls)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{conn_id}/reset")
def reset(conn_id: str):
    try:
        return reset_stats(conn_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))
