"""Validated application settings loaded from the root ``.env`` file."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ingestion.chunking import CHUNKING_VERSION

# Repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

LLMProviderName = Literal["openai_compatible"]
EmbeddingProviderName = Literal["openai_compatible"]
VectorStoreName = Literal["pgvector"]
# ``none`` keeps figures visible but not searchable by their contents.
VisionProviderName = Literal["none", "openai_compatible"]

# All queries use hybrid retrieval and cross-encoder reranking.
RerankProviderName = Literal["cross_encoder"]

# OpenAI ``reasoning_effort``. Reasoning models spend their output budget on
# hidden thinking before the answer; on a strict single-JSON contract that can
# leave an empty reply once ``max_tokens`` is exhausted. ``none`` switches the
# thinking off on servers that honour the parameter (FILOS does). Empty sends
# nothing, which keeps plain local models untouched.
ReasoningEffort = Literal["", "none", "low", "medium", "high"]


class ConfigurationError(RuntimeError):
    """Raised when the process is not safely configured to start."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_env: Literal["development", "production"] = "development"
    app_name: str = "DemocraSeek"
    app_base_url: str = "http://localhost:8080"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Shared FILOS credential. Specific provider keys override it.
    institutional_api_key: str = ""

    # LLM
    llm_provider: LLMProviderName = "openai_compatible"
    llm_model: str = "llama3.1:8b"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_max_output_tokens: int = Field(default=1200, ge=64, le=32000)
    llm_timeout_seconds: float = Field(default=180.0, gt=0)
    llm_reasoning_effort: ReasoningEffort = ""

    # Embeddings
    embedding_provider: EmbeddingProviderName = "openai_compatible"
    embedding_model: str = "nomic-embed-text"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_dimensions: int = Field(default=768, ge=8, le=8192)
    embedding_batch_size: int = Field(default=16, ge=1, le=512)

    # Vision; enable it to make figure contents searchable.
    vision_provider: VisionProviderName = "none"
    vision_model: str = ""
    vision_base_url: str = ""
    vision_api_key: str = ""
    vision_timeout_seconds: float = Field(default=180.0, gt=0)
    vision_reasoning_effort: ReasoningEffort = ""
    # Maximum generated figure-description length.
    vision_max_description_chars: int = Field(default=900, ge=100, le=4000)

    # Query-time reranking
    rerank_provider: RerankProviderName = "cross_encoder"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Vector store
    vector_store_provider: VectorStoreName = "pgvector"
    vector_store_url: str = ""
    vector_store_collection: str = "innovade_v1"

    # Corpus
    corpus_path: Path = Path("data/corpus")
    corpus_version: str = "unversioned"
    index_version: str = "1"

    # Chunking; changes require re-indexing.
    chunk_size: int = Field(default=1200, ge=200, le=8000)
    chunk_overlap: int = Field(default=180, ge=0, le=4000)

    # Retrieval
    retrieval_top_k: int = Field(default=6, ge=1, le=50)
    # Candidates fetched from each retriever before reranking.
    retrieval_candidate_k: int = Field(default=10, ge=1, le=100)
    retrieval_score_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    retrieval_max_context_tokens: int = Field(default=4000, ge=500, le=100_000)

    # Onboarding and request limits
    onboarding_config_path: Path = Path("config/onboarding.v2.yaml")
    # Curated example questions for the chat start screen, one entry per locale.
    starter_questions_path: Path = Path("config/starter_questions.yaml")
    max_user_input_chars: int = Field(default=2000, ge=50, le=20000)
    max_conversation_messages: int = Field(default=12, ge=2, le=100)
    rate_limit_requests: int = Field(default=60, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    # Reproducible ingestion output
    index_path: Path = Path("data/index")
    report_path: Path = Path("data/reports")

    # Paths
    @field_validator(
        "corpus_path",
        "onboarding_config_path",
        "starter_questions_path",
        "index_path",
        "report_path",
    )
    @classmethod
    def _absolutise(cls, value: Path) -> Path:
        """Resolve relative paths against the project root, never the CWD."""
        return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()

    @field_validator("vector_store_collection")
    @classmethod
    def _safe_collection_name(cls, value: str) -> str:
        if not value or not all(c.isalnum() or c == "_" for c in value):
            raise ValueError(
                "VECTOR_STORE_COLLECTION must be non-empty and contain only "
                "letters, digits and underscores (it becomes a table name)."
            )
        return value.lower()

    # Cross-field validation
    @model_validator(mode="after")
    def _validate_combination(self) -> Settings:
        problems: list[str] = []

        if self.chunk_overlap >= self.chunk_size:
            problems.append(
                f"CHUNK_OVERLAP ({self.chunk_overlap}) must be smaller than "
                f"CHUNK_SIZE ({self.chunk_size})."
            )

        if self.llm_provider == "openai_compatible":
            if not self.llm_base_url:
                problems.append("LLM_BASE_URL is required when LLM_PROVIDER=openai_compatible.")
            if not self.effective_llm_api_key:
                problems.append(
                    "LLM_API_KEY or INSTITUTIONAL_API_KEY is required when "
                    "LLM_PROVIDER=openai_compatible."
                )
            if not self.llm_model:
                problems.append("LLM_MODEL is required when LLM_PROVIDER=openai_compatible.")

        if self.embedding_provider == "openai_compatible":
            if not self.embedding_base_url:
                problems.append(
                    "EMBEDDING_BASE_URL is required when EMBEDDING_PROVIDER=openai_compatible."
                )
            if not self.effective_embedding_api_key:
                problems.append(
                    "EMBEDDING_API_KEY or INSTITUTIONAL_API_KEY is required when "
                    "EMBEDDING_PROVIDER=openai_compatible."
                )
            if not self.embedding_model:
                problems.append(
                    "EMBEDDING_MODEL is required when EMBEDDING_PROVIDER=openai_compatible."
                )

        if self.vision_provider == "openai_compatible":
            if not self.vision_base_url:
                problems.append(
                    "VISION_BASE_URL is required when VISION_PROVIDER=openai_compatible."
                )
            if not self.effective_vision_api_key:
                problems.append(
                    "VISION_API_KEY or INSTITUTIONAL_API_KEY is required when "
                    "VISION_PROVIDER=openai_compatible."
                )
            if not self.vision_model:
                problems.append(
                    "VISION_MODEL is required when VISION_PROVIDER=openai_compatible."
                )

        if not self.rerank_model:
            problems.append("RERANK_MODEL is required.")

        if self.vector_store_provider == "pgvector" and not self.vector_store_url:
            problems.append("VECTOR_STORE_URL is required when VECTOR_STORE_PROVIDER=pgvector.")

        if problems:
            raise ValueError(
                "Invalid DemocraSeek configuration:\n  - " + "\n  - ".join(problems)
            )
        return self

    # Derived values
    @property
    def effective_llm_api_key(self) -> str:
        return self.llm_api_key or self.institutional_api_key

    @property
    def effective_embedding_api_key(self) -> str:
        return self.embedding_api_key or self.institutional_api_key

    @property
    def effective_vision_api_key(self) -> str:
        return self.vision_api_key or self.institutional_api_key

    @property
    def index_fingerprint(self) -> str:
        """Return the index identity; any change requires re-indexing."""
        # Vision and chunking rules affect which chunks exist.
        return (
            f"{self.embedding_provider}|{self.embedding_model}|{self.embedding_dimensions}"
            f"|{self.chunk_size}|{self.chunk_overlap}|{self.index_version}"
            f"|{self.vision_provider}:{self.vision_model}"
            f"|c{CHUNKING_VERSION}"
        )

    def safe_provider_summary(self) -> dict[str, str | int]:
        """Provider identity suitable for logging. Contains no credentials."""
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_reasoning_effort": self.llm_reasoning_effort or "default",
            "language_provider": self.llm_provider,
            "language_model": self.llm_model,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dimensions": self.embedding_dimensions,
            "retrieval_strategy": "hybrid_rerank",
            "rerank_provider": self.rerank_provider,
            "rerank_model": self.rerank_model,
            "vision_provider": self.vision_provider,
            "vision_model": self.vision_model,
            "vision_reasoning_effort": self.vision_reasoning_effort or "default",
            "vector_store_provider": self.vector_store_provider,
            "vector_store_collection": self.vector_store_collection,
            "corpus_version": self.corpus_version,
            "index_version": self.index_version,
        }


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the validated process-wide settings instance."""
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigurationError(str(exc)) from exc
