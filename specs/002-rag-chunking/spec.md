# Feature Specification: RAG Vector Database with Chunking

**Feature Branch**: `002-rag-chunking`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Add functionality to implementing chunking of the markdown file and storing in a vector database. We will use LangChain powered by local Ollama models. Refer to https://docs.langchain.com/oss/python/langchain/rag for more information on using LangChain to build a RAG. Models, both embedding and for querying, should be specified in environment variables. Use dotenv to load from a local .env file. The processing of the vector database should be a CLI command. Querying the database should be another CLI command."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process Markdown Files into Vector Database (Priority: P1)

As a user, I can process one or more Markdown files into a vector database by running a CLI command that chunks the content and stores embeddings, enabling semantic search capabilities.

**Why this priority**: Establishes the core capability of converting documents into a searchable knowledge base, which is the foundation for RAG functionality.

**Independent Test**: Run the processing command with a path to a valid Markdown file; verify that a vector database is created in `data/db/` with chunked content that can later be queried.

**Acceptance Scenarios**:

1. **Given** a path to a valid Markdown file, **When** I run the processing command with that file path, **Then** the system chunks the content and stores it in a vector database with embeddings in `data/db/`.
2. **Given** a path to a directory containing multiple Markdown files, **When** I run the processing command with that directory path, **Then** the system processes all Markdown files in the directory and stores their chunks in the same vector database in `data/db/`.
3. **Given** an existing vector database in `data/db/`, **When** I run the processing command again, **Then** the system either updates the database with new content or replaces it based on configuration.

---

### User Story 2 - Query the Vector Database (Priority: P1)

As a user, I can query the vector database using natural language questions and receive answers based on the stored document content through semantic search and retrieval.

**Why this priority**: This is the primary value proposition - enabling users to interact with the document content through questions rather than manual searching.

**Independent Test**: After processing at least one Markdown file, run a query command with a question; verify that a relevant answer is returned based on the stored content.

**Acceptance Scenarios**:

1. **Given** a populated vector database, **When** I submit a query about content that exists in the documents, **Then** the system returns an answer extracted from the relevant document chunks.
2. **Given** a query about content that doesn't exist in the documents, **When** I submit the query, **Then** the system indicates that no relevant information was found or returns the best available match.
3. **Given** an empty vector database, **When** I attempt to query, **Then** the system provides a clear message that no documents have been processed yet.

---

### User Story 3 - Configure Models via Environment Variables (Priority: P2)

As a user, I can configure which embedding and query models to use by setting environment variables in a `.env` file, allowing flexibility without code changes.

**Why this priority**: Enables customization and model selection without requiring code modifications, improving operational flexibility.

**Independent Test**: Create a `.env` file with model configuration; run processing and query commands; verify that the specified models are used for embeddings and querying.

**Acceptance Scenarios**:

1. **Given** a `.env` file with embedding and query model names specified, **When** I run processing or query commands, **Then** the system uses those models from the local Ollama installation.
2. **Given** a `.env` file with missing model configuration, **When** I run commands, **Then** the system provides clear error messages indicating which configuration is missing.
3. **Given** a `.env` file with invalid model names, **When** I run commands, **Then** the system provides error messages indicating the model is not available in Ollama.

---

### Edge Cases

- Empty Markdown files: Processing completes without errors, but produces minimal or no chunks.
- Very large Markdown files: System handles files up to 100MB in size without crashing, though processing time may increase proportionally with file size.
- Malformed Markdown: System processes files that may have formatting issues, extracting text content even if structure is imperfect.
- Missing vector database: When querying `data/db/` that doesn't exist or is empty, the query command provides clear error message indicating the database needs to be created first by running the processing command.
- Concurrent processing: If multiple processing commands run simultaneously, system handles conflicts appropriately (e.g., locks or separate database instances).
- Chunk size limits: System handles documents that produce many chunks (thousands) without performance issues.
- Special characters and non-English content: System processes markdown containing various character sets and languages correctly.
- Network issues with Ollama: If Ollama service is unavailable, system provides clear error messages with guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a CLI command to process Markdown files, chunk their content, generate embeddings, and store them in a vector database.
- **FR-002**: The system MUST provide a CLI command to query the vector database using natural language questions and return answers based on stored content.
- **FR-003**: The system MUST read model configuration (embedding model and query model names) from environment variables loaded from a `.env` file in the project root.
- **FR-004**: The system MUST use local Ollama models for both embedding generation and query processing.
- **FR-005**: The system MUST chunk Markdown content in a way that preserves semantic meaning and context.
- **FR-006**: The system MUST persist the vector database to disk in `data/db/` so that it remains available between command invocations.
- **FR-007**: The system MUST handle queries when the database is empty by providing appropriate feedback to the user.
- **FR-008**: The system MUST provide clear error messages when required environment variables are missing or when models are not available in Ollama.
- **FR-009**: The processing command MUST accept a path argument that can be either a single Markdown file path or a directory path containing Markdown files to process.
- **FR-010**: The processing command MUST store the vector database in `data/db/` by default.
- **FR-011**: The query command MUST accept a query string and output the answer to the user.
- **FR-012**: The query command MUST query the vector database from `data/db/` by default.

### Key Entities *(include if feature involves data)*

- **Document Chunk**: A semantically meaningful segment of a Markdown file (attributes: content, source file, position/index, embedding).
- **Vector Database**: A persistent storage system containing document chunks with their embeddings, stored in `data/db/` by default (attributes: location, chunk count, source documents).
- **Query**: A natural language question submitted by the user (attributes: text, timestamp).
- **Query Response**: An answer generated from relevant document chunks (attributes: answer text, source chunks/references).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully process a typical Markdown file (500-5000 lines) into a vector database in under 2 minutes.
- **SC-002**: Users can query the vector database and receive relevant answers for questions about content that exists in the processed documents, with answers retrieved in under 5 seconds for typical queries.
- **SC-003**: Query responses accurately reflect content from the source documents, with the top result being semantically relevant to the query in 90% of test cases.
- **SC-004**: Users can configure models via `.env` file and run both processing and query commands without code modifications, successfully completing end-to-end workflow in a single session.
- **SC-005**: The vector database persists between command invocations, allowing queries to work after processing without re-processing documents.
- **SC-006**: System handles processing of 10+ Markdown files (totaling 50,000+ lines) into a single vector database without crashing or significant performance degradation.

## Assumptions

- Ollama is installed and running locally on the user's machine.
- Required models (embedding and query) are available in the local Ollama installation.
- Users will provide paths to either a single Markdown file or a directory containing Markdown files to process.
- Vector database is stored in `data/db/` directory on local disk with sufficient space for embeddings.
- Users have basic familiarity with CLI tools and environment variable configuration.
- The `.env` file follows standard format (KEY=VALUE pairs).
- Chunking strategy preserves enough context for meaningful semantic search (chunk size and overlap are configured appropriately).
- Local models provide adequate quality for embedding generation and query answering for the use case.

## Dependencies

- Existing Markdown file conversion functionality (from feature 001-setup-docling) produces files that can be processed.
- LangChain framework and related dependencies are available for RAG implementation.
- Ollama service and models are accessible locally.
- Python environment supports required packages (langchain, langchain-community, vector store libraries, python-dotenv).

