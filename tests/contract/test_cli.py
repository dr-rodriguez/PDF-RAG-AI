"""Contract tests for CLI."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


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
        [sys.executable, "-m", "src.cli.main", "--output", "/tmp"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Error" in result.stderr or "required" in result.stderr.lower()


def test_cli_missing_output():
    """Test CLI with missing --output argument."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--input", "/tmp"],
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
            [sys.executable, "-m", "src.cli.main", "--input", "/nonexistent", "--output", str(output_dir)],
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
            [sys.executable, "-m", "src.cli.main", "--input", str(input_dir), "--output", str(output_dir)],
            capture_output=True,
            text=True,
        )
        # Should succeed but process 0 files
        assert result.returncode == 0
        assert "Processed: 0" in result.stdout


def test_cli_json_output():
    """Test CLI with --json flag produces valid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        output_dir = Path(tmpdir) / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "--input",
                str(input_dir),
                "--output",
                str(output_dir),
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Should be valid JSON
        summary = json.loads(result.stdout)
        assert "total" in summary
        assert "succeeded" in summary
        assert "failed" in summary
        assert "results" in summary

