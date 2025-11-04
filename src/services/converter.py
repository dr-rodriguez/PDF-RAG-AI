"""PDF to Markdown conversion service using Docling."""

import logging
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

try:
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
except ImportError as e:
    raise ImportError("Docling is not installed. Please run: uv sync") from e

try:
    from pypdf import PdfReader
except ImportError as e:
    raise ImportError("pypdf is not installed. Please run: uv sync") from e

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


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Get the total number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Total number of pages in the PDF

    Raises:
        Exception: If PDF cannot be read or is corrupted
    """
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as e:
        raise Exception(f"Failed to read PDF page count: {str(e)}") from e


def convert_pdf_to_markdown(document: Document, page_number: int = 2) -> ConversionResult:
    """
    Convert a single PDF document to Markdown using Docling.

    Args:
        document: Document object representing the source PDF
        page_number: Page number to convert

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
        result = converter.convert(str(document.path), page_range=(page_number,page_number))
        md_content = result.document.export_to_markdown()

        # Strip some characters
        md_content = md_content.replace("<!-- image -->", "")

        # Return success result with markdown content
        # Note: output.path is empty, caller should set it when writing file
        return ConversionResult(
            document=document,
            status=ConversionStatus.SUCCESS,
            output=OutputArtifact(
                filename=Path(document.path).stem + f"_page-{page_number}.md",
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

        logger.error(f"Failed to convert page {page_number} of {document.filename}: {error_msg}")
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=error_msg,
        )


def convert_single_file(input_path: str, output_path: str) -> ConversionResult:
    """
    Convert a single PDF file to Markdown, generating one markdown file per page.

    Args:
        input_path: Path to source PDF file
        output_path: Path where Markdown output should be written (base path, actual files will be {stem}_page-{num}.md)

    Returns:
        ConversionResult with conversion status and details. On success, represents processing of all pages.
    """
    pdf_path = Path(input_path).resolve()
    md_path = Path(output_path).resolve()

    # Check if input file exists before creating Document
    if not pdf_path.exists():
        # Create a Document object without validation for error reporting
        # We bypass validation by using object.__setattr__ after creation

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
    output_dir = md_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get total page count
    try:
        num_pages = get_pdf_page_count(pdf_path)
    except Exception as e:
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=f"Failed to get PDF page count: {str(e)}",
        )

    # Process each page
    pdf_stem = pdf_path.stem
    failed_pages = []
    successful_pages = []
    last_output = None

    for page_num in range(1, num_pages + 1):
        logger.info(f"Converting page {page_num}/{num_pages} of {document.filename}")
        # Convert this page
        conversion_result = convert_pdf_to_markdown(document, page_number=page_num)

        if conversion_result.status == ConversionStatus.FAILURE:
            failed_pages.append(page_num)
            logger.warning(f"Failed to convert page {page_num} of {document.filename}: {conversion_result.message}")
            continue

        # Extract markdown content (stored temporarily in message field)
        md_content = conversion_result.message or ""

        # Generate output filename for this page
        md_filename = f"{pdf_stem}_page-{page_num}.md"
        md_file_path = output_dir / md_filename

        # Write to output file (overwrite by default)
        try:
            md_file_path.write_text(md_content, encoding="utf-8")
            successful_pages.append(page_num)
            last_output = OutputArtifact(
                filename=md_filename,
                path=str(md_file_path),
                size_bytes=md_file_path.stat().st_size if md_file_path.exists() else None,
                source_document=document,
            )
        except Exception as e:
            failed_pages.append(page_num)
            logger.error(f"Failed to write page {page_num} of {document.filename}: {str(e)}")

    # Determine overall result
    if failed_pages:
        error_msg = f"Failed to convert {len(failed_pages)} page(s): {failed_pages}"
        if successful_pages:
            error_msg += f" (succeeded: {len(successful_pages)} page(s))"
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message=error_msg,
        )

    # All pages succeeded
    if last_output is None:
        # This shouldn't happen if num_pages > 0, but handle edge case
        return ConversionResult(
            document=document,
            status=ConversionStatus.FAILURE,
            message="No pages to convert",
        )

    # Return success with info about all pages
    return ConversionResult(
        document=document,
        status=ConversionStatus.SUCCESS,
        output=last_output,  # Use last output as representative
        message=f"Converted {num_pages} page(s) successfully",
    )


def convert_batch(input_dir: str, output_dir: str) -> ConversionJob:
    """
    Convert all PDF files in input directory to Markdown files in output directory.

    Each PDF page is converted to a separate markdown file with naming pattern
    {pdf_stem}_page-{page_num}.md.

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
