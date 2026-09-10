---
title: "System overview"
doc_type: explanation
layer: architecture
audience: "developer, maintainer, or technical reviewer"
reader_goal: "understand service boundaries and runtime topology"
reader_state: "knows the project purpose"
source_of_truth: true
status: stable
canonical_sources:
  - "deployment/docker-compose.yml"
  - "backend/app/main.py"
  - "frontend/src/App.tsx"
related_docs:
  - "docs/architecture/ingestion-pipeline.md"
  - "docs/architecture/answering-pipeline.md"
rag_index: true
---

# System overview

## Architecture

### High-level component diagram

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
|                                            | PostgreSQL  |  | Host Ollama    |  |
|                                            | pgvector    |  | llama3.1:8b    |  |
|                                            | + HNSW      |  | nomic-embed    |  |
|                                            | pg_text-    |  | qwen2.5vl:7b   |  |
|                                            | search+BM25 |  +----------------+  |
|                                            +-------------+                      |
|                                                                                |
|  Operator CLI                                                                  |
|     approved files -> extraction -> chunks/figures -> embeddings -> stores     |
|                                                                                |
+--------------------------------------------------------------------------------+
```

### Two flows share one knowledge layer

```text
OFFLINE / OPERATOR CONTROLLED

Approved PDF or image
  -> extract pages and embedded figures
  -> clean and page-scope text
  -> create text and figure chunks
  -> create embeddings
  -> store chunks/vectors/metadata in PostgreSQL
  -> maintain HNSW vector and pg_textsearch BM25 indexes
  -> store document/page/figure mappings in registry
  -> write ingestion report


ONLINE / PER QUESTION

Question + recent history
  -> detect the current question language
  -> translate the question and any non-canonical history to English
  -> normalize and optionally expand an English follow-up
  -> compile presentation policy
  -> dense gate + BM25 candidates + cross-encoder rerank
  -> create E1..En evidence context
  -> assemble system and user prompts
  -> llama3.1:8b returns strict JSON
  -> parse and validate citations
  -> hydrate trusted document/page/figure data from index records
  -> split the validated English answer around [C...] markers
  -> translate only the text segments into the current question's language
  -> reinsert and verify the exact citation-marker sequence
  -> render the translated answer and original source evidence
```

### Important design choices

**Explicit orchestration.** No LangChain or LlamaIndex hides the critical steps.
`backend/app/rag/orchestrator.py` shows the complete request flow in one file.

**Synchronous backend.** Model and database adapters are synchronous. FastAPI
runs synchronous route handlers in its thread pool. The current single-host
workload gains little from adding async complexity and does not stream tokens.

**Small provider interfaces.** LLM, language routing, embeddings, vision,
reranking, and vector storage are isolated behind explicit protocols and
factory branches.

**One index table per collection.** Each collection has its own dimensioned
vector column, pgvector HNSW index, and pg_textsearch BM25 index. A different
embedding shape therefore uses a clean re-index instead of silently mixing
incompatible vectors.

**Operator-controlled ingestion.** Starting the API or copying a file does not
approve or index it. The operator must run the CLI.

**Fail-closed output.** A malformed or unverifiable model response is retried
once, then discarded.

---

## Runtime and deployment topology

### What runs in Docker

`deployment/docker-compose.yml` defines:

| Service | Technology | Purpose | Host port |
|---|---|---|---:|
| `frontend` | nginx 1.31.4 + Vite-built React bundle | UI and same-origin `/api` proxy | `8080` |
| `backend` | Python 3.13 + FastAPI + Uvicorn | API, RAG orchestration, source serving | `8000` |
| `db` | PostgreSQL 18 + pgvector 0.8.6 + pg_textsearch 1.4.0 | chunks, metadata, embeddings, HNSW and BM25 indexes | configurable, active `5434` |

All published host ports bind to `127.0.0.1` by default. The database, direct
backend port and UI are therefore reachable only from the machine running the
demo; nginx still proxies browser `/api` requests over the private Compose
network. A public deployment should place a reviewed TLS reverse proxy in front
of the frontend instead of exposing PostgreSQL or the backend directly.

Docker Desktop may display one `democraseek` group. Expanding it reveals the
three normal containers. Seeing one group does not mean pgvector is missing.

### What remains outside Docker

Ollama runs on the host:

- it can use the workstation's model installation and acceleration;
- large model files are not duplicated in application images;
- containers reach it through `host.docker.internal:11434`.

The project therefore has a Dockerized application stack, but not a
"nothing installed except Docker" runtime. Docker Desktop and Ollama are both
required for the configured local deployment.

### Persistent storage

| Storage | Contents |
|---|---|
| `pgdata18` named volume | PostgreSQL 18 database, collections, HNSW and BM25 indexes |
| `ingestdata18` named volume | Docker runtime registry, page records, and extracted figure PNGs |
| `modelcache` named volume | downloaded cross-encoder model cache |
| host `data/corpus/` | approved source files, mounted read-only |
| host `data/reports/` | ingestion audit reports |

`docker compose stop` or `.\stop-demo.cmd` preserves all named volumes.
`docker compose down` also preserves them unless `--volumes` is explicitly
added. Never use `down --volumes` before a demo unless a full rebuild is
intended.

### Same-origin frontend

nginx serves the UI and proxies `/api/` to the backend. The browser therefore
uses one origin (`http://localhost:8080`) and the bundle does not need a
machine-specific backend URL. This removes the common CORS and hard-coded-host
failure modes.

---
