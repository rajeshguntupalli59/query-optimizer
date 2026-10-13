from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import workload as wl

router = APIRouter(prefix="/workload", tags=["workload"])


class CaptureBody(BaseModel):
    source_connection_id: str
    name: str
    limit: int = 50


class ReplayBody(BaseModel):
    workload_id: str
    target_connection_id: str
    iterations: int = 3
    concurrency: int = 4
    safe_mode: bool = True


@router.get("")
def list_workloads():
    return wl.list_workloads()


@router.get("/{wid}")
def get_workload(wid: str):
    w = wl.get_workload(wid)
    if not w:
        raise HTTPException(404, "Workload not found")
    return w


@router.delete("/{wid}")
def delete_workload(wid: str):
    wl.delete_workload(wid)
    return {"ok": True}


@router.post("/capture")
def capture(body: CaptureBody):
    try:
        return wl.capture_workload(body.source_connection_id, body.name,
                                   max(1, min(body.limit, 500)))
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Capture failed: {str(e)[:300]}")


@router.post("/replay")
def replay(body: ReplayBody):
    w = wl.get_workload(body.workload_id)
    if not w:
        raise HTTPException(404, "Workload not found")
    try:
        return wl.replay_workload(
            w, body.target_connection_id,
            iterations=max(1, min(body.iterations, 20)),
            concurrency=max(1, min(body.concurrency, 32)),
            safe_mode=body.safe_mode)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Replay failed: {str(e)[:300]}")
