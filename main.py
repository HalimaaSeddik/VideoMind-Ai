from app.video_service import process_video
from app.rag.qa import answer_question


def main():
    video_url = input("Enter a YouTube URL: ").strip()

    try:
        metadata = process_video(video_url)

        video_id = metadata["video_id"]

        print("\nVideo is ready!")
        print(f"Video ID: {video_id}")
        print(f"Indexed chunks: {metadata['chunk_count']}")

        print("\nYou can now ask questions about the video.")
        print("Type 'exit' to quit.")

        while True:
            question = input("\nYour question: ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            if not question:
                print("Please enter a question.")
                continue

            result = answer_question(
                video_id=video_id,
                question=question,
                language="Arabic",
            )

            print("\nAnswer:")
            print(result["answer"])

            if result["sources"]:
                print("\nRelevant video sections:")

                for source in result["sources"]:
                    start = source["start"]
                    end = source["end"]

                    print(
                        f"- {start:.1f}s - {end:.1f}s"
                    )

    except Exception as error:
        print(f"\nAn error occurred: {error}")
        raise


if __name__ == "__main__":
    main()