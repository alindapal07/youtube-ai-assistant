import re


def clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Replace multiple spaces/newlines with a single space or neat line breaks
    normalized = re.sub(r"[ \t]+", " ", text)
    normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
    return normalized.strip()


def format_seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to a human-readable HH:MM:SS or MM:SS timestamp."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

