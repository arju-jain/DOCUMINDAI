from fastapi import APIRouter
from backend.app.routes.health import router as health_router
from backend.app.routes.documents import router as documents_router
from backend.app.routes.evaluation import router as evaluation_router
from backend.app.routes.export import router as export_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(evaluation_router)
api_router.include_router(export_router)

__all__ = ["api_router"]
