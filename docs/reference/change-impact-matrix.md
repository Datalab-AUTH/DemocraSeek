---
title: "Configuration change impact"
doc_type: reference
layer: user
audience: "developer or operator"
reader_goal: "determine what restart, rebuild, re-index, or evaluation a change requires"
reader_state: "understands the configuration reference"
source_of_truth: true
status: stable
canonical_sources:
  - ".env.example"
  - "deployment/docker-compose.yml"
  - "backend/app/config.py"
related_docs:
  - "docs/guides/change-models-and-providers.md"
  - "docs/reference/configuration.md"
rag_index: true
---

# Configuration change impact

| Change | Edit | Restart/rebuild | Re-index? | Re-evaluate? |
|---|---|---|---:|---:|
| Answer LLM model/URL/key | `.env` `LLM_*` | restart backend | no | yes, citation/style quality |
| Temperature/output limit | `.env` `LLM_*` | restart backend | no | recommended |
| Top-K/candidate-K/threshold/budget | `.env` `RETRIEVAL_*` | restart backend | no | **yes** |
| Reranker model | `.env` `RERANK_MODEL` | rebuild/restart if model cache changes | no | **yes** |
| Embedding provider/model/dimensions | `.env` `EMBEDDING_*` | restart | **yes** | **yes** |
| Chunk size/overlap | `.env` `CHUNK_*` | restart | **yes** | **yes** |
| Vision provider/model | `.env` `VISION_*` | restart | **yes** | yes |
| Corpus add/update/delete | `data/corpus/` | none | incremental `ingest` | review report |
| Onboarding wording/policy | new versioned YAML + path | rebuild/restart | no | profile review/demo |
| Frontend branding/API URL | Vite build variables | rebuild frontend | no | UI check |
| PostgreSQL host port | `.env` `POSTGRES_HOST_PORT` | recreate port mapping | no | connectivity only |
| Vector-store implementation | new adapter/factory/config | rebuild | re-ingest | full |
| Chunking algorithm code | ingestion code + bump `CHUNKING_VERSION` | rebuild | **yes** | full |
