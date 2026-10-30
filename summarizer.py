from pydantic import BaseModel, Field

from app.llm import client, GROQ_MODEL


class VideoSummary(BaseModel):
    """Structured output for a video summary."""

    title: str = Field(
        description="A short, descriptive title for the video"
    )

    short_summary: str = Field(
        description="A concise summary of the main idea"
    )

    detailed_summary: str = Field(
        description="A detailed summary of the important information"
    )

    key_takeaways: list[str] = Field(
        description="The most important lessons from the video"
    )

    important_concepts: list[str] = Field(
        description="Important concepts explained in the video"
    )


def summarize_transcript(
    transcript: str,
    language: str = "Arabic",
) -> VideoSummary:
    """Generate a structured summary using Groq."""

    if not transcript or not transcript.strip():
        raise ValueError("The transcript cannot be empty.")

    prompt = f"""
Summarize the following video transcript in {language}.

Rules:
1. Use only information supported by the transcript.
2. Do not invent facts or examples.
3. Preserve the speaker's main ideas and important details.
4. Make the summary clear, educational, and well-organized.
5. Write every summary field in {language}.
6. If a detail is not available in the transcript, do not invent it.

Return a valid JSON object with exactly these fields:
- title: string
- short_summary: string
- detailed_summary: string
- key_takeaways: array of strings
- important_concepts: array of strings

Do not include Markdown fences or text outside the JSON object.

VIDEO TRANSCRIPT:
{transcript}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are VideoMind AI, an educational assistant. "
                    "Return the requested summary as valid JSON. "
                    "Ground all claims in the provided transcript."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty summary.")

    try:
        return VideoSummary.model_validate_json(content)
    except ValueError as exc:
        raise ValueError(
            f"Groq returned an invalid summary JSON: {exc}"
        ) from exc
      

    


if __name__ == "__main__":
    sample_transcript = """
    Artificial intelligence is a field of computer science
    that aims to build systems capable of performing tasks
    that normally require human intelligence.

    Machine learning is a subfield of artificial intelligence.
    It allows systems to learn patterns from data.

    Supervised learning uses labeled examples to train a model.
    Unsupervised learning attempts to discover patterns in
    data without predefined labels.

    Deep learning uses neural networks with multiple layers
    to learn complex representations.
    """

    result = summarize_transcript(
        transcript=sample_transcript,
        language="Arabic",
    )

    print("\n===== VIDEOMIND AI SUMMARY =====\n")

    print("TITLE:")
    print(result.title)

    print("\nSHORT SUMMARY:")
    print(result.short_summary)

    print("\nDETAILED SUMMARY:")
    print(result.detailed_summary)

    print("\nKEY TAKEAWAYS:")
    for takeaway in result.key_takeaways:
        print(f"- {takeaway}")

    print("\nIMPORTANT CONCEPTS:")
    for concept in result.important_concepts:
        print(f"- {concept}")

    print("\n===== VALIDATED PYDANTIC OBJECT =====")
    print(result.model_dump_json(indent=2))