"""CLI entry point for PDF-to-Markdown conversion."""

import json
import sys
from pathlib import Path

import click

from src.lib.io_utils import setup_logging
from src.services.converter import convert_batch, format_job_summary, format_job_summary_json


@click.group()
def cli():
    """PDF-to-Markdown conversion tool."""
    setup_logging()


@cli.command()
@click.option(
    "--input",
    "-i",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Input directory containing PDF files",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Output directory for Markdown files",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Emit JSON summary instead of human-readable format",
)
def parse(input: str, output: str, json_output: bool):
    """
    Convert PDF files in input directory to Markdown files in output directory.

    Processes all .pdf files (case-insensitive) in the input directory
    and writes corresponding .md files to the output directory.
    """
    try:
        # Ensure output directory exists
        Path(output).mkdir(parents=True, exist_ok=True)

        # Convert all PDFs
        job = convert_batch(input, output)

        # Output summary
        if json_output:
            summary = format_job_summary_json(job)
            click.echo(json.dumps(summary, indent=2))
        else:
            summary = format_job_summary(job)
            click.echo(summary)

        # Exit with error code if there were failures
        if job.failed > 0:
            sys.exit(1)
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

