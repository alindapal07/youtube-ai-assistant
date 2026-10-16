import re
from typing import Optional
from urllib.parse import parse_qs, urlparse
from backend.app.core.exceptions import VideoIdError

# Standard YouTube ID pattern: 11 characters of [a-zA-Z0-9_-]
YOUTUBE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_video_id(input_val: str) -> str:
    """
    Extract and validate an 11-character YouTube video ID from a URL or raw ID string.

    Supported formats:
    - Raw ID: 'Gfr50f6ZBvo'
    - Watch URL: 'https://www.youtube.com/watch?v=Gfr50f6ZBvo'
    - Short URL: 'https://youtu.be/Gfr50f6ZBvo'
    - Shorts URL: 'https://www.youtube.com/shorts/Gfr50f6ZBvo'
    - Embed URL: 'https://www.youtube.com/embed/Gfr50f6ZBvo'
    - Live URL: 'https://www.youtube.com/live/Gfr50f6ZBvo'

    Raises:
        VideoIdError: If no valid 11-character video ID can be extracted.
    """
    if not input_val or not isinstance(input_val, str):
        raise VideoIdError("Video ID or URL cannot be empty.")

    cleaned = input_val.strip()

    # If it is directly an 11-character string matching the pattern
    if YOUTUBE_ID_PATTERN.match(cleaned):
        return cleaned

    try:
        parsed = urlparse(cleaned)
    except Exception as e:
        raise VideoIdError(f"Malformed URL: {e}") from e

    hostname = (parsed.hostname or "").lower()
    path = parsed.path

    candidate_id: Optional[str] = None

    if "youtube.com" in hostname:
        if path == "/watch":
            query_params = parse_qs(parsed.query)
            v_param = query_params.get("v")
            if v_param:
                candidate_id = v_param[0]
        elif path.startswith("/shorts/"):
            parts = path.split("/")
            if len(parts) > 2:
                candidate_id = parts[2]
        elif path.startswith("/embed/"):
            parts = path.split("/")
            if len(parts) > 2:
                candidate_id = parts[2]
        elif path.startswith("/live/"):
            parts = path.split("/")
            if len(parts) > 2:
                candidate_id = parts[2]
    elif "youtu.be" in hostname:
        parts = path.strip("/").split("/")
        if parts:
            candidate_id = parts[0]

    if candidate_id:
        # Strip any extra query parameters if path splitting captured them
        candidate_id = candidate_id.split("?")[0].split("&")[0]

    if candidate_id and YOUTUBE_ID_PATTERN.match(candidate_id):
        return candidate_id

    raise VideoIdError(f"Could not extract a valid YouTube video ID from: '{input_val}'")


def build_youtube_watch_url(video_id: str, timestamp_seconds: Optional[int] = None) -> str:
    """Build a canonical YouTube watch URL, optionally with a timestamp parameter."""
    validated_id = extract_video_id(video_id)
    url = f"https://www.youtube.com/watch?v={validated_id}"
    if timestamp_seconds is not None and timestamp_seconds > 0:
        url += f"&t={int(timestamp_seconds)}s"
    return url

