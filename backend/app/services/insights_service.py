import asyncio
import re
from typing import List, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from backend.app.core.config import get_settings
from backend.app.core.exceptions import LLMServiceError, ResourceNotFoundError
from backend.app.core.logging import logger
from backend.app.prompts.insights_prompt import (
    notes_prompt,
    questions_prompt,
    summary_prompt,
)
from backend.app.schemas.chat import (
    InterviewQuestionsResponse,
    StudyNotesResponse,
    VideoSummaryResponse,
)
from backend.app.services.rag_service import RAGService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.vector_store_service import VectorStoreService


class InsightsService:
    """Generates structured video summaries, study notes, and interview questions using the indexed transcript."""

    def __init__(
        self,
        vector_store_service: Optional[VectorStoreService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        rag_service: Optional[RAGService] = None,
        llm: Optional[ChatGroq] = None,
    ):
        self.vector_store_service = vector_store_service or VectorStoreService()
        self.retrieval_service = retrieval_service or RetrievalService(k=8, fetch_k=25)
        self.rag_service = rag_service or RAGService()
        self._llm = llm

    def _get_llm(self) -> ChatGroq:
        if self._llm is None:
            settings = get_settings()
            if not settings.GROQ_API_KEY:
                raise LLMServiceError(
                    "GROQ_API_KEY is not configured. Set GROQ_API_KEY to generate video insights."
                )
            try:
                self._llm = ChatGroq(
                    model=settings.GROQ_MODEL,
                    temperature=0.0,
                    api_key=settings.GROQ_API_KEY,
                )
            except Exception as e:
                raise LLMServiceError(f"Could not connect to Groq LLM: {str(e)}") from e
        return self._llm

    def _get_representative_context(self, video_id: str):
        """Retrieve a representative sample of transcript chunks across the video."""
        vector_store = self.vector_store_service.get_index(video_id)
        if vector_store is None:
            raise ResourceNotFoundError(
                f"Video {video_id} has not been processed. Please process the video first."
            )

        # Retrieve high-level diverse chunks
        docs = self.retrieval_service.retrieve(
            vector_store, "main overview core key concepts topics summary conclusion"
        )
        if not docs:
            # Fallback to direct docstore docs if available
            docs = list(vector_store.docstore._dict.values())[:8]

        context_parts = []
        for i, doc in enumerate(docs, 1):
            start = doc.metadata.get("start_seconds", 0.0)
            context_parts.append(f"[Section {i} @ {start:.1f}s]:\n{doc.page_content}")
        context_str = "\n\n".join(context_parts)

        sources = self.rag_service.build_sources(docs, video_id)
        return context_str, sources

    async def generate_summary(self, video_id: str) -> VideoSummaryResponse:
        """Generate a structured summary grounded in the transcript."""
        loop = asyncio.get_running_loop()

        def _run():
            context_str, sources = self._get_representative_context(video_id)
            llm = self._get_llm()
            chain = summary_prompt | llm | StrOutputParser()
            summary_text = chain.invoke({"context": context_str})
            return summary_text.strip(), sources

        summary_text, sources = await loop.run_in_executor(None, _run)
        return VideoSummaryResponse(
            success=True,
            video_id=video_id,
            summary=summary_text,
            sources=sources,
        )

    async def generate_study_notes(self, video_id: str) -> StudyNotesResponse:
        """Generate comprehensive study notes and key takeaways."""
        loop = asyncio.get_running_loop()

        def _run():
            context_str, sources = self._get_representative_context(video_id)
            llm = self._get_llm()
            chain = notes_prompt | llm | StrOutputParser()
            notes_text = chain.invoke({"context": context_str})

            # Extract takeaways
            takeaways: List[str] = []
            capture = False
            for line in notes_text.splitlines():
                if "takeaway" in line.lower() or "key takeaways" in line.lower():
                    capture = True
                    continue
                if capture and line.strip():
                    cleaned_line = line.strip().lstrip("-*1234567890. ")
                    if cleaned_line:
                        takeaways.append(cleaned_line)

            if not takeaways:
                takeaways = [
                    "Review the study notes above for detailed key principles covered in this lecture."
                ]

            return notes_text.strip(), takeaways, sources

        notes_text, takeaways, sources = await loop.run_in_executor(None, _run)
        return StudyNotesResponse(
            success=True,
            video_id=video_id,
            notes=notes_text,
            key_takeaways=takeaways,
            sources=sources,
        )

    async def generate_questions(self, video_id: str) -> InterviewQuestionsResponse:
        """Generate challenging interview questions grounded in transcript content."""
        loop = asyncio.get_running_loop()

        def _run():
            context_str, sources = self._get_representative_context(video_id)
            llm = self._get_llm()
            chain = questions_prompt | llm | StrOutputParser()
            questions_text = chain.invoke({"context": context_str})

            raw_blocks = re.split(r'\n+(?=###?\s+(?:Question|\d+)|\bQuestion\s+\d+:)', questions_text.strip())
            questions: List[str] = [b.strip() for b in raw_blocks if b.strip()]

            if not questions:
                questions = [questions_text.strip()]

            return questions, sources

        questions_list, sources = await loop.run_in_executor(None, _run)
        return InterviewQuestionsResponse(
            success=True,
            video_id=video_id,
            questions=questions_list,
            sources=sources,
        )

