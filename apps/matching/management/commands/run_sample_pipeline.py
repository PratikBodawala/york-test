from __future__ import annotations

from pathlib import Path

from django.core.files import File
from django.core.management import BaseCommand, call_command

from apps.candidates.models import Candidate
from apps.documents.models import Document
from apps.ingestion.tasks import parse_and_index_document
from apps.matching.models import JobRequest
from apps.matching.tasks import generate_candidate_matches


SAMPLE_CANDIDATES = [
    {
        "first_name": "Alice",
        "last_name": "Martin",
        "email": "alice@example.com",
        "headline": "Senior Backend Engineer",
        "file_name": "alice_martin_resume.pdf",
    },
    {
        "first_name": "Ben",
        "last_name": "Shah",
        "email": "ben@example.com",
        "headline": "Data Platform Engineer",
        "file_name": "ben_shah_resume.docx",
    },
    {
        "first_name": "Carla",
        "last_name": "Nguyen",
        "email": "carla@example.com",
        "headline": "Frontend Engineer",
        "file_name": "carla_nguyen_resume.pdf",
    },
]


class Command(BaseCommand):
    help = "Generate sample files, ingest them, and compute ranked candidate matches."

    def handle(self, *args, **options) -> None:
        call_command("generate_sample_inputs")

        base_dir = Path.cwd() / "sample_data"
        resumes_dir = base_dir / "resumes"
        job_file_path = base_dir / "jobs" / "platform_backend_engineer.txt"

        for candidate_payload in SAMPLE_CANDIDATES:
            candidate, _ = Candidate.objects.update_or_create(
                email=candidate_payload["email"],
                defaults={
                    "first_name": candidate_payload["first_name"],
                    "last_name": candidate_payload["last_name"],
                    "headline": candidate_payload["headline"],
                },
            )
            Document.objects.filter(candidate=candidate).delete()

            file_path = resumes_dir / candidate_payload["file_name"]
            with file_path.open("rb") as file_handle:
                document = Document(
                    candidate=candidate,
                    original_filename=file_path.name,
                )
                document.uploaded_file.save(file_path.name, File(file_handle), save=False)
                document.save()

            parse_and_index_document(document.id)
            self.stdout.write(f"Ingested {candidate.display_name}: {file_path.name}")

        job_request = JobRequest.objects.create(
            title="Platform Backend Engineer",
            description_text=job_file_path.read_text(encoding="utf-8"),
        )
        generate_candidate_matches(job_request.id)
        job_request.refresh_from_db()

        self.stdout.write("")
        self.stdout.write("Top candidates")
        for match in job_request.matches.select_related("candidate").order_by("rank"):
            self.stdout.write(
                f"{match.rank}. {match.candidate.display_name} "
                f"(fit={match.fit_score:.2f}, retrieval={match.retrieval_score:.4f})"
            )
