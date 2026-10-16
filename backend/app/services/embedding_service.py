import threading
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings

from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppException
from backend.app.core.logging import logger


class EmbeddingService:
    """Thread-safe singleton service for loading and reusing HuggingFace embeddings."""

    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(EmbeddingService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._embeddings: Optional[HuggingFaceEmbeddings] = None
        self._init_lock = threading.Lock()
        self._initialized = True

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Lazily load the embedding model on first access to speed up server boot."""
        if self._embeddings is None:
            with self._init_lock:
                if self._embeddings is None:
                    try:
                        logger.info(f"Loading HuggingFace embedding model: '{self.model_name}'...")
                        self._embeddings = HuggingFaceEmbeddings(
                            model_name=self.model_name,
                            model_kwargs={"device": "cpu"},
                            encode_kwargs={"normalize_embeddings": True},
                        )
                        logger.info("HuggingFace embedding model loaded successfully.")
                    except Exception as e:
                        logger.error(f"Failed to initialize embedding model '{self.model_name}': {e}", exc_info=True)
                        raise AppException(
                            f"Could not initialize embedding model: {str(e)}", status_code=500
                        ) from e
        return self._embeddings

    def is_loaded(self) -> bool:
        """Check if the embedding model is currently loaded in memory."""
        return self._embeddings is not None


_default_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Factory dependency for retrieving the singleton embedding service."""
    global _default_embedding_service
    if _default_embedding_service is None:
        _default_embedding_service = EmbeddingService()
    return _default_embedding_service

