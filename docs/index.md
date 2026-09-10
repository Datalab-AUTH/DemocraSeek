---
title: "DemocraSeek documentation"
doc_type: reference
layer: user
audience: "users, developers, operators, and reviewers"
reader_goal: "find the right DemocraSeek documentation for the current task"
reader_state: "knows only the project name or has a local checkout"
source_of_truth: true
status: stable
canonical_sources:
  - "README.md"
related_docs:
  - "docs/getting-started/quickstart.md"
  - "docs/architecture/system-overview.md"
rag_index: true
---

# DemocraSeek documentation

Use this page to choose the shortest path to the information you need. The root [README](../README.md) remains the project homepage; detailed project knowledge lives here.

## Getting started

Guided paths for newcomers.

- [Quickstart](getting-started/quickstart.md) — configure, start, ingest, verify, and open a first local deployment.
- [Codebase tour](getting-started/codebase-tour.md) — locate the backend, frontend, deployment, configuration, and launcher entrypoints.

## Guides

Task-focused instructions for routine changes.

- [Daily development workflow](guides/daily-development.md)
- [Customize onboarding safely](guides/customize-onboarding.md)
- [Change models and providers](guides/change-models-and-providers.md)

## Explanation

Background and mental models.

- [Product scope and core concepts](explanation/product-scope-and-concepts.md)

## Architecture

Detailed system behavior and technical boundaries.

- [System overview](architecture/system-overview.md)
- [Ingestion pipeline](architecture/ingestion-pipeline.md)
- [Answering pipeline and prompt assembly](architecture/answering-pipeline.md)
- [Retrieval, PostgreSQL, and data ownership](architecture/retrieval-and-data.md)
- [Evidence, citations, and figures](architecture/evidence-citations-and-figures.md)
- [Frontend and user experience](architecture/frontend-and-api-flow.md)

## Reference

Exact facts for lookup.

- [Concepts and glossary](reference/concepts-and-glossary.md)
- [Onboarding profiles](reference/onboarding-profiles.md)
- [Models and provider boundaries](reference/models-and-providers.md)
- [Configuration](reference/configuration.md)
- [HTTP API contracts](reference/api-contracts.md)
- [Configuration change impact](reference/change-impact-matrix.md)
- [Troubleshooting](reference/troubleshooting.md)

## Operations

Maintainer and corpus-operator procedures.

- [Corpus management](operations/corpus-management.md)
- [Build and release verification](operations/build-and-release.md)

## Documentation boundaries

- Getting-started pages teach a safe first path.
- Guides solve one concrete task.
- Explanation pages provide product context and mental models.
- Architecture pages define system structure and runtime behavior.
- Reference pages provide exact lookup facts.
- Operations pages are maintainer runbooks.

There is no archive in the current documentation set because no historical document was identified that needs to remain available as inactive project truth.
