"""Unit tests for Ollama utilities."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.lib.ollama_utils import (
    get_model_validation_error,
    list_available_models,
    validate_model_available,
    validate_ollama_connection,
)


def test_validate_ollama_connection_success():
    """Test successful Ollama connection validation."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        result = validate_ollama_connection()
        assert result is True


def test_validate_ollama_connection_failure():
    """Test failed Ollama connection validation."""
    with patch("src.lib.ollama_utils.requests.get", side_effect=requests.RequestException("Connection failed")):
        result = validate_ollama_connection()
        assert result is False


def test_validate_ollama_connection_non_200_status():
    """Test Ollama connection validation with non-200 status code."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        result = validate_ollama_connection()
        assert result is False


def test_list_available_models_success():
    """Test listing available models successfully."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"},
            {"name": "mistral"},
            {"name": "nomic-embed-text"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        models = list_available_models()
        assert models == ["llama2", "mistral", "nomic-embed-text"]


def test_list_available_models_connection_error():
    """Test listing models with connection error."""
    with patch(
        "src.lib.ollama_utils.requests.get", side_effect=requests.RequestException("Connection failed")
    ) as mock_get:
        with pytest.raises(RuntimeError, match="Failed to connect to Ollama"):
            list_available_models()

        # Verify it was called with correct URL
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)


def test_list_available_models_custom_base_url():
    """Test listing models with custom base URL."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response) as mock_get:
        list_available_models("http://custom:11434")
        mock_get.assert_called_once_with("http://custom:11434/api/tags", timeout=5)


def test_validate_model_available_true():
    """Test model validation when model is available."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"},
            {"name": "nomic-embed-text"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        result = validate_model_available("llama2")
        assert result is True


def test_validate_model_available_false():
    """Test model validation when model is not available."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        result = validate_model_available("mistral")
        assert result is False


def test_validate_model_available_with_tag():
    """Test model validation with tag format (model:tag)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2:latest"},
            {"name": "llama2:7b"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        # Should match llama2:latest and llama2:7b
        assert validate_model_available("llama2") is True
        assert validate_model_available("llama2:7b") is True
        assert validate_model_available("mistral") is False


def test_validate_model_available_connection_error():
    """Test model validation when connection fails."""
    with patch(
        "src.lib.ollama_utils.requests.get", side_effect=requests.RequestException("Connection failed")
    ):
        result = validate_model_available("llama2")
        assert result is False


def test_get_model_validation_error_success():
    """Test getting validation error message when models are available."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"},
            {"name": "mistral"},
            {"name": "model3"},
            {"name": "model4"},
            {"name": "model5"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        error_msg = get_model_validation_error("unknown-model")
        assert "unknown-model" in error_msg
        assert "Available models" in error_msg
        assert "llama2" in error_msg


def test_get_model_validation_error_connection_failed():
    """Test getting validation error when connection fails."""
    with patch(
        "src.lib.ollama_utils.requests.get", side_effect=requests.RequestException("Connection failed")
    ):
        error_msg = get_model_validation_error("test-model", "http://localhost:11434")
        assert "Cannot connect to Ollama" in error_msg
        assert "http://localhost:11434" in error_msg
        assert "Connection failed" in error_msg


def test_get_model_validation_error_truncates_long_lists():
    """Test that long model lists are truncated in error messages."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": f"model{i}"} for i in range(15)]  # 15 models
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.lib.ollama_utils.requests.get", return_value=mock_response):
        error_msg = get_model_validation_error("unknown")
        # Should show first 10 and indicate total
        assert "model0" in error_msg
        assert "15 total" in error_msg

