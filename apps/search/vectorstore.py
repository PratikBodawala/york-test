from typing import Any

from django.conf import settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector


def get_embeddings() -> OpenAIEmbeddings:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required for embedding documents.")

    return OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )


def get_chat_model() -> ChatOpenAI:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required for reranking candidates.")

    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_RERANK_MODEL,
        temperature=0,
    )


def get_vector_store() -> PGVector:
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.PGVECTOR_COLLECTION,
        connection=settings.PGVECTOR_CONNECTION,
        use_jsonb=True,
    )


def normalize_metadata(raw_metadata: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in raw_metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[key] = value
            continue

        normalized[key] = str(value)
    return normalized
