from __future__ import annotations

import hashlib
from pathlib import Path

from celery import shared_task
from django.utils import timezone

from apps.candidates.name_extraction import infer_candidate_profile_from_resume_text
from apps.documents.models import Document, DocumentChunk, ParseStatus
from apps.search.chunking import build_chunks
from apps.search.vectorstore import get_vector_store, normalize_metadata

from .mime_types import detect_mime_type
from .parsers.registry import parser_registry


def calculate_sha256(file_path: str) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file_handle:
        while True:
            chunk = file_handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@shared_task
def parse_and_index_document(document_id: int) -> dict:
    document = Document.objects.select_related("candidate").get(pk=document_id)
    document.parse_status = ParseStatus.PROCESSING
    document.error_message = ""
    document.save(update_fields=["parse_status", "error_message", "updated_at"])

    try:
        file_path = document.uploaded_file.path
        mime_type = detect_mime_type(file_path)
        parser = parser_registry.get_parser(mime_type)
        parsed_document = parser.parse(file_path)
        if not parsed_document.text.strip():
            raise ValueError("The parser did not extract any text from the document.")

        candidate_profile = infer_candidate_profile_from_resume_text(parsed_document.text)
        document.candidate.first_name = candidate_profile["first_name"]
        document.candidate.last_name = candidate_profile["last_name"]
        document.candidate.headline = candidate_profile["headline"]
        document.candidate.save(update_fields=["first_name", "last_name", "headline", "updated_at"])

        vector_store = get_vector_store()
        old_vector_ids = list(document.chunks.values_list("vector_document_id", flat=True))
        if old_vector_ids:
            vector_store.delete(ids=old_vector_ids)

        chunk_metadata = {
            "candidate_id": document.candidate_id,
            "candidate_name": document.candidate.display_name,
            "document_id": document.id,
            "document_filename": document.original_filename,
            "mime_type": mime_type,
        }
        split_documents = build_chunks(parsed_document.text, chunk_metadata)
        if not split_documents:
            raise ValueError("No chunks were created for the document.")

        vector_documents = []
        chunk_ids: list[str] = []
        chunk_rows: list[DocumentChunk] = []
        for chunk_index, split_document in enumerate(split_documents):
            vector_document_id = f"document-{document.id}-chunk-{chunk_index}"
            metadata = normalize_metadata(split_document.metadata)
            vector_documents.append(split_document)
            chunk_ids.append(vector_document_id)
            chunk_rows.append(
                DocumentChunk(
                    document=document,
                    candidate=document.candidate,
                    chunk_index=chunk_index,
                    chunk_text=split_document.page_content,
                    start_index=int(metadata.get("start_index", 0) or 0),
                    metadata=metadata,
                    vector_document_id=vector_document_id,
                )
            )

        document.chunks.all().delete()
        vector_store.add_documents(vector_documents, ids=chunk_ids)
        DocumentChunk.objects.bulk_create(chunk_rows)

        document.mime_type = mime_type
        document.sha256 = calculate_sha256(file_path)
        document.parser_name = parser.parser_name
        document.parsed_text = parsed_document.text
        document.parser_metadata = parsed_document.metadata
        document.parse_status = ParseStatus.INDEXED
        document.indexed_at = timezone.now()
        document.error_message = ""
        document.save(
            update_fields=[
                "mime_type",
                "sha256",
                "parser_name",
                "parsed_text",
                "parser_metadata",
                "parse_status",
                "indexed_at",
                "error_message",
                "updated_at",
            ]
        )
        return {
            "document_id": document.id,
            "candidate_id": document.candidate_id,
            "mime_type": mime_type,
            "chunk_count": len(chunk_rows),
        }
    except Exception as exc:
        document.parse_status = ParseStatus.FAILED
        document.error_message = str(exc)
        document.save(update_fields=["parse_status", "error_message", "updated_at"])
        raise
