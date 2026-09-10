---
title: "Change models and providers"
doc_type: how-to
layer: user
audience: "developer or operator"
reader_goal: "change the answer, embedding, or vision provider safely"
reader_state: "understands configuration and can rebuild or re-index when required"
source_of_truth: false
status: stable
canonical_sources:
  - "backend/app/providers/factory.py"
  - ".env.example"
related_docs:
  - "docs/reference/models-and-providers.md"
  - "docs/reference/change-impact-matrix.md"
rag_index: true
---

# Change models and providers

For another OpenAI-compatible endpoint:

```dotenv
LLM_PROVIDER=openai_compatible
LLM_MODEL=<provider-model-name>
LLM_BASE_URL=<container-visible-base-url>
LLM_API_KEY=<credential>
```

Then rebuild/restart and review citation and personalisation quality. No
re-index is needed because the answer model is not used to create stored
vectors.

For a non-compatible API, implement `LLMProvider`, add an explicit factory branch
and configuration type, then document and validate the new adapter.

## Switching embeddings

Update provider, model, URL, key, and dimensions together, then re-index.
Existing vectors cannot be compared with vectors from another embedding model.

## Switching the VLM

Update `VISION_*`, ensure the model is present/reachable, then re-index. Existing
figure descriptions remain old until rebuilt.

---
