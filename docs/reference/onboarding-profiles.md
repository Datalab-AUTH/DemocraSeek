---
title: "Onboarding profiles"
doc_type: reference
layer: user
audience: "developer or product maintainer"
reader_goal: "look up onboarding choices, combinations, policy precedence, and boundaries"
reader_state: "already understands DemocraSeek onboarding"
source_of_truth: true
status: stable
canonical_sources:
  - "config/onboarding.v2.yaml"
  - "backend/app/onboarding/compiler.py"
  - "backend/app/schemas/onboarding.py"
related_docs:
  - "docs/guides/customize-onboarding.md"
  - "docs/explanation/product-scope-and-concepts.md"
rag_index: true
---

# Onboarding profiles

## Why onboarding exists

Different users can need the same evidence presented differently. A citizen may
need plain language, a policymaker may need implementation implications, and a
researcher may need concepts and caveats. DemocraSeek captures that need without
allowing it to bias retrieval.

The frontend does not duplicate onboarding wording. It fetches the questions and
choices from `GET /api/onboarding/config`. The backend loads the same versioned
configuration for validation and policy compilation.

## The single source of truth

`config/onboarding.v2.yaml` contains the policy-owned onboarding content:

- `policy_version`;
- the default locale and five selectable locale labels;
- all onboarding form copy and complete non-English translations;
- the precedence explanation;
- five global guardrails;
- four ordered questions;
- stable codes and labels;
- help text and descriptions;
- instructions for each choice;
- optional combination overrides.

The supported interface/onboarding locales are `en`, `el`, `fr`, `es`, and `nl-BE`.
`nl-BE` is shown as **Nederlands (België)**: Belgium has three official
languages but no language called "Belgian"; French is already offered separately.
The configuration loader verifies that every non-default locale contains every
question ID and every choice code. An incomplete translation fails startup
instead of producing a partially translated form.

The language selector is permanently available beside the theme selector on the
welcome page, during onboarding, and in chat. Its value is stored locally and
changes the application interface: navigation, onboarding, composer, status
messages, citation controls, profile controls, and the source drawer. General UI
translations live in `frontend/src/i18n.tsx`; the onboarding questions and
choices remain backend-owned in this YAML file so the frontend never duplicates
policy wording.

Interface locale changes presentation only. A translated onboarding label still
submits the same stable `R`/`I`/`S`/`M` code and therefore compiles to the same
English policy fragment. It is also independent of chat language: the backend
detects the language of every current question, retrieves and generates through
the canonical English pipeline, and returns the answer in that question's
language. For example, a Greek interface can show a French answer to a French
question. User messages, generated answers, document titles, quotations, and
source passages are not rewritten merely because the interface locale changes;
this preserves the conversation and the original evidence.

There are 24 reusable policy fragments:

- 7 roles;
- 6 intents;
- 6 support needs;
- 5 presentation modes.

Their Cartesian product covers:

```text
7 roles x 6 intents x 6 support needs x 5 modes = 1,260 profiles
```

There is no 1,260-row prompt table and no manually written prompt per
combination.

The new guardrails allow a separate `Further reading` section only when the
application explicitly supplies a consortium-reviewed external resource list.
No such list is configured in the current deployment, so the live system
remains knowledge-base-only and returns insufficient evidence rather than
inventing or searching for external links.

## All profile choices

### Role

| Code | Label | Main effect |
|---|---|---|
| `R1` | Citizen / resident | Plain language, everyday and community implications |
| `R2` | Public official / policymaker | Governance, implementation, feasibility, transparency |
| `R3` | Researcher / student | Conceptual precision, distinctions, caveats, visible provenance |
| `R4` | Digital democracy project manager / technology developer | Solution design, feasibility, accessibility, interoperability, data governance, deployment |
| `R5` | Civil society / community organisation | Inclusion, outreach, support, local engagement |
| `R6` | Business / professional | Concise strategic framing, stakeholders, applicability, institutional context |
| `R7` | Other / not sure | Balanced, citizen-friendly default |

### Intent

| Code | Label | Main effect |
|---|---|---|
| `I1` | Understand a concept or topic | Definition, adjacent concepts, why it matters |
| `I2` | Find evidence, examples, or sources | Evidence and provenance first |
| `I3` | Plan a decision, policy, action, or engagement activity | Options, implications, trade-offs, enabling conditions, engagement considerations |
| `I4` | Learn how to participate or use a digital service | Procedural, stepwise, practical guidance |
| `I5` | Explore risks, participation challenges, or inclusion issues | Structural, institutional, cultural, and user-profile dimensions |
| `I6` | Browse / discover relevant knowledge | Curated thematic overview and grounded follow-ups |

### Support need

| Code | Label | Main effect |
|---|---|---|
| `S1` | Understanding unfamiliar terms or concepts | Accessible language, inline definitions, progressive explanation |
| `S2` | Navigating digital tools or online participation processes | Practical support, explicit actions and requirements, no assumed digital experience |
| `S3` | Assessing whether information and sources are reliable | Visible provenance, evidence versus interpretation, uncertainty and limitations |
| `S4` | Connecting the topic to my local or community context | Community/local framing and place-based evidence where available |
| `S5` | Understanding institutional roles, procedures, or responsibilities | Actors, responsibilities, procedural relationships, decision points and next steps |
| `S6` | No specific support needed | No additional support overlay beyond global clarity and accessibility |

### Presentation mode

| Code | Label | Main effect |
|---|---|---|
| `M1` | Simple summary | Short overview and three to five evidence-supported key points |
| `M2` | Step-by-step guidance | Numbered, action-oriented, evidence-supported steps or stages |
| `M3` | Detailed explanation | Structured synthesis of context, implications and caveats |
| `M4` | Evidence with citations | Evidence-first with prominent citations and provenance |
| `M5` | Examples from real life / practice | Scenario-led, source-supported practical examples |

## What "compile the policy" means

Compilation is deterministic string composition, not model inference.

Given the four codes and `policy_version`, `backend/app/onboarding/compiler.py`:

1. verifies that the profile version matches the loaded configuration;
2. resolves each code to one choice in the YAML;
3. collects its instruction lines;
4. applies any explicit combination overrides in stable ID order;
5. emits the global guardrails;
6. emits conflict precedence;
7. emits Support, Intent, Role, and Mode sections in priority order;
8. returns the individual fragments and one inspectable instruction block.

Formula:

```text
Compiled response policy
  = global guardrails
  + support fragment
  + intent fragment
  + role fragment
  + mode fragment
  + matching explicit overrides
```

The same version and codes always produce byte-identical output. Compilation
does not call an LLM, retrieve documents, read conversation history, or use
randomness.

## Precedence

Absolute grounding and safety rules always win. If presentation preferences
conflict, the priority is:

```text
Support > Intent > Role > Mode
```

For example, `S3` requires visible provenance, evidence/interpretation
distinctions and limitations even if `M1` asks for a compact summary. The mode
may shorten the answer, but it cannot override the support need or grounding.

## What the profile can and cannot change

| Can change | Cannot change |
|---|---|
| vocabulary | retrieved candidate pool |
| sentence length | source facts |
| structure | page numbers |
| tone | citation validity |
| amount of explanation | threshold decision |
| framing | insufficient-evidence decision |
| prominence of provenance | document approval status |

The separation is structural: `Retriever.retrieve(question, history)` has no
profile parameter.

The policy is still an instruction to an 8B model, so style adherence is
best-effort. The project validates citation structure, not whether every answer
perfectly follows the requested presentation mode.
