import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.core.logging import logger
from backend.app.schemas.chat import (
    ChatMessage,
    ChatResponse,
    SourceReference,
)
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_store_service import VectorStoreService


class ChatService:
    """Manages conversational state, session isolation, and delegates Q&A to RAGService."""

    def __init__(
        self,
        vector_store_service: Optional[VectorStoreService] = None,
        rag_service: Optional[RAGService] = None,
        max_history_turns: int = 6,
    ):
        self.vector_store_service = vector_store_service or VectorStoreService()
        self.rag_service = rag_service or RAGService()
        self.max_history_turns = max_history_turns
        # Session storage isolated by (video_id, session_id)
        self._history: Dict[str, List[ChatMessage]] = {}

    def _get_session_key(self, video_id: str, session_id: str) -> str:
        return f"{video_id}::{session_id}"

    def get_history(self, video_id: str, session_id: str) -> List[ChatMessage]:
        """Retrieve conversation history for a specific video session."""
        key = self._get_session_key(video_id, session_id)
        return self._history.get(key, [])

    def clear_history(self, video_id: str, session_id: str) -> None:
        """Clear conversation history for a specific video session."""
        key = self._get_session_key(video_id, session_id)
        self._history.pop(key, None)

    def _format_history_text(self, messages: List[ChatMessage]) -> str:
        """Format history list into a concise conversation string for prompt injection."""
        if not messages:
            return "No previous conversation."
        lines = []
        for msg in messages[-self.max_history_turns :]:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    async def answer_question(
        self,
        video_id: str,
        session_id: str,
        question: str,
    ) -> ChatResponse:
        """
        Process a user question:
        1. Ensure video index exists.
        2. Format prior session history.
        3. Execute RAG in thread pool.
        4. Append to session history.
        5. Return response.
        """
        vector_store = self.vector_store_service.get_index(video_id)
        if vector_store is None:
            raise ResourceNotFoundError(
                f"Video {video_id} has not been processed yet. Please process the video before asking questions."
            )

        session_key = self._get_session_key(video_id, session_id)
        existing_history = self._history.setdefault(session_key, [])
        history_text = self._format_history_text(existing_history)

        # Run synchronous RAG chain in executor
        loop = asyncio.get_running_loop()
        answer, sources = await loop.run_in_executor(
            None,
            self.rag_service.answer_query,
            vector_store,
            video_id,
            question,
            history_text,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        # Record user message
        existing_history.append(
            ChatMessage(
                role="user",
                content=question,
                sources=[],
                timestamp=now_iso,
            )
        )

        # Record assistant message
        existing_history.append(
            ChatMessage(
                role="assistant",
                content=answer,
                sources=sources,
                timestamp=now_iso,
            )
        )

        # Trim history if exceeding max storage
        if len(existing_history) > (self.max_history_turns * 2):
            self._history[session_key] = existing_history[-(self.max_history_turns * 2) :]

        return ChatResponse(
            success=True,
            video_id=video_id,
            answer=answer,
            sources=sources,
        )

