import asyncio
from typing import Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS

from backend.app.core.exceptions import AppException
from backend.app.core.logging import logger
from backend.app.repositories.vector_store_repository import VectorStoreRepository
from backend.app.schemas.video import VideoMetadata
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service
from backend.app.services.transcript_service import TranscriptService
from backend.app.utils.video_id import extract_video_id


class VectorStoreService:
    """Coordinates video indexing, deduplication, and vector store retrieval."""

    def __init__(
        self,
        repository: Optional[VectorStoreRepository] = None,
        transcript_service: Optional[TranscriptService] = None,
        document_service: Optional[DocumentService] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.repository = repository or VectorStoreRepository(embedding_service=self.embedding_service)
        self.transcript_service = transcript_service or TranscriptService()
        self.document_service = document_service or DocumentService()
        self._indexing_locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, video_id: str) -> asyncio.Lock:
        if video_id not in self._indexing_locks:
            self._indexing_locks[video_id] = asyncio.Lock()
        return self._indexing_locks[video_id]

    async def get_or_create_index(
        self, video_id: str, language: str = "en", force_reindex: bool = False
    ) -> Tuple[FAISS, VideoMetadata, bool]:
        """
        Build or retrieve an existing FAISS index for the video.

        Returns:
            Tuple of (FAISS instance, VideoMetadata, was_cached: bool)
        """
        canonical_id = extract_video_id(video_id)
        lock = self._get_lock(canonical_id)

        async with lock:
            # 1. Check if index already exists and is valid
            if not force_reindex and self.repository.is_indexed(canonical_id):
                cached_store = self.repository.load_index(canonical_id)
                cached_meta = self.repository.get_metadata(canonical_id)
                if cached_store is not None and cached_meta is not None:
                    logger.info(f"Using cached FAISS index for {canonical_id}")
                    return cached_store, cached_meta, True

            logger.info(f"Building new FAISS index for video: {canonical_id}")

            # 2. Fetch transcript
            # Run blocking transcript fetch in thread pool
            loop = asyncio.get_running_loop()
            transcript = await loop.run_in_executor(
                None, self.transcript_service.fetch_transcript, canonical_id, language
            )

            # 3. Create document chunks
            chunks = self.document_service.create_documents(transcript)

            # 4. Generate embeddings and build FAISS index in thread pool
            def _build_faiss() -> FAISS:
                return FAISS.from_documents(
                    documents=chunks,
                    embedding=self.embedding_service.embeddings,
                )

            logger.info(f"Generating embeddings for {len(chunks)} chunks of {canonical_id}...")
            vector_store = await loop.run_in_executor(None, _build_faiss)

            # 5. Persist index
            metadata = self.repository.save_index(
                video_id=canonical_id,
                vector_store=vector_store,
                chunks=chunks,
                language=transcript.language,
                is_generated=transcript.is_generated,
                title=transcript.title,
            )

            return vector_store, metadata, False

    def get_index(self, video_id: str) -> Optional[FAISS]:
        """Retrieve existing index if present, without building."""
        canonical_id = extract_video_id(video_id)
        return self.repository.load_index(canonical_id)

    def get_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Retrieve metadata for an indexed video."""
        canonical_id = extract_video_id(video_id)
        return self.repository.get_metadata(canonical_id)

