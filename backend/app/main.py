from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppException
from backend.app.core.logging import logger
from backend.app.schemas.common import ErrorResponse, HealthStatusResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    settings = get_settings()
    logger.info("Starting YouTube AI Assistant Backend API...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Port: {settings.API_PORT}")

    # Ensure storage directory exists
    storage_path = Path(settings.FAISS_STORAGE_DIR)
    storage_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"FAISS storage initialized at: {storage_path}")

    if not settings.GROQ_API_KEY:
        logger.warning(
            "GROQ_API_KEY is not set. Chat and insight endpoints will require GROQ_API_KEY to be configured."
        )

    # Pre-warm HuggingFace embedding model at startup so user requests respond instantly
    from backend.app.services.embedding_service import get_embedding_service

    logger.info("Pre-warming HuggingFace embedding model in memory...")
    try:
        get_embedding_service().embeddings
        logger.info("HuggingFace embedding model warmed up and ready in RAM.")
    except Exception as e:
        logger.warning(f"Could not pre-warm embedding model on startup: {e}")

    yield

    logger.info("Shutting down YouTube AI Assistant Backend API...")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="YouTube AI Assistant API",
        description="High-performance backend API powering the YouTube AI Assistant Chrome Extension.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    origins = settings.CORS_ALLOWED_ORIGINS
    if isinstance(origins, str):
        origins = [origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if "*" not in origins else ["*"],
        allow_credentials=True if "*" not in origins else False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized Exception Handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"Handled application exception on {request.url.path}: {exc.message} ({exc.error_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error_code=exc.error_code,
                message=exc.message,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Request validation failure on {request.url.path}: {exc.errors()}")
        err_msgs = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                success=False,
                error_code="VALIDATION_ERROR",
                message=f"Invalid request parameters: {err_msgs}",
                details=exc.errors(),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred.",
            ).model_dump(),
        )

    # Root health endpoint
    @app.get("/health", response_model=HealthStatusResponse, tags=["Health"])
    async def root_health():
        return HealthStatusResponse(
            status="ok",
            environment=settings.ENVIRONMENT,
            version="1.0.0",
        )

    # Register API v1 routes
    app.include_router(api_v1_router)

    return app


app = create_application()

