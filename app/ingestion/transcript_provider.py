import os
import requests


BASE_URL = "https://api.freetranscriptapi.com/v1/transcript"


class TranscriptProviderError(Exception):
    """General error returned by the transcript provider."""


class TranscriptUnavailableError(TranscriptProviderError):
    """The video has no available transcript."""


class TranscriptRateLimitError(TranscriptProviderError):
    """The provider rate limit has been reached."""


class TranscriptAuthenticationError(TranscriptProviderError):
    """The API key is missing or invalid."""


def fetch_transcript_from_provider(
    video_id: str,
    languages: list[str] | None = None,
) -> list[dict]:
    api_key = os.getenv("FREETRANSCRIPT_API_KEY")

    # Arabic is preferred by default. The API can fall back to
    # another available transcript language.
    language = languages[0] if languages else "ar"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    params = {
        "video_url": video_id,
        "lang": language,
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=60,
        )

    except requests.exceptions.Timeout as exc:
        raise TranscriptProviderError(
            "The transcript provider took too long to respond."
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise TranscriptProviderError(
            "Could not connect to the transcript provider."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise TranscriptProviderError(
            f"Transcript request failed: {exc}"
        ) from exc

    if response.status_code == 401:
        raise TranscriptAuthenticationError(
            "The transcript API key is invalid."
        )

    if response.status_code == 402:
        raise TranscriptProviderError(
            "The transcript API account has insufficient credits."
        )

    if response.status_code == 404:
        raise TranscriptUnavailableError(
            "No transcript was found for this video."
        )

    if response.status_code == 429:
        raise TranscriptRateLimitError(
            "The transcript provider rate limit has been reached."
        )

    if response.status_code >= 500:
        raise TranscriptProviderError(
            "The transcript provider is temporarily unavailable."
        )

    if not response.ok:
        raise TranscriptProviderError(
            f"Transcript API returned HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise TranscriptProviderError(
            "The transcript provider returned invalid JSON."
        ) from exc

    raw_segments = data.get("transcript")

    if not isinstance(raw_segments, list) or not raw_segments:
        raise TranscriptUnavailableError(
            "The API response does not contain transcript segments."
        )

    segments = []

    for item in raw_segments:
        text = item.get("text")

        if not isinstance(text, str) or not text.strip():
            continue

        try:
            start = float(item["start"])
            duration = float(item["duration"])
        except (KeyError, TypeError, ValueError):
            continue

        segments.append({
            "text": text.strip(),
            "start": start,
            "duration": duration,
        })

    if not segments:
        raise TranscriptUnavailableError(
            "The transcript contains no valid segments."
        )

    return segments