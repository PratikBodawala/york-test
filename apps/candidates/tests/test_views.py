import json
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase

from apps.candidates.name_extraction import infer_candidate_profile_from_resume_text
from apps.candidates.views import upload_candidate_resume


class CandidateUploadTests(SimpleTestCase):
    def test_infer_candidate_profile_from_resume_text(self):
        candidate_data = infer_candidate_profile_from_resume_text(
            "Alice Martin\nSenior Backend Engineer\nalice@example.com"
        )

        self.assertEqual(candidate_data["first_name"], "Alice")
        self.assertEqual(candidate_data["last_name"], "Martin")
        self.assertEqual(candidate_data["headline"], "Senior Backend Engineer")

    def test_infer_candidate_profile_returns_pending_when_name_missing(self):
        candidate_data = infer_candidate_profile_from_resume_text("alice@example.com\n+1 555 123 1234")

        self.assertEqual(candidate_data["first_name"], "Pending")
        self.assertEqual(candidate_data["last_name"], "Candidate")


class CandidateUploadApiTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("apps.candidates.views.Document.objects.create")
    @patch("apps.candidates.views.Candidate.objects.create")
    @patch("apps.candidates.views.parse_and_index_document.apply_async")
    def test_upload_candidate_resume_handles_multiple_files(
        self,
        mock_apply_async,
        mock_candidate_create,
        mock_document_create,
    ):
        mock_apply_async.side_effect = [
            SimpleNamespace(id="task-1"),
            SimpleNamespace(id="task-2"),
        ]
        mock_candidate_create.side_effect = [
            SimpleNamespace(id=1, display_name="Pending Candidate"),
            SimpleNamespace(id=2, display_name="Pending Candidate"),
        ]
        mock_document_create.side_effect = [
            SimpleNamespace(id=11, original_filename="alice_martin_resume.pdf", parse_status="pending"),
            SimpleNamespace(id=12, original_filename="ben_shah_resume.docx", parse_status="pending"),
        ]

        request = self.factory.post(
            "/api/candidates/upload/",
            data={
                "files": [
                    SimpleUploadedFile("alice_martin_resume.pdf", b"pdf-content"),
                    SimpleUploadedFile("ben_shah_resume.docx", b"docx-content"),
                ]
            },
        )
        response = upload_candidate_resume(request)

        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(payload["upload_count"], 2)
        self.assertEqual(len(payload["uploads"]), 2)
        self.assertEqual(payload["uploads"][0]["candidate_name"], "Pending Candidate")
        self.assertEqual(payload["uploads"][0]["name_source"], "resume_content_pending")
        self.assertEqual(payload["uploads"][1]["candidate_name"], "Pending Candidate")
        self.assertEqual(payload["uploads"][1]["name_source"], "resume_content_pending")
        self.assertEqual(mock_candidate_create.call_count, 2)
        self.assertEqual(mock_document_create.call_count, 2)
        self.assertEqual(mock_apply_async.call_count, 2)
