"""Run mandatory dense-plus-BM25 retrieval and cross-encoder reranking.

Cosine similarity gates evidence; reranker scores only determine ordering.
"""

from __future__ import annotations

import logging
import time

from app.providers.base import EmbeddingProvider, RerankProvider, VectorStore
from app.rag.evidence import EvidenceItem, build_evidence
from app.rag.query import build_retrieval_query
from app.schemas.chat import ConversationMessage
from app.schemas.chunks import RetrievedChunk

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
        collection: str,
        top_k: int,
        score_threshold: float,
        max_context_tokens: int,
        reranker: RerankProvider,
        candidate_k: int,
    ) -> None:
        self._embeddings = embeddings
        self._store = vector_store
        self._collection = collection
        self._top_k = top_k
        self._score_threshold = score_threshold
        self._max_context_tokens = max_context_tokens
        self._reranker = reranker
        # Candidate count contributed by each retriever.
        self._candidate_k = candidate_k

    def retrieve(
        self, question: str, history: list[ConversationMessage] | None = None
    ) -> list[EvidenceItem]:
        """Question (plus limited context) -> ranked, budgeted evidence items."""
        query = build_retrieval_query(question, history)
        embed_started = time.perf_counter()
        query_vector = self._embeddings.embed_query(query)
        timings = {"embedding_ms": _elapsed_ms(embed_started)}
        dense_started = time.perf_counter()
        dense = self._store.search(self._collection, query_vector, self._candidate_k)
        timings["dense_search_ms"] = _elapsed_ms(dense_started)
        relevant = self.apply_threshold(dense)

        # Only dense cosine similarity controls the evidence gate.
        if not relevant:
            self._log(dense, [], [], timings)
            return []

        lexical_started = time.perf_counter()
        lexical = self._lexical_candidates(query)
        timings["lexical_search_ms"] = _elapsed_ms(lexical_started)
        pool = self._merge(relevant, lexical)
        rerank_started = time.perf_counter()
        ordered = self._rerank(query, pool)
        timings["rerank_ms"] = _elapsed_ms(rerank_started)
        evidence = build_evidence(ordered[: self._top_k], self._max_context_tokens)
        self._log(dense, pool, evidence, timings)
        return evidence

    def apply_threshold(self, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return [item for item in candidates if item.score >= self._score_threshold]

    # Hybrid retrieval
    def _lexical_candidates(self, query: str) -> list[RetrievedChunk]:
        """BM25 hits from the shared store, with no invented cosine score."""
        return self._store.lexical_search(self._collection, query, self._candidate_k)

    @staticmethod
    def _merge(
        dense: list[RetrievedChunk], lexical: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """Union by chunk_id, keeping the dense entry so its cosine survives."""
        merged: dict[str, RetrievedChunk] = {item.chunk.chunk_id: item for item in dense}
        for item in lexical:
            merged.setdefault(item.chunk.chunk_id, item)
        return list(merged.values())

    def _rerank(self, query: str, pool: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not pool:  # pragma: no cover - guarded by caller
            return pool
        scores = self._reranker.rerank(query, [item.chunk.chunk_text for item in pool])
        scored = [
            item.model_copy(update={"rerank_score": score})
            for item, score in zip(pool, scores, strict=True)
        ]
        # Stable tie-breaking makes repeated results deterministic.
        scored.sort(key=lambda item: (-(item.rerank_score or 0.0), item.chunk.chunk_id))
        return scored

    def _log(
        self,
        dense: list[RetrievedChunk],
        pool: list[RetrievedChunk],
        evidence: list[EvidenceItem],
        timings: dict[str, float],
    ) -> None:
        top_rerank = evidence[0].retrieved.rerank_score if evidence else None
        logger.info(
            "retrieval_completed",
            extra={
                "strategy": "hybrid_rerank",
                "dense_candidates": len(dense),
                "pool": len(pool),
                "evidence_items": len(evidence),
                "top_score": round(dense[0].score, 4) if dense else None,
                "top_rerank_score": round(top_rerank, 4) if top_rerank is not None else None,
                **timings,
            },
        )


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)
