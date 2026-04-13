# Recruiting RAG POC

Thin-slice Django proof of concept for AI-native candidate matching. The app ingests candidate resumes from local files, parses PDF and DOCX via MIME-based routing, chunks and embeds resume content into Postgres `pgvector`, and returns a ranked Top 10 candidate list for a job description.

## Stack

- Django for the application layer and simple browser UI
- Celery with Redis queues for ingestion and matching jobs
- Postgres with `pgvector` for app data and vector search
- LangChain with OpenAI for embeddings and LLM reranking
- Local file storage under `media/`

## Features

- Upload candidate resumes from the browser UI or API
- Detect file format using MIME type
- Parse at least PDF and DOCX with an extensible parser registry
- Queue one job to parse and index documents into PGVector
- Queue another job to rank the Top 10 candidates for a job description
- Fall back to semantic retrieval-only ranking when the rerank LLM is unavailable
- Generate local sample resumes and a sample job description for a quick smoke flow

## Local Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY` in `.env`.
3. Install dependencies:

```bash
uv sync
```

4. Start Postgres and Redis:

```bash
docker compose up -d
```

5. Run database migrations:

```bash
uv run python manage.py migrate
```

6. Start Celery workers in separate terminals:

```bash
uv run celery -A config worker -Q ingest --loglevel=info
```

```bash
uv run celery -A config worker -Q match --loglevel=info
```

7. Start Django:

```bash
uv run python manage.py runserver
```

8. Open `http://127.0.0.1:8000/`.

## Simplest UI

The root page `/` is the simplest interaction surface.

- Upload a candidate resume file only
- Submit a job title plus job description text
- Check ingestion status by `document_id`
- Check ranked candidate results by `job_request_id`
- View recent documents and recent match requests on the same page

## Sample Data And Smoke Flow

Generate local sample files:

```bash
uv run python manage.py generate_sample_inputs
```

Run the thin-slice sample pipeline:

```bash
uv run python manage.py run_sample_pipeline
```

This command:

- creates sample PDF and DOCX resumes under `sample_data/resumes/`
- creates a sample job description under `sample_data/jobs/`
- ingests the sample resumes
- runs the matching pipeline
- prints ranked candidates in order

## API Endpoints

- `POST /api/candidates/upload/`
- `GET /api/documents/<document_id>/`
- `POST /api/matches/`
- `GET /api/matches/<job_request_id>/`

### Upload Candidate Resume

Multipart form fields:

- `file`

The API derives a lightweight candidate profile from the uploaded filename and creates a synthetic local email for the POC.

### Submit Job Description

```json
{
  "title": "Platform Backend Engineer",
  "description_text": "Need Django, Celery, Redis, Postgres and retrieval experience.",
  "retrieval_k": 50,
  "top_k": 10
}
```

## Validation

Run focused tests:

```bash
uv run python manage.py test apps.ingestion.tests apps.matching.tests
```

Run framework checks:

```bash
uv run python manage.py check
```

## Notes

- The POC assumes Postgres and Redis are running locally.
- The Docker daemon was not available in this environment during implementation, so end-to-end runtime validation against live Postgres/Redis was not completed here.
- `DESIGN.md` explains the production path, cold-start logic, and known failure modes.
