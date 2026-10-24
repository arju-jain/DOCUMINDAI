from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas import HealthResponse
from backend.app.services.ocr_service import ocr_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Returns the operational status of the Multimodal Document Intelligence backend,
    including OCR readiness and active engine.
    """
    return HealthResponse(
        status="ok",
        version=settings.version,
        ocr_available=ocr_service.is_ocr_available,
        ocr_engine=ocr_service.active_engine,
    )
