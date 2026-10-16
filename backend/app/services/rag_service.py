from typing import List, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from backend.app.core.config import get_settings
from backend.app.core.exceptions import LLMServiceError
from backend.app.core.logging import logger
from backend.app.prompts.chat_prompt import chat_prompt
from backend.app.schemas.chat import SourceReference
from backend.app.services.retrieval_service import RetrievalService
from backend.app.utils.video_id import build_youtube_watch_url


class RAGService:
    """Coordinates retrieval, context construction, and Groq LLM response generation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm: Optional[ChatGroq] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self._llm = llm

    def _get_llm(self) -> ChatGroq:
        """Get or initialize ChatGroq client."""
        if self._llm is None:
            settings = get_settings()
            if not settings.GROQ_API_KEY:
                raise LLMServiceError(
                    "GROQ_API_KEY is not configured. Please set GROQ_API_KEY in your environment or .env file."
                )
            try:
                self._llm = ChatGroq(
                    model=settings.GROQ_MODEL,
                    temperature=0.0,
                    api_key=settings.GROQ_API_KEY,
                )
            except Exception as e:
                logger.error(f"Failed to initialize ChatGroq: {e}", exc_info=True)
                raise LLMServiceError(f"Could not connect to Groq LLM: {str(e)}") from e
        return self._llm

    def build_sources(self, documents: List[Document], video_id: str) -> List[SourceReference]:
        """Convert retrieved LangChain Documents into clean, typed SourceReferences."""
        sources: List[SourceReference] = []
        for doc in documents:
            meta = doc.metadata or {}
            start_sec = float(meta.get("start_seconds", 0.0))
            end_sec = float(meta.get("end_seconds", start_sec + 5.0))
            source_url = meta.get("source") or build_youtube_watch_url(video_id, int(start_sec))

            sources.append(
                SourceReference(
                    text=doc.page_content.strip(),
                    start_seconds=start_sec,
                    end_seconds=end_sec,
                    video_url=source_url,
                )
            )
        return sources

    def answer_query(
        self,
        vector_store: FAISS,
        video_id: str,
        question: str,
        chat_history: str = "No prior history.",
    ) -> Tuple[str, List[SourceReference]]:
        """
        Execute RAG workflow:
        1. Retrieve relevant transcript chunks via MMR.
        2. Format context and citations.
        3. Invoke Groq model through LangChain chain.
        4. Return answer and source references.
        """
        # 1. Retrieve chunks
        relevant_docs = self.retrieval_service.retrieve(vector_store, question)

        if not relevant_docs:
            return (
                "The video transcript does not contain any relevant content for this question.",
                [],
            )

        # 2. Build context
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            start = doc.metadata.get("start_seconds", 0.0)
            context_parts.append(f"[Excerpt {i} @ {start:.1f}s]:\n{doc.page_content}")
        context_str = "\n\n".join(context_parts)

        # 3. Build sources
        sources = self.build_sources(relevant_docs, video_id)

        # 4. Invoke LLM chain
        try:
            llm = self._get_llm()
            chain = chat_prompt | llm | StrOutputParser()
            answer = chain.invoke(
                {
                    "context": context_str,
                    "question": question,
                    "chat_history": chat_history,
                }
            )
            return answer.strip(), sources

        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Error executing Groq LLM chain: {e}", exc_info=True)
            raise LLMServiceError(f"Groq API error: {str(e)}") from e

