from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/health", tags=["Monitoring"], summary="Liveness probe")
async def health() -> HealthResponse:
    """Return a simple liveness signal for load balancers / orchestrators."""
    return HealthResponse()
