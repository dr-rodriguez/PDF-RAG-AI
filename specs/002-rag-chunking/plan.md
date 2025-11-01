# Implementation Plan: RAG Vector Database with Chunking

**Branch**: `002-rag-chunking` | **Date**: 2025-01-27 | **Spec**: specs/002-rag-chunking/spec.md
**Input**: Feature specification from `/specs/002-rag-chunking/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement RAG (Retrieval-Augmented Generation) functionality to chunk Markdown files, generate embeddings using local Ollama models, store them in a vector database, and enable semantic querying. The system provides CLI commands for processing files (with deduplication on re-processing) and querying the database, with all models and parameters configurable via `.env` file. Uses LangChain framework for RAG orchestration with local Ollama models for both embeddings and query generation.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13  
**Primary Dependencies**: LangChain, langchain-community, langchain-chroma (ChromaDB integration), Ollama integration, python-dotenv, Click for CLI  
**Storage**: ChromaDB vector database with SQLite backend, persisted to `data/db/` directory  
**Testing**: pytest  
**Target Platform**: Local execution on Windows/macOS/Linux (Ollama must be running locally)  
**Project Type**: Single project (CLI-first utilities and services)  
**Performance Goals**: Process 500-5000 line Markdown file in under 2 minutes; query responses in under 5 seconds  
**Constraints**: Must use local Ollama models (no remote API calls); chunk size and overlap configurable via env vars with defaults; minimum similarity threshold for retrieval  
**Scale/Scope**: Handle 10+ Markdown files (50,000+ lines) in single database; support thousands of chunks per document

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file (`.specify/memory/constitution.md`) not found in repository. Applying common best practices based on project patterns from previous features:

- CLI-first with text I/O: PASS (planned CLI commands for processing and querying)
- Testable, stage-oriented pipeline: PASS (processing and querying are distinct stages)
- Observability and provenance: PASS (source file tracking in chunks; structured logging)
- Local execution defaults: PASS (local Ollama models, local vector database)
- Deterministic dependencies: PASS (will pin LangChain and vector store versions)

Gate evaluation: PASS. Design follows established patterns from feature 001-setup-docling.

**Post-Design Re-evaluation**:
- CLI commands (`process` and `query`) implemented with human-readable output
- RAG service follows testable pipeline pattern (processing → querying stages)
- Source file tracking in chunk metadata enables observability and provenance
- Local-only execution (Ollama + ChromaDB local persistence) maintains no remote dependencies
- Dependency versions will be pinned (LangChain, langchain-chroma, langchain-community)

**Status**: PASS. All gates remain satisfied after Phase 1 design completion.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── cli/
│   └── main.py           # CLI entry point with process and query commands
├── services/
│   ├── converter.py      # Existing: PDF-to-Markdown conversion
│   └── rag_service.py    # New: RAG processing and querying orchestration
├── models/
│   └── types.py          # Existing: Data classes; extend with RAG types
└── lib/
    └── io_utils.py       # Existing: Filesystem helpers
```

**Structure Decision**: Single-project CLI-first layout consistent with feature 001-setup-docling. New RAG service handles chunking, embedding generation, vector store operations, and query processing. CLI commands extend existing `main.py` with `process` and `query` subcommands.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None identified | - | - |
