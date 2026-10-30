
from pathlib import Path
from typing import Any

import chromadb
import ollama




EMBEDDING_MODEL = "embeddinggemma"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"

# Persistent storage: the database remains available after restarting.
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


def get_video_collection(video_id: str):
    """Get or create a separate vector collection for a video."""

    collection_name = f"video_{video_id}"

    return  chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts using Ollama."""

    if not texts:
        return []

    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return response["embeddings"]


def index_chunks(
    video_id: str,
    chunks: list[dict[str, Any]],
) -> int:
    """
    Generate embeddings and store timestamped chunks in Chroma.

    Returns the number of indexed chunks.
    """

    if not chunks:
        return 0

    collection = get_video_collection(video_id)

    # Create one embedding for each transcript chunk.
    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts)

    # Use stable IDs so re-indexing updates existing chunks.
    ids = [
        f"chunk_{chunk['chunk_id']}"
        for chunk in chunks
    ]

    metadatas = [
        {
            "chunk_id": int(chunk["chunk_id"]),
            "start": float(chunk["start"]),
            "end": float(chunk["end"]),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


def search_similar_chunks(
    video_id: str,
    question: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find transcript chunks semantically related to a question."""

    if not question.strip():
        raise ValueError("The question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = get_video_collection(video_id)

    if collection.count() == 0:
        return []

    # Convert the question into a vector using the same model.
    query_embedding = create_embeddings([question])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    retrieved_chunks = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        retrieved_chunks.append(
            {
                "chunk_id": metadata["chunk_id"],
                "start": metadata["start"],
                "end": metadata["end"],
                "text": document,
                "distance": distance,
            }
        )

    return retrieved_chunks
