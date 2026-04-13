from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand
from docx import Document as DocxDocument


SAMPLE_JOB_DESCRIPTION = """Platform Backend Engineer

We are hiring a backend engineer to build recruiting platform services at scale.
The role needs strong Python, Django, Postgres, Redis, Celery, and API design experience.
Experience with vector search, retrieval pipelines, ranking systems, resume parsing, and production observability is a strong plus.
The engineer should be comfortable designing asynchronous document ingestion flows and turning unstructured data into ranked candidate outputs.
"""


SAMPLE_RESUMES = [
    {
        "file_name": "alice_martin_resume.pdf",
        "mime_family": "pdf",
        "lines": [
            "Alice Martin",
            "Senior Backend Engineer",
            "Skills: Python, Django, Celery, Redis, PostgreSQL, pgvector, APIs",
            "Built document ingestion services for hiring workflows.",
            "Implemented semantic search and ranking pipelines with LLM-assisted review.",
            "Led observability improvements for async workers and queue backlogs.",
        ],
    },
    {
        "file_name": "ben_shah_resume.docx",
        "mime_family": "docx",
        "lines": [
            "Ben Shah",
            "Data Platform Engineer",
            "Skills: Python, Airflow, Postgres, ETL, embeddings, batch processing",
            "Built retrieval pipelines over large candidate datasets.",
            "Comfortable with ranking systems and analytics, but less Django experience.",
        ],
    },
    {
        "file_name": "carla_nguyen_resume.pdf",
        "mime_family": "pdf",
        "lines": [
            "Carla Nguyen",
            "Frontend Engineer",
            "Skills: TypeScript, React, design systems, accessibility",
            "Worked on internal hiring dashboards and recruiter-facing interfaces.",
            "Limited backend and infrastructure experience.",
        ],
    },
]


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(lines: list[str]) -> bytes:
    content_commands = ["BT", "/F1 12 Tf", "50 770 Td", "14 TL"]
    for index, line in enumerate(lines):
        escaped_line = escape_pdf_text(line)
        if index == 0:
            content_commands.append(f"({escaped_line}) Tj")
        else:
            content_commands.append(f"T* ({escaped_line}) Tj")
    content_commands.append("ET")
    stream = "\n".join(content_commands).encode("latin-1", errors="replace")

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
        + stream
        + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    body = bytearray(header)
    offsets = [0]
    for object_bytes in objects:
        offsets.append(len(body))
        body.extend(object_bytes)

    xref_start = len(body)
    xref_lines = [f"xref\n0 {len(offsets)}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref_lines.append(f"{offset:010d} 00000 n \n")
    body.extend("".join(xref_lines).encode("latin-1"))
    body.extend(
        (
            "trailer\n"
            f"<< /Size {len(offsets)} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_start}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(body)


class Command(BaseCommand):
    help = "Generate local sample resumes and a sample job description."

    def handle(self, *args, **options) -> None:
        base_dir = Path.cwd() / "sample_data"
        resumes_dir = base_dir / "resumes"
        jobs_dir = base_dir / "jobs"
        resumes_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)

        for resume in SAMPLE_RESUMES:
            file_path = resumes_dir / resume["file_name"]
            if resume["mime_family"] == "docx":
                docx_document = DocxDocument()
                for line in resume["lines"]:
                    docx_document.add_paragraph(line)
                docx_document.save(file_path)
            else:
                file_path.write_bytes(build_simple_pdf(resume["lines"]))
            self.stdout.write(f"Created {file_path}")

        job_file_path = jobs_dir / "platform_backend_engineer.txt"
        job_file_path.write_text(SAMPLE_JOB_DESCRIPTION, encoding="utf-8")
        self.stdout.write(f"Created {job_file_path}")
