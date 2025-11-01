"""Unit tests for RAG service."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.types import (
    ChunkingConfiguration,
    ModelConfiguration,
    ProcessingResult,
    ProcessingStatus,
    QueryResponse,
    RetrievalConfiguration,
    VectorDatabaseConfiguration,
)
from src.services.rag_service import (
    chunk_text,
    process_batch,
    process_file,
    process_query,
)


def test_chunk_text():
    """Test text chunking with default configuration."""
    config = ChunkingConfiguration(chunk_size=10, chunk_overlap=2)
    text = "This is a test document with multiple sentences."
    chunks = chunk_text(text, config)

    assert len(chunks) > 1
    # All chunks should be strings
    assert all(isinstance(chunk, str) for chunk in chunks)
    # Total content should be preserved (with some overlap)
    # Note: Some chunkers may trim whitespace, so allow small differences
    total_length = sum(len(chunk) for chunk in chunks)
    # Account for potential whitespace trimming - should be close to original length
    assert total_length >= len(text) - 2  # Allow up to 2 chars difference for whitespace


def test_chunk_text_small_text():
    """Test chunking text smaller than chunk size."""
    config = ChunkingConfiguration(chunk_size=1000, chunk_overlap=200)
    text = "Small text"
    chunks = chunk_text(text, config)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_process_file_empty_file(tmp_path):
    """Test processing an empty file."""
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("")

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    with (
        patch("src.services.rag_service.generate_embeddings"),
        patch("src.services.rag_service.initialize_vector_database"),
    ):
        result = process_file(
            str(empty_file),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert result.status == ProcessingStatus.SUCCESS
        assert result.chunks_added == 0
        assert result.chunks_skipped == 0
        assert "empty" in result.message.lower()


def test_process_file_success(tmp_path):
    """Test successful file processing with mocked components."""
    test_file = tmp_path / "test.md"
    test_file.write_text("This is test content. " * 100)  # Make it long enough to chunk

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration(chunk_size=50, chunk_overlap=10)
    vector_db_config = VectorDatabaseConfiguration()

    # Mock embeddings
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.1] * 384

    # Mock vector store
    mock_vector_store = MagicMock()
    mock_vector_store._collection.count.return_value = 0
    mock_vector_store.get.return_value = {"documents": [], "metadatas": []}

    with (
        patch("src.services.rag_service.generate_embeddings", return_value=mock_embeddings),
        patch(
            "src.services.rag_service.initialize_vector_database", return_value=mock_vector_store
        ),
        patch("src.services.rag_service.check_chunk_exists", return_value=False),
    ):
        result = process_file(
            str(test_file),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert result.status == ProcessingStatus.SUCCESS
        assert result.chunks_added > 0
        assert result.processing_time_ms >= 0


def test_process_file_deduplication(tmp_path):
    """Test file processing with chunk deduplication."""
    test_file = tmp_path / "test.md"
    test_file.write_text("Test content. " * 50)

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration(chunk_size=50, chunk_overlap=10)
    vector_db_config = VectorDatabaseConfiguration()

    mock_embeddings = MagicMock()
    mock_vector_store = MagicMock()
    mock_vector_store._collection.count.return_value = 0
    mock_vector_store.get.return_value = {"documents": ["Test content."], "metadatas": []}

    # First chunk exists, second doesn't
    chunk_exists_calls = [True, False, False]

    def side_effect(*args):
        return chunk_exists_calls.pop(0) if chunk_exists_calls else False

    with (
        patch("src.services.rag_service.generate_embeddings", return_value=mock_embeddings),
        patch(
            "src.services.rag_service.initialize_vector_database", return_value=mock_vector_store
        ),
        patch("src.services.rag_service.check_chunk_exists", side_effect=side_effect),
    ):
        result = process_file(
            str(test_file),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert result.status == ProcessingStatus.SUCCESS
        assert result.chunks_skipped > 0  # At least one was skipped


def test_process_file_error_handling(tmp_path):
    """Test error handling during file processing."""
    test_file = tmp_path / "test.md"
    test_file.write_text("Test content")

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    with patch(
        "src.services.rag_service.generate_embeddings", side_effect=RuntimeError("Model not found")
    ):
        result = process_file(
            str(test_file),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert result.status == ProcessingStatus.FAILURE
        assert result.message is not None
        assert "Model not found" in result.message


def test_process_batch_single_file(tmp_path):
    """Test batch processing with a single file."""
    test_file = tmp_path / "test.md"
    test_file.write_text("Test content. " * 50)

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration(chunk_size=50, chunk_overlap=10)
    vector_db_config = VectorDatabaseConfiguration()

    mock_embeddings = MagicMock()
    mock_vector_store = MagicMock()
    mock_vector_store._collection.count.return_value = 0
    mock_vector_store.get.return_value = {"documents": [], "metadatas": []}

    with (
        patch("src.services.rag_service.generate_embeddings", return_value=mock_embeddings),
        patch(
            "src.services.rag_service.initialize_vector_database", return_value=mock_vector_store
        ),
        patch("src.services.rag_service.check_chunk_exists", return_value=False),
        patch("src.services.rag_service.process_file") as mock_process_file,
    ):
        mock_result = ProcessingResult(
            source_file=str(test_file),
            status=ProcessingStatus.SUCCESS,
            chunks_added=5,
            chunks_skipped=0,
        )
        mock_process_file.return_value = mock_result

        job = process_batch(
            str(test_file),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert job.total_files == 1
        assert job.succeeded == 1
        assert len(job.results) == 1


def test_process_batch_directory(tmp_path):
    """Test batch processing with a directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.md").write_text("Content 1. " * 50)
    (test_dir / "file2.md").write_text("Content 2. " * 50)

    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    mock_embeddings = MagicMock()
    mock_vector_store = MagicMock()
    mock_vector_store._collection.count.return_value = 0
    mock_vector_store.get.return_value = {"documents": [], "metadatas": []}

    with (
        patch("src.services.rag_service.generate_embeddings", return_value=mock_embeddings),
        patch(
            "src.services.rag_service.initialize_vector_database", return_value=mock_vector_store
        ),
        patch("src.services.rag_service.check_chunk_exists", return_value=False),
    ):
        job = process_batch(
            str(test_dir),
            str(tmp_path / "db"),
            model_config,
            chunking_config,
            vector_db_config,
        )

        assert job.total_files == 2
        assert len(job.results) == 2


def test_process_batch_nonexistent_path(tmp_path):
    """Test batch processing with non-existent path."""
    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    chunking_config = ChunkingConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    job = process_batch(
        str(tmp_path / "nonexistent"),
        str(tmp_path / "db"),
        model_config,
        chunking_config,
        vector_db_config,
    )

    assert job.total_files == 0
    assert job.failed == 1
    assert len(job.results) == 1
    assert job.results[0].status == ProcessingStatus.FAILURE


def test_process_query_success(tmp_path):
    """Test successful query processing."""
    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    retrieval_config = RetrievalConfiguration(top_k=4)
    vector_db_config = VectorDatabaseConfiguration()

    # Mock vector store and retriever
    mock_retriever = MagicMock()
    mock_vector_store = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10  # Non-empty database
    mock_vector_store._collection = mock_collection
    mock_vector_store.as_retriever.return_value = mock_retriever

    # Mock LLM and chain
    mock_llm = MagicMock()
    mock_qa_chain = MagicMock()
    mock_qa_chain.invoke.return_value = {"result": "This is the answer to your question."}

    with (
        patch("src.services.rag_service.validate_model_available", return_value=True),
        patch("src.services.rag_service.generate_embeddings"),
        patch(
            "src.services.rag_service.setup_vector_retriever",
            return_value=(mock_retriever, mock_vector_store),
        ),
        patch("src.services.rag_service.Ollama", return_value=mock_llm),
        patch("src.services.rag_service.RetrievalQA.from_chain_type", return_value=mock_qa_chain),
    ):
        response = process_query(
            "What is the main topic?",
            str(tmp_path / "db"),
            model_config,
            retrieval_config,
            vector_db_config,
        )

        assert isinstance(response, QueryResponse)
        assert response.answer == "This is the answer to your question."
        assert response.retrieved_chunks == 4  # top_k value


def test_process_query_empty_database(tmp_path):
    """Test query with empty database."""
    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    retrieval_config = RetrievalConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    mock_collection = MagicMock()
    mock_collection.count.return_value = 0  # Empty database

    with (
        patch("src.services.rag_service.validate_model_available", return_value=True),
        patch("src.services.rag_service.generate_embeddings"),
        patch("src.services.rag_service.setup_vector_retriever") as mock_setup,
    ):
        # Simulate empty database error
        mock_vector_store = MagicMock()
        mock_vector_store._collection.count.return_value = 0
        mock_setup.side_effect = RuntimeError("Vector database is empty")

        with pytest.raises(RuntimeError, match="Vector database is empty"):
            process_query(
                "Test query",
                str(tmp_path / "db"),
                model_config,
                retrieval_config,
                vector_db_config,
            )


def test_process_query_model_unavailable(tmp_path):
    """Test query with unavailable model."""
    model_config = ModelConfiguration(embedding_model="test", query_model="unavailable")
    retrieval_config = RetrievalConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    with (
        patch("src.services.rag_service.validate_model_available", return_value=False),
        patch(
            "src.services.rag_service.get_model_validation_error",
            return_value="Model 'unavailable' not found",
        ),
    ):
        with pytest.raises(RuntimeError, match="Model 'unavailable' not found"):
            process_query(
                "Test query",
                str(tmp_path / "db"),
                model_config,
                retrieval_config,
                vector_db_config,
            )


def test_process_query_empty_answer(tmp_path):
    """Test query that returns empty answer."""
    model_config = ModelConfiguration(embedding_model="test", query_model="test")
    retrieval_config = RetrievalConfiguration()
    vector_db_config = VectorDatabaseConfiguration()

    mock_retriever = MagicMock()
    mock_vector_store = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    mock_vector_store._collection = mock_collection
    mock_vector_store.as_retriever.return_value = mock_retriever

    mock_qa_chain = MagicMock()
    mock_qa_chain.invoke.return_value = {"result": ""}  # Empty answer

    with (
        patch("src.services.rag_service.validate_model_available", return_value=True),
        patch("src.services.rag_service.generate_embeddings"),
        patch(
            "src.services.rag_service.setup_vector_retriever",
            return_value=(mock_retriever, mock_vector_store),
        ),
        patch("src.services.rag_service.Ollama"),
        patch("src.services.rag_service.RetrievalQA.from_chain_type", return_value=mock_qa_chain),
    ):
        with pytest.raises(RuntimeError, match="No relevant chunks found"):
            process_query(
                "Test query",
                str(tmp_path / "db"),
                model_config,
                retrieval_config,
                vector_db_config,
            )
