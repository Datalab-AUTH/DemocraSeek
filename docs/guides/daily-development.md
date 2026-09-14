---
title: "Daily development workflow"
doc_type: how-to
layer: user
audience: "developer or operator"
reader_goal: "start, inspect, rebuild, and stop the local stack during routine work"
reader_state: "has completed the first installation"
source_of_truth: false
status: stable
canonical_sources:
  - "start-demo.cmd"
  - "stop-demo.cmd"
  - "ingest.cmd"
  - "deployment/docker-compose.yml"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/reference/troubleshooting.md"
rag_index: true
---

# Daily development workflow

```powershell
.\start-demo.cmd            # validates providers + .env, starts Docker, waits for /api/ready, opens the UI
.\start-demo.cmd -Build     # after code, dependency, or frontend changes
.\start-demo.cmd -NoBrowser
.\stop-demo.cmd             # stops, keeps database and index
.\ingest.cmd                # index new or changed corpus files; see the corpus management guide
```

Open: UI `http://localhost:8080` · API docs `http://localhost:8000/docs` ·
readiness `http://localhost:8000/api/ready`

Status and logs:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env ps
docker compose -f deployment\docker-compose.yml --env-file .env logs --tail 100 backend
Invoke-RestMethod http://localhost:8000/api/corpus
```
