from django.conf import settings
from langchain_core.documents import Document as LangChainDocument

from apps.candidates.models import Candidate
from apps.matching.models import JobRequest
from apps.matching.services import CandidateSummary, aggregate_candidates, rerank_candidates


def test_aggregate_candidates_groups_by_candidate(monkeypatch) -> None:
    alice = Candidate(
        id=1,
        first_name="Alice",
        last_name="Martin",
        email="alice@example.com",
        headline="Senior Backend Engineer",
    )
    ben = Candidate(
        id=2,
        first_name="Ben",
        last_name="Shah",
        email="ben@example.com",
        headline="Data Platform Engineer",
    )

    class DummyVectorStore:
        def similarity_search_with_score(self, query: str, k: int):
            return [
                (
                    LangChainDocument(
                        page_content="Strong Django, Celery, and Redis background.",
                        metadata={"candidate_id": 1},
                    ),
                    0.92,
                ),
                (
                    LangChainDocument(
                        page_content="Built retrieval ranking services on Postgres.",
                        metadata={"candidate_id": 1},
                    ),
                    0.88,
                ),
                (
                    LangChainDocument(
                        page_content="Strong ETL and data platform experience.",
                        metadata={"candidate_id": 2},
                    ),
                    0.73,
                ),
            ]

    monkeypatch.setattr("apps.matching.services.get_vector_store", lambda: DummyVectorStore())
    monkeypatch.setattr(
        "apps.matching.services.Candidate.objects.in_bulk",
        lambda candidate_ids: {1: alice, 2: ben},
    )

    summaries = aggregate_candidates(
        JobRequest(
            title="Platform Backend Engineer",
            description_text="Need Django, Celery, Redis, and ranking pipelines.",
            retrieval_k=10,
            top_k=10,
        )
    )

    assert [summary.candidate.id for summary in summaries] == [1, 2]
    assert summaries[0].retrieval_score > summaries[1].retrieval_score
    assert len(summaries[0].supporting_chunks) == 2


def test_rerank_candidates_falls_back_without_openai(monkeypatch) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    alice = Candidate(
        id=1,
        first_name="Alice",
        last_name="Martin",
        email="alice@example.com",
        headline="Senior Backend Engineer",
    )
    ben = Candidate(
        id=2,
        first_name="Ben",
        last_name="Shah",
        email="ben@example.com",
        headline="Data Platform Engineer",
    )

    summaries = [
        CandidateSummary(
            candidate=alice,
            retrieval_score=0.92,
            supporting_chunks=["Strong Django, Celery, and Redis background."],
        ),
        CandidateSummary(
            candidate=ben,
            retrieval_score=0.73,
            supporting_chunks=["Strong ETL and data platform experience."],
        ),
    ]
    results = rerank_candidates(
        JobRequest(
            title="Platform Backend Engineer",
            description_text="Need Django, Celery, Redis, and ranking pipelines.",
            retrieval_k=10,
            top_k=10,
        ),
        summaries,
    )

    assert [result["candidate"].id for result in results] == [1, 2]
    assert results[0]["fit_score"] > results[1]["fit_score"]
    assert "semantic retrieval score only" in results[0]["risks"][0]
