import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.youtube import (
    extract_video_id,
    fetch_transcript,
)
from app.processing.chunking import create_chunks
from app.rag.vector_store import (
    get_video_collection,
    index_chunks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = PROJECT_ROOT / "data" / "videos"


def get_metadata_path(video_id: str) -> Path:
    """Return the path of a video's metadata file."""

    return METADATA_DIR / f"{video_id}.json"


def load_video_metadata(video_id: str) -> dict | None:
    """Load saved metadata if it exists."""

    metadata_path = get_metadata_path(video_id)

    if not metadata_path.exists():
        return None

    with metadata_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def process_video(
    video_url: str,
    force_reindex: bool = False,
) -> dict:
    """
    Extract, chunk, and index a video only when necessary.

    Existing indexed videos are reused by default.
    """

    video_id = extract_video_id(video_url)

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    collection = get_video_collection(video_id)
    metadata = load_video_metadata(video_id)

    # Reuse existing data when both metadata and vectors exist.
    if (
        not force_reindex
        and metadata is not None
        and collection.count() > 0
    ):
        print("Video already indexed. Reusing saved data.")
        return metadata

    if force_reindex:
        from app.rag.vector_store import chroma_client

        chroma_client.delete_collection(
            name=f"video_{video_id}"
        )

    print("Extracting transcript...")
    segments = fetch_transcript(video_url)

    print("Creating timestamped chunks...")
    chunks = create_chunks(
        segments,
        max_chars=2500,
        overlap_segments=2,
    )

    if not chunks:
        raise ValueError("No usable transcript chunks were created.")

    print(f"Indexing {len(chunks)} chunks...")
    indexed_count = index_chunks(video_id, chunks)

    metadata = {
        "video_id": video_id,
        "source_url": video_url,
        "transcript_segment_count": len(segments),
        "chunk_count": indexed_count,
        "embedding_model": ("embeddinggemma"if os.getenv("EMBEDDING_PROVIDER", "ollama").lower()== "ollama"else "gemini-embedding-001"),
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = get_metadata_path(video_id)

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Video indexed successfully: {video_id}")
    print(f"Metadata saved to: {metadata_path}")

    return metadata