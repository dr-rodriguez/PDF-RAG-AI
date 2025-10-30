# Feature Specification: PDF-to-Markdown Conversion Setup

**Feature Branch**: `001-setup-docling`  
**Created**: 2025-10-30  
**Status**: Draft  
**Input**: User description: "Let's start the initial setup. We will want an input directory for PDFs and an output for markdown files. Let's focus on just the docling setup and the parsing logic for now, refer to https://docling-project.github.io/docling/examples/minimal/  for information. The python code should be in a separate directory than input/output files as the code should be kept minimal and simple."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert a single PDF to Markdown (Priority: P1)

As a user, I can point the system at one PDF in an input location and receive a corresponding Markdown file in the output location with the same base filename.

**Why this priority**: Establishes the core value of transforming content to a portable, editable format.

**Independent Test**: Place one valid PDF in the input directory and run the conversion; verify a Markdown file is created in the output directory with expected filename mapping and non-empty content.

**Acceptance Scenarios**:

1. **Given** an input directory containing `report.pdf`, **When** the conversion runs, **Then** `report.md` appears in the output directory.
2. **Given** the output already contains `report.md`, **When** conversion runs again, **Then** `report.md` is overwritten by default.

---

### User Story 2 - Batch convert PDFs in a folder (Priority: P2)

As a user, I can place multiple PDFs in the input directory and run a single operation to convert all of them to Markdown outputs.

**Why this priority**: Improves throughput and reduces manual effort for multi-file workflows.

**Independent Test**: Place three valid PDFs in the input directory; run conversion; verify three Markdown files are produced with matching base filenames and a summary indicates 3 successes.

**Acceptance Scenarios**:

1. **Given** `a.pdf`, `b.pdf`, `c.pdf` in input, **When** conversion runs, **Then** `a.md`, `b.md`, `c.md` appear in output.
2. **Given** non-PDF files in input, **When** conversion runs, **Then** they are ignored and not processed.

---

### User Story 3 - Clear reporting of failures (Priority: P3)

As a user, I receive a concise summary of successes and failures, with per-file error messages for any PDFs that could not be converted.

**Why this priority**: Enables troubleshooting and operational visibility without digging into internal logs.

**Independent Test**: Include one corrupted or unsupported PDF in input; run conversion; verify a human-readable summary with at least one failure entry including the filename and a short reason.

**Acceptance Scenarios**:

1. **Given** a corrupted `bad.pdf` in input, **When** conversion runs, **Then** the summary reports 1 failure for `bad.pdf` with an explanation.
2. **Given** at least one successful and one failed file, **When** conversion completes, **Then** the summary shows counts for total, succeeded, and failed.

---

### Edge Cases

- Empty input directory: run completes with 0 processed, 0 output files, summary indicates no work.
- Duplicate base names: if `input/report.pdf` and `input/report (1).pdf` exist, outputs are `report.md` and `report (1).md` respectively.
- Large files (>100MB) or long documents (>1k pages): conversion may take longer; system should still complete without crashing.
- Encrypted/password-protected PDFs: mark as failures with a clear message indicating protection.
- Image-only PDFs: content is still converted; if text extraction is limited, output may contain minimal text with placeholders.
- Non-PDF files: ignored without error; not counted as failures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow configuration of an input directory for source PDFs and an output directory for generated Markdown files.
- **FR-002**: The system MUST convert each `.pdf` file found in the input directory into a `.md` file in the output directory using the same base filename.
- **FR-003**: The system MUST support converting a single specified PDF and batch-converting all PDFs in the input directory.
- **FR-004**: The system MUST overwrite existing output files with the same name by default.
- **FR-005**: The system MUST produce a human-readable summary at the end with counts of total files, successes, and failures.
- **FR-006**: The system MUST record a per-file error message for each failed conversion in the summary output.
- **FR-007**: The system MUST ignore non-PDF files in the input directory without treating them as failures.
- **FR-008**: The system MUST complete without crashing when encountering large files, encrypted PDFs, or corrupted PDFs; such files MUST be reported as failures with clear reasons.

### Key Entities *(include if feature involves data)*

- **Document**: A source PDF to be converted (attributes: filename, path, size).
- **OutputArtifact**: A generated Markdown file (attributes: filename, path, size, sourceDocument).
- **ConversionJob**: A run that processes one or more Documents (attributes: startTime, endTime, total, succeeded, failed, messages[]).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single typical PDF converts to Markdown successfully, producing a readable, non-empty Markdown file.
- **SC-002**: Batch conversion handles multiple PDFs in one run, producing Markdown files for all valid inputs and reporting failures for invalid ones.
- **SC-003**: 95% of valid, non-encrypted PDFs produce non-empty Markdown outputs without manual intervention.
- **SC-004**: Users can configure and run conversion end-to-end without reading source code, using a single documented entry point.

## Assumptions

- Input and output directories are accessible on local disk at run time.
- Overwrite behavior is acceptable as a default for initial setup; future features may add alternative strategies.
- No authentication or permissions model is required for file access beyond OS-level permissions.


