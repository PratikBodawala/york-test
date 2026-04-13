from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from langchain_core.documents import Document

from apps.matching import services


@dataclass
class FakeCandidate:
    id: int
    display_name: str
    headline: str = ""


class MatchingServiceTests(SimpleTestCase):
    def test_fallback_rankings_preserve_order(self):
        summaries = [
            services.CandidateSummary(
                candidate=FakeCandidate(id=1, display_name="Alice Martin"),
                retrieval_score=0.91,
                supporting_chunks=["Python Django Celery"],
            ),
            services.CandidateSummary(
                candidate=FakeCandidate(id=2, display_name="Ben Shah"),
                retrieval_score=0.73,
                supporting_chunks=["ETL and embeddings"],
            ),
        ]

        rankings = services.fallback_rankings(summaries, top_k=10)

        self.assertEqual(rankings[0]["candidate"].display_name, "Alice Martin")
        self.assertEqual(rankings[0]["rank"], 1)
        self.assertGreater(rankings[0]["final_score"], rankings[1]["final_score"])

    def test_aggregate_candidates_groups_chunks_by_candidate(self):
        fake_job_request = SimpleNamespace(
            description_text="Need Django and Celery",
            retrieval_k=10,
            top_k=10,
        )
        vector_results = [
            (
                Document(
                    page_content="Built Django APIs",
                    metadata={"candidate_id": 1},
                ),
                0.9,
            ),
            (
                Document(
                    page_content="Scaled Celery workers",
                    metadata={"candidate_id": 1},
                ),
                0.8,
            ),
            (
                Document(
                    page_content="React dashboards",
                    metadata={"candidate_id": 2},
                ),
                0.5,
            ),
        ]
        candidates_map = {
            1: FakeCandidate(id=1, display_name="Alice Martin"),
            2: FakeCandidate(id=2, display_name="Carla Nguyen"),
        }

        with (
            patch("apps.matching.services.get_vector_store") as mock_get_vector_store,
            patch("apps.matching.services.Candidate.objects.in_bulk", return_value=candidates_map),
        ):
            mock_get_vector_store.return_value.similarity_search_with_score.return_value = vector_results
            summaries = services.aggregate_candidates(fake_job_request)

        self.assertEqual([summary.candidate.id for summary in summaries], [1, 2])
        self.assertEqual(len(summaries[0].supporting_chunks), 2)
        self.assertGreater(summaries[0].retrieval_score, summaries[1].retrieval_score)

    @override_settings(OPENAI_API_KEY="")
    def test_rerank_candidates_uses_fallback_without_api_key(self):
        fake_job_request = SimpleNamespace(
            title="Backend Engineer",
            description_text="Need Django",
            top_k=2,
        )
        summaries = [
            services.CandidateSummary(
                candidate=FakeCandidate(id=1, display_name="Alice Martin"),
                retrieval_score=0.82,
                supporting_chunks=["Django APIs"],
            ),
        ]

        rankings = services.rerank_candidates(fake_job_request, summaries)

        self.assertEqual(len(rankings), 1)
        self.assertIn("semantic retrieval score", rankings[0]["explanation"])
