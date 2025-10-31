"""Unit tests for I/O utilities."""

import pytest

from src.lib.io_utils import (
    ensure_output_directory,
    find_pdf_files,
    map_pdf_to_output_path,
    validate_input_directory,
    validate_output_directory,
)


def test_validate_input_directory_exists(tmp_path):
    """Test input directory validation with existing directory."""
    result = validate_input_directory(str(tmp_path))
    assert result == tmp_path.resolve()


def test_validate_input_directory_not_exists():
    """Test input directory validation with non-existent directory."""
    with pytest.raises(ValueError, match="does not exist"):
        validate_input_directory("/nonexistent/dir")


def test_validate_input_directory_not_a_directory(tmp_path):
    """Test input directory validation with file instead of directory."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")
    with pytest.raises(ValueError, match="not a directory"):
        validate_input_directory(str(file_path))


def test_validate_output_directory(tmp_path):
    """Test output directory validation."""
    result = validate_output_directory(str(tmp_path))
    assert result == tmp_path.resolve()


def test_ensure_output_directory_creates_missing(tmp_path):
    """Test that ensure_output_directory creates missing directories."""
    new_dir = tmp_path / "new" / "nested" / "dir"
    result = ensure_output_directory(str(new_dir))
    assert new_dir.exists()
    assert new_dir.is_dir()
    assert result == new_dir.resolve()


def test_find_pdf_files(tmp_path):
    """Test PDF file discovery."""
    # Create some test files
    (tmp_path / "test1.pdf").write_text("pdf content")
    (tmp_path / "test2.pdf").write_text("pdf content")
    (tmp_path / "test.txt").write_text("text content")
    (tmp_path / "TEST3.PDF").write_text("pdf content")  # Case insensitive

    pdf_files = find_pdf_files(str(tmp_path))
    assert len(pdf_files) == 3
    filenames = {f.name for f in pdf_files}
    assert "test1.pdf" in filenames
    assert "test2.pdf" in filenames
    assert "TEST3.PDF" in filenames
    assert "test.txt" not in filenames


def test_find_pdf_files_empty_directory(tmp_path):
    """Test PDF file discovery with empty directory."""
    pdf_files = find_pdf_files(str(tmp_path))
    assert len(pdf_files) == 0


def test_map_pdf_to_output_path(tmp_path):
    """Test PDF to Markdown path mapping."""
    pdf_path = tmp_path / "input" / "document.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_text("pdf content")

    output_dir = tmp_path / "output"
    result = map_pdf_to_output_path(pdf_path, str(output_dir))

    assert result == output_dir / "document.md"
    assert output_dir.exists()  # Directory should be created


def test_map_pdf_to_output_path_preserves_stem(tmp_path):
    """Test that path mapping preserves base filename."""
    pdf_path = tmp_path / "file with spaces.pdf"
    pdf_path.write_text("pdf content")

    output_dir = tmp_path / "output"
    result = map_pdf_to_output_path(pdf_path, str(output_dir))

    assert result.name == "file with spaces.md"
