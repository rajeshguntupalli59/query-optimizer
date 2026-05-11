from fastapi import APIRouter, HTTPException
from schemas import ConnectionCreate, ConnectionResponse
import services.connection_manager as cm

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionResponse])
@router.get("/", response_model=list[ConnectionResponse], include_in_schema=False)
def list_connections():
    return cm.list_connections()


@router.post("", response_model=ConnectionResponse, status_code=201)
@router.post("/", response_model=ConnectionResponse, status_code=201, include_in_schema=False)
def add_connection(body: ConnectionCreate):
    return cm.add_connection(body)


@router.delete("/{conn_id}", status_code=204)
def delete_connection(conn_id: str):
    if not cm.delete_connection(conn_id):
        raise HTTPException(404, "Connection not found")


@router.post("/{conn_id}/test")
def test_connection(conn_id: str):
    return cm.test_connection(conn_id)
