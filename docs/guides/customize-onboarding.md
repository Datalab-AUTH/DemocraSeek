---
title: "Customize onboarding safely"
doc_type: how-to
layer: user
audience: "developer or product maintainer"
reader_goal: "change onboarding copy or policy without changing retrieval truth"
reader_state: "can edit versioned configuration and verify the application"
source_of_truth: false
status: stable
canonical_sources:
  - "config/onboarding.v2.yaml"
  - "backend/app/onboarding/compiler.py"
related_docs:
  - "docs/reference/onboarding-profiles.md"
  - "docs/reference/configuration.md"
rag_index: true
---

# Customize onboarding safely

Do not silently edit an already-published policy version.

1. Copy `config/onboarding.v2.yaml` to a new versioned file, for example
   `config/onboarding.v3.yaml`.
2. Change `policy_version`.
3. Edit questions, labels, fragments, guardrails, precedence, or overrides.
4. Set `ONBOARDING_CONFIG_PATH=config/onboarding.v3.yaml`.
5. Rebuild/restart the backend and frontend deployment.
6. Have users review their profile again.

A stored profile carries the version under which it was created. A mismatched
profile is rejected with HTTP `409`; it is never silently reinterpreted. An
onboarding-only change does not require re-indexing because document vectors do
not change.

If only a translation is corrected without changing the meaning of a choice,
edit the corresponding entry under `translations`, rebuild/restart backend and
frontend, and do not re-index. If a prompt, label, code, or instruction changes
meaning, treat it as a policy change and follow the versioned procedure above.
