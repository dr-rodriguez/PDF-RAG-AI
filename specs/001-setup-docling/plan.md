# Implementation Plan: PDF-to-Markdown Conversion Setup

**Branch**: `001-setup-docling` | **Date**: 2025-10-30 | **Spec**: specs/001-setup-docling/spec.md
**Input**: Feature specification from `/specs/001-setup-docling/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Convert PDFs in a user-specified input directory to Markdown files in an output directory using Docling via a CLI entry point (`--input`, `--output`). Initial implementation focuses on deterministic parsing (pinned Docling) and a simple, testable pipeline for single and batch modes with clear summary reporting.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13  
**Primary Dependencies**: Docling, Click for CLI  
**Storage**: Local filesystem for inputs/outputs; no DB  
**Testing**: pytest  
**Target Platform**: Local execution on Windows/macOS/Linux  
**Project Type**: Single project (CLI-first utilities and services)  
**Performance Goals**: Complete typical PDFs (<50MB, <500 pages) without timeouts; large files may be slower
**Constraints**: Deterministic outputs; reproducible runs with pinned dependencies; overwrite outputs by default; structured summary logging  
**Scale/Scope**: Single CLI, small codebase focused on parse stage; future stages (chunk, embed, index, query) out of scope for this feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from `/.specify/memory/constitution.md`:

- Docling must be used for parsing and version must be pinned. Status: PASS (pin exact version at implementation time; lockfile records it; initial constraint `>=1,<2`).
- CLI-first with text I/O; JSON output should be supported. Status: PASS (planned CLI with human-readable summary; JSON mode to be added in scope confirmation).
- Testable, stage-oriented pipeline. Status: PASS for parse stage; chunk/embed/index/query deferred.
- Observability and provenance. Status: PASS (structured summary; capture source filename/page counts when available from Docling).
- Local execution defaults. Status: PASS (no remote calls in this feature).

Gate evaluation: PASS post-design. JSON output flag designed; Docling pinning strategy defined (exact version to be pinned during dependency add, recorded in `uv.lock`).

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
│   └── main.py           # CLI entry point (Typer/Click)
├── services/
│   └── converter.py      # Docling integration and orchestration
├── models/
│   └── types.py          # Data classes for results/summary
└── lib/
    └── io_utils.py       # Filesystem helpers, validation

tests/
├── unit/
│   ├── test_converter.py
│   └── test_io_utils.py
└── contract/
    └── test_cli.py
```

**Structure Decision**: Single-project CLI-first layout to support deterministic parsing and testability.
