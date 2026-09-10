---
title: "Evidence, citations, and figures"
doc_type: reference
layer: architecture
audience: "developer or technical reviewer"
reader_goal: "verify citation validation and multimodal evidence behavior"
reader_state: "understands the answering pipeline"
source_of_truth: true
status: stable
canonical_sources:
  - "backend/app/rag/citations.py"
  - "backend/app/rag/evidence.py"
  - "backend/app/ingestion/figures.py"
related_docs:
  - "docs/architecture/answering-pipeline.md"
  - "docs/reference/api-contracts.md"
rag_index: true
---

# Evidence, citations, and figures

## Citations, supporting quotes, and validation

### Evidence IDs versus citation IDs

- `E1`, `E2`, ... identify evidence items inside one model request.
- `C1`, `C2`, ... are reader-facing citation markers in the answer.
- An `E` identifier must never appear in final prose.
- The LLM proposes the mapping from each citation to one retrieved evidence ID.
- The backend supplies all trusted source metadata.

### What a supporting quote is

The model is asked to copy a short, verbatim passage from the selected evidence
that supports the claim. It is not generated metadata and it is not accepted on
trust.

For text evidence, the validator:

1. collapses whitespace in the chunk and proposed quote;
2. requires at least 20 characters;
3. searches for the normalized quote as a literal substring;
4. if found, slices the displayed excerpt from the real chunk;
5. if not found, ignores the model quote and displays the chunk head.

The quote lookup uses literal substring search after normalization. Regular
expressions are used for citation/evidence marker syntax, not to determine
semantic support.

For figure evidence there is no verbatim sentence inside a chart. The displayed
excerpt is the caption plus VLM description and is explicitly labelled as a
derived figure description.

For external evidence the same quote check still runs server-side, but neither
the quote nor a fallback chunk excerpt is returned to the browser. The user sees
only reviewed bibliographic metadata and the external link.

### Deterministic structural checks

`backend/app/rag/citations.py` verifies:

1. a grounded answer lists at least one citation;
2. each citation ID has valid `C<number>` syntax;
3. citation IDs are unique;
4. every referenced evidence ID was actually retrieved;
5. raw `[E...]` markers are rewritten only when their mapping is unambiguous;
6. any remaining raw evidence marker rejects the answer;
7. every `[C...]` marker in prose has a citation object;
8. grounded prose contains at least one marker;
9. citation objects not used in prose are dropped;
10. duplicate citations to the same evidence collapse;
11. surviving citations are renumbered in order of first appearance;
12. text supporting quotes are verified or replaced with a safe chunk excerpt;
13. document, page, chunk, and URL fields come from the indexed chunk.

### Example

Model output:

```json
{
  "status": "grounded",
  "answer": "Low trust can reduce participation [C7].",
  "citations": [
    {
      "citation_id": "C7",
      "evidence_id": "E2",
      "supporting_quote": "Low trust can reduce participation."
    }
  ]
}
```

If `E2` was retrieved and the quote exists, the backend can return:

```json
{
  "answer": "Low trust can reduce participation [C1].",
  "citations": [
    {
      "citation_id": "C1",
      "evidence_id": "E2",
      "document_id": "...",
      "document_title": "...",
      "page_number": 123,
      "chunk_id": "...",
      "supporting_excerpt": "Low trust can reduce participation.",
      "excerpt_source": "model_quote_verified",
      "source_url": "/api/sources/...?page=123"
    }
  ]
}
```

The model never gets to decide that the page is 123.

### Retry behavior

On the first parsing or citation-structure failure, the orchestrator appends a
correction block and generates again. When the model had already judged the
evidence sufficient, the correction asks it to fix form rather than escape to
`insufficient_evidence`. A second failure discards the answer.

### What validation proves

It proves that a displayed citation points to a real passage or derived figure
description that was retrieved for this request, and that the source metadata
shown to the user is trusted.

### What validation does not prove

It does not prove that every natural-language claim is logically entailed by the
cited passage. A model could attach a real citation to an unsupported
interpretation.

Claim-level entailment/Natural Language Inference (NLI) would split the answer
into claims and ask a separate model whether each claim is supported,
contradicted, or unknown given its cited evidence. That is not implemented.
Adding it would improve semantic verification but add latency, another model,
threshold calibration, and its own false-positive/false-negative evaluation.

The accurate delivery statement is:

> DemocraSeek validates citation traceability and quote provenance. It does not
> currently guarantee claim-level semantic entailment.

---

## Figures and multimodal RAG

### Three separate capabilities

**Display a relevant image.** When a validated citation resolves to a page, the
registry attaches figures stored for that page. The answer LLM does not choose
file paths.

**Answer from visual content.** During ingestion, the VLM describes a kept
figure. The description becomes searchable evidence.

**Use a standalone image as a document.** An approved image file becomes a
one-page document with one figure and can follow the same retrieval/citation
path.

### Current state

The active `.env` enables:

```dotenv
VISION_PROVIDER=openai_compatible
VISION_MODEL=qwen2.5vl:7b
VISION_BASE_URL=http://host.docker.internal:11434/v1
VISION_API_KEY=ollama
```

After ingestion, the generated report records kept figures and retrievable
figure chunks. That report is the correct way to confirm that the VLM actually
ran; merely having the model installed is not enough.

### Runtime behavior

```text
INGESTION TIME
figure PNG + caption
  -> qwen2.5vl:7b description
  -> caption + description
  -> nomic-embed-text vector
  -> pgvector figure chunk

QUESTION TIME
question
  -> retrieve figure description like normal text
  -> llama3.1:8b answers from that text
  -> citation validator labels it figure_description
  -> registry attaches original PNG
  -> reader compares answer with image
```

The answer LLM does not receive image bytes at chat time.

### Honesty controls

- VLM text is labelled derived, never quoted as original document text.
- The prompt warns that descriptions may be incomplete.
- Exact numbers or trends may be stated only when the description contains them.
- Caption-only items cannot be presented as visually understood.
- The original figure is shown so the reader can inspect it.

### Limitations

- no OCR for text rendered inside an image;
- no extraction of arbitrary PDF vector graphics;
- caption-image association is order-based;
- repeated-content filtering can discard a legitimate repeated diagram;
- a VLM description can omit or misread visual detail;
- no claim-level entailment check over the description.

### Changing or disabling vision

Changing `VISION_PROVIDER` or `VISION_MODEL` changes which figure chunks exist
and what they contain. Pull the model, update configuration, then run:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli reindex --yes
```

Set `VISION_PROVIDER=none` when only deterministic image display is needed. A
re-index is still required.

---
