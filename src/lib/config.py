"""Configuration loading utility for RAG services."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.models.types import (
    ChunkingConfiguration,
    ModelConfiguration,
    RetrievalConfiguration,
    VectorDatabaseConfiguration,
)


def load_config() -> tuple[
    ModelConfiguration,
    ChunkingConfiguration,
    RetrievalConfiguration,
    VectorDatabaseConfiguration,
]:
    """
    Load configuration from environment variables.

    Loads environment variables from .env file (if present) and returns
    configuration objects with validation.

    Returns:
        Tuple of (ModelConfiguration, ChunkingConfiguration, RetrievalConfiguration, VectorDatabaseConfiguration)

    Raises:
        ValueError: If required environment variables are missing or invalid.
    """
    # Load .env file from project root
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Load required model configuration
    embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL")
    query_model = os.getenv("OLLAMA_QUERY_MODEL")

    if not embedding_model:
        raise ValueError("Missing required environment variable: OLLAMA_EMBEDDING_MODEL")
    if not query_model:
        raise ValueError("Missing required environment variable: OLLAMA_QUERY_MODEL")

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    model_config = ModelConfiguration(
        embedding_model=embedding_model,
        query_model=query_model,
        ollama_base_url=ollama_base_url,
    )

    # Load chunking configuration with defaults
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    chunking_config = ChunkingConfiguration(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Load retrieval configuration with defaults
    top_k = int(os.getenv("RETRIEVER_TOP_K", "4"))
    min_similarity = float(os.getenv("RETRIEVER_MIN_SIMILARITY", "0.0"))
    retrieval_config = RetrievalConfiguration(
        top_k=top_k,
        min_similarity=min_similarity,
    )

    # Load vector database configuration with defaults
    collection_name = os.getenv("VECTOR_DB_COLLECTION_NAME", "documents")
    vector_db_config = VectorDatabaseConfiguration(collection_name=collection_name)

    return model_config, chunking_config, retrieval_config, vector_db_config

