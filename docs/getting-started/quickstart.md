---
title: "Quickstart"
doc_type: tutorial
layer: user
audience: "new developer or operator"
reader_goal: "complete a first local installation and grounded-answer check"
reader_state: "has a fresh checkout and the required host tools"
source_of_truth: false
status: stable
canonical_sources:
  - "start-demo.cmd"
  - "ingest.cmd"
  - "deployment/docker-compose.yml"
  - ".env.example"
related_docs:
  - "docs/guides/daily-development.md"
  - "docs/operations/corpus-management.md"
rag_index: true
---

# Quickstart

## Prerequisites

- Windows 10/11 with PowerShell for the included launchers;
- Docker Desktop with Compose v2;
- Ollama;
- enough disk/RAM for `llama3.1:8b`, `nomic-embed-text`,
  `qwen2.5vl:7b`, Docker images, and the reranker;
- internet for first image build/model downloads unless artifacts are preloaded.

Python and Node are not required on the host for normal Docker runtime.

This section covers the first installation. For the day-to-day workflow after
that (`start-demo.cmd`, `-Build`, `stop-demo.cmd`, status checks, and logs),
see the [daily development workflow](../guides/daily-development.md).

## 1. Configure

```powershell
Copy-Item .env.example .env
```

Review:

- PostgreSQL host port;
- corpus version;
- local model names;
- whether vision is enabled;
- retrieval values.

Do not commit `.env`.

## 2. Pull local models

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama pull qwen2.5vl:7b
```

## 3. Add approved corpus files

Place INNOVADE documents in `data/corpus/internal/` and downloaded third-party
documents in `data/corpus/external/`. Record external attribution and URLs in
`data/corpus/corpus.metadata.yaml`. This reviewed manifest is the single source
of corpus attribution metadata and also shows the required schema.

## 4. Build and start infrastructure/application

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env up -d --build
```

On a new index, readiness can remain unavailable until ingestion. That is
expected.

## 5. Ingest

```powershell
.\ingest.cmd
```

The launcher starts Ollama and Docker Desktop if needed, verifies that the
embedding and vision models are installed, runs the ingestion, and prints the
resulting corpus status. The equivalent explicit command is:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli ingest
```

The first run can take significant time because the VLM describes each figure
and embeddings are created. Do not interrupt it unless necessary.

## 6. Verify and open

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/ready
```

Then open `http://localhost:8080` or run:

```powershell
pnpm dev
```

This is a short alias for the existing Windows launcher. `\.\start-demo.cmd`
remains available when Node and pnpm are not installed.

## 7. Pre-presentation check

Run `start-demo.cmd`, confirm `/api/ready` reports `ready`, check that
`/api/corpus` has no unexpected pending files, and rehearse one grounded answer
whose citation opens the correct source.

---
