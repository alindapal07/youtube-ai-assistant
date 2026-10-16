import logging
import sys
from backend.app.core.config import get_settings


class SensitiveDataFilter(logging.Filter):
    """Filter that masks API keys and sensitive tokens in log output."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            settings = get_settings()
            if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY) > 6:
                record.msg = record.msg.replace(
                    settings.GROQ_API_KEY, f"{settings.GROQ_API_KEY[:4]}...[REDACTED]"
                )
        return True


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logger = logging.getLogger("youtube_ai_assistant")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()

