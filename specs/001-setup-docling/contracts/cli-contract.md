# CLI Contract: pdf-rag-ai parse

## Command

```
pdf-rag parse --input <INPUT_DIR> --output <OUTPUT_DIR> [--json]
```

## Arguments
- `--input`, `-i` (required): Absolute or relative path to directory containing source PDFs.
- `--output`, `-o` (required): Absolute or relative path to directory where Markdown files will be written. Created if missing.
- `--json` (optional): Emit machine-readable JSON summary to stdout. Human-readable summary is default.

## Behavior
- Converts each `*.pdf` (case-insensitive) under `--input` (non-recursive v1) to a corresponding `*.md` in `--output` with the same base filename.
- Overwrites existing outputs by default.
- Non-PDF files are ignored.

## Exit Codes
- `0`: Completed; conversions may include failures but summary reflects counts.
- `1`: Invalid arguments or I/O errors (e.g., missing input directory, cannot create output directory).

## Human-readable Summary (default)
```
Processed: <total> | Succeeded: <succeeded> | Failed: <failed>
- <filename.pdf>: OK -> <filename.md>
- <bad.pdf>: ERROR: <reason>
```

## JSON Summary (`--json`)
```json
{
  "startTime": "2025-10-30T12:34:56Z",
  "endTime": "2025-10-30T12:35:10Z",
  "durationMs": 14000,
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "doclingVersion": "1.x.y",
  "results": [
    {
      "document": { "filename": "a.pdf", "path": "...", "numPages": 12 },
      "status": "success",
      "output": { "filename": "a.md", "path": "...", "sizeBytes": 10240 }
    },
    {
      "document": { "filename": "bad.pdf", "path": "..." },
      "status": "failure",
      "message": "Encrypted PDF not supported"
    }
  ]
}
```

## Notes
- Future options (out of scope for v1): recursive directory walk, glob filters, parallelism, dry-run.

