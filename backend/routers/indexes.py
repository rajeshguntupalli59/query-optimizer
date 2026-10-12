from fastapi import APIRouter, HTTPException
from schemas import QueryRequest
from services.index_advisor import recommend_indexes, test_index_impact

router = APIRouter(prefix="/indexes", tags=["indexes"])


@router.post("/recommend")
def index_recommendations(body: QueryRequest):
    try:
        return recommend_indexes(body.connection_id, body.sql)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


class ImpactRequest(QueryRequest):
    ddl: str


@router.post("/test-impact")
def index_impact(body: ImpactRequest):
    try:
        return test_index_impact(body.connection_id, body.ddl, body.sql)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))
