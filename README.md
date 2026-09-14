# DemocraSeek

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB.svg?logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/FastAPI-0.141.1-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI 0.141.1" />
  <img src="https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1.svg?logo=postgresql&logoColor=white" alt="PostgreSQL with pgvector" />
  <img src="https://img.shields.io/badge/Docker-Compose_v2+-2496ED.svg?logo=docker&logoColor=white" alt="Docker Compose" />
</p>

<p align="center">
  <b>A locally deployed, profile-aware, citation-grounded RAG application for the approved INNOVADE knowledge base.</b>
</p>

<p align="center">
  <a href="docs/getting-started/quickstart.md"><b>Quickstart</b></a> ·
  <a href="docs/index.md"><b>Documentation</b></a> ·
  <a href="docs/architecture/system-overview.md"><b>Architecture</b></a> ·
  <a href="docs/reference/api-contracts.md"><b>API</b></a>
</p>

---

## What is DemocraSeek?

A user chooses four onboarding preferences, asks a question in their own language, receives an answer in that same language shaped for the profile, and can inspect the exact document, page, passage, and figure behind each returned citation.

Internally, questions and conversation context are translated to English before retrieval and generation. If the indexed evidence is not sufficient, the system fails closed instead of using the model's general knowledge.

DemocraSeek has two central promises:

- **Grounding and traceability.** Every displayed citation resolves to evidence retrieved from the approved index. Document, page, chunk, excerpt, file, and figure metadata come from trusted ingestion records rather than from the LLM.
- **Presentation-only personalisation.** Onboarding can change wording, structure, depth, tone, and framing. It cannot change retrieval, source facts, citation validity, or the decision to return insufficient evidence.

Read [Product scope and core concepts](docs/explanation/product-scope-and-concepts.md) for the complete product boundary and mental model.

## System architecture

```text
                             LOCAL WORKSTATION
+--------------------------------------------------------------------------------+
|                                                                                |
|  Browser                                                                       |
|     | HTTP :8080                                                               |
|     v                                                                          |
|  +---------------------+       /api proxy       +---------------------------+   |
|  | React + nginx       | ---------------------> | FastAPI backend           |   |
|  | static frontend     |                        |                           |   |
|  +---------------------+                        | onboarding compiler       |   |
|                                                 | RAG orchestrator          |   |
|                                                 | citation validator        |   |
|                                                 | corpus/source API         |   |
|                                                 +----+----------+-----------+   |
|                                                      |          |               |
|                                 SQL + vectors        |          | OpenAI API    |
|                                                      v          v compatible    |
|                                            +-------------+  +----------------+  |
|                                            | PostgreSQL  |  | FILOS services |  |
|                                            | pgvector    |  | datalab-2      |  |
|                                            | + HNSW      |  | nomic-embed    |  |
|                                            | pg_text-    |  | datalab-vision |  |
|                                            | search+BM25 |  +----------------+  |
|                                            +-------------+                      |
|                                                                                |
|  Operator CLI                                                                  |
|     approved files -> extraction -> chunks/figures -> embeddings -> stores     |
|                                                                                |
+--------------------------------------------------------------------------------+
```

| Boundary | Responsibility |
|---|---|
| React + nginx | Serve the UI and proxy same-origin `/api` requests |
| FastAPI | Validate requests, compile onboarding policy, orchestrate RAG, validate citations, and serve source data |
| PostgreSQL | Store chunks, vectors, metadata, and dense/BM25 indexes |
| FILOS services | Provide answer generation, language handling, embeddings, and vision through OpenAI-compatible APIs |
| Operator CLI | Approve and ingest corpus files; maintain derived index state |

See [System overview](docs/architecture/system-overview.md) for the full runtime topology and design choices.

## Quickstart

### Prerequisites

- Windows 10/11 with PowerShell for the included launchers
- Docker Desktop with Compose v2
- Access to the AUTH FILOS services and an institutional API key
- Enough disk and RAM for Docker images and the local reranker
- Network access for FILOS, image downloads, and the reranker model

Python and Node are not required on the host for normal Docker runtime.

### 1. Configure

```powershell
Copy-Item .env.example .env
```

Set `INSTITUTIONAL_API_KEY`, then review the local ports, corpus version, and retrieval values. Do not commit `.env`.

### 2. Add approved corpus files

Place INNOVADE documents in `data/corpus/internal/` and downloaded third-party documents in `data/corpus/external/`. Record external attribution and URLs in `data/corpus/corpus.metadata.yaml`.

### 3. Build, start, and ingest

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env up -d --build
.\ingest.cmd
```

A new index can remain unavailable until ingestion completes.

### 4. Verify and open

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/ready
.\start-demo.cmd
```

| Surface | Address |
|---|---|
| User interface | [http://localhost:8080](http://localhost:8080) |
| Interactive API documentation | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Readiness | [http://localhost:8000/api/ready](http://localhost:8000/api/ready) |
| Corpus status | [http://localhost:8000/api/corpus](http://localhost:8000/api/corpus) |

For explanations, expected results, and first-run caveats, use the full [Quickstart](docs/getting-started/quickstart.md).

## How it works

| Flow | Sequence |
|---|---|
| Offline ingestion | Approved file → page and figure extraction → cleaning → chunks → embeddings → PostgreSQL indexes → registry and report |
| Online answering | Question → language normalization → profile policy → dense and BM25 retrieval → reranking → grounded generation → citation validation → translated answer and source evidence |

The two flows share one approved knowledge layer. Starting the API or copying a file does not approve or index it; an operator must run the ingestion CLI.

## Repository structure

```text
DemocraSeek/
|-- backend/app/                    FastAPI application, ingestion, RAG, providers
|-- config/onboarding.v2.yaml       onboarding source of truth
|-- data/                           corpus mount, registry/reports, generated index data
|-- deployment/                     Dockerfiles, Compose, nginx
|-- docs/                           project documentation
|-- frontend/src/                   React application
|-- scripts/                        PowerShell launcher implementations
|-- ingest.cmd                      corpus operations entrypoint
|-- start-demo.cmd                  guarded local startup
|-- stop-demo.cmd                   local shutdown
`-- .env.example                   environment configuration template
```

Use the [Codebase tour](docs/getting-started/codebase-tour.md) for the detailed backend, frontend, deployment, and configuration map.

## Outputs and local state

| Path or volume | Purpose | Committed? |
|---|---|---:|
| `data/corpus/` | Approved source files mounted for ingestion | No, except metadata and placeholders |
| `data/index/` / `ingestdata18` | Registry, figures, and derived ingestion state | No |
| `data/reports/` | Ingestion reports | No |
| `pgdata18` | PostgreSQL data and retrieval indexes | No |
| `modelcache` | Downloaded reranker artifacts | No |

## Verification

The repository currently contains no tracked automated test suite. Release confidence comes from deterministic configuration, build, readiness, corpus-status, and grounded-answer checks:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env config --quiet
docker compose -f deployment\docker-compose.yml --env-file .env build
docker compose -f deployment\docker-compose.yml --env-file .env up -d
docker compose -f deployment\docker-compose.yml --env-file .env ps
Invoke-RestMethod http://localhost:8000/api/ready
```

These checks establish operational readiness; they do not replace an independently reviewed quality benchmark when the corpus, models, or retrieval parameters change. See [Build and release verification](docs/operations/build-and-release.md).

## Documentation

The [documentation index](docs/index.md) routes readers by intent:

- Newcomers: [Quickstart](docs/getting-started/quickstart.md) and [Codebase tour](docs/getting-started/codebase-tour.md)
- Developers: [Architecture](docs/architecture/system-overview.md), [Configuration](docs/reference/configuration.md), and [API contracts](docs/reference/api-contracts.md)
- Operators: [Daily workflow](docs/guides/daily-development.md), [Corpus management](docs/operations/corpus-management.md), and [Troubleshooting](docs/reference/troubleshooting.md)
- Product and research reviewers: [Product scope and core concepts](docs/explanation/product-scope-and-concepts.md), [Onboarding profiles](docs/reference/onboarding-profiles.md), and [Evidence, citations, and figures](docs/architecture/evidence-citations-and-figures.md)

## Project boundary

DemocraSeek is not a general-purpose chatbot, an autonomous agent, a knowledge graph, an OCR platform, or a public multi-tenant SaaS product. Its current delivery boundary is a professional local demo and controlled single-host deployment.

Public production still requires authentication and authorization, shared rate limiting, monitoring, backups, high availability, and deployment and legal review.
