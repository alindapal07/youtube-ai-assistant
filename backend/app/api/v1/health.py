import os
from pathlib import Path
from fastapi import APIRouter, Depends
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.common import HealthStatusResponse, ReadinessStatusResponse
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthStatusResponse)
async def get_health(settings: Settings = Depends(get_settings)):
    """Health check returning basic service status."""
    return HealthStatusResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
    )


@router.get("/ready", response_model=ReadinessStatusResponse)
async def check_readiness(
    settings: Settings = Depends(get_settings),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    """Readiness probe checking Groq configuration, storage write access, and embedding service."""
    storage_path = Path(settings.FAISS_STORAGE_DIR)
    storage_writable = os.access(storage_path, os.W_OK) if storage_path.exists() else False

    groq_configured = bool(settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 0)
    embedding_ready = embedding_service.is_loaded()

    status = "ready" if (storage_writable and groq_configured) else "degraded"

    return ReadinessStatusResponse(
        status=status,
        groq_configured=groq_configured,
        embedding_model_ready=embedding_ready,
        storage_writable=storage_writable,
    )

