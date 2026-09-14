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
  - "Jenkinsfile"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/reference/troubleshooting.md"
rag_index: true
---

# Build and release verification

The delivery repository contains no tracked automated test suite or evaluation
harness. The Jenkins pipeline builds and pushes the database, backend, and
frontend images; it does not run behavioral tests. Generated dependencies and
build output are not stored because Docker reconstructs them from the pinned
manifests.

Before publishing or handing over a revision, run these checks from the
repository root:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env config --quiet
docker compose -f deployment\docker-compose.yml --env-file .env build
docker compose -f deployment\docker-compose.yml --env-file .env up -d
docker compose -f deployment\docker-compose.yml --env-file .env ps
Invoke-RestMethod http://localhost:8000/api/ready
```

The release is operationally ready when the database and backend are healthy,
the readiness response is `ready`, the frontend opens, and one grounded answer
can open its original source. After an ingestion change, also inspect:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/corpus
```

This is runtime verification, not a substitute for an independently reviewed
quality benchmark when the corpus, models, or retrieval parameters change.

## Jenkins delivery pipeline

`Jenkinsfile` checks out the selected revision, builds all three Docker images,
and pushes them to the configured registry. Registry destination and credential
IDs are operator-owned Jenkins settings. A successful Jenkins build proves that
the images built and were pushed; it does not prove readiness, ingestion, or
grounded-answer quality.
