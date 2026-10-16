from unittest.mock import MagicMock, patch
import pytest
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from backend.app.core.exceptions import (
    TranscriptDisabledError,
    TranscriptNotFoundError,
    VideoUnavailableError,
)
from backend.app.services.document_service import DocumentService
from backend.app.services.transcript_service import (
    TranscriptResult,
    TranscriptService,
    TranscriptSnippetData,
)


def test_transcript_fetch_success():
    mock_api = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.is_generated = False
    mock_transcript.language_code = "en"
    mock_transcript.fetch.return_value = [
        {"text": "Hello world", "start": 0.0, "duration": 2.5},
        {"text": "Welcome to LangChain", "start": 2.5, "duration": 3.0},
    ]

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
    mock_api.list.return_value = mock_transcript_list

    service = TranscriptService(api_client=mock_api)
    result = service.fetch_transcript("Gfr50f6ZBvo")

    assert result.video_id == "Gfr50f6ZBvo"
    assert len(result.snippets) == 2
    assert result.snippets[0].text == "Hello world"
    assert result.snippets[0].start == 0.0
    assert result.is_generated is False
    assert result.language == "en"
    assert "Hello world Welcome to LangChain" in result.full_text


def test_transcript_fallback_to_generated():
    mock_api = MagicMock()
    mock_generated_transcript = MagicMock()
    mock_generated_transcript.is_generated = True
    mock_generated_transcript.language_code = "en"
    mock_generated_transcript.fetch.return_value = [
        {"text": "Auto caption content", "start": 10.0, "duration": 4.0}
    ]

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_manually_created_transcript.side_effect = Exception("No manual transcript")
    mock_transcript_list.find_generated_transcript.return_value = mock_generated_transcript
    mock_api.list.return_value = mock_transcript_list

    service = TranscriptService(api_client=mock_api)
    result = service.fetch_transcript("Gfr50f6ZBvo")

    assert result.is_generated is True
    assert len(result.snippets) == 1
    assert result.snippets[0].text == "Auto caption content"


def test_transcript_disabled_error():
    mock_api = MagicMock()
    mock_api.list.side_effect = TranscriptsDisabled("Gfr50f6ZBvo")

    service = TranscriptService(api_client=mock_api)
    with pytest.raises(TranscriptDisabledError):
        service.fetch_transcript("Gfr50f6ZBvo")


def test_transcript_not_found_error():
    mock_api = MagicMock()
    mock_api.list.side_effect = NoTranscriptFound("Gfr50f6ZBvo", ["en"], [])

    service = TranscriptService(api_client=mock_api)
    with pytest.raises(TranscriptNotFoundError):
        service.fetch_transcript("Gfr50f6ZBvo")


def test_video_unavailable_error():
    mock_api = MagicMock()
    mock_api.list.side_effect = VideoUnavailable("Gfr50f6ZBvo")

    service = TranscriptService(api_client=mock_api)
    with pytest.raises(VideoUnavailableError):
        service.fetch_transcript("Gfr50f6ZBvo")


def test_document_chunking_with_timestamps():
    service = DocumentService(chunk_size=100, chunk_overlap=20)
    snippets = [
        TranscriptSnippetData(text=f"Sentence number {i} in the tutorial.", start=float(i * 10), duration=8.0)
        for i in range(20)
    ]
    transcript = TranscriptResult(
        video_id="Gfr50f6ZBvo",
        snippets=snippets,
        language="en",
        is_generated=False,
    )

    docs = service.create_documents(transcript)
    assert len(docs) > 1
    for doc in docs:
        assert "video_id" in doc.metadata
        assert "start_seconds" in doc.metadata
        assert "end_seconds" in doc.metadata
        assert "source" in doc.metadata
        assert doc.metadata["video_id"] == "Gfr50f6ZBvo"

