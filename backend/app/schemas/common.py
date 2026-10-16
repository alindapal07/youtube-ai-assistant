from typing import Any, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Standard success response schema."""

    success: bool = Field(default=True, description="Indicates operation success")
    message: Optional[str] = Field(default=None, description="Optional informational message")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = Field(default=False, description="Always False for error responses")
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable error explanation")
    details: Optional[Any] = Field(default=None, description="Optional structured error details")


class HealthStatusResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="ok", description="Application service status")
    environment: str = Field(..., description="Current deployment environment")
    version: str = Field(..., description="Application version")


class ReadinessStatusResponse(BaseModel):
    """Readiness probe response schema."""

    status: str = Field(..., description="Ready status (ready / degraded / not_ready)")
    groq_configured: bool = Field(..., description="Whether GROQ_API_KEY is configured")
    embedding_model_ready: bool = Field(..., description="Whether embedding model is initialized")
    storage_writable: bool = Field(..., description="Whether vector storage directory is writable")

