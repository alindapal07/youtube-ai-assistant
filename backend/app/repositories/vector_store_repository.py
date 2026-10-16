import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from backend.app.core.config import get_settings
from backend.app.core.exceptions import VectorStoreError
from backend.app.core.logging import logger
from backend.app.schemas.video import VideoMetadata
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service


class VectorStoreRepository:
    """Manages disk persistence, metadata validation, and caching of FAISS vector stores."""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        settings = get_settings()
        self.storage_dir = Path(storage_dir or settings.FAISS_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_service = embedding_service or get_embedding_service()
        self.cache_ttl_hours = settings.CACHE_TTL_HOURS
        # In-memory index cache for rapid response
        self._memory_cache: Dict[str, FAISS] = {}
        self._metadata_cache: Dict[str, VideoMetadata] = {}

    def _get_video_dir(self, video_id: str) -> Path:
        return self.storage_dir / video_id

    def _get_metadata_path(self, video_id: str) -> Path:
        return self._get_video_dir(video_id) / "metadata.json"

    def is_indexed(self, video_id: str) -> bool:
        """Check whether a valid, unexpired index exists for the video."""
        metadata = self.get_metadata(video_id)
        if metadata is None:
            return False

        # Verify FAISS files exist
        video_dir = self._get_video_dir(video_id)
        index_file = video_dir / "index.faiss"
        pkl_file = video_dir / "index.pkl"

        return index_file.exists() and pkl_file.exists()

    def get_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Load and validate index metadata, checking for expiration."""
        if video_id in self._metadata_cache:
            meta = self._metadata_cache[video_id]
            if meta.expires_at:
                try:
                    exp = datetime.fromisoformat(meta.expires_at)
                    if datetime.now(timezone.utc) > exp:
                        logger.info(f"In-memory index for video {video_id} has expired.")
                        self.evict(video_id)
                        return None
                except Exception:
                    pass
            return meta

        meta_file = self._get_metadata_path(video_id)
        if not meta_file.exists():
            return None

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check expiration
            expires_at_str = data.get("expires_at")
            if expires_at_str:
                exp_dt = datetime.fromisoformat(expires_at_str)
                if datetime.now(timezone.utc) > exp_dt:
                    logger.info(f"Disk index for video {video_id} has expired. Invalidating.")
                    self.evict(video_id)
                    return None

            # Verify model compatibility
            saved_model = data.get("embedding_model")
            current_model = self.embedding_service.model_name
            if saved_model != current_model:
                logger.warning(
                    f"Index model mismatch for {video_id}: saved with '{saved_model}', "
                    f"current is '{current_model}'. Invalidating."
                )
                self.evict(video_id)
                return None

            metadata = VideoMetadata(
                video_id=data["video_id"],
                video_url=data.get("video_url", f"https://www.youtube.com/watch?v={video_id}"),
                title=data.get("title"),
                language=data.get("language", "en"),
                is_generated=data.get("is_generated", False),
                total_chunks=data.get("total_chunks", 0),
                created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                expires_at=expires_at_str,
            )
            self._metadata_cache[video_id] = metadata
            return metadata

        except Exception as e:
            logger.error(f"Corrupted or invalid metadata for video {video_id}: {e}")
            self.evict(video_id)
            return None

    def save_index(
        self,
        video_id: str,
        vector_store: FAISS,
        chunks: List[Document],
        language: str = "en",
        is_generated: bool = False,
        title: Optional[str] = None,
    ) -> VideoMetadata:
        """Persist FAISS index and validated metadata to storage."""
        video_dir = self._get_video_dir(video_id)
        video_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.cache_ttl_hours)

        try:
            # 1. Save FAISS binary index
            vector_store.save_local(str(video_dir))

            # 2. Save metadata JSON
            metadata = VideoMetadata(
                video_id=video_id,
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                title=title,
                language=language,
                is_generated=is_generated,
                total_chunks=len(chunks),
                created_at=now.isoformat(),
                expires_at=expires_at.isoformat(),
            )

            raw_meta = metadata.model_dump()
            raw_meta["embedding_model"] = self.embedding_service.model_name

            with open(self._get_metadata_path(video_id), "w", encoding="utf-8") as f:
                json.dump(raw_meta, f, indent=2)

            # 3. Store in memory cache
            self._memory_cache[video_id] = vector_store
            self._metadata_cache[video_id] = metadata

            logger.info(f"Saved FAISS index for {video_id} with {len(chunks)} chunks.")
            return metadata

        except Exception as e:
            logger.error(f"Failed to save FAISS index for {video_id}: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to persist index: {str(e)}") from e

    def load_index(self, video_id: str) -> Optional[FAISS]:
        """Load an existing FAISS index from memory or disk after verifying integrity."""
        # Check in-memory cache first
        if video_id in self._memory_cache:
            if self.is_indexed(video_id):
                return self._memory_cache[video_id]
            else:
                self.evict(video_id)

        # Validate metadata before loading from disk
        if not self.is_indexed(video_id):
            return None

        video_dir = self._get_video_dir(video_id)
        try:
            logger.info(f"Loading FAISS index from disk for video: {video_id}")
            vector_store = FAISS.load_local(
                folder_path=str(video_dir),
                embeddings=self.embedding_service.embeddings,
                allow_dangerous_deserialization=True,
            )
            self._memory_cache[video_id] = vector_store
            return vector_store

        except Exception as e:
            logger.error(f"Failed to load FAISS index for video {video_id}: {e}", exc_info=True)
            self.evict(video_id)
            raise VectorStoreError(f"Corrupted or invalid vector index for video {video_id}.") from e

    def evict(self, video_id: str) -> None:
        """Remove a video index from memory cache and storage directory."""
        self._memory_cache.pop(video_id, None)
        self._metadata_cache.pop(video_id, None)
        video_dir = self._get_video_dir(video_id)
        if video_dir.exists():
            try:
                shutil.rmtree(video_dir)
                logger.info(f"Evicted index directory for video: {video_id}")
            except Exception as e:
                logger.warning(f"Could not delete index directory {video_dir}: {e}")

