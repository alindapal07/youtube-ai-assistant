from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.app.utils.video_id import extract_video_id


class SourceReference(BaseModel):
    """Citation referencing a specific section of the YouTube transcript."""

    text: str = Field(..., description="Transcript excerpt content")
    start_seconds: float = Field(..., description="Start timestamp in seconds")
    end_seconds: float = Field(..., description="End timestamp in seconds")
    video_url: str = Field(..., description="Direct link to YouTube video at this timestamp")


class ChatRequest(BaseModel):
    """User question payload."""

    video_id: str = Field(..., description="Target YouTube video ID or URL")
    session_id: str = Field(default="default", description="Conversation session identifier")
    question: str = Field(..., min_length=1, max_length=1000, description="User question text")

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, v: str) -> str:
        return extract_video_id(v)

    @field_validator("question")
    @classmethod
    def validate_question(cls, q: str) -> str:
        cleaned = q.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or whitespace only.")
        return cleaned


class ChatResponse(BaseModel):
    """AI Assistant response with grounded transcript citations."""

    success: bool = Field(default=True, description="Whether question answering succeeded")
    video_id: str = Field(..., description="Associated YouTube video ID")
    answer: str = Field(..., description="Generated answer from Groq LLM")
    sources: List[SourceReference] = Field(default_factory=list, description="Retrieved transcript sources")


class ChatMessage(BaseModel):
    """A single message entry in a conversation session."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    sources: List[SourceReference] = Field(default_factory=list, description="Associated source citations")
    timestamp: str = Field(..., description="ISO 8601 creation timestamp")


class ChatHistoryResponse(BaseModel):
    """Conversation history response for a video session."""

    success: bool = Field(default=True)
    video_id: str
    session_id: str
    messages: List[ChatMessage]


class VideoSummaryResponse(BaseModel):
    """Executive summary response for a video."""

    success: bool = Field(default=True)
    video_id: str
    summary: str
    sources: List[SourceReference] = Field(default_factory=list)


class StudyNotesResponse(BaseModel):
    """Structured study notes and key takeaways."""

    success: bool = Field(default=True)
    video_id: str
    notes: str
    key_takeaways: List[str]
    sources: List[SourceReference] = Field(default_factory=list)


class InterviewQuestionsResponse(BaseModel):
    """Grounded interview and revision questions."""

    success: bool = Field(default=True)
    video_id: str
    questions: List[str]
    sources: List[SourceReference] = Field(default_factory=list)

