import pytest
from backend.app.core.exceptions import VideoIdError
from backend.app.utils.video_id import build_youtube_watch_url, extract_video_id


def test_extract_video_id_raw():
    assert extract_video_id("Gfr50f6ZBvo") == "Gfr50f6ZBvo"
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_watch_url():
    url = "https://www.youtube.com/watch?v=Gfr50f6ZBvo"
    assert extract_video_id(url) == "Gfr50f6ZBvo"

    url_with_params = "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=120s&feature=shared"
    assert extract_video_id(url_with_params) == "Gfr50f6ZBvo"


def test_extract_video_id_short_url():
    url = "https://youtu.be/Gfr50f6ZBvo"
    assert extract_video_id(url) == "Gfr50f6ZBvo"

    url_with_param = "https://youtu.be/Gfr50f6ZBvo?t=45"
    assert extract_video_id(url_with_param) == "Gfr50f6ZBvo"


def test_extract_video_id_shorts_url():
    url = "https://www.youtube.com/shorts/Gfr50f6ZBvo"
    assert extract_video_id(url) == "Gfr50f6ZBvo"


def test_extract_video_id_embed_url():
    url = "https://www.youtube.com/embed/Gfr50f6ZBvo"
    assert extract_video_id(url) == "Gfr50f6ZBvo"


def test_extract_video_id_live_url():
    url = "https://www.youtube.com/live/Gfr50f6ZBvo"
    assert extract_video_id(url) == "Gfr50f6ZBvo"


def test_extract_video_id_invalid():
    with pytest.raises(VideoIdError):
        extract_video_id("")

    with pytest.raises(VideoIdError):
        extract_video_id("invalid-id")

    with pytest.raises(VideoIdError):
        extract_video_id("https://vimeo.com/123456789")

    with pytest.raises(VideoIdError):
        extract_video_id("https://www.google.com")


def test_build_youtube_watch_url():
    assert (
        build_youtube_watch_url("Gfr50f6ZBvo")
        == "https://www.youtube.com/watch?v=Gfr50f6ZBvo"
    )
    assert (
        build_youtube_watch_url("Gfr50f6ZBvo", timestamp_seconds=125)
        == "https://www.youtube.com/watch?v=Gfr50f6ZBvo&t=125s"
    )

