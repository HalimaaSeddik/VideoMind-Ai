import ollama
from pydantic import BaseModel, Field

MODEL_NAME = "phi3"



class VideoSummary(BaseModel):
    """Structured output for a video summary."""

    title: str = Field(description="A short, descriptive title for the video")

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


def summarize_transcript(transcript: str, language: str = "Arabic") -> str:
    """
    Generate a structured summary of a video transcript.

    Args:
        transcript: The transcript text to summarize.
        language: The language of the generated summary.

    Returns:
        A structured summary as a string.
    """

    if not transcript or not transcript.strip():
        raise ValueError("The transcript cannot be empty.")

    prompt = f"""
    You are an expert educational assistant.

    Your task is to summarize a video transcript accurately.

    Rules:
    1. Use only information supported by the transcript.
    2. Do not invent facts or examples.
    3. Preserve the speaker's main ideas and important details.
    4. Organize the summary using clear headings.
    5. Write the output in {language}.

    Return the following sections:

    1. TITLE
    2. SHORT SUMMARY
    3. DETAILED SUMMARY
    4. KEY TAKEAWAYS
    5. IMPORTANT CONCEPTS

    VIDEO TRANSCRIPT:
    {transcript}
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format=VideoSummary.model_json_schema(),
    )
    content = response.message.content
    if not content :
        raise ValueError("The model returned an empty response.")
    summary = VideoSummary.model_validate_json(content)

    return summary


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