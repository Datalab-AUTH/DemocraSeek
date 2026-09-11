---
title: "Troubleshooting"
doc_type: reference
layer: user
audience: "developer or operator"
reader_goal: "diagnose common startup, model, indexing, database, and frontend failures"
reader_state: "has attempted the relevant workflow"
source_of_truth: true
status: stable
canonical_sources:
  - "start-demo.cmd"
  - "ingest.cmd"
  - "deployment/docker-compose.yml"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/operations/corpus-management.md"
rag_index: true
---

# Troubleshooting

## Docker Desktop shows only one DemocraSeek item

Compose groups services under one project. Expand it or run:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env ps
```

Expected normal services: `db`, `backend`, `frontend`.

## `start-demo.cmd` times out on readiness

Inspect:

```powershell
Invoke-RestMethod http://localhost:8000/api/ready
docker compose -f deployment\docker-compose.yml --env-file .env logs --tail 150 backend
docker compose -f deployment\docker-compose.yml --env-file .env logs --tail 100 db
```

Common causes:

- no ingested corpus in the Docker `ingestdata18` volume;
- model unavailable;
- incompatible fingerprint;
- database unavailable;
- pending approved files;
- reranker download/cache failure.

## Missing Ollama model

```powershell
ollama list
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama pull qwen2.5vl:7b
```

Model names in `.env` must match installed tags.

## Container cannot reach Ollama

Ensure:

```dotenv
LLM_BASE_URL=http://host.docker.internal:11434/v1
EMBEDDING_BASE_URL=http://host.docker.internal:11434/v1
VISION_BASE_URL=http://host.docker.internal:11434/v1
```

Check that `http://localhost:11434/api/tags` works on the host and that VPN or
firewall rules do not block Docker-to-host traffic.

## PostgreSQL port conflict

Choose a free `POSTGRES_HOST_PORT`. The backend continues to use `db:5432`
inside Compose, so `VECTOR_STORE_URL` does not use the host port.

## A copied file is not searchable

Copying is not ingestion. Run `ingest`, inspect the report, and check
`GET /api/corpus` for `pending_files`.

## Index incompatible after configuration change

Run a controlled full rebuild:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli reindex --yes
```

Do not suppress the compatibility error.

## Answer is rejected despite good evidence

The answer model likely broke JSON, citation marker, or evidence-ID rules. Check
backend logs for `generation_parse_rejected` or
`citation_validation_rejected`. The validator is intentionally stricter than a
best-effort display.

## Chat ends with a gateway timeout

Check whether nginx or a model provider ended the request. The shipped proxy
waits up to 900 seconds, while each normal LLM or vision call has a 180-second
provider timeout. Backend structured logs include language, retrieval,
generation, and translation durations so the slow stage can be identified.

## Image is shown but cannot answer from it

Possible causes:

- the current Docker index was created with `VISION_PROVIDER=none`;
- the figure has no caption and VLM description failed;
- the figure was filtered or is vector-only;
- the image text requires OCR;
- `.env` changed without re-indexing.

Check the latest report for `figure descriptions` and `figures searchable`.

## Host registry differs from running Docker

Compose uses the `ingestdata18` named volume, not host `data/index/`. Run the CLI
through Compose to inspect the active Docker index.

## Frontend changes are not visible

Vite assets are baked into the image:

```powershell
.\start-demo.cmd -Build
```

A normal restart reuses the old image.
