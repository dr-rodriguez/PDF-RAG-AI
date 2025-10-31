"""Unit tests for converter service."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from src.models.types import ConversionJob, ConversionStatus
from src.services.converter import (
    convert_batch,
    convert_single_file,
    format_job_summary,
)


def test_convert_single_file_nonexistent():
    """Test single file conversion with non-existent PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.md"
        result = convert_single_file("/nonexistent/file.pdf", str(output_path))
        assert result.status == ConversionStatus.FAILURE
        assert result.message is not None
        assert "Failed to read document" in result.message or "does not exist" in result.message


def test_convert_batch_empty_directory(tmp_path):
    """Test batch conversion with empty input directory."""
    output_dir = tmp_path / "output"
    job = convert_batch(str(tmp_path), str(output_dir))
    assert job.total == 0
    assert job.succeeded == 0
    assert job.failed == 0
    assert len(job.results) == 0


def test_format_job_summary_empty_job():
    """Test formatting empty job summary."""
    job = ConversionJob(start_time=datetime.now(UTC), end_time=datetime.now(UTC))
    summary = format_job_summary(job)
    assert "Processed: 0" in summary
    assert "Succeeded: 0" in summary
    assert "Failed: 0" in summary
