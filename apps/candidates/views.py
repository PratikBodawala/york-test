from uuid import uuid4

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.documents.models import Document
from apps.ingestion.tasks import parse_and_index_document

from .name_extraction import infer_candidate_profile_from_resume_text
from .models import Candidate


def build_pending_candidate_profile() -> dict[str, str]:
    candidate_data = infer_candidate_profile_from_resume_text("")
    candidate_data["email"] = f"uploaded-{uuid4().hex[:12]}@local.resume"
    return candidate_data


@csrf_exempt
@require_http_methods(["POST"])
def upload_candidate_resume(request: HttpRequest) -> JsonResponse:
    uploaded_files = request.FILES.getlist("files")
    if not uploaded_files:
        uploaded_file = request.FILES.get("file")
        if uploaded_file is not None:
            uploaded_files = [uploaded_file]

    if not uploaded_files:
        return JsonResponse({"error": "At least one resume file is required."}, status=400)

    uploads: list[dict] = []
    for uploaded_file in uploaded_files:
        candidate_data = build_pending_candidate_profile()
        candidate = Candidate.objects.create(
            first_name=candidate_data["first_name"],
            last_name=candidate_data["last_name"],
            email=candidate_data["email"],
            headline=candidate_data["headline"],
        )
        document = Document.objects.create(
            candidate=candidate,
            uploaded_file=uploaded_file,
            original_filename=uploaded_file.name,
        )
        async_result = parse_and_index_document.apply_async(args=(document.id,))
        uploads.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.display_name,
                "name_source": "resume_content_pending",
                "document_id": document.id,
                "file_name": document.original_filename,
                "parse_status": document.parse_status,
                "task_id": async_result.id,
            }
        )

    return JsonResponse(
        {
            "upload_count": len(uploads),
            "uploads": uploads,
        },
        status=202,
    )


@require_GET
def document_status(request: HttpRequest, document_id: int) -> JsonResponse:
    try:
        document = Document.objects.select_related("candidate").get(pk=document_id)
    except Document.DoesNotExist:
        return JsonResponse({"error": "Document not found."}, status=404)

    payload = {
        "document_id": document.id,
        "candidate_id": document.candidate_id,
        "candidate_name": document.candidate.display_name,
        "file_name": document.original_filename,
        "mime_type": document.mime_type,
        "parse_status": document.parse_status,
        "parser_name": document.parser_name,
        "error_message": document.error_message,
        "chunk_count": document.chunks.count(),
        "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
    }
    return JsonResponse(payload)
