---
title: "Models and provider boundaries"
doc_type: reference
layer: user
audience: "developer or operator"
reader_goal: "look up active models, providers, interfaces, and their roles"
reader_state: "understands the runtime architecture"
source_of_truth: true
status: stable
canonical_sources:
  - ".env.example"
  - "backend/app/providers/factory.py"
  - "backend/app/providers/base.py"
related_docs:
  - "docs/guides/change-models-and-providers.md"
  - "docs/reference/configuration.md"
rag_index: true
---

# Models and provider boundaries

## Active local stack

| Function | Provider | Model | Why |
|---|---|---|---|
| Answer generation | Ollama via OpenAI-compatible adapter | `llama3.1:8b` | Best citation-format discipline among locally tested small instruction models |
| Language detection and translation | same local LLM provider | `llama3.1:8b` | Keeps queries, history, and generation canonical in English while returning answers in the user's language |
| Embeddings | Ollama via OpenAI-compatible adapter | `nomic-embed-text` | Local, multilingual-capable semantic embeddings; measured with current corpus; 768d |
| Reranking | local `sentence-transformers` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Improves ordering of dense+BM25 candidate union |
| Figure understanding | Ollama via OpenAI-compatible adapter | `qwen2.5vl:7b` | Creates searchable descriptions of charts/diagrams during ingestion |
| Search storage | PostgreSQL | pgvector 0.8.6 + pg_textsearch 1.4.0 | Persistent chunks/metadata, HNSW cosine search, shared BM25 search |

All answer, translation, embedding, and vision endpoints are currently local
Ollama. There is no remote fallback. Language routing deliberately inherits the
answer LLM configuration, so enabling multilingual answers adds no duplicate
environment variables and changing `LLM_PROVIDER`, endpoint, or model changes
both answer generation and translation after a restart. It never changes the
index fingerprint and does not require re-ingestion.

## Why `llama3.1:8b`

The deciding requirement was not only fluency; it was strict JSON and citation
marker discipline. In same-question local testing, `qwen2.5:7b` and
`qwen2.5:3b` repeatedly dropped or invented markers and their answers were
rejected. `llama3.1:8b` produced valid cited output more reliably.

Reasoning models that emit `<think>` blocks are unsuitable for the current strict
single-JSON contract unless an adapter removes and validates that envelope.

## Why `nomic-embed-text`

It is a dedicated embedding model, not the answer LLM. It runs locally through
the same Ollama API, returns 768-dimensional vectors, and was used to calibrate
the current threshold. Keeping the embedding model independent means the answer
model can change without rebuilding the index.

A direct Hugging Face embedding provider is not implemented. The type
`EmbeddingProviderName = Literal["openai_compatible"]` means the configuration
accepts exactly one adapter: the real embeddings API client. Any other value
is rejected by configuration validation.

## Reranker

The cross-encoder is downloaded and run inside the backend container. It is not
served by Ollama. It operates only at question time and changes no stored vector,
so changing its model requires restart and re-evaluation, not re-indexing.

The shipped MS MARCO model is primarily English. A multilingual corpus should
evaluate a multilingual cross-encoder.

## VLM

`qwen2.5vl:7b` runs only during ingestion. It does not receive every chat
question. Its descriptions are embedded as figure chunks so the normal answer
LLM can later reason over text. This keeps online answering simpler and avoids a
vision call per question.

## Provider interfaces

Six replaceable boundaries live in `backend/app/providers/base.py`:

- `LLMProvider`;
- `LanguageProvider`;
- `EmbeddingProvider`;
- `VisionProvider`;
- `RerankProvider`;
- `VectorStore`.

OpenAI-compatible adapters can point to Ollama or another compatible endpoint.
A genuinely different protocol requires a new adapter, one explicit factory
branch, and configuration validation.

## Relationship to RAG-Anything

The code does not import or depend on the `raganything` package.

The multimodal pattern is conceptually similar: describe an image with a vision
model, embed the description, and retrieve it as text. DemocraSeek implements
that narrow pattern directly and does not adopt RAG-Anything's broader parsing,
knowledge-graph/LightRAG, or multi-modal orchestration stack.

RAG-Anything can provide richer heterogeneous-document parsing, modality
relationships, OCR integrations, and graph-assisted retrieval. It would also add
dependencies, operational complexity, migration work, and a different evidence
model. It is not automatically faster or more accurate for this corpus. Adopt
it only after a benchmark shows that the current PDF/figure pipeline is the
actual bottleneck.
