class AppException(Exception):
    """Base exception for YouTube AI Assistant errors."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class VideoIdError(AppException):
    """Raised when a video ID or URL is invalid."""

    def __init__(self, message: str = "Invalid YouTube video ID or URL."):
        super().__init__(message=message, status_code=400, error_code="INVALID_VIDEO_ID")


class TranscriptNotFoundError(AppException):
    """Raised when no transcript is found for the requested video/language."""

    def __init__(self, message: str = "No transcript found for this video."):
        super().__init__(message=message, status_code=404, error_code="TRANSCRIPT_NOT_FOUND")


class TranscriptDisabledError(AppException):
    """Raised when transcripts are disabled for the video."""

    def __init__(self, message: str = "Transcripts are disabled for this video."):
        super().__init__(message=message, status_code=403, error_code="TRANSCRIPTS_DISABLED")


class VideoUnavailableError(AppException):
    """Raised when the video is private or unavailable."""

    def __init__(self, message: str = "The requested YouTube video is unavailable."):
        super().__init__(message=message, status_code=404, error_code="VIDEO_UNAVAILABLE")


class VectorStoreError(AppException):
    """Raised on FAISS index read/write/corruption errors."""

    def __init__(self, message: str = "Vector index error."):
        super().__init__(message=message, status_code=500, error_code="VECTOR_STORE_ERROR")


class LLMServiceError(AppException):
    """Raised when Groq or LLM provider errors out."""

    def __init__(self, message: str = "AI model provider error."):
        super().__init__(message=message, status_code=502, error_code="LLM_PROVIDER_ERROR")


class ResourceNotFoundError(AppException):
    """Raised when a requested resource (like an un-indexed video) is not found."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND")

