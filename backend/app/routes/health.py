from fastapi import APIRouter
from backend.app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Returns the operational status of the Multimodal Document Intelligence backend."""
    return HealthResponse(status="ok")
