# pdf-rag-ai

PDF-to-Markdown conversion tool using Docling for RAG (Retrieval-Augmented Generation) pipelines.

## Features

- Convert PDF files to Markdown format using Docling
- Batch processing of multiple PDFs
- Human-readable output
- Error handling for encrypted, corrupted, and invalid PDFs
- Overwrite protection with clear reporting

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

### Basic Conversion

```bash
# Convert all PDFs in input directory to Markdown in output directory
uv run python -m src.cli.main --input ./input --output ./output
```

## CLI Reference

### Command: `parse`

```bash
pdf-rag parse --input <INPUT_DIR> --output <OUTPUT_DIR>
```

**Arguments:**
- `--input`, `-i` (required): Path to directory containing source PDFs
- `--output`, `-o` (required): Path to directory where Markdown files will be written (created if missing)

**Exit Codes:**
- `0`: Conversion completed successfully (may include failures, but no I/O errors)
- `1`: Invalid arguments or I/O errors

## Expected Behavior

- Converts every `*.pdf` (case-insensitive) in `--input` to `*.md` in `--output`
- Overwrites existing output files by default
- Non-PDF files are ignored
- Prints summary with counts (total, succeeded, failed) and per-file outcomes

## Error Handling

The tool handles various error scenarios:

- **Encrypted PDFs**: Reported as failures with clear message
- **Corrupted PDFs**: Detected and reported with error details
- **I/O Errors**: Missing directories, permission issues, etc.
- **Docling Errors**: Parsing failures are caught and reported

All failures are included in the summary output with descriptive error messages.

## Development

### Running Tests

```bash
uv run pytest
```

### Linting and Formatting

```bash
uv run ruff check .
uv run ruff format .
```

## License

See LICENSE file for details.

