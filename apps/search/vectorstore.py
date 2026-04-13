import threading
import time
from typing import Any

from django.conf import settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy.exc import IntegrityError


_VECTOR_STORE: PGVector | None = None
_VECTOR_STORE_LOCK = threading.Lock()


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


def build_vector_store() -> PGVector:
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.PGVECTOR_COLLECTION,
        connection=settings.PGVECTOR_CONNECTION,
        use_jsonb=True,
    )


def should_retry_vector_store_initialization(exc: IntegrityError) -> bool:
    message = str(exc)
    return (
        "pg_type_typname_nsp_index" in message
        or "langchain_pg_collection" in message
        or "already exists" in message
    )


def get_vector_store() -> PGVector:
    global _VECTOR_STORE

    if _VECTOR_STORE is not None:
        return _VECTOR_STORE

    with _VECTOR_STORE_LOCK:
        if _VECTOR_STORE is not None:
            return _VECTOR_STORE

        try:
            _VECTOR_STORE = build_vector_store()
        except IntegrityError as exc:
            if not should_retry_vector_store_initialization(exc):
                raise
            # Another worker likely created the schema first; retry once after the race settles.
            time.sleep(0.5)
            _VECTOR_STORE = build_vector_store()

        return _VECTOR_STORE


def normalize_metadata(raw_metadata: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in raw_metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[key] = value
            continue

        normalized[key] = str(value)
    return normalized
