
import re
from urllib.parse import parse_qs, urlparse

#from youtube_transcript_api import YouTubeTranscriptApi

from app.ingestion.transcript_provider import (
    fetch_transcript_from_provider,
)


def extract_video_id(url: str) -> str:
    """Extract and validate a YouTube video ID from a URL."""

    parsed_url = urlparse(url.strip())
    hostname = (parsed_url.hostname or "").lower()

    allowed_hosts = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }

    if hostname not in allowed_hosts:
        raise ValueError("Please provide a valid YouTube URL.")

    video_id = None

    if hostname.endswith("youtu.be"):
        video_id = parsed_url.path.strip("/").split("/")[0]

    elif parsed_url.path == "/watch":
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    else:
        match = re.match(
            r"^/(?:shorts|embed|live)/([A-Za-z0-9_-]+)",
            parsed_url.path,
        )
        if match:
            video_id = match.group(1)

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Could not extract a valid YouTube video ID.")

    return video_id


def fetch_transcript(
    url: str,
    languages: list[str] | None = None,
) -> list[dict]:
    video_id = extract_video_id(url)

    return fetch_transcript_from_provider(
        video_id=video_id,
        languages=languages,
    )

""" def fetch_transcript(
    url: str,
    languages: list[str] | None = None,
) -> list[dict]:
    
    #Fetch available captions for a YouTube video.

    #Each returned segment contains text, start time, and duration.
    

    video_id = extract_video_id(url)

    if languages is None:
        languages = ["ar", "en", "fr"]

    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=languages)

    segments = []

    for snippet in transcript:
        segments.append(
            {
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration,
            }
        )

    if not segments:
        raise ValueError("The video transcript is empty.")

    return segments

 """
def segments_to_text(segments: list[dict]) -> str:
    """Combine transcript segments into a single text."""

    return " ".join(
        segment["text"].strip()
        for segment in segments
        if segment["text"].strip()
    )


if __name__ == "__main__":
    video_url = input("Enter a YouTube URL: ").strip()

    try:
        video_id = extract_video_id(video_url)
        print(f"\nVideo ID: {video_id}")

        segments = fetch_transcript(video_url)
        transcript_text = segments_to_text(segments)

        print(f"\nNumber of segments: {len(segments)}")
        print("\nFirst 5 transcript segments:")

        for segment in segments[:5]:
            print(
                f"[{segment['start']:.1f}s] "
                f"{segment['text']}"
            )

        print("\nTranscript preview:")
        print(transcript_text[:1000])

    except ValueError as error:
        print(f"Input error: {error}")

    except Exception as error:
        print(f"Could not retrieve the transcript: {error}")
        print(
            "Check your internet connection and whether "
            "captions are available for this video."
        )
