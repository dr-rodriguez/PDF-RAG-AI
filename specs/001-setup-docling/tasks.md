---
description: "Task list for PDF-to-Markdown Conversion Setup feature"
---

# Tasks: PDF-to-Markdown Conversion Setup

**Input**: Design documents from `/specs/001-setup-docling/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/cli/, src/services/, src/models/, src/lib/, tests/unit/, tests/contract/)
- [X] T002 [P] Initialize Python project dependencies: add docling (pinned version) and click to pyproject.toml
- [X] T003 [P] Configure pytest testing framework in pyproject.toml
- [X] T004 [P] Configure linting and formatting tools (ruff/black) in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create Document data class in src/models/types.py with attributes: filename, path, sizeBytes, numPages
- [X] T006 [P] Create OutputArtifact data class in src/models/types.py with attributes: filename, path, sizeBytes, sourceDocument
- [X] T007 [P] Create ConversionResult data class in src/models/types.py with attributes: document, status (enum), message, output
- [X] T008 [P] Create ConversionJob data class in src/models/types.py with attributes: startTime, endTime, total, succeeded, failed, results, doclingVersion
- [X] T009 [P] Implement conservative validation helpers in src/lib/io_utils.py: validate_input_directory, validate_output_directory, ensure_output_directory
- [X] T010 [P] Implement file discovery helpers in src/lib/io_utils.py: find_pdf_files, map_pdf_to_output_path
- [X] T011 [P] Implement logging configuration in src/lib/io_utils.py: setup_logging for structured summary output

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Convert a single PDF to Markdown (Priority: P1) 🎯 MVP

**Goal**: Convert one PDF file from input directory to a Markdown file in output directory with matching base filename

**Independent Test**: Place one valid PDF (`report.pdf`) in the input directory and run the conversion; verify `report.md` is created in the output directory with non-empty content. If `report.md` already exists, it should be overwritten.

### Implementation for User Story 1

- [X] T012 [US1] Implement Docling integration function in src/services/converter.py: convert_pdf_to_markdown(document: Document) -> ConversionResult
- [X] T013 [US1] Implement single-file conversion orchestration in src/services/converter.py: convert_single_file(input_path: str, output_path: str) -> ConversionResult
- [X] T014 [US1] Implement CLI command structure in src/cli/main.py: parse command with --input and --output flags using Click
- [X] T015 [US1] Wire single-file conversion in src/cli/main.py: connect parse command to converter service for first PDF found
- [X] T016 [US1] Add error handling in src/services/converter.py: catch Docling exceptions, encrypted PDF errors, and return ConversionResult with failure status
- [X] T017 [US1] Implement output file overwrite logic in src/services/converter.py: ensure existing markdown files are overwritten by default

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Single PDF conversion works end-to-end.

---

## Phase 4: User Story 2 - Batch convert PDFs in a folder (Priority: P2)

**Goal**: Process all PDF files in the input directory in a single run, producing corresponding Markdown files for each

**Independent Test**: Place three valid PDFs (`a.pdf`, `b.pdf`, `c.pdf`) in the input directory; run conversion; verify three Markdown files (`a.md`, `b.md`, `c.md`) are produced. Non-PDF files should be ignored and not processed.

### Implementation for User Story 2

- [X] T018 [US2] Extend converter service in src/services/converter.py: implement convert_batch(input_dir: str, output_dir: str) -> ConversionJob that processes all PDFs sequentially
- [X] T019 [US2] Update CLI command in src/cli/main.py: modify parse command to process all PDFs in input directory (replace single-file logic)
- [X] T020 [US2] Implement file filtering in src/services/converter.py: ensure only .pdf files (case-insensitive) are processed, ignore non-PDF files
- [X] T021 [US2] Add batch job tracking in src/services/converter.py: collect all ConversionResults, update ConversionJob counts (total, succeeded, failed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Batch conversion handles multiple PDFs in one run.

---

## Phase 5: User Story 3 - Clear reporting of failures (Priority: P3)

**Goal**: Provide concise human-readable summary with per-file success/failure status and error messages for failed conversions

**Independent Test**: Include one corrupted or encrypted PDF in input directory; run conversion; verify human-readable summary shows counts (total, succeeded, failed) and per-file outcomes with failure reason for the problematic file.

### Implementation for User Story 3

- [X] T022 [US3] Implement human-readable summary formatter in src/services/converter.py: format_job_summary(job: ConversionJob) -> str with format "Processed: X | Succeeded: Y | Failed: Z" and per-file lines
- [X] T023 [US3] Add JSON summary formatter in src/services/converter.py: format_job_summary_json(job: ConversionJob) -> dict matching contract schema
- [X] T024 [US3] Implement --json flag handling in src/cli/main.py: add --json option to parse command, emit JSON summary when enabled
- [X] T025 [US3] Wire summary output in src/cli/main.py: after ConversionJob completes, emit summary (human-readable or JSON based on flag)
- [X] T026 [US3] Enhance error messages in src/services/converter.py: provide clear failure reasons (encrypted PDF, corrupted file, Docling parsing error, etc.)

**Checkpoint**: All user stories should now be independently functional. Complete end-to-end pipeline with clear reporting.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027 [P] Add unit tests for converter service in tests/unit/test_converter.py: test single file conversion, batch conversion, error handling
- [X] T028 [P] Add unit tests for I/O utilities in tests/unit/test_io_utils.py: test directory validation, PDF discovery, path mapping
- [X] T029 [P] Add contract tests for CLI in tests/contract/test_cli.py: test parse command with various inputs, verify exit codes, summary formats
- [X] T030 Verify quickstart.md instructions work end-to-end: test install, usage examples, troubleshooting scenarios
- [X] T031 Update README.md with feature documentation: usage examples, CLI reference, error handling guide
- [X] T032 Pin exact Docling version in pyproject.toml: replace constraint with exact version (e.g., docling==1.x.y) as per research.md decision
- [X] T033 Add docling version tracking in ConversionJob: capture and include doclingVersion in job summary for provenance
- [X] T034 Validate edge cases per spec.md: empty input directory, duplicate base names, large files, image-only PDFs, encrypted PDFs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2 → P3)
  - US2 builds on US1's converter service (sequential execution recommended)
  - US3 builds on US2's batch processing (sequential execution recommended)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 converter service - Extends single-file logic to batch processing
- **User Story 3 (P3)**: Depends on US2 batch processing - Adds reporting on top of batch job results

### Within Each User Story

- Models before services (Foundation phase provides models)
- Services before CLI endpoints
- Core conversion logic before error handling enhancements
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup Phase**: T002, T003, T004 can run in parallel (different config sections)
- **Foundational Phase**: T005-T011 can all run in parallel (different classes/functions in different files)
- **User Story 1**: Limited parallelism - sequential conversion pipeline
- **User Story 2**: Extends US1 service sequentially
- **User Story 3**: Extends US2 job tracking sequentially
- **Polish Phase**: T027, T028, T029 can run in parallel (different test files); T030-T034 can be worked on independently

---

## Parallel Example: Foundational Phase

```bash
# Launch all model creation tasks together (different data classes in same file, but can be worked on in parallel):
Task: "Create Document data class in src/models/types.py"
Task: "Create OutputArtifact data class in src/models/types.py"
Task: "Create ConversionResult data class in src/models/types.py"
Task: "Create ConversionJob data class in src/models/types.py"

# Launch all I/O utility tasks together (different functions in same file):
Task: "Implement validation helpers in src/lib/io_utils.py"
Task: "Implement file discovery helpers in src/lib/io_utils.py"
Task: "Implement logging configuration in src/lib/io_utils.py"
```

---

## Parallel Example: Polish Phase

```bash
# Launch all test tasks together (different test files):
Task: "Add unit tests for converter service in tests/unit/test_converter.py"
Task: "Add unit tests for I/O utilities in tests/unit/test_io_utils.py"
Task: "Add contract tests for CLI in tests/contract/test_cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T011) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T012-T017)
4. **STOP and VALIDATE**: Test single PDF conversion independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Complete Polish phase → Final validation
6. Each story adds value without breaking previous stories

### Sequential Team Strategy

Recommended approach for this feature:

1. Team completes Setup + Foundational together (or in parallel where marked [P])
2. Once Foundational is done:
   - Developer works on User Story 1 (single file conversion)
   - Then User Story 2 (batch extension)
   - Then User Story 3 (reporting)
   - Then Polish phase
3. Stories build sequentially but each delivers independent value

---

## Task Summary

- **Total Tasks**: 34
- **Setup Tasks**: 4 (T001-T004)
- **Foundational Tasks**: 7 (T005-T011) - All parallelizable
- **User Story 1 Tasks**: 6 (T012-T017)
- **User Story 2 Tasks**: 4 (T018-T021)
- **User Story 3 Tasks**: 5 (T022-T026)
- **Polish Tasks**: 8 (T027-T034)

### Parallel Opportunities

- **Foundational Phase**: 7 tasks can be worked on in parallel (different files/functions)
- **Polish Phase**: 3 test tasks can be written in parallel (different test files)
- **User Stories**: Sequential recommended due to service extension pattern

### Independent Test Criteria

- **User Story 1**: Single PDF → Single Markdown file with matching base name, overwrite works
- **User Story 2**: Multiple PDFs → Multiple Markdown files, non-PDFs ignored
- **User Story 3**: Batch run with failures → Clear summary with counts and per-file error messages

### Suggested MVP Scope

**MVP = User Story 1 only** (Phases 1, 2, 3):
- Setup project structure and dependencies
- Create foundational data models and I/O utilities
- Implement single PDF conversion with CLI
- Delivers core value: PDF → Markdown transformation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Docling version must be pinned exactly as per research.md decision
- Sequential processing per research.md (no parallelism in v1 conversion)
- All file paths use forward slashes per Python conventions (Windows will handle correctly)

