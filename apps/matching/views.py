import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import JobRequest
from .tasks import generate_candidate_matches


@csrf_exempt
@require_http_methods(["POST"])
def create_match_request(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    title = str(payload.get("title", "")).strip()
    description_text = str(payload.get("description_text", "")).strip()
    if not title or not description_text:
        return JsonResponse({"error": "title and description_text are required."}, status=400)

    retrieval_k = int(payload.get("retrieval_k", 50))
    top_k = int(payload.get("top_k", 10))
    job_request = JobRequest.objects.create(
        title=title,
        description_text=description_text,
        retrieval_k=retrieval_k,
        top_k=top_k,
    )
    async_result = generate_candidate_matches.apply_async(args=(job_request.id,))
    return JsonResponse(
        {
            "job_request_id": job_request.id,
            "status": job_request.status,
            "task_id": async_result.id,
        },
        status=202,
    )


@require_GET
def match_status(request: HttpRequest, job_request_id: int) -> JsonResponse:
    try:
        job_request = JobRequest.objects.prefetch_related("matches__candidate").get(pk=job_request_id)
    except JobRequest.DoesNotExist:
        return JsonResponse({"error": "Job request not found."}, status=404)

    matches_payload = [
        {
            "candidate_id": match.candidate_id,
            "candidate_name": match.candidate.display_name,
            "headline": match.candidate.headline,
            "rank": match.rank,
            "retrieval_score": match.retrieval_score,
            "fit_score": match.fit_score,
            "final_score": match.final_score,
            "matched_skills": match.matched_skills,
            "risks": match.risks,
            "explanation": match.explanation,
            "supporting_chunks": match.supporting_chunks,
        }
        for match in job_request.matches.all().order_by("rank")
    ]
    return JsonResponse(
        {
            "job_request_id": job_request.id,
            "title": job_request.title,
            "status": job_request.status,
            "error_message": job_request.error_message,
            "created_at": job_request.created_at.isoformat(),
            "completed_at": job_request.completed_at.isoformat() if job_request.completed_at else None,
            "matches": matches_payload,
        }
    )
