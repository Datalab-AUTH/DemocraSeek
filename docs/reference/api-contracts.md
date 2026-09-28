---
title: "HTTP API contracts"
doc_type: reference
layer: user
audience: "API consumer or developer"
reader_goal: "look up endpoints, payloads, response states, and errors"
reader_state: "knows HTTP and JSON"
source_of_truth: true
status: stable
canonical_sources:
  - "backend/app/api"
  - "backend/app/schemas"
related_docs:
  - "docs/architecture/frontend-and-api-flow.md"
  - "docs/reference/troubleshooting.md"
rag_index: true
---

# HTTP API contracts

Interactive OpenAPI documentation is available at
`http://localhost:8000/docs`.

| Method and endpoint | Purpose |
|---|---|
| `GET /api/health` | Process liveness; does not require provider/database readiness |
| `GET /api/ready` | Database, index compatibility, registry, corpus, and pending-file readiness |
| `GET /api/corpus` | Indexed documents, counts, pending files, curated starter questions per locale |
| `GET /api/onboarding/config` | Versioned questions, translations, locale metadata, labels, codes |
| `POST /api/onboarding/compile` | Validate a profile and inspect compiled policy |
| `POST /api/chat` | Grounded or insufficient-evidence response |
| `GET /api/sources/{document_id}?page=N` | Trusted document metadata and page preview |
| `GET /api/sources/{document_id}/figures/{figure_id}` | Stored figure PNG |
| `GET /api/sources/{document_id}/file` | Original approved file |

## Chat request shape

Conceptually:

```json
{
  "question": "What is digital democracy?",
  "profile": {
    "policy_version": "2.0",
    "role_code": "R1",
    "intent_code": "I1",
    "support_code": "S1",
    "mode_code": "M1"
  },
  "history": [
    {
      "role": "user",
      "content": "Πες μου για τη συμμετοχή.",
      "canonical_content": "Tell me about participation.",
      "language_code": "el",
      "language_name": "Greek"
    },
    {
      "role": "assistant",
      "content": "...",
      "canonical_content": "...",
      "language_code": "el",
      "language_name": "Greek"
    }
  ]
}
```

The canonical and language fields are optional for third-party clients. The
official frontend uses the values returned by the preceding response; when
canonical text is absent, the backend translates that history message before
using it. Previous language metadata is consulted only for a genuinely
ambiguous follow-up.

## Chat response states

`grounded` includes answer text and citations. `insufficient_evidence` contains
a safe user-facing answer, no citations, and an internal-safe reason code. Both
states also include:

- `language_code` and `language_name`: detected language of the current question;
- `canonical_question`: English question actually used by retrieval;
- `canonical_answer`: validated English answer before final translation.

The canonical fields are conversation state, not hidden reasoning or model
chain-of-thought.

## Error contract

The API returns a stable safe error body and request ID. Important classes:

| HTTP | Example code | Meaning |
|---:|---|---|
| 400 | `invalid_question`, `unknown_code` | invalid user/profile input |
| 404 | `document_not_found` | unknown source ID |
| 409 | `policy_version_mismatch` | stored profile uses another policy |
| 422 | `validation_error` | malformed request |
| 429 | `rate_limited` | request window exceeded |
| 503 | `index_incompatible`, `provider_unavailable` | runtime dependency/index unavailable |
| 500 | `internal_error` | unexpected error; internal detail remains in logs |

---
