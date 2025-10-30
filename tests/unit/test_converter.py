"""Unit tests for converter service."""

import tempfile
from datetime import datetime
from pathlib import Path

from src.models.types import ConversionJob, ConversionStatus
from src.services.converter import (
    convert_batch,
    convert_single_file,
    format_job_summary,
    format_job_summary_json,
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
    job = ConversionJob(
        start_time=datetime.now(datetime.UTC), end_time=datetime.now(datetime.UTC)
    )
    summary = format_job_summary(job)
    assert "Processed: 0" in summary
    assert "Succeeded: 0" in summary
    assert "Failed: 0" in summary


def test_format_job_summary_json_empty_job():
    """Test formatting empty job summary as JSON."""
    job = ConversionJob(
        startTime=datetime.now(datetime.UTC), endTime=datetime.now(datetime.UTC)
    )
    summary = format_job_summary_json(job)
    assert summary["total"] == 0
    assert summary["succeeded"] == 0
    assert summary["failed"] == 0
    assert "startTime" in summary
    assert "endTime" in summary
    assert "doclingVersion" in summary
    assert summary["results"] == []


def test_format_job_summary_json_structure():
    """Test that JSON summary has correct structure."""
    job = ConversionJob(
        startTime=datetime(2025, 1, 1, 12, 0, 0),
        endTime=datetime(2025, 1, 1, 12, 0, 5),
        total=0,
        succeeded=0,
        failed=0,
        doclingVersion="2.59.0",
    )
    summary = format_job_summary_json(job)
    required_keys = [
        "startTime",
        "endTime",
        "durationMs",
        "total",
        "succeeded",
        "failed",
        "doclingVersion",
        "results",
    ]
    for key in required_keys:
        assert key in summary, f"Missing required key: {key}"

