---
title: "Product scope and core concepts"
doc_type: explanation
layer: user
audience: "newcomer, stakeholder, or developer"
reader_goal: "understand what DemocraSeek is, what it guarantees, and what it does not claim"
reader_state: "needs the product and evidence-grounding mental model"
source_of_truth: false
status: stable
canonical_sources:
  - "README.md"
  - "backend/app/rag/orchestrator.py"
  - "config/onboarding.v2.yaml"
related_docs:
  - "docs/architecture/system-overview.md"
  - "docs/reference/concepts-and-glossary.md"
rag_index: true
---

# Product scope and core concepts

## Executive overview

### What the user experiences

1. A welcome page introduces DemocraSeek and INNOVADE without exposing technical detail.
2. `Start your conversation` continues to chat when a valid local profile exists;
   otherwise it opens the four-step onboarding.
3. The user selects the onboarding interface language: English (default), Greek,
   French, Spanish, or Dutch for Belgium (`nl-BE`).
4. The backend validates the selected role, intent, support need, and answer mode.
5. The user asks a question in a language supported by the configured LLM about
   the approved INNOVADE knowledge base.
6. The language layer detects that language and creates a canonical English
   question and English conversation context.
7. DemocraSeek retrieves candidate passages with semantic and lexical search.
8. A cross-encoder reranks the combined candidate pool.
9. The answer LLM receives only the selected evidence, recent English conversation
   context, and a deterministic response policy compiled from the profile.
10. The backend validates the model's English JSON answer and citations.
11. The validated answer is translated to the current question's language while
   citation markers are preserved deterministically.
12. The frontend shows the answer, compact citation controls, source excerpts,
   full page context, original files, and associated figures.
13. If retrieval, generation, validation, or translation fails, the request
   fails closed rather than displaying an unverifiable result. If evidence is
   absent, the user receives an
   insufficient-evidence response rather than an unsupported answer.

### Shipped provider profile

The versioned `.env.example` points answer and language work to FILOS
`datalab-2:latest`, embeddings to `nomic-embed-text:latest`, and vision work to
`datalab-vision-1:latest`. The vector collection is
`innovade_filos_nomic_v1`.

Corpus counts belong to the running deployment, not the repository. Check
`/api/ready`, `/api/corpus`, and the latest ingestion report instead of relying
on copied counts in documentation.

### The two main architectural promises

**Grounding and traceability.** Every citation displayed to the reader resolves
to an evidence item that was actually retrieved from the approved index.
Document, page, chunk, excerpt, file, and figure metadata come from trusted
ingestion records rather than from the LLM.

**Presentation-only personalisation.** The onboarding profile can change wording,
structure, depth, tone, and framing. It cannot change retrieval, source facts,
citation validity, or the decision to return insufficient evidence.

### What the project does not claim

DemocraSeek is not a general-purpose chatbot, an autonomous agent, a knowledge
graph, an OCR platform, or a public multi-tenant SaaS product. Its current
delivery boundary is a professional local demo and controlled single-host
deployment. Public production still requires authentication/authorization,
shared rate limiting, monitoring, backups, high availability, and a deployment
and legal review.

---

## Problem, scope, and requirement sources

### The problem

Long project deliverables contain useful evidence, but a reader must know where
to search, understand technical terminology, and manually verify any statement
they want to rely on. A normal chatbot reduces the effort but introduces a new
risk: it can answer from model memory, invent detail, or produce a convincing
citation that does not resolve to a real source.

DemocraSeek addresses both problems:

- it retrieves only from an operator-approved corpus;
- it adapts presentation for different audiences;
- it exposes the source behind each returned citation;
- it rejects structurally unverifiable answers;
- it reports insufficient evidence when the corpus cannot support an answer.

### Requirement and content boundaries

The project was shaped by three different kinds of source. They must not be
confused:

| Source | Role in the project | Automatically searchable? |
|---|---|---|
| DemocraSeek Onboarding v2 | Product and response-policy requirements | No |
| INNOVADE D5.1 and D5.2 | Social, empirical, and pedagogical design context | No, unless separately approved and placed in the corpus |
| Files in `data/corpus/` | Approved knowledge base used for answers | Yes, after ingestion |
| `config/onboarding.v2.yaml` | Executable onboarding wording and policy | Used for policy compilation, not factual retrieval |
| Application code | System behavior | No |

An instruction in a requirements PDF is not executed merely because the file
exists. A document becomes answer evidence only when an operator places it in
the approved corpus and runs ingestion.

### Product scope

Included:

- four-step, versioned onboarding;
- deterministic response-policy compilation;
- PDF and standalone-image ingestion;
- page-scoped text chunks;
- figure extraction and optional vision descriptions;
- semantic retrieval, BM25, and cross-encoder reranking;
- pgvector persistence with an HNSW index;
- strict JSON generation contract;
- deterministic citation validation;
- source and figure inspection in the frontend;
- incremental corpus management;
- Docker-based runtime and one-command Windows demo launchers.

Excluded from the current scope:

- user accounts and permissions;
- UI document upload;
- OCR of scanned pages or text inside images;
- live web search;
- model training or fine-tuning;
- claim-level entailment validation;
- analytics and behavioral tracking;
- distributed queues or microservices;
- Kubernetes or cloud-specific manifests;
- automated test suites, fixtures, and evaluation harnesses;
- public-production operational controls.

---

## Final mental model

DemocraSeek has one approved knowledge path and one presentation policy path.

```text
KNOWLEDGE PATH
approved file
  -> page-aware chunks and figure descriptions
  -> embeddings + pgvector + registry
  -> hybrid retrieval and reranking
  -> evidence IDs
  -> citation validation
  -> inspectable source

PRESENTATION PATH
four onboarding codes
  -> deterministic versioned policy
  -> generation instructions
  -> wording, structure, depth, and framing
```

They meet only at answer generation. The knowledge path decides what evidence is
available. The presentation path decides how that evidence should be explained.
The validator then decides whether the resulting citation structure is safe
enough to show.
