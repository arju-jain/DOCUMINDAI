import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("document_intelligence")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multimodal Document Intelligence backend API for automated invoice understanding, field extraction, and validation.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints under /api
app.include_router(api_router)


@app.get("/api", include_in_schema=False)
def api_info():
    return {
        "message": "Multimodal Document Intelligence API is running.",
        "documentation": "/docs",
        "health_check": "/api/health",
    }


# Mount frontend static files if configured and directory exists
if settings.serve_frontend and settings.frontend_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "Multimodal Document Intelligence API is running.",
            "documentation": "/docs",
            "health_check": "/api/health",
        }


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
