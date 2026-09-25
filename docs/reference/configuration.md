---
title: "Configuration reference"
doc_type: reference
layer: user
audience: "developer or operator"
reader_goal: "look up environment variables and configuration validation rules"
reader_state: "has a local checkout"
source_of_truth: true
status: stable
canonical_sources:
  - ".env.example"
  - "backend/app/config.py"
  - "deployment/docker-compose.yml"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/reference/change-impact-matrix.md"
rag_index: true
---

# Configuration reference

## Single configuration source

The root `.env` is the only environment configuration used by the running
deployment. Docker Compose injects it into the backend and reads the same file
for ports, mounts, PostgreSQL credentials, and frontend build arguments. There
are no secondary Docker-specific environment files and no duplicated
`DOCKER_LLM_*`, `DOCKER_EMBEDDING_*`, or `DOCKER_VISION_*` variables.

`backend/app/config.py` provides typed validation, safe fallback values, and
cross-field checks; it is not a second operator configuration file.
`.env.example` contains the complete versioned template. `config/onboarding.v2.yaml` and `config/starter_questions.yaml` remain separate because they are
versioned product policy and curated start-screen questions, not infrastructure/provider configuration.

## Active demo configuration

| Area | Active value |
|---|---|
| Environment | `development` |
| Answer LLM | FILOS `datalab-2:latest` |
| Language routing | same FILOS model; automatic per turn |
| Embeddings | FILOS `nomic-embed-text:latest`, 768d |
| Vision | FILOS `datalab-vision-1:latest` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Vector store | pgvector collection `innovade_filos_nomic_v1` |
| PostgreSQL host port | `5434` |
| Chunking | 1,200 chars, 180 overlap |
| Retrieval | 10 candidates per branch, top 6, threshold 0.65, 4,000-token budget |
| History | 12 recent messages for generation |
| Onboarding | `config/onboarding.v2.yaml`, policy `2.0` |

## Application and logging

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `APP_NAME` | `DemocraSeek` | display/logging name |
| `APP_BASE_URL` | `http://localhost:8080` | allowed production application origin |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `FRONTEND_HOST_PORT` | `8080` | host port for the user interface |
| `BACKEND_HOST_PORT` | `8000` | host port for API/operator access |

## Shared institutional credential

| Variable | Shipped value | Meaning |
|---|---|---|
| `INSTITUTIONAL_API_KEY` | empty | shared FILOS credential used when a provider-specific key is empty |

## Answer LLM

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `openai_compatible` | shipped adapter; works with compatible local or remote services |
| `LLM_MODEL` | `datalab-2:latest` | shipped FILOS model identifier |
| `LLM_BASE_URL` | `https://filos.csd.auth.gr/ollama/v1` | endpoint as seen from the backend container |
| `LLM_API_KEY` | empty | provider-specific override for `INSTITUTIONAL_API_KEY` |
| `LLM_TEMPERATURE` | `0.0` | deterministic answering recommended |
| `LLM_MAX_OUTPUT_TOKENS` | `1200` | output ceiling |
| `LLM_TIMEOUT_SECONDS` | `180` | provider timeout |
| `LLM_REASONING_EFFORT` | `none` | disables hidden reasoning on FILOS; leave empty for plain local models |

## Embeddings

| Variable | Default | Meaning |
|---|---|---|
| `EMBEDDING_PROVIDER` | `openai_compatible` | shipped embedding adapter |
| `EMBEDDING_MODEL` | `nomic-embed-text:latest` | shipped FILOS embedding model identifier |
| `EMBEDDING_BASE_URL` | `https://filos.csd.auth.gr/ollama/v1` | endpoint as seen from the backend container |
| `EMBEDDING_API_KEY` | empty | provider-specific override for `INSTITUTIONAL_API_KEY` |
| `EMBEDDING_DIMENSIONS` | `768` | must match returned vectors |
| `EMBEDDING_BATCH_SIZE` | `16` | ingestion batch size |

## Vision

| Variable | Default | Meaning |
|---|---|---|
| `VISION_PROVIDER` | `openai_compatible` | `none` or `openai_compatible` |
| `VISION_MODEL` | `datalab-vision-1:latest` | shipped FILOS VLM identifier |
| `VISION_BASE_URL` | `https://filos.csd.auth.gr/ollama/v1` | endpoint as seen from the backend container |
| `VISION_API_KEY` | empty | provider-specific override for `INSTITUTIONAL_API_KEY` |
| `VISION_TIMEOUT_SECONDS` | `180` | per-image call timeout |
| `VISION_REASONING_EFFORT` | `none` | disables hidden reasoning on FILOS; leave empty for plain local models |
| `VISION_MAX_DESCRIPTION_CHARS` | `900` | stored description cap |

## Reranking and retrieval

| Variable | Default | Meaning |
|---|---|---|
| `RERANK_PROVIDER` | `cross_encoder` | mandatory retrieval stage |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | local reranking model |
| `RETRIEVAL_CANDIDATE_K` | `10` | candidates from each retriever |
| `RETRIEVAL_TOP_K` | `6` | maximum evidence items |
| `RETRIEVAL_SCORE_THRESHOLD` | `0.65` | dense relevance gate |
| `RETRIEVAL_MAX_CONTEXT_TOKENS` | `4000` | evidence-context budget |

The `.env` overrides are authoritative for the active deployment. Code defaults
are safe generic defaults, not evidence that the active runtime uses them.

## Vector store and PostgreSQL

| Variable | Default | Meaning |
|---|---|---|
| `VECTOR_STORE_PROVIDER` | `pgvector` | persistent production store |
| `VECTOR_STORE_URL` | required | container-visible PostgreSQL DSN |
| `VECTOR_STORE_COLLECTION` | `innovade_filos_nomic_v1` | safe alphanumeric/underscore collection |
| `POSTGRES_HOST_PORT` | `5434` | host mapping only |
| `POSTGRES_USER` | `democraseek` | Compose database user |
| `POSTGRES_PASSWORD` | `change-this-password` | Compose password placeholder; replace it |
| `POSTGRES_DB` | `democraseek` | Compose database name |

Inside Compose, the backend always connects to `db:5432`; host port selection
does not alter container networking.

## Corpus, chunking, and paths

Paths exist at two levels. The `*_HOST_PATH` variables are read by Docker Compose
and point at a folder on the machine running the deployment; Compose resolves them
relative to `deployment/`, where the compose file lives. The remaining path
variables are the container-side locations the backend sees. The `Default` column
is the code default: `.env.example` sets container-absolute values such as
`/app/data/corpus`.

| Variable | Default | Meaning |
|---|---|---|
| `CORPUS_HOST_PATH` | set in `.env` | host folder holding the approved files, bind-mounted read-only; `.env.example` uses `../data/corpus` |
| `REPORT_HOST_PATH` | set in `.env` | host folder receiving ingestion reports; `.env.example` uses `../data/reports` |
| `CORPUS_PATH` | `data/corpus` | approved source directory as seen inside the container |
| `CORPUS_VERSION` | `unversioned` | audit label, not vector invalidation by itself |
| `INDEX_VERSION` | `1` | manual index invalidation lever |
| `INDEX_PATH` | `data/index` | registry and derived figure location; Compose mounts the `ingestdata18` volume here |
| `REPORT_PATH` | `data/reports` | ingestion reports |
| `CHUNK_SIZE` | `1200` | characters per chunk |
| `CHUNK_OVERLAP` | `180` | repeated characters between adjacent chunks |

## Onboarding and request limits

| Variable | Default | Meaning |
|---|---|---|
| `ONBOARDING_CONFIG_PATH` | `config/onboarding.v2.yaml` | versioned policy |
| `STARTER_QUESTIONS_PATH` | `config/starter_questions.yaml` | hand-written start-screen questions, every locale per entry; validated at startup |
| `MAX_USER_INPUT_CHARS` | `2000` | normalized question limit |
| `MAX_CONVERSATION_MESSAGES` | `12` | recent messages sent to generation |
| `RATE_LIMIT_REQUESTS` | `60` | requests per process/window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | window duration |

## Frontend variables

Passed to the frontend image as build arguments and embedded into the bundle:

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | empty | leave empty for same-origin `/api` |
| `VITE_APP_NAME` | `DemocraSeek` | UI application name |
| `VITE_PROJECT_NAME` | `INNOVADE` | UI project label |
| `VITE_LOGO_URL` | `/logo.svg` | reviewed logo bundled with the frontend |

These four are baked in when the image is built, so changing any of them requires
rebuilding the frontend image.

Read only by the Vite dev server, never by the Docker deployment:

| Variable | Default | Meaning |
|---|---|---|
| `VITE_DEV_API_TARGET` | `http://127.0.0.1:8000` | backend that `npm run dev` proxies `/api` to |

`npm run dev` serves the UI on port `5173` and proxies `/api` to this target,
mirroring what nginx does inside the container. That is what lets
`VITE_API_BASE_URL` stay empty in both environments and keeps CORS out of the
picture. Docker Compose never passes this variable, so it has no effect on a
container run.

One detail worth knowing when running the frontend outside Docker: Vite reads all
`VITE_*` values from the repository root `.env`, not from `frontend/`, because
`frontend/vite.config.ts` sets `envDir: ".."`. Without that, Vite would silently
see no `VITE_*` variables, the API base URL would fall back to empty, and every
`/api` request would be answered by the dev server's SPA fallback with
`index.html` - which surfaces in the browser as a JSON parse error.

## Configuration validation

Run inside the delivery runtime:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli check-config
```

Validation rejects missing provider fields, invalid collection names, impossible
chunk overlap, unsupported provider names, and incompatible provider
combinations.
