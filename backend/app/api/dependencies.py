from functools import lru_cache
from fastapi import Depends

from backend.app.core.config import Settings, get_settings
from backend.app.repositories.vector_store_repository import VectorStoreRepository
from backend.app.services.chat_service import ChatService
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service
from backend.app.services.insights_service import InsightsService
from backend.app.services.rag_service import RAGService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.transcript_service import TranscriptService
from backend.app.services.vector_store_service import VectorStoreService


@lru_cache()
def get_transcript_service() -> TranscriptService:
    return TranscriptService()


@lru_cache()
def get_document_service() -> DocumentService:
    return DocumentService()


@lru_cache()
def get_vector_store_repository(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> VectorStoreRepository:
    return VectorStoreRepository(embedding_service=embedding_service)


@lru_cache()
def get_vector_store_service(
    repository: VectorStoreRepository = Depends(get_vector_store_repository),
    transcript_service: TranscriptService = Depends(get_transcript_service),
    document_service: DocumentService = Depends(get_document_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> VectorStoreService:
    return VectorStoreService(
        repository=repository,
        transcript_service=transcript_service,
        document_service=document_service,
        embedding_service=embedding_service,
    )


@lru_cache()
def get_retrieval_service() -> RetrievalService:
    return RetrievalService()


@lru_cache()
def get_rag_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RAGService:
    return RAGService(retrieval_service=retrieval_service)


@lru_cache()
def get_chat_service(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatService:
    return ChatService(vector_store_service=vector_store_service, rag_service=rag_service)


@lru_cache()
def get_insights_service(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> InsightsService:
    return InsightsService(
        vector_store_service=vector_store_service,
        retrieval_service=retrieval_service,
        rag_service=rag_service,
    )

