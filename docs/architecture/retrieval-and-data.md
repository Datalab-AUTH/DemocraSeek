---
title: "Retrieval, PostgreSQL, and data ownership"
doc_type: reference
layer: architecture
audience: "developer, maintainer, or retrieval reviewer"
reader_goal: "verify hybrid retrieval, indexing, persistence, and ownership boundaries"
reader_state: "understands RAG terminology"
source_of_truth: true
status: stable
canonical_sources:
  - "backend/app/providers/vectorstore_pgvector.py"
  - "backend/app/rag/retriever.py"
  - "backend/app/corpus/registry.py"
related_docs:
  - "docs/architecture/ingestion-pipeline.md"
  - "docs/reference/configuration.md"
rag_index: true
---

# Retrieval, PostgreSQL, and data ownership

## Hybrid retrieval, reranking, Top-K, threshold, and HNSW

### The exact query-time algorithm

Every grounded query uses the same `hybrid_rerank` path. There is no dense-only
runtime option.

```text
question (+ limited history when needed)
  -> nomic-embed-text query vector
  -> pgvector dense search: candidate_k results
  -> cosine threshold gate
       no dense result passes -> insufficient evidence
       at least one passes    -> continue
  -> BM25: candidate_k lexical results
  -> union by chunk_id
  -> cross-encoder scores every query/chunk pair
  -> deterministic sort by rerank score, then chunk_id
  -> first top_k items
  -> whole-chunk context-budget filter
  -> E1..En evidence for generation
```

A subtle but important detail: BM25 cannot open the evidence gate on its own.
At least one dense candidate must pass the calibrated cosine threshold. This
keeps the insufficient-evidence decision on one measured score scale. BM25 then
improves candidate coverage and the reranker decides ordering.

### Why dense and BM25 are combined

Dense retrieval is strong for semantic paraphrase but can smooth away exact
names and acronyms. BM25 is strong for exact tokens but weaker for paraphrase.
The cross-encoder sees the complete query and chunk together, so it can reorder
their merged candidates more accurately than rank fusion alone.

An engineering check on ten manually verified figure/caption questions found:

| Strategy | Correct page in top 6 |
|---|---:|
| Dense-only baseline | 6/10 |
| BM25 only | 10/10 |
| Rank fusion without reranker | 7/10 |
| Dense candidates + reranker | 8/10 |
| Shipped hybrid candidates + reranker | 10/10 |

The set was small and proper-noun-heavy, so these are development results, not a
general quality claim. A larger reviewed evaluation set is still needed.

### Candidate K, Top-K, and context budget

Active values:

```dotenv
RETRIEVAL_CANDIDATE_K=10
RETRIEVAL_TOP_K=6
RETRIEVAL_MAX_CONTEXT_TOKENS=4000
```

- `candidate_k=10`: dense and BM25 can each contribute up to ten items before
  deduplication and reranking;
- `top_k=6`: at most six reranked items become evidence;
- context budget 4,000: approximate token ceiling for evidence; chunks are
  removed whole, not truncated.

Increasing these values can improve recall but increases reranking/generation
latency and can distract the answer model. They should be measured, not
increased automatically.

### Threshold

`RETRIEVAL_SCORE_THRESHOLD=0.65` is a minimum cosine similarity applied only to
dense candidates before BM25 and reranking. It is not a cross-encoder cutoff.

For the approved D2.1 corpus with `nomic-embed-text`, measured on-topic top scores
were approximately 0.72-0.88 and reviewed off-topic questions peaked near 0.61.
The value 0.65 sat between those groups. The threshold is a property of the
corpus, chunking, and embedding model; it is not universal.

When the corpus or embedding model changes, evaluate answered and unanswerable
questions again before selecting a new threshold.

### HNSW

`backend/app/providers/vectorstore_pgvector.py` creates:

```sql
CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
```

Dense search orders by pgvector cosine distance. The SQL is HNSW-compatible, and
PostgreSQL's planner decides when the index is cost-effective. On a tiny corpus,
a sequential scan may still be cheaper; as the corpus grows, HNSW avoids an
exhaustive exact comparison against every vector.

### BM25 lifecycle and scale

BM25 is a shared, disk-backed `pg_textsearch` 1.4.0 index on `chunk_text` inside
PostgreSQL 18. It uses `text_config='simple'`, `k1=1.5`, and `b=0.75` to remain
close to the reference BM25 used for the retrieval measurement. The extension
implements top-K index scans; unrelated zero-score rows are not admitted to the
candidate pool.

The database owns index consistency. A committed insert, update, or delete is
visible to every backend instance without loading all chunks into application
RAM, polling chunk counts, or restarting the backend. `ensure_index()` creates
the extension and BM25 index idempotently, so the normal `ingest` command also
performs schema migration for an existing collection without re-embedding
unchanged documents.

The pinned database image is built by `deployment/Dockerfile.database` and
preloads `pg_textsearch`, as required by the extension. PostgreSQL may choose a
sequential scan for a very small corpus, but BM25 corpus statistics still come
from the index; on the active corpus, the verified top-K plan uses the BM25
index. At larger scale, monitor query plans, index size, write/compaction cost,
and retrieval quality rather than replacing the application retrieval API.

---

## PostgreSQL search layer, registry, and data ownership

### What PostgreSQL stores

The collection table stores one row per searchable chunk:

- `chunk_id` primary key;
- `document_id`;
- `page_number`;
- `chunk_text`;
- serialized chunk metadata;
- fixed-dimension embedding vector.

It also has:

- a document ID index for replacement/removal;
- an HNSW vector index with `vector_cosine_ops`;
- a shared BM25 index on `chunk_text` using `pg_textsearch`.

A metadata table records collection compatibility: embedding provider/model,
dimensions, chunking settings, corpus/index identity, and fingerprint.

### What the registry stores

The registry under `INDEX_PATH` stores:

```text
documents.json
pages/<document_id>.json
figures/<document_id>.json
figures/<document_id>/*.png
```

It contains:

- approved filename and stable document ID;
- checksum, title, type, deliverable metadata;
- page/chunk/figure counts;
- index fingerprint and ingestion timestamp;
- cleaned page text and review flags;
- figure IDs, exact page, caption, dimensions, content hash, and safe relative
  stored path.

### Why both are needed

| Need | PostgreSQL search layer | Registry |
|---|---:|---:|
| semantic nearest-neighbor search | yes | no |
| chunk text and embedding | yes | no |
| shared BM25 index/search | yes | no |
| stable document inventory | partial | yes |
| full cited-page context | no | yes |
| original file resolution | no | yes |
| figure PNG resolution | no | yes |
| safe ID-to-path mapping | no | yes |
| corpus status and pending files | partial | yes |

After retrieval, PostgreSQL says which chunk is relevant. The registry lets the
application safely show the exact page, original file, and associated figure.

### Path safety

The source API accepts IDs, not arbitrary filesystem paths. Registry resolution
checks that a resolved source or figure path remains under the approved root.
This prevents path traversal such as requesting `../../secret`.

### The `data/` folders

| Folder | Purpose | Source or derived? | Backup priority |
|---|---|---|---|
| `data/corpus/` | approved input documents | source of truth | highest |
| `data/index/` | registry/pages/figures for non-Docker local execution | derived | rebuildable |
| Docker `ingestdata18` volume | registry/pages/figures used by Compose backend | derived | useful for fast recovery |
| `data/reports/` | ingestion audit reports | derived audit trail | retain latest/important reports |

The host `data/index/` is not the Docker runtime registry because Compose mounts
the named `ingestdata18` volume at `/app/data/index`. This distinction explains why
host and container chunk/registry snapshots can differ after separate runs.

---
