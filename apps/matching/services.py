from __future__ import annotations

import json
from dataclasses import dataclass

from django.conf import settings
from pydantic import BaseModel, Field

from apps.candidates.models import Candidate
from apps.search.vectorstore import get_chat_model, get_vector_store

from .models import JobRequest


@dataclass(slots=True)
class CandidateSummary:
    candidate: Candidate
    retrieval_score: float
    supporting_chunks: list[str]


class CandidateRanking(BaseModel):
    candidate_id: int
    fit_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    explanation: str


class RerankResponse(BaseModel):
    rankings: list[CandidateRanking]


def aggregate_candidates(job_request: JobRequest) -> list[CandidateSummary]:
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(
        query=job_request.description_text,
        k=job_request.retrieval_k,
    )

    grouped: dict[int, dict] = {}
    for document, score in results:
        candidate_id = int(document.metadata["candidate_id"])
        grouped_entry = grouped.setdefault(
            candidate_id,
            {
                "scores": [],
                "chunks": [],
            },
        )
        grouped_entry["scores"].append(float(score))
        if document.page_content not in grouped_entry["chunks"]:
            grouped_entry["chunks"].append(document.page_content)

    candidates = Candidate.objects.in_bulk(grouped.keys())
    summaries: list[CandidateSummary] = []
    for candidate_id, grouped_entry in grouped.items():
        candidate = candidates.get(candidate_id)
        if candidate is None:
            continue

        top_scores = sorted(grouped_entry["scores"], reverse=True)[:3]
        average_score = sum(top_scores) / len(top_scores)
        diversity_bonus = min(len(grouped_entry["chunks"]), 3) * 0.01
        summaries.append(
            CandidateSummary(
                candidate=candidate,
                retrieval_score=round(average_score + diversity_bonus, 4),
                supporting_chunks=grouped_entry["chunks"][:3],
            )
        )

    summaries.sort(key=lambda summary: summary.retrieval_score, reverse=True)
    rerank_pool_size = max(job_request.top_k * 2, 15)
    return summaries[:rerank_pool_size]


def rerank_candidates(job_request: JobRequest, summaries: list[CandidateSummary]) -> list[dict]:
    if not summaries:
        return []

    if not settings.OPENAI_API_KEY:
        return fallback_rankings(summaries, top_k=job_request.top_k)

    model = get_chat_model().with_structured_output(RerankResponse)
    payload = {
        "job_request": {
            "title": job_request.title,
            "description_text": job_request.description_text,
        },
        "candidates": [
            {
                "candidate_id": summary.candidate.id,
                "candidate_name": summary.candidate.display_name,
                "headline": summary.candidate.headline,
                "retrieval_score": summary.retrieval_score,
                "supporting_chunks": summary.supporting_chunks,
            }
            for summary in summaries
        ],
    }
    messages = [
        (
            "system",
            (
                "You are ranking candidates for a hiring platform. "
                "Use only the supplied evidence. "
                "Return every candidate in best-to-worst order. "
                "Give each candidate a fit_score from 0 to 100, matched_skills, risks, "
                "and a concise explanation."
            ),
        ),
        ("human", json.dumps(payload, indent=2)),
    ]

    try:
        response = model.invoke(messages)
    except Exception:
        return fallback_rankings(summaries, top_k=job_request.top_k)

    summary_map = {summary.candidate.id: summary for summary in summaries}
    ranked_results: list[dict] = []
    seen_candidate_ids: set[int] = set()
    for rank_index, ranking in enumerate(response.rankings, start=1):
        summary = summary_map.get(ranking.candidate_id)
        if summary is None:
            continue
        seen_candidate_ids.add(ranking.candidate_id)
        ranked_results.append(
            {
                "candidate": summary.candidate,
                "rank": rank_index,
                "retrieval_score": summary.retrieval_score,
                "fit_score": float(ranking.fit_score),
                "final_score": float(ranking.fit_score),
                "matched_skills": ranking.matched_skills,
                "risks": ranking.risks,
                "explanation": ranking.explanation,
                "supporting_chunks": summary.supporting_chunks,
            }
        )

    if len(ranked_results) < job_request.top_k:
        fallback_results = fallback_rankings(
            [summary for summary in summaries if summary.candidate.id not in seen_candidate_ids],
            top_k=job_request.top_k,
        )
        for fallback_result in fallback_results:
            fallback_result["rank"] = len(ranked_results) + 1
            ranked_results.append(fallback_result)
            if len(ranked_results) >= job_request.top_k:
                break

    return ranked_results[: job_request.top_k]


def fallback_rankings(summaries: list[CandidateSummary], top_k: int) -> list[dict]:
    results: list[dict] = []
    for rank_index, summary in enumerate(summaries[:top_k], start=1):
        top_excerpt = summary.supporting_chunks[0][:280]
        results.append(
            {
                "candidate": summary.candidate,
                "rank": rank_index,
                "retrieval_score": summary.retrieval_score,
                "fit_score": round(summary.retrieval_score * 100, 2),
                "final_score": round(summary.retrieval_score * 100, 2),
                "matched_skills": [],
                "risks": ["LLM reranker unavailable; using semantic retrieval score only."],
                "explanation": (
                    "Ranked by semantic retrieval score. "
                    f"Top evidence: {top_excerpt}"
                ),
                "supporting_chunks": summary.supporting_chunks,
            }
        )
    return results
