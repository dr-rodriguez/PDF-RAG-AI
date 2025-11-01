# CLI Contract: pdf-rag-ai process and query

## Command: process

```
pdf-rag process <PATH> [--db-path <DB_PATH>]
```

### Arguments
- `PATH` (positional, required): Path to a single Markdown file or directory containing Markdown files to process.
- `--db-path`, `-d` (optional): Path to vector database directory. Defaults to `data/db/`.

### Behavior
- Processes Markdown files (`.md` extension, case-insensitive) from the specified path.
- If PATH is a directory, processes all `.md` files in that directory (non-recursive v1).
- Chunks each file's content using configured chunk size and overlap (from `.env` or defaults).
- Generates embeddings using the configured Ollama embedding model.
- Stores chunks and embeddings in the vector database at `--db-path` (default: `data/db/`).
- Appends new chunks to existing database if database already exists.
- Deduplicates chunks: skips chunks that already exist for the same source file (prevents duplicates on re-processing).
- Creates database directory if it doesn't exist.

### Exit Codes
- `0`: Processing completed successfully (may include files that were skipped due to deduplication).
- `1`: Invalid arguments, I/O errors, missing configuration, or Ollama model unavailable.

### Output
```
Processing Markdown files...
- processing.md: Added 15 chunks (3 skipped - duplicates)
- large-doc.md: Added 127 chunks (0 skipped)
- empty.md: Added 0 chunks (0 skipped - file too small)

Summary: Processed 3 files | Added 142 chunks | Skipped 3 chunks
Database location: data/db/
```

### Error Messages
- `Error: Path does not exist: <PATH>`
- `Error: Missing required environment variable: OLLAMA_EMBEDDING_MODEL`
- `Error: Ollama embedding model '<model>' not found. Available models: ...`
- `Error: Failed to create database directory: <path>`
- `Error: Failed to process file '<file>': <reason>`

### Notes
- Future options (out of scope for v1): recursive directory walk, glob filters, dry-run, verbose logging mode.

---

## Command: query

```
pdf-rag query <QUERY_TEXT> [--db-path <DB_PATH>]
```

### Arguments
- `QUERY_TEXT` (positional, required): Natural language question to query the vector database.
- `--db-path`, `-d` (optional): Path to vector database directory. Defaults to `data/db/`.

### Behavior
- Queries the vector database at `--db-path` (default: `data/db/`) using the provided query text.
- Generates query embedding using the configured Ollama embedding model.
- Performs similarity search to retrieve top K chunks that exceed the minimum similarity threshold.
- Generates answer using the configured Ollama query model with retrieved chunks as context.
- Outputs only the generated answer text (no source file names or chunk references).

### Exit Codes
- `0`: Query completed successfully and answer was generated.
- `1`: Invalid arguments, database not found, missing configuration, Ollama model unavailable, or no relevant chunks found (below similarity threshold).

### Output
```
What is the main topic of the documents?

[Generated answer text only, no source citations]
```

### Error Messages
- `Error: Missing required environment variable: OLLAMA_QUERY_MODEL`
- `Error: Vector database not found at '<db-path>'. Run 'pdf-rag process' first.`
- `Error: Vector database is empty. Process some documents first.`
- `Error: Ollama query model '<model>' not found. Available models: ...`
- `Error: No relevant chunks found (all chunks below similarity threshold <threshold>)`

### Notes
- If database exists but is empty (no chunks), provides clear message per FR-007.
- Query text can contain spaces (use quotes in shell: `pdf-rag query "What is the answer?"`).
- Future options (out of scope for v1): interactive query mode, query history, source citations option.

---

## Environment Variables (`.env` file)

### Required Variables
- `OLLAMA_EMBEDDING_MODEL`: Name of Ollama embedding model (e.g., `nomic-embed-text`, `all-minilm`)
- `OLLAMA_QUERY_MODEL`: Name of Ollama LLM model for query answering (e.g., `llama2`, `mistral`, `llama3`)

### Optional Variables (with defaults)
- `CHUNK_SIZE`: Chunk size in characters (default: `1000`)
- `CHUNK_OVERLAP`: Overlap between chunks in characters (default: `200`)
- `RETRIEVER_TOP_K`: Number of top chunks to retrieve (default: `4`)
- `RETRIEVER_MIN_SIMILARITY`: Minimum similarity threshold 0.0-1.0 (default: `0.0`)
- `OLLAMA_BASE_URL`: Ollama API base URL (default: `http://localhost:11434`)

### Example `.env` file
```env
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_QUERY_MODEL=llama2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVER_TOP_K=4
RETRIEVER_MIN_SIMILARITY=0.0
```

