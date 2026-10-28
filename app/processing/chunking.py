from typing import Any


def create_chunks(
    segments: list[dict[str, Any]],
    max_chars: int = 2500,
    overlap_segments: int = 2,
) -> list[dict[str, Any]]:
    """
    Split timestamped transcript segments into smaller chunks.

    Args:
        segments: Transcript segments containing text, start, duration.
        max_chars: Approximate maximum number of characters per chunk.
        overlap_segments: Number of segments repeated between chunks.

    Returns:
        A list of chunks containing text and timestamps.
    """

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    if overlap_segments < 0:
        raise ValueError("overlap_segments cannot be negative.")

    if not segments:
        return []

    chunks = []
    current_segments = []
    current_chars = 0

    def save_chunk(items: list[dict[str, Any]]) -> None:
        if not items:
            return

        text = " ".join(
            item["text"].strip()
            for item in items
            if item["text"].strip()
        )

        if not text:
            return

        start = items[0]["start"]
        end = max(
            item["start"] + item["duration"]
            for item in items
        )

        chunks.append(
            {
                "chunk_id": len(chunks) + 1,
                "text": text,
                "start": start,
                "end": end,
                "char_count": len(text),
                    
            }
        )

    for segment in segments:
        text = segment["text"].strip()

        if not text:
            continue

        # A single segment may itself exceed max_chars.
        if len(text) > max_chars:
            if current_segments:
                save_chunk(current_segments)

                if overlap_segments:
                    current_segments = current_segments[
                        -overlap_segments:
                    ]
                else:
                    current_segments = []

                current_chars = sum(
                    len(item["text"].strip()) + 1
                    for item in current_segments
                )

            save_chunk([segment])

            # Avoid repeating the oversized segment indefinitely.
            current_segments = []
            current_chars = 0
            continue

        additional_chars = len(text) + (1 if current_segments else 0)

        if (
            current_segments
            and current_chars + additional_chars > max_chars
        ):
            save_chunk(current_segments)

            # Keep a small overlap to preserve context.
            if overlap_segments:
                current_segments = current_segments[
                    -overlap_segments:
                ]
            else:
                current_segments = []

            current_chars = sum(
                len(item["text"].strip()) + 1
                for item in current_segments
            )

        current_segments.append(segment)
        current_chars += len(text) + 1

    if current_segments:
        save_chunk(current_segments)

    return chunks


if __name__ == "__main__":
    # Small test dataset: no internet connection is needed.
    sample_segments = [
        {
            "text": "Introduction to artificial intelligence.",
            "start": 0.0,
            "duration": 4.0,
        },
        {
            "text": "Machine learning is a subfield of AI.",
            "start": 4.0,
            "duration": 4.0,
        },
        {
            "text": "Supervised learning uses labeled data.",
            "start": 8.0,
            "duration": 4.0,
        },
        {
            "text": "Deep learning uses neural networks.",
            "start": 12.0,
            "duration": 4.0,
        },
        {
            "text": "Neural networks can learn complex patterns.",
            "start": 16.0,
            "duration": 4.0,
        },
    ]

    chunks = create_chunks(
        sample_segments,
        max_chars=100,
        overlap_segments=1,
    )

    for chunk in chunks:
        print(f"\nChunk {chunk['chunk_id']}")
        print(f"Time: {chunk['start']}s - {chunk['end']}s")
        print(f"Characters: {chunk['char_count']}")
        print(f"Text: {chunk['text']}")