---
title: "Concepts and glossary"
doc_type: reference
layer: user
audience: "newcomer, developer, or reviewer"
reader_goal: "look up DemocraSeek terminology"
reader_state: "has read the project overview"
source_of_truth: true
status: stable
canonical_sources:
  - "backend/app/schemas"
  - "backend/app/rag"
  - "backend/app/ingestion"
related_docs:
  - "docs/explanation/product-scope-and-concepts.md"
  - "docs/architecture/system-overview.md"
rag_index: true
---

# Concepts and glossary

| Term | Meaning in DemocraSeek |
|---|---|
| Corpus | The approved files under `data/corpus/` |
| Page | A source page with a stable 1-based page number |
| Chunk | A page-scoped text or figure-description unit used for retrieval |
| Embedding | A numeric vector representing the semantic content of a query or chunk |
| Dense retrieval | Nearest-neighbor search between the query vector and stored chunk vectors |
| BM25 | Shared PostgreSQL lexical retrieval (`pg_textsearch`) that rewards exact term overlap, useful for names and acronyms |
| Cross-encoder reranker | A model that scores each query-candidate pair and reorders the candidate pool |
| Evidence ID | Temporary request-local identifier such as `E1`; only the LLM contract uses it |
| Citation ID | Reader-facing marker such as `C1` displayed as `[C1]` |
| Supporting quote | Text the LLM claims to have copied from an evidence item; verified before display |
| Registry | Trusted JSON records that map stable IDs to documents, pages, and figure files |
| LLM | The answer-generation model, shipped as FILOS `datalab-2:latest` |
| VLM | The ingestion-time vision-language model, shipped as FILOS `datalab-vision-1:latest` |
| RAG | Retrieve evidence first, then generate an answer from that evidence |
| Index fingerprint | Identity of all settings/code versions that determine stored chunks and vectors |
| Re-index | Delete and rebuild derived index state from the approved corpus |

A useful mental model is:

```text
Approved documents
        |
        v
Searchable, page-aware evidence
        |
        v
Retrieve evidence for one question
        |
        v
Generate under profile and grounding rules
        |
        v
Validate citations and resolve trusted sources
        |
        v
Answer the reader can inspect
```
