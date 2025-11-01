"""Unit tests for configuration loading."""

import os
from unittest.mock import patch

import pytest

from src.lib.config import load_config
from src.models.types import (
    ChunkingConfiguration,
    ModelConfiguration,
    RetrievalConfiguration,
    VectorDatabaseConfiguration,
)


def test_load_config_required_variables_missing():
    """Test that missing required environment variables raise ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(
            ValueError, match="Missing required environment variable: OLLAMA_EMBEDDING_MODEL"
        ):
            load_config()


def test_load_config_missing_query_model():
    """Test that missing query model raises ValueError."""
    with patch.dict(os.environ, {"OLLAMA_EMBEDDING_MODEL": "test-embed"}, clear=True):
        with pytest.raises(
            ValueError, match="Missing required environment variable: OLLAMA_QUERY_MODEL"
        ):
            load_config()


def test_load_config_with_all_required():
    """Test loading configuration with all required variables."""
    with patch.dict(
        os.environ,
        {
            "OLLAMA_EMBEDDING_MODEL": "test-embed",
            "OLLAMA_QUERY_MODEL": "test-query",
        },
        clear=True,
    ):
        model_config, chunking_config, retrieval_config, vector_db_config = load_config()

        assert isinstance(model_config, ModelConfiguration)
        assert model_config.embedding_model == "test-embed"
        assert model_config.query_model == "test-query"
        assert model_config.ollama_base_url == "http://localhost:11434"  # Default

        assert isinstance(chunking_config, ChunkingConfiguration)
        assert chunking_config.chunk_size == 1000  # Default
        assert chunking_config.chunk_overlap == 200  # Default

        assert isinstance(retrieval_config, RetrievalConfiguration)
        assert retrieval_config.top_k == 4  # Default
        assert retrieval_config.min_similarity == 0.0  # Default

        assert isinstance(vector_db_config, VectorDatabaseConfiguration)
        assert vector_db_config.collection_name == "documents"  # Default


def test_load_config_with_custom_values():
    """Test loading configuration with all custom values."""
    with patch.dict(
        os.environ,
        {
            "OLLAMA_EMBEDDING_MODEL": "custom-embed",
            "OLLAMA_QUERY_MODEL": "custom-query",
            "OLLAMA_BASE_URL": "http://custom:11434",
            "CHUNK_SIZE": "2000",
            "CHUNK_OVERLAP": "400",
            "RETRIEVER_TOP_K": "8",
            "RETRIEVER_MIN_SIMILARITY": "0.5",
            "VECTOR_DB_COLLECTION_NAME": "custom-collection",
        },
        clear=True,
    ):
        model_config, chunking_config, retrieval_config, vector_db_config = load_config()

        assert model_config.embedding_model == "custom-embed"
        assert model_config.query_model == "custom-query"
        assert model_config.ollama_base_url == "http://custom:11434"

        assert chunking_config.chunk_size == 2000
        assert chunking_config.chunk_overlap == 400

        assert retrieval_config.top_k == 8
        assert retrieval_config.min_similarity == 0.5

        assert vector_db_config.collection_name == "custom-collection"


def test_load_config_loads_from_env_file(tmp_path):
    """Test that load_config loads from .env file if present."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OLLAMA_EMBEDDING_MODEL=env-embed\nOLLAMA_QUERY_MODEL=env-query\nCHUNK_SIZE=1500\n"
    )

    # Mock Path(__file__) to point to a fake file in tmp_path
    fake_config_file = tmp_path / "lib" / "config.py"
    fake_config_file.parent.mkdir(parents=True)

    with patch("src.lib.config.__file__", str(fake_config_file)):
        with patch.dict(os.environ, {}, clear=True):
            model_config, chunking_config, _, _ = load_config()

            # Values should come from .env file
            assert model_config.embedding_model == "env-embed"
            assert model_config.query_model == "env-query"
            assert chunking_config.chunk_size == 1500


def test_load_config_env_file_overrides_env_vars(tmp_path):
    """Test that environment variables override .env file values."""
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_EMBEDDING_MODEL=file-embed\n")

    fake_config_file = tmp_path / "lib" / "config.py"
    fake_config_file.parent.mkdir(parents=True)

    with patch("src.lib.config.__file__", str(fake_config_file)):
        # python-dotenv doesn't override existing env vars by default
        # So existing env var should remain
        with patch.dict(
            os.environ,
            {"OLLAMA_EMBEDDING_MODEL": "env-embed", "OLLAMA_QUERY_MODEL": "env-query"},
            clear=True,
        ):
            model_config, _, _, _ = load_config()

            # Environment variable should take precedence
            assert model_config.embedding_model == "env-embed"
