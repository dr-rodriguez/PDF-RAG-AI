"""Ollama connection and model validation utilities."""

import requests
from requests.exceptions import RequestException


def validate_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """
    Validate that Ollama is running and accessible.

    Args:
        base_url: Ollama API base URL

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except RequestException:
        return False


def list_available_models(base_url: str = "http://localhost:11434") -> list[str]:
    """
    List available Ollama models.

    Args:
        base_url: Ollama API base URL

    Returns:
        List of available model names

    Raises:
        RuntimeError: If Ollama is not accessible
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        models = [model["name"] for model in data.get("models", [])]
        return models
    except RequestException as e:
        raise RuntimeError(f"Failed to connect to Ollama at {base_url}: {e}") from e


def validate_model_available(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Validate that a specific Ollama model is available.

    Args:
        model_name: Name of the model to check
        base_url: Ollama API base URL

    Returns:
        True if model is available, False otherwise
    """
    try:
        available_models = list_available_models(base_url)
        # Check if model_name matches any available model (support tags like model:tag)
        return any(
            model_name == model or model.startswith(f"{model_name}:") for model in available_models
        )
    except RuntimeError:
        return False


def get_model_validation_error(model_name: str, base_url: str = "http://localhost:11434") -> str:
    """
    Get detailed error message for unavailable model.

    Args:
        model_name: Name of the model that is unavailable
        base_url: Ollama API base URL

    Returns:
        Error message string
    """
    try:
        available_models = list_available_models(base_url)
        available_list = ", ".join(available_models[:10])  # Show first 10
        if len(available_models) > 10:
            available_list += f", ... ({len(available_models)} total)"
        return (
            f"Ollama model '{model_name}' not found. "
            f"Available models: {available_list}"
        )
    except RuntimeError as e:
        return f"Cannot connect to Ollama at {base_url}. {str(e)}"

