"""CLI entry point for PDF-to-Markdown conversion and RAG processing."""

import sys
from pathlib import Path

import click

from src.lib.config import load_config
from src.lib.io_utils import setup_logging
from src.lib.ollama_utils import (
    get_model_validation_error,
    validate_model_available,
    validate_ollama_connection,
)
from src.models.types import ProcessingStatus, Query
from src.services.converter import convert_batch, format_job_summary
from src.services.rag_service import process_batch, query


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
def parse(input: str, output: str):
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


@cli.command()
@click.argument("path", type=click.Path(exists=False))
@click.option(
    "--db-path",
    "-d",
    default="data/db",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Path to vector database directory (default: data/db)",
)
def process(path: str, db_path: str):
    """
    Process Markdown files into vector database.

    Processes Markdown files from PATH (file or directory) and stores chunked
    content with embeddings in the vector database at --db-path.
    """
    try:
        # Validate path exists
        path_obj = Path(path)
        if not path_obj.exists():
            click.echo(f"Error: Path does not exist: {path}", err=True)
            sys.exit(1)

        # Load configuration
        try:
            model_config, chunking_config, retrieval_config, vector_db_config = load_config()
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

        # Validate Ollama connection
        if not validate_ollama_connection(model_config.ollama_base_url):
            click.echo(
                f"Error: Cannot connect to Ollama at {model_config.ollama_base_url}. "
                "Ensure Ollama is running.",
                err=True,
            )
            sys.exit(1)

        # Validate embedding model availability
        if not validate_model_available(model_config.embedding_model, model_config.ollama_base_url):
            error_msg = get_model_validation_error(
                model_config.embedding_model, model_config.ollama_base_url
            )
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        # Ensure database directory exists
        db_path_obj = Path(db_path)
        try:
            db_path_obj.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            click.echo(f"Error: Failed to create database directory: {db_path}: {e}", err=True)
            sys.exit(1)

        # Process files
        click.echo("Processing Markdown files...")
        job = process_batch(path, db_path, model_config, chunking_config, vector_db_config)

        # Format and display results
        output_lines = []
        for result in job.results:
            if result.status == ProcessingStatus.SUCCESS:
                skipped_msg = ""
                if result.chunks_skipped > 0:
                    skipped_msg = f" ({result.chunks_skipped} skipped - duplicates)"
                output_lines.append(
                    f"- {Path(result.source_file).name}: "
                    f"Added {result.chunks_added} chunks{skipped_msg}"
                )
            else:
                output_lines.append(
                    f"- {Path(result.source_file).name}: ERROR: {result.message or 'Unknown error'}"
                )

        if output_lines:
            click.echo("\n".join(output_lines))

        # Summary
        total_skipped = sum(r.chunks_skipped for r in job.results)
        click.echo(
            f"\nSummary: Processed {job.total_files} files | "
            f"Added {job.total_chunks_added} chunks | "
            f"Skipped {total_skipped} chunks"
        )
        click.echo(f"Database location: {db_path}")

        # Exit with error code if there were failures
        if job.failed > 0:
            sys.exit(1)
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Failed to process file '{path}': {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query_text", type=str)
@click.option(
    "--db-path",
    "-d",
    default="data/db",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Path to vector database directory (default: data/db)",
)
def query_cmd(query_text: str, db_path: str):
    """
    Query the vector database with a natural language question.

    Processes QUERY_TEXT through the vector database and returns an answer
    based on the stored document content.
    """
    try:
        # Validate query text
        if not query_text or not query_text.strip():
            click.echo("Error: Query text cannot be empty", err=True)
            sys.exit(1)

        # Load configuration
        try:
            model_config, chunking_config, retrieval_config, vector_db_config = load_config()
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

        # Validate database path exists (check before model validation for better error messages)
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            click.echo(
                f"Error: Vector database not found at '{db_path}'. Run 'pdf-rag process' first.",
                err=True,
            )
            sys.exit(1)

        # Check if database directory is empty or uninitialized
        # ChromaDB creates chroma.sqlite3 or collection directories when initialized
        db_files = list(db_path_obj.iterdir())
        is_empty_db = len(db_files) == 0
        # Check for ChromaDB signature files
        has_chromadb_files = any(
            f.name == "chroma.sqlite3" or (f.is_dir() and f.name.startswith("chroma"))
            for f in db_files
        )
        if is_empty_db or not has_chromadb_files:
            click.echo(
                "Error: Vector database is empty. Process some documents first.",
                err=True,
            )
            sys.exit(1)

        # Validate Ollama connection
        if not validate_ollama_connection(model_config.ollama_base_url):
            click.echo(
                f"Error: Cannot connect to Ollama at {model_config.ollama_base_url}. "
                "Ensure Ollama is running.",
                err=True,
            )
            sys.exit(1)

        # Validate query model availability
        if not validate_model_available(model_config.query_model, model_config.ollama_base_url):
            error_msg = get_model_validation_error(
                model_config.query_model, model_config.ollama_base_url
            )
            click.echo(f"Error: {error_msg}", err=True)
            sys.exit(1)

        # Create query object and process
        query_obj = Query(text=query_text)
        response = query(
            query_obj,
            db_path,
            model_config,
            retrieval_config,
            vector_db_config,
        )

        # Output only the answer text (per CLI contract)
        click.echo(response.answer)
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        error_msg = str(e)
        # Map specific errors to contract messages
        if "Vector database not found" in error_msg:
            click.echo(
                "Error: Vector database not found at '<db-path>'. Run 'pdf-rag process' first.",
                err=True,
            )
        elif "Vector database is empty" in error_msg:
            click.echo("Error: Vector database is empty. Process some documents first.", err=True)
        elif "not found" in error_msg.lower() and "ollama" in error_msg.lower():
            click.echo(f"Error: {error_msg}", err=True)
        elif "No relevant chunks found" in error_msg:
            click.echo(f"Error: {error_msg}", err=True)
        else:
            click.echo(f"Error: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Query failed: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
