# Phase 0 Research: PDF-to-Markdown Conversion Setup

## Docling Version Pinning

- Decision: Pin Docling to the latest stable at implementation time and record the exact version in `uv.lock`. Initial target: `docling>=1.0,<2.0` with a concrete pin (e.g., `docling==1.x.y`).
- Rationale: Ensures deterministic, reproducible parsing while allowing security/bugfix updates via deliberate repins.
- Alternatives considered:
  - Float on latest: Rejected due to non-determinism and breakage risk.
  - Pin to an older minor: Acceptable but offers no benefit unless a known regression exists.

## CLI Framework (Click vs Typer vs argparse)

- Decision: Use Click.
- Rationale: You prefer Click and are familiar with it; robust, mature CLI framework with excellent composability and ecosystem.
- Alternatives considered:
  - Typer: Nice type-hint ergonomics, but adds another abstraction over Click and is unnecessary given familiarity with Click.
  - argparse: Standard library, minimal deps, but verbose and less ergonomic for growth.

## Output Modes (Human-readable and JSON)

- Decision: Support both human-readable summary (default) and JSON via `--json` flag for machine consumption.
- Rationale: Aligns with Constitution IV (CLI-first with text I/O and JSON). Enables scripting and observability.
- Alternatives considered:
  - Human-readable only: Simpler but blocks automation.
  - JSON only: Poor UX for humans.

## Performance and Resource Handling

- Decision: Process files sequentially for simplicity; ensure graceful handling for large PDFs (streaming where Docling supports it). No parallelism in v1.
- Rationale: Keeps initial implementation simple and robust; avoids concurrency edge cases. Upgrade path exists if needed.
- Alternatives considered:
  - Parallel conversion: Faster on many files but adds complexity to error handling and logging.

## Logging and Observability

- Decision: Use `logging` (stdlib) with structured keys in summary. Include counts (total, succeeded, failed) and per-file outcomes. Emit provenance (source filename; pages if available).
- Rationale: Satisfies Constitution V with minimal dependencies.
- Alternatives considered:
  - Structured logging libraries: More features but unnecessary for v1 scope.

## Filesystem Semantics

- Decision: Overwrite outputs by default (per spec). Ignore non-PDF files. Validate `--input` exists and `--output` is creatable.
- Rationale: Matches FR-004/007 and keeps UX predictable.
- Alternatives considered:
  - Fail on existing outputs: Conflicts with FR-004.

## Summary of Resolved Clarifications

- Docling: pin exact version in project lockfile; initial constraint `>=1,<2` with a concrete pin during implementation.
- CLI: Click.
- Output: Add `--json` for machine-readable summary; human-readable default.
- Performance: Sequential processing, large-file friendly; no parallelism.
- Logging: stdlib `logging`, structured summary emitted at end.

