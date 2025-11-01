# pdf-rag-ai

PDF-to-Markdown conversion tool using Docling for RAG (Retrieval-Augmented Generation) pipelines.

## Features

- Convert PDF files to Markdown format using Docling
- Batch processing of multiple PDFs
- RAG (Retrieval-Augmented Generation) with vector database storage
- Process Markdown files into vector database with chunking and embeddings
- Query vector database with natural language questions
- Local Ollama model integration for embeddings and query generation
- Human-readable output
- Error handling for encrypted, corrupted, and invalid PDFs
- Overwrite protection with clear reporting

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

### PDF-to-Markdown Conversion

```bash
# Convert all PDFs in input directory to Markdown in output directory
pdf-rag parse --input ./data/input --output ./data/output
```

### RAG Processing and Querying

First, configure your `.env` file (see `.env.example`):

```bash
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_QUERY_MODEL=llama2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVER_TOP_K=4
RETRIEVER_MIN_SIMILARITY=0.0
```

Then process Markdown files into the vector database:

```bash
# Process a single file
pdf-rag process data/output/document.md

# Process all files in a directory
pdf-rag process data/output/
```

Query the vector database:

```bash
pdf-rag query "What is the main topic of the documents?"
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

### Command: `process`

```bash
pdf-rag process <PATH> [--db-path <DB_PATH>]
```

Process Markdown files into a vector database by chunking content and storing embeddings.

**Arguments:**
- `PATH` (required): Path to a Markdown file or directory containing Markdown files
- `--db-path`, `-d` (optional): Path to vector database directory (default: `data/db/`)

**Exit Codes:**
- `0`: Processing completed successfully
- `1`: Invalid arguments, I/O errors, missing configuration, or Ollama model unavailable

### Command: `query`

```bash
pdf-rag query <QUERY_TEXT> [--db-path <DB_PATH>]
```

Query the vector database with a natural language question.

**Arguments:**
- `QUERY_TEXT` (required): Natural language question
- `--db-path`, `-d` (optional): Path to vector database directory (default: `data/db/`)

**Exit Codes:**
- `0`: Query completed successfully and answer was generated
- `1`: Invalid arguments, database not found, missing configuration, Ollama model unavailable, or no relevant chunks found

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

