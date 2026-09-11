"""Persist chunks with pgvector HNSW and pg_textsearch BM25 indexes."""

from __future__ import annotations

import json
import logging

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.providers.base import (
    IndexIncompatibleError,
    ProviderError,
    incompatible_index_message,
    missing_index_message,
)
from app.schemas.chunks import Chunk, ChunkMetadata, IndexMetadata, RetrievedChunk

logger = logging.getLogger(__name__)

_METADATA_TABLE = "ds_index_metadata"


class PgVectorStore:
    def __init__(self, *, dsn: str, pool_min: int = 1, pool_max: int = 4) -> None:
        self._dsn = dsn
        try:
            self._pool = ConnectionPool(dsn, min_size=pool_min, max_size=pool_max, open=False)
            self._pool.open(wait=True, timeout=15.0)
        except Exception as exc:  # psycopg raises a wide range here
            raise ProviderError(
                f"Cannot connect to the vector store: {type(exc).__name__}"
            ) from exc

    @property
    def provider_name(self) -> str:
        return "pgvector"

    # Schema
    def ensure_index(self, metadata: IndexMetadata) -> IndexMetadata:
        table = _table_name(metadata.collection)
        try:
            with self._pool.connection() as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.execute("CREATE EXTENSION IF NOT EXISTS pg_textsearch")
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_METADATA_TABLE} (
                        collection            text PRIMARY KEY,
                        embedding_provider    text NOT NULL,
                        embedding_model       text NOT NULL,
                        embedding_dimensions  integer NOT NULL,
                        chunk_size            integer NOT NULL,
                        chunk_overlap         integer NOT NULL,
                        corpus_version        text NOT NULL,
                        index_version         text NOT NULL,
                        updated_at            timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                existing = self._read_metadata(conn, metadata.collection)
                if (
                    existing is not None
                    and existing.compatibility_key() != metadata.compatibility_key()
                ):
                    raise IndexIncompatibleError(incompatible_index_message(existing, metadata))

                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        chunk_id     text PRIMARY KEY,
                        document_id  text NOT NULL,
                        page_number  integer NOT NULL,
                        chunk_text   text NOT NULL,
                        metadata     jsonb NOT NULL,
                        embedding    vector({metadata.embedding_dimensions}) NOT NULL
                    )
                    """
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {table}_doc_idx ON {table} (document_id)"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {table}_vec_idx ON {table} "
                    f"USING hnsw (embedding vector_cosine_ops)"
                )
                # Use the measured BM25 settings with simple tokenisation.
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {table}_text_idx ON {table} "
                    f"USING bm25 (chunk_text) "
                    f"WITH (text_config='simple', k1=1.5, b=0.75)"
                )

                conn.execute(
                    f"""
                    INSERT INTO {_METADATA_TABLE} (
                        collection, embedding_provider, embedding_model, embedding_dimensions,
                        chunk_size, chunk_overlap, corpus_version, index_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (collection) DO UPDATE SET
                        corpus_version = EXCLUDED.corpus_version,
                        updated_at = now()
                    """,
                    (
                        metadata.collection,
                        metadata.embedding_provider,
                        metadata.embedding_model,
                        metadata.embedding_dimensions,
                        metadata.chunk_size,
                        metadata.chunk_overlap,
                        metadata.corpus_version,
                        metadata.index_version,
                    ),
                )
        except psycopg.Error as exc:
            raise ProviderError(
                "Cannot create the PostgreSQL vector/BM25 indexes. Use the shipped "
                "database image, which installs and preloads pg_textsearch."
            ) from exc
        return metadata

    def get_index_metadata(self, collection: str) -> IndexMetadata | None:
        with self._pool.connection() as conn:
            try:
                return self._read_metadata(conn, collection)
            except psycopg.errors.UndefinedTable:
                return None

    def rebuild_index(self, metadata: IndexMetadata) -> None:
        table = _table_name(metadata.collection)
        with self._pool.connection() as conn:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.execute(
                f"DELETE FROM {_METADATA_TABLE} WHERE collection = %s", (metadata.collection,)
            )
        self.ensure_index(metadata)

    # Data
    def upsert_chunks(
        self, collection: str, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length.")
        if not chunks:
            return 0
        table = _table_name(collection)
        rows = [
            (
                chunk.chunk_id,
                chunk.metadata.document_id,
                chunk.metadata.page_number,
                chunk.chunk_text,
                json.dumps(chunk.metadata.model_dump()),
                _to_pgvector(embedding),
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {table}
                    (chunk_id, document_id, page_number, chunk_text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    page_number = EXCLUDED.page_number,
                    chunk_text  = EXCLUDED.chunk_text,
                    metadata    = EXCLUDED.metadata,
                    embedding   = EXCLUDED.embedding
                """,
                rows,
            )
        return len(rows)

    def delete_document(self, collection: str, document_id: str) -> int:
        table = _table_name(collection)
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE document_id = %s", (document_id,))
            return cur.rowcount

    def search(
        self, collection: str, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        table = _table_name(collection)
        vector = _to_pgvector(query_embedding)
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            try:
                cur.execute(
                    f"""
                    WITH nearest AS MATERIALIZED (
                        SELECT chunk_id, chunk_text, metadata,
                               embedding <=> %s::vector AS distance
                        FROM {table}
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    )
                    SELECT chunk_id, chunk_text, metadata, 1 - distance AS score
                    FROM nearest
                    ORDER BY distance, chunk_id
                    LIMIT %s
                    """,
                    (vector, vector, top_k, top_k),
                )
            except psycopg.errors.UndefinedTable as exc:
                # The dense search opens the evidence gate: a missing table is an
                # operator error and must surface as one, never as "no evidence".
                raise IndexIncompatibleError(missing_index_message(collection)) from exc
            records = cur.fetchall()
        return [
            RetrievedChunk(
                chunk=Chunk(
                    chunk_id=row["chunk_id"],
                    chunk_text=row["chunk_text"],
                    metadata=ChunkMetadata.model_validate(row["metadata"]),
                ),
                score=float(row["score"]),
            )
            for row in records
        ]

    def lexical_search(
        self, collection: str, query: str, top_k: int
    ) -> list[RetrievedChunk]:
        """Return top BM25 hits with cosine ``score=0.0``."""
        table = _table_name(collection)
        index = f"{table}_text_idx"
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            try:
                cur.execute(
                    f"""
                    WITH ranked AS MATERIALIZED (
                        SELECT chunk_id, chunk_text, metadata,
                               chunk_text <@> to_bm25query(%s, %s) AS bm25_distance
                        FROM {table}
                        ORDER BY bm25_distance
                        LIMIT %s
                    )
                    SELECT chunk_id, chunk_text, metadata
                    FROM ranked
                    WHERE bm25_distance < 0
                    ORDER BY bm25_distance, chunk_id
                    """,
                    (query, index, top_k),
                )
            except psycopg.errors.UndefinedTable:
                return []
            rows = cur.fetchall()
        return [
            RetrievedChunk(
                chunk=Chunk(
                    chunk_id=row["chunk_id"],
                    chunk_text=row["chunk_text"],
                    metadata=ChunkMetadata.model_validate(row["metadata"]),
                ),
                score=0.0,
            )
            for row in rows
        ]

    def count(self, collection: str) -> int:
        table = _table_name(collection)
        with self._pool.connection() as conn, conn.cursor() as cur:
            try:
                cur.execute(f"SELECT count(*) FROM {table}")
            except psycopg.errors.UndefinedTable:
                return 0
            result = cur.fetchone()
            return int(result[0]) if result else 0

    def health_check(self) -> None:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:
            raise ProviderError(f"Vector store unreachable: {type(exc).__name__}") from exc

    def close(self) -> None:
        self._pool.close()

    # Helpers
    @staticmethod
    def _read_metadata(conn: psycopg.Connection, collection: str) -> IndexMetadata | None:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"SELECT collection, embedding_provider, embedding_model, embedding_dimensions, "
                f"chunk_size, chunk_overlap, corpus_version, index_version "
                f"FROM {_METADATA_TABLE} WHERE collection = %s",
                (collection,),
            )
            row = cur.fetchone()
        return IndexMetadata.model_validate(row) if row else None


def _table_name(collection: str) -> str:
    """Build a safe identifier. Collection names are validated in app.config."""
    if not collection or not all(c.isalnum() or c == "_" for c in collection):
        raise ValueError(f"Unsafe collection name: {collection!r}")
    return f"ds_chunks_{collection.lower()}"


def _to_pgvector(vector: list[float]) -> str:
    return "[" + ",".join(repr(float(value)) for value in vector) + "]"


