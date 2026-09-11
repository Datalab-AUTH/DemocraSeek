---
title: "Build and release verification"
doc_type: how-to
layer: operations
audience: "maintainer or release reviewer"
reader_goal: "verify a local build before handoff or presentation"
reader_state: "has configured the runtime environment"
source_of_truth: true
status: stable
canonical_sources:
  - "deployment/docker-compose.yml"
  - "start-demo.cmd"
  - "backend/app/api/routes_health.py"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/reference/troubleshooting.md"
rag_index: true
---

# Build and release verification

The repository contains a small standard-library backend regression suite for
request bounds and ingestion artifact rollback. It intentionally adds no test
framework or frontend test dependency. Generated dependencies and build output
are not stored; Docker reconstructs them from the pinned manifests.

Before publishing or handing over a revision, run these checks from the
repository root:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env config --quiet
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m unittest discover -s tests -p "test_*.py" -v
docker compose -f deployment\docker-compose.yml --env-file .env build
docker compose -f deployment\docker-compose.yml --env-file .env up -d
docker compose -f deployment\docker-compose.yml --env-file .env ps
Invoke-RestMethod http://localhost:8000/api/ready
```

Also run `ruff check backend` when Ruff is available locally and `npm run build`
inside `frontend/`. The production frontend Docker build runs the same TypeScript
check before bundling.

The release is operationally ready when the database and backend are healthy,
the readiness response is `ready`, the frontend opens, and one grounded answer
can open its original source. After an ingestion change, also inspect:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/corpus
```

This is runtime verification, not a substitute for an independently reviewed
quality benchmark when the corpus, models, or retrieval parameters change.
