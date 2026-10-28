import json
from pathlib import Path

from app.ingestion.youtube import (
    extract_video_id,
    fetch_transcript,
    segments_to_text,
)
from app.processing.chunking import create_chunks
from summarizer import summarize_transcript


OUTPUT_DIR = Path("outputs")


def summarize_video(
    video_url: str,
    language: str = "Arabic",
) -> dict:
    """
    Run the complete video summarization pipeline.

    Steps:
        1. Extract the video transcript.
        2. Split it into timestamped chunks.
        3. Summarize each chunk.
        4. Combine partial summaries.
        5. Generate the final summary.
        6. Save the results as JSON.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Identify the video.
    video_id = extract_video_id(video_url)

    print("\n[1/5] Extracting video transcript...")

    segments = fetch_transcript(video_url)

    if not segments:
        raise ValueError("No transcript segments were found.")

    print(f"      Retrieved {len(segments)} segments.")

    # Step 2: Prepare chunks.
    print("\n[2/5] Splitting transcript into chunks...")

    chunks = create_chunks(
        segments,
        max_chars=2500,
        overlap_segments=2,
    )

    if not chunks:
        raise ValueError("Could not create transcript chunks.")

    print(f"      Created {len(chunks)} chunks.")

    # Step 3: Summarize each chunk sequentially.
    print("\n[3/5] Summarizing individual chunks...")

    partial_summaries = []

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"      Summarizing chunk {index}/{len(chunks)} "
            f"({chunk['start']:.1f}s - {chunk['end']:.1f}s)"
        )

        summary = summarize_transcript(
            transcript=chunk["text"],
            language=language,
        )

        partial_summaries.append(
            {
                "chunk_id": chunk["chunk_id"],
                "start": chunk["start"],
                "end": chunk["end"],
                "summary": summary.model_dump(),
            }
        )

    # Step 4: Combine the partial summaries.
    print("\n[4/5] Combining partial summaries...")

    combined_text_parts = []

    for item in partial_summaries:
        summary = item["summary"]

        combined_text_parts.append(
            f"""
            Transcript section:
            {item['start']:.1f}s - {item['end']:.1f}s

            Title: {summary['title']}

            Short summary:
            {summary['short_summary']}

            Detailed summary:
            {summary['detailed_summary']}

            Key takeaways:
            {chr(10).join(summary['key_takeaways'])}

            Important concepts:
            {chr(10).join(summary['important_concepts'])}
            """
        )

    combined_text = "\n\n".join(combined_text_parts)

    # Step 5: Produce the final summary.
    print("\n[5/5] Generating final summary...")

    final_summary = summarize_transcript(
        transcript=combined_text,
        language=language,
    )

    result = {
        "video_id": video_id,
        "source_url": video_url,
        "transcript_segment_count": len(segments),
        "chunk_count": len(chunks),
        "partial_summaries": partial_summaries,
        "final_summary": final_summary.model_dump(),
    }

    # Save the output so we can reuse it later.
    output_path = OUTPUT_DIR / f"{video_id}_summary.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nResults saved to: {output_path}")

    return result


if __name__ == "__main__":
    url = input("Enter a YouTube video URL: ").strip()

    try:
        result = summarize_video(url)

        print("\n" + "=" * 50)
        print("FINAL VIDEO SUMMARY")
        print("=" * 50)

        final = result["final_summary"]

        print(f"\nTITLE:\n{final['title']}")
        print(f"\nSHORT SUMMARY:\n{final['short_summary']}")
        print(f"\nDETAILED SUMMARY:\n{final['detailed_summary']}")

        print("\nKEY TAKEAWAYS:")
        for takeaway in final["key_takeaways"]:
            print(f"- {takeaway}")

        print("\nIMPORTANT CONCEPTS:")
        for concept in final["important_concepts"]:
            print(f"- {concept}")

    except Exception as error:
        print(f"\nPipeline failed: {error}")
        raise