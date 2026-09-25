---
title: "Corpus management"
doc_type: how-to
layer: operations
audience: "corpus operator or maintainer"
reader_goal: "inspect, ingest, update, remove, rebuild, and back up corpus state"
reader_state: "understands the approved-corpus boundary"
source_of_truth: true
status: stable
canonical_sources:
  - "ingest.cmd"
  - "backend/app/cli.py"
  - "data/corpus/corpus.metadata.yaml"
related_docs:
  - "docs/architecture/ingestion-pipeline.md"
  - "docs/reference/troubleshooting.md"
rag_index: true
---

# Corpus management

All commands below run from the repository root through the backend image.
`ingest.cmd` wraps the common ones with the same provider and Docker checks the
demo launcher performs: `.\ingest.cmd`, `-Only "<file>"`, `-Force`, `-Status`,
and `-Reindex -Yes`. Local Ollama is checked only when a configured endpoint
points to it. Removing a single document has no launcher flag and uses the
explicit command below.

## Status

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli status
```

## Incremental ingestion

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli ingest
```

## One exact file

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli ingest --only "Approved document.pdf"
```

## Force reprocessing

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli ingest --force
```

## Remove one indexed document

Find its stable ID with `status`, then:

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli remove <document_id>
```

## Full rebuild

```powershell
docker compose -f deployment\docker-compose.yml --env-file .env run --rm backend python -m app.cli reindex --yes
```

This is destructive only to derived index state. The approved corpus remains the
source of truth.

## Add, update, and delete behavior

- **Add:** copy approved file, run `ingest`.
- **Update:** replace file while retaining its filename if stable identity should
  remain, run `ingest`.
- **Delete:** delete source and run a full corpus `ingest`, or explicitly
  `remove <document_id>`.
- **Configuration affecting vectors/chunks:** run `reindex --yes`, not ordinary
  incremental ingestion.

## Backups

At minimum back up:

- approved `data/corpus/`;
- deployment `.env` in a secure location;
- PostgreSQL/pgvector/pg_textsearch if re-indexing time matters;
- Docker `ingestdata18` if extracted page/figure artifacts must be restored fast;
- important ingestion reports.

Everything except source documents and configuration is derivable, but a VLM
re-index can be slow.
