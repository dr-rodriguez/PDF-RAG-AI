"""PDF to Markdown conversion service using Docling."""

import logging
from datetime import UTC, datetime
from pathlib import Path

try:
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
except ImportError as e:
    raise ImportError("Docling is not installed. Please run: uv sync") from e

from src.lib.io_utils import map_pdf_to_output_path
from src.models.types import (
    ConversionJob,
    ConversionResult,
    ConversionStatus,
    Document,
    OutputArtifact,
)

# Get docling version for provenance
try:
    import docling

    DOCLING_VERSION = docling.__version__
except (ImportError, AttributeError):
    DOCLING_VERSION = "unknown"

logger = logging.getLogger(__name__)


def convert_pdf_to_markdown(document: Document) -> ConversionResult:
    """
    Convert a single PDF document to Markdown using Docling.

    Args:
        document: Document object representing the source PDF

    Returns:
        ConversionResult with status, markdown content accessible via output (on success),
        or error message (on failure). Note: output.path will be empty; caller should set it.
    """
    try:
        # Some explicit options for more control
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = False
        pipeline_options.table_structure_options.do_cell_matching = False
        pipeline_options.ocr_options.lang = ["en"]
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4, device=AcceleratorDevice.AUTO
        )

        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )

        # Convert PDF to Markdown
        result = converter.convert(str(document.path))
        md_content = result.document.export_to_markdown()

        # Return success result with markdown content
        # Note: output.path is empty, caller should set it when writing file
        return ConversionResult(
            document=document,
            status=ConversionStatus.SUCCESS,
            output=OutputArtifact(
                filename=Path(document.path).stem + ".md",
                path="",  # Will be set by caller when writing file
                source_document=document,
            ),
            message=md_content,  # Store markdown content in message temporarily
        )

    except Exception as e:
        error_msg = str(e)
        # Enhance error messages for common cases
        if "encrypted" in error_msg.lower() or "password" in error_msg.lower():
            error_msg = "Encrypted PDF not supported"
        elif "corrupted" in error_msg.lower() or "invalid" in error_msg.lower():
            error_msg = "Corrupted or invalid PDF file"
        else:
            error_msg = f"Docling parsing error: {error_msg}"

        logger.error(f"Failed to convert {document.filename}: {error_msg}")
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=error_msg,
        )


def convert_single_file(input_path: str, output_path: str) -> ConversionResult:
    """
    Convert a single PDF file to Markdown.

    Args:
        input_path: Path to source PDF file
        output_path: Path where Markdown output should be written

    Returns:
        ConversionResult with conversion status and details
    """
    pdf_path = Path(input_path).resolve()
    md_path = Path(output_path).resolve()

    # Check if input file exists before creating Document
    if not pdf_path.exists():
        # Create a Document object without validation for error reporting
        # We bypass validation by using object.__setattr__ after creation
        from dataclasses import fields

        document_dict = {
            "filename": pdf_path.name if pdf_path.name.endswith(".pdf") else pdf_path.name + ".pdf",
            "path": str(pdf_path),
            "size_bytes": None,
        }
        # Create Document instance and manually set attributes to bypass validation
        document = Document.__new__(Document)
        for field in fields(Document):
            setattr(document, field.name, document_dict.get(field.name, field.default))
        # Don't call __post_init__ which would validate

        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=f"Failed to read document: Document path does not exist: {str(pdf_path)}",
        )

    # Create Document object
    try:
        document = Document(
            filename=pdf_path.name,
            path=str(pdf_path),
            size_bytes=pdf_path.stat().st_size if pdf_path.exists() else None,
        )
    except Exception as e:
        # For other exceptions, create Document without validation for error reporting
        from dataclasses import fields

        document_dict = {
            "filename": pdf_path.name if pdf_path.name.endswith(".pdf") else pdf_path.name + ".pdf",
            "path": str(pdf_path),
            "size_bytes": None,
        }
        document = Document.__new__(Document)
        for field in fields(Document):
            setattr(document, field.name, document_dict.get(field.name, field.default))

        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=f"Failed to read document: {str(e)}",
        )

    # Ensure output directory exists
    md_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert PDF to Markdown using the conversion function
    conversion_result = convert_pdf_to_markdown(document)

    # If conversion failed, return early
    if conversion_result.status == ConversionStatus.FAILURE:
        return conversion_result

    # Extract markdown content (stored temporarily in message field)
    md_content = conversion_result.message or ""

    # Write to output file (overwrite by default)
    try:
        md_path.write_text(md_content, encoding="utf-8")

        # Update result with actual output artifact and clear temporary message
        return ConversionResult(
            document=document,
            status=ConversionStatus.SUCCESS,
            output=OutputArtifact(
                filename=md_path.name,
                path=str(md_path),
                size_bytes=md_path.stat().st_size if md_path.exists() else None,
                source_document=document,
            ),
            message=None,  # Clear temporary storage
        )

    except Exception as e:
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=f"Failed to write output file: {str(e)}",
        )


def convert_batch(input_dir: str, output_dir: str) -> ConversionJob:
    """
    Convert all PDF files in input directory to Markdown files in output directory.

    Args:
        input_dir: Path to directory containing PDF files
        output_dir: Path to directory where Markdown files will be written

    Returns:
        ConversionJob with results and summary statistics
    """
    from src.lib.io_utils import find_pdf_files

    job = ConversionJob(
        start_time=datetime.now(UTC),
        docling_version=DOCLING_VERSION,
    )

    # Find all PDF files
    pdf_files = find_pdf_files(input_dir)
    job.total = len(pdf_files)

    # Process each PDF sequentially
    for pdf_path in pdf_files:
        md_path = map_pdf_to_output_path(pdf_path, output_dir)
        result = convert_single_file(str(pdf_path), str(md_path))
        job.add_result(result)

    job.end_time = datetime.now(UTC)
    return job


def format_job_summary(job: ConversionJob) -> str:
    """
    Format a human-readable summary of the conversion job.

    Args:
        job: ConversionJob to format

    Returns:
        Formatted string summary
    """
    lines = [
        f"Processed: {job.total} | Succeeded: {job.succeeded} | Failed: {job.failed}",
    ]

    for result in job.results:
        if result.status == ConversionStatus.SUCCESS and result.output:
            lines.append(f"- {result.document.filename}: OK -> {result.output.filename}")
        else:
            lines.append(
                f"- {result.document.filename}: ERROR: {result.message or 'Unknown error'}"
            )

    return "\n".join(lines)
