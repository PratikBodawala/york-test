# Recruitment system design for AI candidate matching
_Exported on 4/13/2026 at 14:46:52 GMT+5:30 from Cursor (3.0.16)_

---

**User**

Goal:
recruitment system for a hiring platform operating at scale. The current keyword-matching approach produces low-quality candidate-to-role matches.
The business needs a smarter, AI-native replacement.

create Django project with celery, redis, queue, use sqlite, use langchain with openai, implement rag using this reference: https://docs.langchain.com/oss/python/langchain/rag
vector store: PGVector, identify file format using mime type,
- there should be one job to parse the document and update into pgvector db
- another job takes a candidate description and search top 10 best candidates - in order. 



Context:
Active Candidates
50,000 profiles in the system

Live Job Openings
1,500 roles open at any time

Current Problem
Keyword matching — produces poor-quality candidate-to-role matches

Goal
A ranked Top 10 Candidates list per job role



Constraints:
- Parses resumes and job descriptions from multiple file formats
- Builds a pipeline from document ingestion through to a ranked candidate output
- Returns the Top 10 best-matched candidates for a given job role
- Is designed with concurrency and scale in mind, even if not fully implemented in the POC
- Local file storage instead of S3
- In-memory or local queuing instead of SQS or equivalent
- Lightweight local DB or flat file instead of a managed database
1. File Format Handling
Ingestion must support at minimum PDF and DOCX formats. Your parsing approach should be extensible to additional formats without a full rewrite.

2. Data Pipeline

Define and implement the full flow: raw document intake → parsing → scoring → ranked output.

The pipeline does not need to be production-grade, but the design must be. Use DESIGN.md to document what a production version would look like.

3. Cold Start Accuracy

Explain how your system handles a brand-new job posting with no historical data or prior match signals. Your approach must be reasoned and defensible — not deferred to future work.



Output:
Deliverable
Description

Code Repository
A working thin-slice POC covering the core pipeline logic. Must run locally against the provided sample inputs.

create DESIGN.md
Architecture document covering: system design, data flow, how you would scale to production (e.g. S3, queuing, distributed workers), and known failure modes



---

**Cursor**

I’m narrowing down the two decisions that materially affect the plan before I map the project structure and data flow.

**Two Planning Decisions**

> **You asked for `sqlite` and also `PGVector`. Which local setup do you want for the POC?**
> - Use `sqlite` for Django app data and a separate local Postgres + `pgvector` service for embeddings/search
> - Use Postgres + `pgvector` for everything and ignore `sqlite` ✔
> - Keep only `sqlite`; I want you to propose an alternative to `PGVector`

> **For the ranking job, what should the input be for generating the Top 10 candidates?**
> - A job description document/file
> - A text job description or role summary ✔
> - Either file or text, normalized into the same pipeline
> - I literally want candidate-description-driven search, not job-role-driven ranking

I have the key choices now: Postgres with `pgvector` for the POC, and ranking driven by job-description text. Next I’m checking the repo state and pulling the LangChain RAG reference details so the plan lines up with the actual starting point.

The repo is a blank slate, so the plan can assume a fresh Django codebase rather than adapting existing app conventions. I’m extracting just the relevant RAG workflow details now so the plan reflects the LangChain reference instead of a generic retrieval design.

I’ve confirmed the repo is empty and the LangChain reference cleanly separates indexing from retrieval, which maps well onto the two Celery jobs you want. I’m doing one last pass on the PGVector/LangChain integration so the plan names the right local components and package boundaries.

I have enough context to lay out a concrete build plan. The main design choice I’m encoding is a thin-slice POC that uses LangChain’s indexing pattern for ingestion, then a retrieval-plus-rerank matching flow so cold-start ranking works without historical labels.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

I’m starting with the scaffold and dependency layout, then I’ll move straight through ingestion, matching, and docs without pausing between phases.

I’m checking the local Python tooling before I wire files together so I can validate the scaffold instead of just writing it blind.

I’ve confirmed the toolchain is present. I’m pinning down the exact `langchain-postgres` API surface before I write the vector-store wrapper, so the project can be executed and not just read.

I’m laying down the project manifest and local service config first so the rest of the scaffold can be validated against real dependencies.

The manifest and service definitions are in place. I’m syncing dependencies now so I can generate the Django baseline and catch package/API issues early.

I’ve got the base Django project created. Next I’m replacing the default settings with the real project wiring and adding the domain apps/packages the POC needs.

The data models and parser abstraction are in place. I’m wiring the ingestion job now, including MIME detection, parser dispatch, chunking, and PGVector writes.

I’m moving into the ranking flow now: retrieval from PGVector, aggregation by candidate, then a LangChain/OpenAI rerank with a deterministic fallback so the pipeline still works if the model call is unavailable.

The core app wiring is complete enough to validate. I’m running Django’s checks before I generate migrations so I can fix structural issues while the code surface is still small.

Migrations are generated. I need a live Postgres/Redis stack to run real migrations and end-to-end verification, so I’m checking for any existing terminal sessions before starting local services.

The main code path is written. I’m checking diagnostics now so I can clean up low-friction issues before adding tests and docs.

I’m adding a reproducible local demo path now so the repo includes sample inputs and a one-command thin-slice run, not just APIs and worker tasks.

---

**User**

generate simplest ui for for interaction

---

**Cursor**

I’ve got the backend thin slice in place, and I’m adding the simplest possible interaction layer now: one page to upload resumes, submit a job description, and view statuses/results without needing a separate frontend.

I ran into an unexpected change in `config/settings.py` that I did not make: it now imports `dotenv` and calls `dotenv.load_dotenv('.env')`, but `python-dotenv` is not in the project dependencies.

Before I keep editing, I need your direction:
1. Keep the `dotenv` behavior, and I’ll add the dependency plus wire it in cleanly.
2. Remove that change and continue with plain environment-variable loading only.

I’ve paused work until you choose, since I don’t want to overwrite something you may have intended.

---

**User**

keep dotenv 

---

**Cursor**

I’m keeping the `dotenv` flow and resuming from there. Next I’m wiring the lightweight HTML UI, then I’ll finish tests, docs, and a validation pass.

I’m filling in the missing support around the backend now: dependency cleanup, a tiny browser UI, and a few targeted tests so the thin slice is actually usable.

I’m adding the browser page now. It’ll stay intentionally minimal: two forms, recent items, and direct status/result views backed by the existing APIs.

The UI shell is in. I’m adding focused tests now for parser routing and ranking fallback/aggregation so the important behavior is covered without heavy test scaffolding.

The code surface is basically complete now. I’m syncing dependencies and running checks/tests next so I can fix anything mechanical before I write the final docs.

Checks and targeted tests are clean. I’m finishing the repository docs now so setup, UI usage, sample flow, cold-start rationale, and production scaling are all captured in the repo.

I’ve finished the docs and I’m doing one final verification pass over the edited files so I can close this out cleanly.

Implemented the full POC, including a very simple browser UI at `/` for interaction.

The app now has:
- a Django/Celery/Redis/Postgres scaffold with `pgvector` and LangChain/OpenAI wiring
- MIME-based PDF and DOCX ingestion with an async parse-and-index job
- async job-description-driven retrieval, candidate aggregation, LLM reranking, and persisted Top 10 results
- a minimal UI in `templates/ui/index.html` backed by `apps/ui/views.py` and the existing JSON APIs
- sample data commands plus `README.md` and `DESIGN.md`

The simplest UI lets you:
- upload a candidate resume
- submit a job description
- check document ingestion status
- check ranked match results
- see recent documents and match jobs

Key files for that UI are `templates/ui/index.html`, `apps/ui/views.py`, and `config/urls.py`.

Validation passed:
- `uv run python manage.py check`
- `uv run python manage.py test apps.ingestion.tests apps.matching.tests`

One limitation remains: I could not run a full live end-to-end flow against Dockerized Postgres/Redis here because the Docker daemon was unavailable in this environment. Once Docker is running locally, follow `README.md` to start services, run migrations, start Celery workers, and use the UI at `http://127.0.0.1:8000/`.

Natural next step: if you want, I can add auto-refresh/polling to the UI so document and match status updates appear without manually pressing the status buttons.

---

**User**

while upload candidate resume, take only resume file, update api and ui

---

**Cursor**

I’m updating the upload flow to accept only the resume file, and I’m tracing that change through both the API behavior and the simple UI so they stay aligned.

I’m simplifying the upload contract itself now: the backend will synthesize a candidate profile from the filename, and the UI will show that expectation instead of asking for manual fields.

I’ve updated the API and UI contract. I’m adding one tiny regression test for filename-based candidate identity generation, then I’ll re-run checks.

I’m tightening the filename parsing slightly so common suffixes like `resume` or `cv` don’t end up in the generated candidate name.

Updated the upload flow so candidate resume upload now takes only the `file`.

What changed:
- `POST /api/candidates/upload/` now accepts just the uploaded resume file.
- The backend derives a lightweight candidate profile from the filename in `apps/candidates/views.py`.
- The simple UI in `templates/ui/index.html` now only shows the file picker for resume upload.
- `README.md` was updated to reflect the new API contract.
- Added a small regression test for filename-based candidate identity generation in `apps/candidates/tests/test_views.py`.

Behavior now:
- Uploading `alice_martin_resume.pdf` will auto-create a candidate like `Alice Martin`.
- Common suffixes like `resume`, `cv`, and `profile` are ignored in the generated name.
- A synthetic local email is generated for the POC.

Verification passed:
- `uv run python manage.py check`
- `uv run python manage.py test apps.candidates.tests apps.ingestion.tests apps.matching.tests`

If you want, I can make the filename parsing a bit smarter next, for example handling patterns like `Martin_Alice_2026.pdf` or extracting names from the parsed resume text instead of the filename.

---

**User**

worker is not executing task, tries, method delay and apply_async

---

**Cursor**

I’m checking the Celery wiring and the current worker/runtime state first so I can tell whether this is a queue/config issue or a worker startup issue.

I’ve confirmed the task definitions and Celery bootstrap look structurally correct. Next I’m checking the active terminal output and the worker’s registered tasks/queues to find where the task is getting stuck.

I found the root cause: the worker is alive, and the tasks are registered, but the worker is only consuming the `default` queue while your tasks are routed to `ingest` and `match`. I’m fixing the Celery queue config so a normal worker can consume those queues too.

I’ve patched the queue config. I’m verifying the settings still load cleanly, and then I’ll tell you exactly what to restart so the worker begins consuming the task queues.

Root cause found: your worker was running, and the tasks were registered, but the worker was only consuming the `default` queue.

Your tasks are explicitly routed here in `config/settings.py`:
- `apps.ingestion.tasks.parse_and_index_document` -> `ingest`
- `apps.matching.tasks.generate_candidate_matches` -> `match`

But the live worker was listening only to:
- `default`

So `delay()` and `apply_async()` were enqueueing successfully, just into queues that your worker was not consuming.

I updated `config/settings.py` to declare all three queues explicitly:

```python
CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("ingest"),
    Queue("match"),
)
```

That keeps the logical queue split, but allows a standard worker process to consume those queues too.

What you need to do now:
1. Restart the Celery worker.
2. Start it normally with:
   ```bash
   uv run celery -A config worker --loglevel=info
   ```
   or, if you want explicit queue binding:
   ```bash
   uv run celery -A config worker -Q default,ingest,match --loglevel=info
   ```

Why this happened:
- `delay()` is just shorthand for `apply_async()`, so both behaved the same.
- The problem was not task submission.
- The problem was queue consumption.

I also verified the project still loads cleanly with:
- `uv run python manage.py check`

If you want, I can also update `README.md` so the worker startup instructions match this fix exactly.

---

**User**

upload candidate resume should be handling multiple file upload

---

**Cursor**

I’m updating the upload path to accept multiple resume files in one request and reflecting that in the simple UI so batch ingestion works end to end.

I’m changing the upload endpoint to batch-create one candidate/document/task per file and returning a list of queued uploads so the UI can show the batch result.

The API/UI change is in. I’m updating docs and adding a regression test for multi-file submission so the batch behavior is covered.

I’m running a quick verification pass now to make sure the new batch upload contract works and didn’t break the rest of the flow.

The new behavior is implemented; the only failing verification step was DB test setup permissions in this environment. I’m switching that regression test to a mocked request-based test so it validates the API shape without requiring test database creation.

I’ve removed the DB dependency from the regression test. I’m re-running checks and tests once more so the multi-file flow is fully validated.

The batch upload code is fine; the failing piece is just the request-construction in the mocked test. I’m fixing that and rerunning the suite.

Updated the candidate upload flow to support multiple resume files in one request.

What changed:
- `POST /api/candidates/upload/` now accepts multiple files under `files`.
- The backend creates one candidate, one document, and one ingestion task per uploaded file.
- The response now returns:
  - `upload_count`
  - `uploads` list with `candidate_id`, `candidate_name`, `document_id`, `file_name`, `parse_status`, and `task_id`
- The simple UI now uses a multi-select file input and submits batches.
- After upload, the UI auto-fills the document status lookup with the first returned `document_id`.
- `README.md` now documents the batch upload contract.
- Added a regression test for multi-file upload behavior.

Validation passed:
- `uv run python manage.py check`
- `uv run python manage.py test apps.candidates.tests apps.ingestion.tests apps.matching.tests`

New upload contract:
- form field: `files`
- supports one or many `.pdf` / `.docx` files in the same request

If you want, I can also make the UI render each uploaded file as a small status row and poll ingestion progress for all returned `document_id`s automatically.

---

**User**

determine candidate name "display_name" from resume content, not from file name

---

**Cursor**

I’m moving name inference into the ingestion path so the candidate’s `display_name` comes from parsed resume text instead of the filename.

I’m shifting name inference out of the upload request and into resume parsing, so the final `display_name` is taken from the extracted content itself.

I’ve moved the actual name extraction into ingestion. Now I’m updating the tests and the UI/docs text to reflect that names are resolved after parsing, not at upload time.

The behavioral change is in place. I’m running checks and tests now to make sure the new content-based name extraction path is clean.

Updated the flow so candidate `display_name` is now derived from resume content, not the filename.

What changed:
- Added `apps/candidates/name_extraction.py` to infer candidate name and headline from parsed resume text.
- `POST /api/candidates/upload/` now creates a placeholder candidate first, with `candidate_name` returned as `Pending Candidate`.
- `apps/ingestion/tasks.py` now updates the candidate’s `first_name`, `last_name`, and `headline` immediately after parsing the resume text, before chunking/indexing.
- The UI text now correctly says names are inferred after ingestion completes.
- `README.md` was updated to document the new behavior.
- Added tests for:
  - extracting name/headline from resume content
  - fallback when no clear name is present
  - upload API returning pending name state before parsing

Behavior now:
- Upload response: placeholder candidate, `name_source: "resume_content_pending"`
- After the ingestion worker parses the resume, the candidate record is updated from the resume’s content
- `document_status` will then show the real parsed `candidate_name`

Validation passed:
- `uv run python manage.py check`
- `uv run python manage.py test apps.candidates.tests apps.ingestion.tests apps.matching.tests`

If you want, I can make the name extraction smarter next by handling formats like:
- `LASTNAME, Firstname`
- resumes where the first line is a title and the name appears slightly below
- names extracted from PDF headers with noisy spacing

---

**User**

ignore if already created 

sqlalchemy.exc.IntegrityError: (psycopg.errors.UniqueViolation) duplicate key value violates unique constraint "pg_type_typname_nsp_index"
DETAIL:  Key (typname, typnamespace)=(langchain_pg_collection, 2200) already exists.
[SQL: 
CREATE TABLE langchain_pg_collection (
	uuid UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	cmetadata JSON, 
	PRIMARY KEY (uuid), 
	UNIQUE (name)
)


---

**Cursor**

I’m tracing where PGVector is initialized so I can make table creation idempotent instead of blowing up when the collection metadata already exists.

This looks like repeated/concurrent PGVector schema setup. I’m checking the actual `langchain-postgres` constructor options so I can fix it at the right layer instead of just masking the exception.

I’ve confirmed the library eagerly runs schema setup during `PGVector(...)` construction. I’m inspecting that setup path now so I can make initialization safe when the tables already exist.

The race is likely in table creation, not extension creation. I’m checking whether `langchain-postgres` protects `create_tables_if_not_exists()`; if it doesn’t, I’ll add our own one-time schema init around it.

I’m implementing this as idempotent PGVector initialization: cache the store per process, and if table creation hits the duplicate-key race, retry once after another worker finishes creating the schema.

The runtime fix is in. I’m adding a focused regression test around the retry behavior and then I’ll run checks again.

I’m running a quick validation pass now so the retry logic is covered and the change doesn’t introduce any new issues.

Handled this by making PGVector initialization idempotent on our side.

What was happening:
- `langchain-postgres` runs schema setup eagerly inside `PGVector(...)`.
- If two workers/processes try to initialize it at the same time, Postgres can raise:
  `duplicate key value violates unique constraint "pg_type_typname_nsp_index"`
- That is a schema-creation race, not a real business-data duplication problem.

What I changed in `apps/search/vectorstore.py`:
- added a per-process cached vector store singleton
- added a lock so repeated calls in the same process do not reinitialize PGVector
- if initialization throws the duplicate-schema `IntegrityError`, the code now:
  1. detects that specific “already created” race
  2. waits briefly
  3. retries once

So effectively it now ignores the “already created” case and proceeds.

Validation passed:
- `uv run python manage.py check`
- `uv run python manage.py test apps.candidates.tests apps.ingestion.tests apps.matching.tests apps.search.tests`

This should resolve the exact error you posted without changing the external API. If you want, I can also add a small startup/prewarm command to initialize PGVector schema once before workers begin processing, which would reduce the chance of cross-process races even further.

