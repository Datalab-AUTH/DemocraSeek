"""Operator CLI: corpus management and configuration checks.

Ingestion is an operator action against a directory of approved files. There is
no upload endpoint and no admin UI, so an end user cannot introduce a document
into the official corpus.

Documents enter the index through exactly one command, `ingest`.

    python -m app.cli check-config
    python -m app.cli ingest [--force] [--only FILE.pdf]
    python -m app.cli remove DOCUMENT_ID
    python -m app.cli reindex
    python -m app.cli status
"""

from __future__ import annotations

import json
import sys

import typer

from app.config import ConfigurationError, get_settings
from app.corpus.registry import CorpusRegistry
from app.ingestion.pipeline import IngestionService
from app.logging_setup import configure_logging
from app.providers.base import IndexIncompatibleError
from app.providers.factory import build_embeddings, build_reranker, build_vector_store, build_vision

cli = typer.Typer(add_completion=False, help="DemocraSeek corpus and operations CLI.")


def _service() -> IngestionService:
    settings = get_settings()
    configure_logging(settings.log_level)
    return IngestionService(
        settings=settings,
        embeddings=build_embeddings(settings),
        vector_store=build_vector_store(settings),
        vision=build_vision(settings),
    )


@cli.command("check-config")
def check_config() -> None:
    """Validate settings and provider configuration without touching data."""
    try:
        settings = get_settings()
    except ConfigurationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(json.dumps(settings.safe_provider_summary(), indent=2))
    problems: list[str] = []
    if not settings.corpus_path.is_dir():
        problems.append(f"CORPUS_PATH does not exist: {settings.corpus_path}")
    if not settings.onboarding_config_path.is_file():
        problems.append(f"ONBOARDING_CONFIG_PATH does not exist: {settings.onboarding_config_path}")

    try:
        build_embeddings(settings)
        build_vision(settings)
        build_reranker(settings)
        build_vector_store(settings).health_check()
    except Exception as exc:
        problems.append(f"{type(exc).__name__}: {exc}")

    if problems:
        for problem in problems:
            typer.secho(f"  - {problem}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("Configuration OK.", fg=typer.colors.GREEN)


@cli.command("ingest")
def ingest(
    force: bool = typer.Option(False, "--force", help="Re-process even unchanged documents."),
    only: str | None = typer.Option(None, "--only", help="Ingest a single filename."),
    quiet: bool = typer.Option(False, "--quiet", help="Print JSON only."),
) -> None:
    """Ingest every approved file from CORPUS_PATH.

    Adding a file to the corpus directory never indexes it on its own.
    """
    settings = get_settings()
    service = _service()

    try:
        report = service.ingest(force=force, only=only)
    except IndexIncompatibleError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    json_path, text_path = report.write(settings.report_path)
    if quiet:
        typer.echo(json.dumps(report.model_dump(), indent=2))
    else:
        typer.echo(report.render_text())
        typer.echo(f"Reports written to:\n  {json_path}\n  {text_path}")
    if report.files_failed:
        raise typer.Exit(code=1)


@cli.command("remove")
def remove(document_id: str) -> None:
    """Remove one document from the index and the registry."""
    service = _service()
    try:
        record = service.remove_document(document_id)
    except KeyError as exc:
        typer.secho(f"Unknown document id: {document_id}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Removed {record.filename} ({record.chunk_count} chunks).", fg=typer.colors.GREEN)
    typer.echo(
        "The PDF itself was not deleted. Delete it from CORPUS_PATH as well, "
        "otherwise the next `ingest` will restore it."
    )


@cli.command("reindex")
def reindex(
    yes: bool = typer.Option(False, "--yes", help="Do not ask for confirmation."),
) -> None:
    """Drop the named index and rebuild it from the approved files.

    Required after changing the embedding provider, model, dimensions, chunk
    size, chunk overlap, vision provider or INDEX_VERSION.
    """
    settings = get_settings()
    if not yes:
        typer.confirm(
            f"This drops collection {settings.vector_store_collection!r} and rebuilds it "
            f"from {settings.corpus_path}. Continue?",
            abort=True,
        )
    report = _service().reindex()
    json_path, text_path = report.write(settings.report_path)
    typer.echo(report.render_text())
    typer.echo(f"Reports written to:\n  {json_path}\n  {text_path}")


@cli.command("status")
def status() -> None:
    """Show what is currently indexed."""
    settings = get_settings()
    store = build_vector_store(settings)
    registry = CorpusRegistry(settings.index_path, settings.corpus_path)
    documents = registry.load()
    metadata = store.get_index_metadata(settings.vector_store_collection)

    typer.echo(
        json.dumps(
            {
                "collection": settings.vector_store_collection,
                "index_metadata": metadata.model_dump() if metadata else None,
                "current_index_fingerprint": settings.index_fingerprint,
                "chunks_in_store": store.count(settings.vector_store_collection),
                "documents": [
                    {
                        "document_id": record.document_id,
                        "filename": record.filename,
                        "pages": record.page_count,
                        "chunks": record.chunk_count,
                        "checksum": record.document_checksum[:12],
                        "fingerprint_matches_config": (
                            record.index_fingerprint == settings.index_fingerprint
                        ),
                    }
                    for record in sorted(documents.values(), key=lambda r: r.document_id)
                ],
            },
            indent=2,
        )
    )


def main() -> None:
    try:
        cli()
    except ConfigurationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
