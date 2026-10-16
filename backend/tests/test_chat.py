from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_chat_service, get_vector_store_service
from backend.app.main import app
from backend.app.schemas.chat import ChatMessage, ChatResponse, SourceReference
from backend.app.schemas.video import VideoMetadata
from backend.app.services.chat_service import ChatService


def test_chat_service_session_isolation():
    mock_vector_service = MagicMock()
    mock_rag_service = MagicMock()
    chat_service = ChatService(
        vector_store_service=mock_vector_service,
        rag_service=mock_rag_service,
        max_history_turns=4,
    )

    # Seed history for video 1, session A
    chat_service._history["video1::sessA"] = [
        ChatMessage(role="user", content="Question 1", sources=[], timestamp="2026-10-14T12:00:00Z"),
        ChatMessage(role="assistant", content="Answer 1", sources=[], timestamp="2026-10-14T12:00:05Z"),
    ]

    # Seed history for video 2, session A
    chat_service._history["video2::sessA"] = [
        ChatMessage(role="user", content="Question 2", sources=[], timestamp="2026-10-14T12:05:00Z"),
        ChatMessage(role="assistant", content="Answer 2", sources=[], timestamp="2026-10-14T12:05:05Z"),
    ]

    # Verify video 1 session A history is isolated
    hist1 = chat_service.get_history("video1", "sessA")
    assert len(hist1) == 2
    assert hist1[0].content == "Question 1"

    # Verify video 2 session A history is isolated
    hist2 = chat_service.get_history("video2", "sessA")
    assert len(hist2) == 2
    assert hist2[0].content == "Question 2"

    # Verify clear history only affects targeted video session
    chat_service.clear_history("video1", "sessA")
    assert len(chat_service.get_history("video1", "sessA")) == 0
    assert len(chat_service.get_history("video2", "sessA")) == 2


def test_chat_api_endpoint():
    mock_chat_svc = MagicMock()
    mock_chat_svc.answer_question = AsyncMock(
        return_value=ChatResponse(
            success=True,
            video_id="Gfr50f6ZBvo",
            answer="This is a test response.",
            sources=[
                SourceReference(
                    text="Transcript snippet",
                    start_seconds=10.0,
                    end_seconds=20.0,
                    video_url="https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=10s",
                )
            ],
        )
    )

    app.dependency_overrides[get_chat_service] = lambda: mock_chat_svc

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/chat",
            json={
                "video_id": "Gfr50f6ZBvo",
                "session_id": "test-session",
                "question": "What is discussed?",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["video_id"] == "Gfr50f6ZBvo"
        assert data["answer"] == "This is a test response."
        assert len(data["sources"]) == 1
    finally:
        app.dependency_overrides.clear()

