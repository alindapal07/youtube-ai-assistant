from typing import Optional
from pydantic import BaseModel, Field, field_validator
from backend.app.utils.video_id import extract_video_id


class VideoProcessRequest(BaseModel):
    """Request payload to process and index a YouTube video transcript."""

    video_id: str = Field(..., description="YouTube video ID or full URL")
    language: str = Field(default="en", description="Preferred language code (e.g., 'en', 'es')")

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, v: str) -> str:
        return extract_video_id(v)


class VideoProcessResponse(BaseModel):
    """Response returned after processing a video transcript."""

    success: bool = Field(default=True, description="Whether processing succeeded")
    video_id: str = Field(..., description="Canonical 11-character YouTube video ID")
    title: Optional[str] = Field(default=None, description="Authoritative video title")
    status: str = Field(..., description="Processing status (e.g. 'ready')")
    chunks_created: int = Field(..., description="Number of text chunks indexed")
    cached: bool = Field(..., description="True if loaded from existing index cache")


class VideoMetadata(BaseModel):
    """Metadata regarding an indexed video."""

    video_id: str
    video_url: str
    title: Optional[str] = None
    language: str
    is_generated: bool
    total_chunks: int
    created_at: str
    expires_at: Optional[str] = None


class VideoInfoResponse(BaseModel):
    """Response with safe video status and index metadata."""

    video_id: str = Field(..., description="Canonical 11-character YouTube video ID")
    title: Optional[str] = Field(default=None, description="Authoritative video title")
    status: str = Field(..., description="'ready' if indexed, 'not_indexed' otherwise")
    indexed: bool = Field(..., description="True if vector index exists")
    chunks_count: Optional[int] = Field(default=None, description="Number of indexed chunks if ready")
    metadata: Optional[VideoMetadata] = Field(default=None, description="Detailed safe metadata")

