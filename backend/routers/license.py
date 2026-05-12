from fastapi import APIRouter
from pydantic import BaseModel
from license import activate, get_license_status

router = APIRouter(prefix="/license", tags=["license"])


class ActivateRequest(BaseModel):
    key: str


@router.get("")
def status():
    return get_license_status()


@router.post("/activate")
def do_activate(body: ActivateRequest):
    return activate(body.key)
