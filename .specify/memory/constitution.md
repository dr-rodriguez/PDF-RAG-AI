<!--
Sync Impact Report
- Version change: (none) → 1.0.0
- Modified principles: N/A (initial ratification)
- Added sections: Core Principles (5), Additional Constraints, Development Workflow, Governance
- Removed sections: None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check references remain compatible)
  - ✅ .specify/templates/spec-template.md (No conflicting mandatory sections)
  - ✅ .specify/templates/tasks-template.md (Task grouping by stories aligns)
  - ⚠ .specify/templates/commands/ (directory not present in repo)
- Follow-up TODOs: None
-->

# PDF RAG AI Constitution

## Core Principles

### I. Deterministic PDF Parsing via Docling (NON-NEGOTIABLE)
All PDF ingestion MUST use Docling to convert PDFs to Markdown. The Docling
version MUST be pinned. Generated Markdown and intermediate artifacts MUST be
committed or reproducibly generated, and MUST NOT be manually edited.

Rationale: Ensures consistent, auditable parsing that is reproducible across
environments and over time.

### II. Local LLM Execution with Ollama
The LLM inference MUST run locally via Ollama by default. Model selection and
parameters MUST be configurable. Remote model calls MAY be enabled explicitly
by users but are DISABLED by default.

Rationale: Preserves privacy, reduces cost, and simplifies ops.

### III. Testable, Stage-Oriented Pipeline
The pipeline MUST be organized into clear stages: parse → chunk → embed →
index → query. Each stage MUST have unit and/or integration tests. Chunking
and sampling MUST be seedable to enable deterministic tests.

Rationale: Enables isolated verification, easier debugging, and safer changes.

### IV. CLI-First with Text I/O
Each stage MUST expose a CLI. Inputs via stdin/args; normal output to stdout;
errors to stderr.

Rationale: Improves composability, scripting, and observability.

### V. Observability and Versioning Discipline
The system MUST emit structured logs with stage, timing, and counts (pages,
chunks, tokens). All generated chunks MUST carry provenance (source file,
page/section). Breaking changes to data or CLIs MUST bump MAJOR; additive
changes MINOR; fixes PATCH (Semantic Versioning).

Rationale: Traceability for RAG quality and stable consumer contracts.

## Additional Constraints

- Data Privacy: Inputs remain local by default; no external calls unless
  explicitly configured.
- Scale: Large PDFs MUST be processed in streaming or batched fashion to avoid
  memory exhaustion.
- Pluggability: Vector store and embedding model MUST be replaceable behind a
  small adapter surface.
- Reproducibility: End-to-end runs MUST be replayable given the same inputs,
  config, and pinned dependency set.
- Code Simplicity: Scripts MUST be kept simple and appropriate for
  intermediate-level Python developers. Avoid over-engineering and complex
  abstractions that hinder readability and maintainability.

## Development Workflow

- Reviews MUST verify compliance with Core Principles.
- Tests MUST pass for affected stages before merge.
- CLI contracts are treated as public APIs; changes follow versioning rules.
- Runtime guidance belongs in `README.md` and CLI `--help` output.

## Governance

- The Constitution supersedes conflicting practices in this repo.
- Amendments: Propose via PR with a Sync Impact Report, migration notes, and
  version bump rationale. Approval required via normal review.
- Versioning: Semantic Versioning for this Constitution: MAJOR for breaking
  governance changes; MINOR for new or materially expanded sections; PATCH for
  clarifications.
- Compliance: All PRs MUST include a Constitution Check in plans/specs where
  applicable.

**Version**: 1.1.0 | **Ratified**: 2025-10-30 | **Last Amended**: 2025-10-30
