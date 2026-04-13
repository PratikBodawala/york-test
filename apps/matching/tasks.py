from celery import shared_task
from django.utils import timezone

from .models import CandidateMatch, JobRequest, MatchStatus
from .services import aggregate_candidates, rerank_candidates


@shared_task
def generate_candidate_matches(job_request_id: int) -> dict:
    job_request = JobRequest.objects.get(pk=job_request_id)
    job_request.status = MatchStatus.PROCESSING
    job_request.error_message = ""
    job_request.completed_at = None
    job_request.save(update_fields=["status", "error_message", "completed_at", "updated_at"])

    try:
        CandidateMatch.objects.filter(job_request=job_request).delete()

        candidate_summaries = aggregate_candidates(job_request)
        ranked_results = rerank_candidates(job_request, candidate_summaries)

        match_rows = [
            CandidateMatch(
                job_request=job_request,
                candidate=result["candidate"],
                rank=result["rank"],
                retrieval_score=result["retrieval_score"],
                fit_score=result["fit_score"],
                final_score=result["final_score"],
                matched_skills=result["matched_skills"],
                risks=result["risks"],
                explanation=result["explanation"],
                supporting_chunks=result["supporting_chunks"],
            )
            for result in ranked_results
        ]
        CandidateMatch.objects.bulk_create(match_rows)

        job_request.status = MatchStatus.COMPLETED
        job_request.completed_at = timezone.now()
        job_request.save(update_fields=["status", "completed_at", "updated_at"])
        return {
            "job_request_id": job_request.id,
            "match_count": len(match_rows),
        }
    except Exception as exc:
        job_request.status = MatchStatus.FAILED
        job_request.error_message = str(exc)
        job_request.save(update_fields=["status", "error_message", "updated_at"])
        raise
