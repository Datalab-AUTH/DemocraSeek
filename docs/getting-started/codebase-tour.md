---
title: "Codebase tour"
doc_type: tutorial
layer: user
audience: "new developer"
reader_goal: "find the main repository areas and implementation entrypoints"
reader_state: "has read the project overview"
source_of_truth: false
status: stable
canonical_sources:
  - "backend/app"
  - "frontend/src"
  - "deployment"
  - "scripts"
related_docs:
  - "docs/architecture/system-overview.md"
  - "docs/index.md"
rag_index: true
---

# Codebase tour

## Clean top-level structure

```text
democraseek/
|-- backend/app/                    backend application
|-- config/onboarding.v2.yaml       onboarding source of truth
|-- data/
|   |-- corpus/                     approved source files
|   |-- index/                      generated registry/page/figure artefacts
|   `-- reports/                    generated ingestion reports
|-- deployment/                     Dockerfiles, Compose, nginx
|-- frontend/                       React/TypeScript application
|-- scripts/                        demo start/stop scripts
|-- .dockerignore
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- requirements.txt
|-- ingest.cmd
|-- start-demo.cmd
|-- stop-demo.cmd
|-- docs/                           detailed project documentation
`-- README.md                       repository homepage
```

Generated `.venv`, `node_modules`, `dist`, Python caches, tool caches, and old
reports are deliberately absent. They are reconstructed from pinned manifests.

## Backend code map

| Path | Responsibility |
|---|---|
| `app/main.py` | FastAPI application factory |
| `app/cli.py` | `check-config`, `ingest`, `remove`, `reindex`, `status` |
| `app/config.py` | typed settings, validation, fingerprint |
| `app/logging_setup.py` | structured redacted logging |
| `app/api/deps.py` | builds provider/store/orchestrator object graph once |
| `app/api/routes_chat.py` | chat endpoint |
| `app/api/routes_onboarding.py` | onboarding configuration and compilation |
| `app/api/routes_sources.py` | source page, original file, figure endpoints |
| `app/api/routes_health.py` | health, readiness, corpus status |
| `app/api/errors.py` | stable safe API errors |
| `app/api/middleware.py` | request IDs, timing, access log |
| `app/api/rate_limit.py` | in-memory sliding window |
| `app/services/multilingual_chat.py` | language detection, English canonical context, final translation |
| `app/onboarding/config_loader.py` | YAML validation |
| `app/onboarding/compiler.py` | four codes to deterministic policy |
| `app/ingestion/pipeline.py` | complete ingestion orchestration |
| `app/ingestion/pdf_extract.py` | pages, checksum, OCR-review signals |
| `app/ingestion/cleaning.py` | repeated header/footer cleanup |
| `app/ingestion/headings.py` | headings, contents-page detection, topics |
| `app/ingestion/chunking.py` | deterministic page-scoped chunks |
| `app/ingestion/figures.py` | PDF image extraction/filter/caption/VLM chunks |
| `app/ingestion/standalone_images.py` | approved image document support |
| `app/ingestion/lock.py` | single-writer protection |
| `app/ingestion/report.py` | JSON/text audit reports |
| `app/rag/orchestrator.py` | complete online answer flow |
| `app/rag/query.py` | validation and follow-up retrieval query |
| `app/rag/retriever.py` | dense gate, hybrid candidates, reranking |
| `app/rag/evidence.py` | evidence IDs and context budget |
| `app/rag/prompt.py` | fixed system prompt and user prompt assembly |
| `app/rag/generator.py` | strict output parsing |
| `app/rag/citations.py` | structural validation and safe excerpts |
| `app/corpus/registry.py` | document/page/figure records and safe path resolution |
| `app/providers/base.py` | provider protocols |
| `app/providers/factory.py` | explicit adapter selection |
| `app/providers/language_llm.py` | LLM language routing and citation-safe translation |
| `app/providers/*openai_compatible.py` | real LLM/embedding/vision adapters |
| `app/providers/rerank_cross_encoder.py` | real reranker |
| `app/providers/vectorstore_pgvector.py` | PostgreSQL CRUD, HNSW cosine search, and shared BM25 search |
| `app/schemas/` | internal/API Pydantic data contracts |

Start code reading with:

1. `backend/app/rag/orchestrator.py`;
2. `backend/app/rag/retriever.py`;
3. `backend/app/rag/prompt.py`;
4. `backend/app/rag/citations.py`;
5. `backend/app/ingestion/pipeline.py`;
6. `backend/app/api/deps.py`.

## Frontend code map

| Path | Responsibility |
|---|---|
| `src/App.tsx` | configuration, profile, and conversation lifecycle |
| `src/api/client.ts` | fetch wrapper |
| `src/api/types.ts` | frontend API contracts |
| `src/i18n.tsx` | application UI translations and locale context |
| `src/components/Welcome.tsx` | first-session INNOVADE introduction and entry routing |
| `src/components/LanguageSelector.tsx` | persistent language control shared by welcome, onboarding, and chat |
| `src/components/Onboarding.tsx` | backend-driven four-step onboarding |
| `src/components/ChatPanel.tsx` | messages, composer, requests |
| `src/components/AnswerMessage.tsx` | answer and inline citations |
| `src/components/SourceDrawer.tsx` | evidence/page/figure/original source |
| `src/components/FigureGallery.tsx` | cited figures |
| `src/components/Header.tsx` | app identity and profile controls |
| `src/components/Footer.tsx` | INNOVADE/EU marks and application-wide legal copy |
| `src/hooks/useProfile.ts` | versioned local profile |
| `src/hooks/useOnboardingLocale.ts` | persistent local interface-language preference (legacy key retained) |
| `src/hooks/useTheme.ts` | theme preference |
| `src/lib/excerpt.ts` | source excerpt presentation helpers |
| `src/styles.css` | visual system and responsive layout |

## Deployment files

| File | Responsibility |
|---|---|
| `deployment/docker-compose.yml` | the complete local service topology |
| `deployment/Dockerfile.backend` | non-root Python 3.13 backend image |
| `deployment/Dockerfile.database` | PostgreSQL 18 + pgvector image with `pg_textsearch` preloaded |
| `deployment/Dockerfile.frontend` | Node build stage and nginx runtime |
| `deployment/nginx.conf` | static serving, same-origin API proxy, headers |
| `.dockerignore` | excludes mounted data, local configuration, docs, dependencies, and caches |
| `scripts/start-demo.ps1` | guarded one-command startup |
| `scripts/stop-demo.ps1` | non-destructive stop |
| `scripts/ingest.ps1` | guarded corpus ingestion, status, and reindex |

Reviewed frontend marks are served from `frontend/public/`, including
`logo.svg`, `logo_innovade_full.svg`, and `eu_funded_en.svg`.

---
