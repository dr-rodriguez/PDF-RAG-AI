# Quickstart: PDF-to-Markdown Conversion

## Prerequisites
- Python 3.13+
- `uv` installed (or use `pip`)

## Install
```bash
# from repo root
uv sync
```

## Usage
```bash
# Single run (non-recursive v1)
python -m src.cli.main --input ./input --output ./output

# JSON summary
python -m src.cli.main -i ./input -o ./output --json
```

## Expected Behavior
- Converts every `*.pdf` in `--input` to `*.md` in `--output` (overwrite by default).
- Prints a summary with total, succeeded, failed; `--json` prints machine-readable summary.

## Troubleshooting
- Ensure `--input` exists and is readable.
- Ensure `--output` is writable; it will be created if missing.
- For encrypted/corrupted PDFs, outputs a failure entry with a reason.
