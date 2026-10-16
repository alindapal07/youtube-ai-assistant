from dataclasses import dataclass
from typing import List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
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
from backend.app.core.logging import logger
from backend.app.utils.video_id import extract_video_id


@dataclass
class TranscriptSnippetData:
    """Individual transcript snippet with precise timing information."""

    text: str
    start: float
    duration: float


@dataclass
class TranscriptResult:
    """Full transcript result containing snippets and track metadata."""

    video_id: str
    snippets: List[TranscriptSnippetData]
    language: str
    is_generated: bool
    title: Optional[str] = None

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.snippets)


class TranscriptService:
    """Service responsible for retrieving and normalizing YouTube transcripts."""

    def __init__(self, api_client: Optional[YouTubeTranscriptApi] = None):
        self.api = api_client or YouTubeTranscriptApi()

    @staticmethod
    def fetch_video_title(video_id: str) -> Optional[str]:
        """Fetch canonical video title from YouTube oEmbed."""
        import json
        import urllib.request
        try:
            canonical_id = extract_video_id(video_id)
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={canonical_id}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("title")
        except Exception:
            return None

    def fetch_transcript(self, video_id: str, preferred_language: str = "en") -> TranscriptResult:
        """
        Fetch transcript snippets for a validated YouTube video ID.
        """
        canonical_id = extract_video_id(video_id)
        video_title = self.fetch_video_title(canonical_id)
        logger.info(f"Fetching transcript for video ID: {canonical_id} (pref lang: {preferred_language})")

        languages_to_try = [preferred_language]
        if preferred_language != "en":
            languages_to_try.append("en")

        try:
            # First attempt to inspect the transcript list for manual/auto metadata
            selected_transcript = None
            is_generated = False
            detected_lang = preferred_language

            try:
                transcript_list = self.api.list(canonical_id)

                # 1. Try manual transcript in preferred languages
                try:
                    selected_transcript = transcript_list.find_manually_created_transcript(languages_to_try)
                    is_generated = False
                except Exception:
                    pass

                # 2. Try generated transcript in preferred languages
                if not selected_transcript:
                    try:
                        selected_transcript = transcript_list.find_generated_transcript(languages_to_try)
                        is_generated = True
                    except Exception:
                        pass

                # 3. Fallback to generic find_transcript for preferred languages
                if not selected_transcript:
                    try:
                        selected_transcript = transcript_list.find_transcript(languages_to_try)
                        is_generated = getattr(selected_transcript, "is_generated", False)
                    except Exception:
                        pass

                # 4. If still not found, check ALL available transcripts for this video
                if not selected_transcript:
                    available = list(transcript_list)
                    if not available:
                        raise TranscriptNotFoundError(f"No transcripts found for video {canonical_id}.")

                    # Prefer translatable to English
                    translatable = next((t for t in available if getattr(t, "is_translatable", False)), None)
                    if translatable:
                        try:
                            selected_transcript = translatable.translate("en")
                            detected_lang = "en (auto-translated)"
                            is_generated = getattr(translatable, "is_generated", True)
                        except Exception:
                            selected_transcript = available[0]
                            is_generated = getattr(selected_transcript, "is_generated", True)
                    else:
                        # Use the primary available transcript (e.g. Hindi, Spanish, French, etc.)
                        selected_transcript = available[0]
                        is_generated = getattr(selected_transcript, "is_generated", True)

                detected_lang = getattr(selected_transcript, "language_code", detected_lang)
                raw_snippets = selected_transcript.fetch()

            except (AttributeError, TypeError):
                # Fallback directly to fetch() if list() is not supported on mock/api
                raw_snippets = self.api.fetch(canonical_id, languages=languages_to_try)
                is_generated = False

            # Normalize snippets into structured dataclass items
            snippets: List[TranscriptSnippetData] = []
            for item in raw_snippets:
                # Handle both dict-like items and object-like FetchedTranscriptSnippet
                if isinstance(item, dict):
                    text = item.get("text", "")
                    start = float(item.get("start", 0.0))
                    duration = float(item.get("duration", 0.0))
                else:
                    text = getattr(item, "text", "")
                    start = float(getattr(item, "start", 0.0))
                    duration = float(getattr(item, "duration", 0.0))

                cleaned_text = text.replace("\n", " ").strip()
                if cleaned_text:
                    snippets.append(
                        TranscriptSnippetData(
                            text=cleaned_text,
                            start=start,
                            duration=duration,
                        )
                    )

            if not snippets:
                raise TranscriptNotFoundError(f"Transcript for video {canonical_id} contains no text.")

            logger.info(
                f"Successfully retrieved {len(snippets)} snippets for {canonical_id} "
                f"(lang={detected_lang}, generated={is_generated})"
            )

            return TranscriptResult(
                video_id=canonical_id,
                snippets=snippets,
                language=detected_lang,
                is_generated=is_generated,
                title=video_title,
            )

        except TranscriptsDisabled as e:
            logger.warning(f"Transcripts disabled for video {canonical_id}: {e}")
            raise TranscriptDisabledError(
                f"Transcripts are disabled by the creator for video {canonical_id}."
            ) from e

        except NoTranscriptFound as e:
            logger.warning(f"No transcript found for video {canonical_id}: {e}")
            raise TranscriptNotFoundError(
                f"No transcript tracks could be retrieved for video {canonical_id}."
            ) from e

        except VideoUnavailable as e:
            logger.warning(f"Video {canonical_id} is unavailable: {e}")
            raise VideoUnavailableError(f"Video {canonical_id} is unavailable or private.") from e

        except (TranscriptDisabledError, TranscriptNotFoundError, VideoUnavailableError):
            raise

        except Exception as e:
            logger.error(f"Unexpected error fetching transcript for {canonical_id}: {e}", exc_info=True)
            raise TranscriptNotFoundError(f"Failed to retrieve transcript: {str(e)}") from e

