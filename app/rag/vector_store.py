import math
import os
from pathlib import Path
from typing import Any

import chromadb
import ollama
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Select the embedding provider: "ollama" or "gemini".
EMBEDDING_PROVIDER = os.getenv(
    "EMBEDDING_PROVIDER",
    "ollama",
).lower()

OLLAMA_MODEL = "embeddinggemma"
GEMINI_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


def get_video_collection(video_id: str):
    """Get or create a separate vector collection for a video."""

    return chroma_client.get_or_create_collection(
        name=f"video_{video_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _normalize_embedding(
    embedding: list[float],
) -> list[float]:
    """Normalize an embedding vector to unit length."""

    norm = math.sqrt(sum(value * value for value in embedding))

    if norm == 0:
        raise ValueError("Received an empty embedding vector.")

    return [value / norm for value in embedding]


def create_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """Generate embeddings using the configured provider."""

    if not texts:
        return []

    if EMBEDDING_PROVIDER == "ollama":
        response = ollama.embed(
            model=OLLAMA_MODEL,
            input=texts,
        )

        embeddings = response["embeddings"]

    elif EMBEDDING_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is required when "
                "EMBEDDING_PROVIDER=gemini."
            )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.embed_content(
            model=GEMINI_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSIONS,
            ),
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned no embeddings."
            )

        embeddings = [
            _normalize_embedding(list(item.values))
            for item in response.embeddings
        ]

    else:
        raise ValueError(
            f"Unsupported embedding provider: "
            f"{EMBEDDING_PROVIDER!r}. "
            "Choose 'ollama' or 'gemini'."
        )

    if len(embeddings) != len(texts):
        raise RuntimeError(
            "The number of embeddings does not match "
            "the number of input texts."
        )

    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(embedding)}."
            )

    return embeddings


def index_chunks(
    video_id: str,
    chunks: list[dict[str, Any]],
) -> int:
    """Generate embeddings and store transcript chunks."""

    if not chunks:
        return 0

    collection = get_video_collection(video_id)

    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts)

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
    """Retrieve transcript chunks related to a question."""

    if not question.strip():
        raise ValueError("The question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = get_video_collection(video_id)

    count = collection.count()

    if count == 0:
        return []

    query_embedding = create_embeddings([question])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    retrieved_chunks = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
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