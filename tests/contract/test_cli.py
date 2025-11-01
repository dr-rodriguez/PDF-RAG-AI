"""Contract tests for CLI."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def get_minimal_env():
    """Get minimal environment with OLLAMA vars set to empty to prevent .env loading."""
    # Set OLLAMA vars to empty strings so they exist but are empty.
    # This prevents load_config from loading .env file (since vars exist)
    # but causes it to raise ValueError because they're empty.
    minimal_env = {}
    # Set OLLAMA vars to empty to block .env loading
    minimal_env["OLLAMA_EMBEDDING_MODEL"] = ""
    minimal_env["OLLAMA_QUERY_MODEL"] = ""
    # Include essential vars for Python to work
    if "PATH" in os.environ:
        minimal_env["PATH"] = os.environ["PATH"]
    # On Windows, include SYSTEMROOT and USERPROFILE for Python to work properly
    if sys.platform == "win32":
        if "SYSTEMROOT" in os.environ:
            minimal_env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        if "USERPROFILE" in os.environ:
            minimal_env["USERPROFILE"] = os.environ["USERPROFILE"]
    else:
        # Unix-like systems
        if "HOME" in os.environ:
            minimal_env["HOME"] = os.environ["HOME"]
    return minimal_env


def get_test_env_with_ollama():
    """Get minimal environment with OLLAMA vars set for tests that need them."""
    env = get_minimal_env()
    # Override OLLAMA vars with test values
    env["OLLAMA_EMBEDDING_MODEL"] = "test"
    env["OLLAMA_QUERY_MODEL"] = "test"
    return env


def test_cli_help():
    """Test that CLI shows help message."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "PDF-to-Markdown" in result.stdout or "Convert PDF" in result.stdout


def test_cli_missing_input():
    """Test CLI with missing --input argument."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "parse", "--output", "/tmp"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Error" in result.stderr or "required" in result.stderr.lower()


def test_cli_missing_output():
    """Test CLI with missing --output argument."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "parse", "--input", "/tmp"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Error" in result.stderr or "required" in result.stderr.lower()


def test_cli_nonexistent_input():
    """Test CLI with non-existent input directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "parse",
                "--input",
                "/nonexistent",
                "--output",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


def test_cli_empty_input_directory():
    """Test CLI with empty input directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        output_dir = Path(tmpdir) / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "parse",
                "--input",
                str(input_dir),
                "--output",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        # Should succeed but process 0 files
        assert result.returncode == 0
        assert "Processed: 0" in result.stdout


def test_cli_process_missing_config():
    """Test process command with missing configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("# Test\n\nContent here.")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "process",
                str(test_file),
            ],
            capture_output=True,
            text=True,
            env=get_minimal_env(),  # Minimal environment without app vars
        )
        assert result.returncode != 0
        assert "Missing required environment variable" in result.stderr


def test_cli_process_nonexistent_path():
    """Test process command with non-existent path."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.main",
            "process",
            "/nonexistent/path.md",
        ],
        capture_output=True,
        text=True,
        env=get_test_env_with_ollama(),
    )
    assert result.returncode != 0
    assert "Path does not exist" in result.stderr


def test_cli_query_missing_config():
    """Test query command with missing configuration."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.main",
            "query",
            "What is the topic?",
        ],
        capture_output=True,
        text=True,
        env=get_minimal_env(),  # Minimal environment without app vars
    )
    assert result.returncode != 0
    assert "Missing required environment variable" in result.stderr


def test_cli_query_empty_database(tmp_path):
    """Test query command with empty database."""
    db_path = tmp_path / "db"
    db_path.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.main",
            "query",
            "What is the topic?",
            "--db-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
        env=get_test_env_with_ollama(),
    )
    assert result.returncode != 0
    assert "Vector database not found" in result.stderr or "empty" in result.stderr.lower()


def test_cli_query_nonexistent_database():
    """Test query command with non-existent database."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli.main",
            "query",
            "What is the topic?",
            "--db-path",
            "/nonexistent/db",
        ],
        capture_output=True,
        text=True,
        env=get_test_env_with_ollama(),
    )
    assert result.returncode != 0
    assert "Vector database not found" in result.stderr
