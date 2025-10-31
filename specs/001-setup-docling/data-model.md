# Data Model: PDF-to-Markdown Conversion

## Entities

### Document
- Attributes:
  - `filename`: string (base name, e.g., `report.pdf`)
  - `path`: string (absolute path to input file)
  - `sizeBytes`: integer (optional)
  - `numPages`: integer (optional, if available from Docling)
- Validation:
  - Extension must be `.pdf` (case-insensitive)
  - Path must exist and be readable

### OutputArtifact
- Attributes:
  - `filename`: string (base name, e.g., `report.md`)
  - `path`: string (absolute path to output file)
  - `sizeBytes`: integer (optional)
  - `sourceDocument`: reference to `Document`
- Validation:
  - Resides under specified output directory
  - Overwritten by default if exists

### ConversionResult
- Attributes:
  - `document`: `Document`
  - `status`: enum { `success`, `failure` }
  - `message`: string (on failure)
  - `output`: `OutputArtifact` (on success)

### ConversionJob
- Attributes:
  - `startTime`: datetime (ISO 8601)
  - `endTime`: datetime (ISO 8601)
  - `total`: integer
  - `succeeded`: integer
  - `failed`: integer
  - `results`: list<`ConversionResult`>
- Derived:
  - `durationMs`

## Relationships
- A `ConversionJob` processes many `Document`s and yields zero or one `OutputArtifact` per `Document`.
- An `OutputArtifact` references exactly one `Document`.

## State Transitions
- `Document` → parse via Docling → `OutputArtifact` (success) or error (`ConversionResult.status=failure`).

## Notes
- Provenance: retain source filename (and pages if available) in emitted metadata.
- Determinism: pin Docling version; record version and tool metadata in job summary for traceability.

