# DemocraSeek — Developer Quick Guide

Short, practical version of the full handbook in [README.md](README.md).

---
## 1. What it is

A local-first, citation-grounded RAG application over an approved INNOVADE
knowledge base.

- The user completes a 4-step onboarding (role, intent, support need, presentation
  mode) and then asks questions in their own language.
- The question and recent history are translated to English, retrieval runs in
  English, the answer is generated in English, validated, and translated back.
- Every citation resolves to a real indexed passage: document, page, excerpt,
  original file, and figures come from ingestion records, not from the LLM.
- If evidence is insufficient or validation fails, the system **fails closed** —
  it returns an insufficient-evidence answer instead of an unverifiable one.

Two guarantees worth remembering:

| Guarantee | Meaning |
|---|---|
| Grounding | Displayed citations always map to actually retrieved evidence |
| Presentation-only personalisation | The profile changes wording, structure, and tone only. It **cannot** change retrieval, facts, page numbers, or the insufficient-evidence decision. `Retriever.retrieve(question, history)` has no profile parameter. |

---

## 2. How it works

### Offline (operator-driven ingestion)

```text
approved PDF/image in data/corpus/
  -> extract pages + embedded figures
  -> clean text, page-scoped chunking
  -> VLM describes figures -> figure chunks
  -> embeddings
  -> PostgreSQL (chunks + vectors + metadata, HNSW + BM25 indexes)
  -> registry (document/page/figure mappings) + ingestion report
```

Copying a file into `data/corpus/` does **not** index it. You must run the CLI.

### Online (per question)

```text
question + history
  -> detect language, translate to canonical English
  -> compile presentation policy from the 4 onboarding codes (deterministic, no LLM)
  -> dense retrieval (threshold gate) + BM25 -> cross-encoder rerank -> top-K evidence
  -> system + user prompt -> llama3.1:8b returns strict JSON
  -> parse + validate citations -> hydrate trusted metadata from the index
  -> translate answer text around [C...] markers, verify marker sequence
  -> render answer + source evidence
```

### Runtime topology

| Component | Where | Host port |
|---|---|---:|
| `frontend` — nginx + Vite-built React, proxies `/api` | Docker | `8080` |
| `backend` — Python 3.13, FastAPI/Uvicorn | Docker | `8000` |
| `db` — PostgreSQL 18 + pgvector + pg_textsearch | Docker | `5434` |
| Ollama — `llama3.1:8b`, `nomic-embed-text`, `qwen2.5vl:7b` | **Host, not Docker** | `11434` |

Containers reach Ollama through `host.docker.internal:11434`. All host ports bind
to `127.0.0.1`. The browser uses a single origin (`http://localhost:8080`), so
there is no CORS setup and no hard-coded backend URL in the bundle.

Persistent state lives in named volumes: `pgdata18` (database), `ingestdata18`
(registry + extracted figures), `modelcache` (reranker). `docker compose down`
keeps them unless you add `--volumes` — do not add it unless you want a full rebuild.

---

## 3. Prerequisites

- Windows 10/11 with PowerShell (for the included launchers)
- Docker Desktop with Compose v2
- Ollama on the host
- Disk/RAM for `llama3.1:8b`, `nomic-embed-text`, `qwen2.5vl:7b`, the Docker
  images, and the reranker

Python and Node are **not** required on the host for normal Docker runtime.

---

## 4. The corpus: where the files go and how to index them

### The corpus does not come with the repository

Corpus documents are gitignored and distributed out of band. The reviewed
`corpus.metadata.yaml` remains in the repository because it contains attribution
rather than document contents and is the single metadata manifest used by ingestion.

The index is machine-local too. `pgdata18` (chunks and vectors) and `ingestdata18`
(registry, page records, figure PNGs) are Docker named volumes that never travel
with the repository, so **every new machine runs its own `ingest`** even though
the checkout is identical.

### Where to copy the files

Two variables in `.env` describe one folder from two sides:

| Variable | Value in `.env.example` | Side |
|---|---|---|
| `CORPUS_HOST_PATH` | `../data/corpus` | on your disk — **this is where the files go** |
| `CORPUS_PATH` | `/app/data/corpus` | inside the backend container |

Compose bind-mounts the first onto the second, read-only:

```yaml
- ${CORPUS_HOST_PATH}:${CORPUS_PATH}:ro
```

`CORPUS_HOST_PATH` is resolved **relative to `deployment/`**, because that is where
the compose file lives — so the default `../data/corpus` means `data/corpus/` at
the repository root. Change it only if your documents live outside the repository;
leave `CORPUS_PATH` alone.

`REPORT_HOST_PATH` (`../data/reports`) works the same way and is where ingestion
reports land on your disk. The registry is the exception: it lives in the
`ingestdata18` volume rather than on the host, which is why host `data/index/`
stays empty when you run through Compose.

### Corpus layout

```text
data/corpus/
├── internal/   # interface may show excerpts, pages, figures, and the local file
├── external/   # local copy is searchable but never exposed by the API
└── corpus.metadata.yaml
```

The scanner is recursive. Files directly under `data/corpus/` remain compatible
and are treated as internal, but new material should use the two named folders.

### What may go in

`.pdf`, `.png`, `.jpg` / `.jpeg`, `.webp`, `.bmp`, `.tif` / `.tiff`, `.gif`.

There is no upload endpoint. Placing a file on disk is the only way in, and
approving the corpus is deliberately an operator action.

`corpus.metadata.yaml` supplies reviewed metadata keyed by an exact filename or
corpus-relative path. Internal entries are optional. Every external file must
have `document_title`, non-empty `authors`, non-empty `publishers`,
`publication_date`, and an absolute HTTP(S) `external_url`. An incomplete
external file is rejected instead of being shown with invented attribution.

Changing source metadata is detected by its own fingerprint, so the normal
incremental `ingest` updates that document. External source files, page text,
excerpts, and extracted images are never returned to the browser; citations show
the reviewed bibliography and link instead.

### Indexing

Copying a file **does not** index it. The launcher does the whole thing from the
repository root:

```powershell
.\ingest.cmd                          # incremental - the normal one
.\ingest.cmd -Only "Document.pdf"     # one exact file
.\ingest.cmd -Force                   # force reprocessing
.\ingest.cmd -Status                  # what is indexed right now, changes nothing
.\ingest.cmd -Reindex -Yes            # full rebuild of derived index state
```

It starts Ollama and Docker Desktop if they are down, checks that the embedding
and vision models are actually installed, runs the command, and prints the corpus
status afterwards. The stack does not need to be up first — Compose starts the
database on its own. `-Reindex` refuses to run without `-Yes`, because it throws
away the whole index and pays the full ingestion cost again.

Everything it does is a wrapper over one CLI, which you can also call directly:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli <command>
```

| Command | Purpose |
|---|---|
| `check-config` | validate `.env` before starting |
| `status` | indexed documents, stable IDs, counts |
| `ingest` | incremental — the normal one |
| `ingest --only "Document.pdf"` | one exact file |
| `ingest --force` | force reprocessing |
| `remove <document_id>` | drop one indexed document (no launcher flag) |
| `reindex --yes` | full rebuild of derived index state |

- **Add:** copy the file, run `ingest`.
- **Update:** replace the file keeping the same filename (stable identity), run `ingest`.
- **Delete:** delete the source and run a full `ingest`, or `remove <document_id>`.
- **Change that affects vectors or chunks:** `reindex --yes`, not incremental ingest.

The first run is slow because the VLM describes every kept figure. `reindex` is
destructive only to derived index state — `data/corpus/` remains the source of truth.

### Confirming it worked

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/corpus   # pending_files must be empty
Invoke-RestMethod http://localhost:8000/api/ready    # must report "ready"
```

`/api/ready` fails closed and names the cause:

| Message | Meaning |
|---|---|
| `missing: run python -m app.cli ingest` | the collection has never been indexed |
| `empty: no documents ingested` | the registry holds no documents |
| `incompatible with current configuration: re-index required` | embeddings, chunking, or `INDEX_VERSION` changed since indexing |

A file sitting in the corpus folder unindexed does **not** fail readiness — it
appears as `pending_files`, so "I copied a file and nothing happened" stays
distinguishable from a broken system.

The full report lands in `data/reports/`. It is the only reliable way to confirm
how many figures were kept and whether the VLM actually described them.

---

## 5. First run

```powershell
# 1. configuration
Copy-Item .env.example .env      # then review ports, model names, vision, retrieval

# 2. models on the host
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama pull qwen2.5vl:7b

# 3. approved documents - NOT in the repository, see section 4
#    copy them into data/corpus/

# 4. build and start
docker compose -f deployment\docker-compose.yml --env-file .env up -d --build

# 5. ingest (slow on first run: the VLM describes every figure)
.\ingest.cmd

# 6. verify
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
Invoke-RestMethod http://localhost:8000/api/ready
```

Before ingestion, `/api/ready` is expected to report not-ready. Do not commit `.env`.

## 6. Daily run

```powershell
.\start-demo.cmd            # validates .env, starts Ollama + Docker, waits for /api/ready, opens the UI
.\start-demo.cmd -Build     # after code, dependency, or frontend changes
.\start-demo.cmd -NoBrowser
.\stop-demo.cmd             # stops, keeps database and index
.\ingest.cmd                # index new or changed corpus files (see section 4)
```

Open: UI `http://localhost:8080` · API docs `http://localhost:8000/docs` ·
readiness `http://localhost:8000/api/ready`

Status and logs:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env ps
docker compose -f deployment\docker-compose.yml --env-file .env logs --tail 100 backend
Invoke-RestMethod http://localhost:8000/api/corpus
```

## 7. Configuration — where to change what

**Single source: the root `.env`.** Compose injects it into the backend and also
reads it for ports, mounts, PostgreSQL credentials, and frontend build args. There
are no secondary Docker-specific env files. `.env.example` holds the same variable
names with safe template values. `backend/app/config.py` only does typed validation
and cross-field checks — it is not a second operator config file.

`config/onboarding.v2.yaml` is separate on purpose: it is versioned product policy,
not infrastructure configuration.

Key groups in `.env`:

| Group | Variables | Notes |
|---|---|---|
| App | `APP_ENV`, `LOG_LEVEL`, `FRONTEND_HOST_PORT`, `BACKEND_HOST_PORT` | |
| Answer LLM | `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_TEMPERATURE`, `LLM_MAX_OUTPUT_TOKENS`, `LLM_TIMEOUT_SECONDS` | `openai_compatible` adapter; Ollama accepts `ollama` as the key |
| Embeddings | `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_BATCH_SIZE` | dimensions must match the returned vectors |
| Vision | `VISION_PROVIDER` (`none` / `openai_compatible`), `VISION_MODEL`, `VISION_BASE_URL`, `VISION_MAX_DESCRIPTION_CHARS` | |
| Retrieval | `RETRIEVAL_CANDIDATE_K` (10), `RETRIEVAL_TOP_K` (6), `RETRIEVAL_SCORE_THRESHOLD` (0.65), `RETRIEVAL_MAX_CONTEXT_TOKENS` (4000), `RERANK_MODEL` | the actual tuning knobs |
| Store | `VECTOR_STORE_COLLECTION`, `VECTOR_STORE_URL`, `POSTGRES_HOST_PORT`, `POSTGRES_USER` / `PASSWORD` / `DB` | inside Compose the backend always talks to `db:5432` |
| Corpus | `CORPUS_PATH`, `INDEX_PATH`, `REPORT_PATH`, `CHUNK_SIZE` (1200), `CHUNK_OVERLAP` (180), `INDEX_VERSION` | |
| Limits | `ONBOARDING_CONFIG_PATH`, `MAX_USER_INPUT_CHARS`, `MAX_CONVERSATION_MESSAGES`, `RATE_LIMIT_*` | |
| Frontend (build-time) | `VITE_API_BASE_URL` (leave empty for same-origin), `VITE_APP_NAME`, `VITE_PROJECT_NAME`, `VITE_LOGO_URL` | baked into the image; needs `-Build` |
| Frontend (dev server only) | `VITE_DEV_API_TARGET` | where `npm run dev` proxies `/api`, default `http://127.0.0.1:8000`; Compose never passes it |

Validate before starting:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli check-config
```

### What each change requires

| Change | Edit | Restart/rebuild | Re-index? |
|---|---|---|---:|
| Answer LLM model / URL / key | `.env` `LLM_*` | restart backend | no |
| Top-K, candidate-K, threshold, budget | `.env` `RETRIEVAL_*` | restart backend | no |
| Reranker model | `.env` `RERANK_MODEL` | rebuild/restart | no |
| Embedding provider / model / dimensions | `.env` `EMBEDDING_*` | restart | **yes** |
| Chunk size / overlap | `.env` `CHUNK_*` | restart | **yes** |
| Vision provider / model | `.env` `VISION_*` | restart | **yes** |
| Corpus add / update / delete | `data/corpus/` | none | incremental `ingest` |
| Onboarding wording or policy | new versioned YAML + `ONBOARDING_CONFIG_PATH` | rebuild/restart | no |
| Frontend branding / API URL | `VITE_*` | rebuild frontend | no |
| PostgreSQL host port | `.env` `POSTGRES_HOST_PORT` | recreate port mapping | no |
| Chunking algorithm code | ingestion code + bump `CHUNKING_VERSION` | rebuild | **yes** |

Switching to another OpenAI-compatible endpoint is just `LLM_PROVIDER`,
`LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY` plus a restart — the answer model does
not create stored vectors. For a non-compatible API, implement `LLMProvider` in
[backend/app/providers/base.py](backend/app/providers/base.py) and add an explicit
branch in [backend/app/providers/factory.py](backend/app/providers/factory.py).
Switching embeddings means updating provider, model, URL, key **and** dimensions
together, then re-indexing — vectors from different models cannot be compared.

---

## 8. Onboarding — where to change what

[config/onboarding.v2.yaml](config/onboarding.v2.yaml) is the single source of
truth: `policy_version`, the five locales (`en`, `el`, `fr`, `es`, `nl-BE`) with
full translations, all form copy, five global guardrails, four ordered questions
with stable codes, per-choice instruction lines, and optional combination overrides.

The frontend duplicates none of this wording — it fetches
`GET /api/onboarding/config`. The backend loads the same file for validation and
policy compilation. If a non-default locale is missing any question ID or choice
code, startup fails.

The four questions: **Role** `R1`–`R7`, **Intent** `I1`–`I6`, **Support need**
`S1`–`S6`, **Presentation mode** `M1`–`M5` → 7 × 6 × 6 × 5 = 1,260 profiles.

[backend/app/onboarding/compiler.py](backend/app/onboarding/compiler.py) turns the
four codes into a policy string by deterministic composition — no LLM, no
retrieval, no randomness, so the same codes always produce byte-identical output:

```text
compiled policy = global guardrails + support + intent + role + mode + matching overrides
precedence on conflict: Support > Intent > Role > Mode
```

**To change onboarding safely** — never edit a published policy version in place:

1. Copy `config/onboarding.v2.yaml` to `config/onboarding.v3.yaml`.
2. Change `policy_version`.
3. Edit questions, labels, fragments, guardrails, precedence, or overrides.
4. Set `ONBOARDING_CONFIG_PATH=config/onboarding.v3.yaml` in `.env`.
5. Rebuild/restart backend and frontend, then have users review their profile.

No re-index is needed — document vectors do not depend on onboarding. A stored
profile carries the version it was created under; a mismatch is rejected with HTTP
`409` and never silently reinterpreted.

For a translation fix that does not change meaning, edit the entry under
`translations`, rebuild/restart, and do not re-index. Anything that changes the
meaning of a label, code, or instruction is a policy change → use the versioned
procedure above.

---

## 9. HTTP API

Interactive docs: `http://localhost:8000/docs`.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | liveness only |
| `GET /api/ready` | database, index compatibility, registry, corpus, pending files |
| `GET /api/corpus` | indexed documents, counts, pending files, starter questions |
| `GET /api/onboarding/config` | versioned questions, translations, locale metadata |
| `POST /api/onboarding/compile` | validate a profile, inspect the compiled policy |
| `POST /api/chat` | grounded or insufficient-evidence response |
| `GET /api/sources/{document_id}?page=N` | trusted metadata + page preview |
| `GET /api/sources/{document_id}/figures/{figure_id}` | stored figure PNG |
| `GET /api/sources/{document_id}/file` | original approved file |

A chat request carries `question`, `profile` (`policy_version`, `role_code`,
`intent_code`, `support_code`, `mode_code`), and `history`. Responses include
`language_code`, `canonical_question`, and `canonical_answer` (the validated
English answer before translation) — these are conversation state, not hidden
reasoning.

Error codes worth knowing: `409 policy_version_mismatch`, `429 rate_limited`,
`503 index_incompatible` / `provider_unavailable`.

---

## 10. Code map

```text
backend/app/          FastAPI backend
config/               onboarding.v2.yaml — onboarding source of truth
data/                 corpus/ (approved sources), index/, reports/
deployment/           Dockerfiles, docker-compose.yml, nginx.conf
frontend/             React + TypeScript
scripts/              start-demo.ps1 / stop-demo.ps1
```

Read the backend in this order:

| Order | File | Why |
|---:|---|---|
| 1 | [backend/app/rag/orchestrator.py](backend/app/rag/orchestrator.py) | the entire online flow in one file — no LangChain/LlamaIndex hiding steps |
| 2 | [backend/app/rag/retriever.py](backend/app/rag/retriever.py) | dense gate, hybrid candidates, reranking |
| 3 | [backend/app/rag/prompt.py](backend/app/rag/prompt.py) | system prompt + user prompt assembly |
| 4 | [backend/app/rag/citations.py](backend/app/rag/citations.py) | structural citation validation |
| 5 | [backend/app/ingestion/pipeline.py](backend/app/ingestion/pipeline.py) | complete ingestion orchestration |
| 6 | [backend/app/api/deps.py](backend/app/api/deps.py) | builds the provider/store/orchestrator object graph once |

Other useful entry points: [backend/app/cli.py](backend/app/cli.py) (all operator
commands), [backend/app/config.py](backend/app/config.py) (typed settings and
fingerprint), [backend/app/providers/factory.py](backend/app/providers/factory.py)
(adapter selection),
[backend/app/providers/vectorstore_pgvector.py](backend/app/providers/vectorstore_pgvector.py)
(HNSW cosine + BM25 search),
[backend/app/services/multilingual_chat.py](backend/app/services/multilingual_chat.py)
(language routing and citation-safe translation).

Frontend: [frontend/src/App.tsx](frontend/src/App.tsx) (config, profile, and
conversation lifecycle),
[Onboarding.tsx](frontend/src/components/Onboarding.tsx) (backend-driven form),
[ChatPanel.tsx](frontend/src/components/ChatPanel.tsx),
[SourceDrawer.tsx](frontend/src/components/SourceDrawer.tsx) (evidence, page,
figure, original source), [useProfile.ts](frontend/src/hooks/useProfile.ts)
(versioned local profile), [i18n.tsx](frontend/src/i18n.tsx).

The backend is deliberately synchronous — FastAPI runs sync handlers in its thread
pool, and there is no token streaming.

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `start-demo.cmd` times out on readiness | Check `/api/ready` and backend logs. Usually: nothing ingested in the `ingestdata18` volume, missing model, fingerprint mismatch, db unavailable, pending files, or reranker download failure |
| Container cannot reach Ollama | `*_BASE_URL` must be `http://host.docker.internal:11434/v1`; verify `http://localhost:11434/api/tags` on the host; check VPN/firewall |
| Missing model | `ollama list`, then pull. Tags in `.env` must match installed tags exactly |
| PostgreSQL port conflict | Change `POSTGRES_HOST_PORT`; `VECTOR_STORE_URL` still uses `db:5432` |
| A copied file is not searchable | Copying is not ingestion — run `ingest`, then check `pending_files` in `/api/corpus` |
| Index incompatible after a config change | `reindex --yes`. Do not suppress the compatibility error |
| Answer rejected despite good evidence | The model broke JSON, marker, or evidence-ID rules — look for `generation_parse_rejected` or `citation_validation_rejected` in backend logs |
| Figure shown but unusable for answering | Index built with `VISION_PROVIDER=none`, VLM description failed, figure filtered, or `.env` changed without re-index — check the latest report |
| Host registry differs from Docker | Compose uses the `ingestdata18` volume, not host `data/index/` — run the CLI through Compose |
| Frontend changes not visible | Vite assets are baked into the image — `.\start-demo.cmd -Build` |
| Docker Desktop shows one item | Compose groups the three services (`db`, `backend`, `frontend`) under one project — expand it |

---
