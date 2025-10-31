"""I/O utilities for file operations and validation."""

import logging
from pathlib import Path


def validate_input_directory(input_dir: str) -> Path:
    """
    Validate that the input directory exists and is readable.

    Args:
        input_dir: Path to input directory

    Returns:
        Path object for the validated directory

    Raises:
        ValueError: If directory doesn't exist or isn't readable
    """
    path = Path(input_dir).resolve()
    if not path.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if not path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")
    # Check if directory is readable by attempting to access it
    try:
        list(path.iterdir())
    except PermissionError:
        raise ValueError(f"Input directory is not readable: {input_dir}")
    return path


def validate_output_directory(output_dir: str) -> Path:
    """
    Validate that the output directory can be created or is writable.

    Args:
        output_dir: Path to output directory

    Returns:
        Path object for the validated/created directory

    Raises:
        ValueError: If directory cannot be created or isn't writable
    """
    path = Path(output_dir).resolve()
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {output_dir}")
    return path


def ensure_output_directory(output_dir: str) -> Path:
    """
    Ensure the output directory exists, creating it if necessary.

    Args:
        output_dir: Path to output directory

    Returns:
        Path object for the created/existing directory

    Raises:
        OSError: If directory cannot be created
    """
    path = validate_output_directory(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_pdf_files(input_dir: str) -> list[Path]:
    """
    Find all PDF files in the input directory (non-recursive).

    Args:
        input_dir: Path to input directory

    Returns:
        List of Path objects for PDF files found

    Raises:
        ValueError: If input directory validation fails
    """
    path = validate_input_directory(input_dir)
    pdf_files = []
    for item in path.iterdir():
        if item.is_file() and item.suffix.lower() == ".pdf":
            pdf_files.append(item)
    return sorted(pdf_files)


def map_pdf_to_output_path(pdf_path: Path, output_dir: str) -> Path:
    """
    Map a PDF file path to its corresponding Markdown output path.

    Args:
        pdf_path: Path to source PDF file
        output_dir: Path to output directory

    Returns:
        Path object for the output Markdown file

    Raises:
        ValueError: If output directory validation fails
    """
    output_path = ensure_output_directory(output_dir)
    md_filename = pdf_path.stem + ".md"
    return output_path / md_filename


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for structured summary output.

    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
