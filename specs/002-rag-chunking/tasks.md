---
description: "Task list for RAG Vector Database with Chunking feature implementation"
---

# Tasks: RAG Vector Database with Chunking

**Input**: Design documents from `/specs/002-rag-chunking/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency management

- [X] T001 Add LangChain dependencies to pyproject.toml (langchain, langchain-community, langchain-chroma)
- [X] T002 [P] Add python-dotenv dependency to pyproject.toml for environment variable management
- [X] T003 [P] Create data/db/ directory structure for vector database persistence
- [X] T004 [P] Create .env.example file in project root with required configuration variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create ModelConfiguration dataclass in src/models/types.py with embedding_model, query_model, ollama_base_url attributes
- [X] T006 [P] Create ChunkingConfiguration dataclass in src/models/types.py with chunk_size and chunk_overlap attributes
- [X] T007 [P] Create RetrievalConfiguration dataclass in src/models/types.py with top_k and min_similarity attributes
- [X] T007a [P] Create VectorDatabaseConfiguration dataclass in src/models/types.py with collection_name attribute (default: "documents")
- [X] T008 Implement configuration loading utility in src/lib/config.py to load environment variables from .env file with validation and defaults
- [X] T009 [P] Implement Ollama connection validation utility in src/lib/ollama_utils.py to check model availability

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Process Markdown Files into Vector Database (Priority: P1) 🎯 MVP

**Goal**: Enable users to process Markdown files into a vector database by chunking content and storing embeddings, enabling semantic search capabilities.

**Independent Test**: Run the processing command with a path to a valid Markdown file; verify that a vector database is created in `data/db/` with chunked content that can later be queried.

### Implementation for User Story 1

- [X] T010 [US1] Create DocumentChunk dataclass in src/models/types.py with id, content, source_file, chunk_index, embedding, metadata attributes
- [X] T011 [US1] Create VectorDatabase dataclass in src/models/types.py with location, store_type, collection_name attributes
- [X] T012 [US1] Create ProcessingResult dataclass in src/models/types.py with source_file, status, chunks_added, chunks_skipped, message, processing_time_ms attributes
- [X] T013 [US1] Create ProcessingJob dataclass in src/models/types.py with start_time, end_time, total_files, succeeded, failed, total_chunks_added, results attributes
- [X] T014 [US1] Implement chunking function in src/services/rag_service.py using RecursiveCharacterTextSplitter with configurable chunk size and overlap. Note: Fixed-size chunking with overlap is deterministic (no randomness), satisfying Constitution Principle III requirement for seedable/deterministic chunking
- [X] T015 [US1] Implement vector database initialization in src/services/rag_service.py to create or load ChromaDB collection in data/db/ using collection name from configuration (defaults to "documents" until US3 config loader is integrated)
- [X] T016 [US1] Implement embedding generation function in src/services/rag_service.py using OllamaEmbeddings from langchain_community with configured model. Include error handling for Ollama model unavailability (validated via T009, error handling integrated in T022)
- [X] T017 [US1] Implement chunk deduplication logic in src/services/rag_service.py to check if chunk content + source_file already exists before adding
- [X] T018 [US1] Implement process_file function in src/services/rag_service.py to process a single Markdown file: read, chunk, embed, deduplicate, and store in vector database
- [X] T019 [US1] Implement process_batch function in src/services/rag_service.py to process multiple Markdown files from a directory path
- [X] T020 [US1] Add process command to src/cli/main.py CLI with PATH argument (file or directory) and optional --db-path flag, integrating with rag_service
- [X] T021 [US1] Implement output formatting for process command in src/cli/main.py to display file-by-file results and summary statistics
- [X] T022 [US1] Add error handling for process command in src/cli/main.py for missing paths, I/O errors, missing configuration, and Ollama model unavailability

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Query the Vector Database (Priority: P1)

**Goal**: Enable users to query the vector database using natural language questions and receive answers based on stored document content through semantic search and retrieval.

**Independent Test**: After processing at least one Markdown file, run a query command with a question; verify that a relevant answer is returned based on the stored content.

### Implementation for User Story 2

- [X] T023 [US2] Create Query dataclass in src/models/types.py with text and timestamp attributes
- [X] T024 [US2] Create QueryResponse dataclass in src/models/types.py with answer and retrieved_chunks attributes
- [X] T025 [US2] Implement vector database retriever setup in src/services/rag_service.py using ChromaDB retriever with configurable top_k and similarity filtering
- [X] T026 [US2] Implement query processing function in src/services/rag_service.py using LangChain RetrievalQA chain with Ollama LLM for answer generation
- [X] T027 [US2] Implement similarity threshold filtering in src/services/rag_service.py to only return chunks exceeding min_similarity threshold
- [X] T028 [US2] Implement query function in src/services/rag_service.py to process a natural language query and return answer text only (no source metadata)
- [X] T029 [US2] Add query command to src/cli/main.py CLI with QUERY_TEXT argument and optional --db-path flag
- [X] T030 [US2] Implement output formatting for query command in src/cli/main.py to display only the generated answer text
- [X] T031 [US2] Add error handling for query command in src/cli/main.py for empty database, missing configuration, Ollama model unavailability, and no relevant chunks found

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Configure Models, Chunking, and Retrieval via Environment Variables (Priority: P2)

**Goal**: Enable users to configure embedding and query models, chunk size and overlap parameters, and retrieval parameters (top K count and similarity threshold) by setting environment variables in a `.env` file, allowing flexibility without code changes.

**Independent Test**: Create a `.env` file with model, chunking, and retrieval configuration; run processing and query commands; verify that the specified models, chunking parameters, and retrieval settings are used.

### Implementation for User Story 3

- [X] T032 [US3] Extend configuration loading in src/lib/config.py to load OLLAMA_EMBEDDING_MODEL and OLLAMA_QUERY_MODEL from environment variables with validation
- [X] T033 [US3] Extend configuration loading in src/lib/config.py to load CHUNK_SIZE and CHUNK_OVERLAP from environment variables with defaults (1000, 200)
- [X] T034 [US3] Extend configuration loading in src/lib/config.py to load RETRIEVER_TOP_K and RETRIEVER_MIN_SIMILARITY from environment variables with defaults (4, 0.0)
- [X] T035 [US3] Extend configuration loading in src/lib/config.py to load OLLAMA_BASE_URL from environment variables with default (http://localhost:11434)
- [X] T035a [US3] Extend configuration loading in src/lib/config.py to load VECTOR_DB_COLLECTION_NAME from environment variables with default ("documents")
- [X] T036 [US3] Update src/services/rag_service.py to use ModelConfiguration from config loader for embedding and query model initialization
- [X] T037 [US3] Update src/services/rag_service.py to use ChunkingConfiguration from config loader for chunking parameters
- [X] T038 [US3] Update src/services/rag_service.py to use RetrievalConfiguration from config loader for retrieval parameters
- [X] T038a [US3] Update src/services/rag_service.py to use VectorDatabaseConfiguration from config loader for collection name when initializing ChromaDB
- [X] T039 [US3] Add validation error messages in src/lib/config.py for missing required environment variables (OLLAMA_EMBEDDING_MODEL, OLLAMA_QUERY_MODEL)
- [X] T040 [US3] Integrate Ollama model validation in src/lib/config.py to check model availability and provide clear error messages for unavailable models
- [X] T041 [US3] Update .env.example file with all configuration variables and example values

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 [P] Add comprehensive error messages throughout src/cli/main.py for all error cases per CLI contract
- [X] T043 [P] Add structured logging for RAG operations in src/services/rag_service.py with stage, timing, and counts (chunks, tokens) per Constitution Principle V for observability and debugging
- [X] T044 [P] Update README.md with usage instructions for process and query commands
- [X] T045 Code cleanup and refactoring across all RAG components
- [ ] T046 Run quickstart.md validation to ensure all scenarios work end-to-end
- [ ] T047 Add performance validation: verify processing time for 500-5000 line file is under 2 minutes (validates SC-001). Consider validating incrementally during US1 implementation
- [ ] T048 Add performance validation: verify query responses are returned in under 5 seconds (validates SC-002). Consider validating incrementally during US2 implementation
- [ ] T049 Add validation for SC-003: Verify semantic relevance accuracy (90% test case threshold) with defined test case criteria and evaluation method

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start implementation after Foundational (Phase 2) in parallel with US1, but requires US1-completed data for functional testing (needs processed vector database to query)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Can be integrated into US1 and US2 as they're implemented

### Within Each User Story

- Models before services
- Services before CLI commands
- Core implementation before error handling and formatting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Foundational tasks T006, T007, T007a, T009 can run in parallel (different files)
- Models within US1 (T010-T013) can run in parallel (different dataclasses)
- US3 configuration tasks (T032-T035a) can run in parallel (different config sections)
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create DocumentChunk dataclass in src/models/types.py"
Task: "Create VectorDatabase dataclass in src/models/types.py"
Task: "Create ProcessingResult dataclass in src/models/types.py"
Task: "Create ProcessingJob dataclass in src/models/types.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Process files)
4. Complete Phase 4: User Story 2 (Query database)
5. **STOP and VALIDATE**: Test both stories independently and together
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Process files, verify database creation
3. Add User Story 2 → Test independently → Query database, verify answers
4. Add User Story 3 → Test independently → Verify configuration flexibility
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (processing)
   - Developer B: Prepare User Story 2 (can start models, but query needs processed data)
   - Developer C: User Story 3 (configuration - can work alongside US1/US2)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- US2 depends on US1 for functional testing (needs processed data), but can be implemented in parallel
- US3 enhances US1 and US2 with configuration, so can be integrated during their implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

