"""Data models for PDF-to-Markdown conversion."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ConversionStatus(str, Enum):
    """Status of a PDF conversion operation."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class Document:
    """Represents a source PDF document."""

    filename: str
    path: str
    size_bytes: int | None = None
    num_pages: int | None = None

    def __post_init__(self):
        """Validate document attributes."""
        if not self.filename.lower().endswith(".pdf"):
            raise ValueError(f"Document filename must have .pdf extension: {self.filename}")
        if not Path(self.path).exists():
            raise ValueError(f"Document path does not exist: {self.path}")


@dataclass
class OutputArtifact:
    """Represents a generated Markdown output file."""

    filename: str
    path: str
    size_bytes: int | None = None
    source_document: Document | None = None

    def __post_init__(self):
        """Validate output artifact attributes."""
        if not self.filename.lower().endswith(".md"):
            raise ValueError(f"Output filename must have .md extension: {self.filename}")


@dataclass
class ConversionResult:
    """Result of converting a single PDF document."""

    document: Document
    status: ConversionStatus
    message: str | None = None
    output: OutputArtifact | None = None

    def __post_init__(self):
        """Validate conversion result consistency."""
        if self.status == ConversionStatus.SUCCESS and self.output is None:
            raise ValueError("ConversionResult with SUCCESS status must have output")
        if self.status == ConversionStatus.FAILURE and self.message is None:
            raise ValueError("ConversionResult with FAILURE status must have message")


@dataclass
class ConversionJob:
    """Represents a batch conversion job processing multiple PDFs."""

    start_time: datetime
    end_time: datetime | None = None
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[ConversionResult] = field(default_factory=list)
    docling_version: str | None = None

    @property
    def duration_ms(self) -> int | None:
        """Calculate job duration in milliseconds."""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() * 1000)

    def add_result(self, result: ConversionResult) -> None:
        """Add a conversion result and update counters."""
        self.results.append(result)
        self.total += 1
        if result.status == ConversionStatus.SUCCESS:
            self.succeeded += 1
        else:
            self.failed += 1


# RAG Configuration Models


@dataclass
class ModelConfiguration:
    """Configuration for Ollama embedding and query models."""

    embedding_model: str
    query_model: str
    ollama_base_url: str = "http://localhost:11434"

    def __post_init__(self):
        """Validate model configuration."""
        if not self.embedding_model:
            raise ValueError("embedding_model must be non-empty")
        if not self.query_model:
            raise ValueError("query_model must be non-empty")


@dataclass
class ChunkingConfiguration:
    """Configuration for text chunking parameters."""

    chunk_size: int = 1000
    chunk_overlap: int = 200

    def __post_init__(self):
        """Validate chunking configuration."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive integer > 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative integer")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")


@dataclass
class RetrievalConfiguration:
    """Configuration for retrieval parameters."""

    top_k: int = 4
    min_similarity: float = 0.0

    def __post_init__(self):
        """Validate retrieval configuration."""
        if self.top_k <= 0:
            raise ValueError("top_k must be positive integer > 0")
        if not 0.0 <= self.min_similarity <= 1.0:
            raise ValueError("min_similarity must be float in range [0.0, 1.0]")


@dataclass
class VectorDatabaseConfiguration:
    """Configuration for vector database."""

    collection_name: str = "documents"

    def __post_init__(self):
        """Validate vector database configuration."""
        if not self.collection_name:
            raise ValueError("collection_name must be non-empty string")


# RAG Processing Models


@dataclass
class DocumentChunk:
    """Represents a chunk of document content with embedding."""

    id: str
    content: str
    source_file: str
    chunk_index: int
    embedding: list[float] | None = None
    metadata: dict | None = None

    def __post_init__(self):
        """Validate document chunk attributes."""
        if not self.content:
            raise ValueError("content must be non-empty string")
        if not self.source_file:
            raise ValueError("source_file must be non-empty string")
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be non-negative integer")


@dataclass
class VectorDatabase:
    """Represents a vector database instance."""

    location: str
    store_type: str = "ChromaDB"
    collection_name: str = "documents"

    def __post_init__(self):
        """Validate vector database attributes."""
        if not self.location:
            raise ValueError("location must be non-empty string")


class ProcessingStatus(str, Enum):
    """Status of a file processing operation."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class ProcessingResult:
    """Result of processing a single Markdown file."""

    source_file: str
    status: ProcessingStatus
    chunks_added: int = 0
    chunks_skipped: int = 0
    message: str | None = None
    processing_time_ms: int = 0

    def __post_init__(self):
        """Validate processing result consistency."""
        if self.status == ProcessingStatus.FAILURE and not self.message:
            raise ValueError("ProcessingResult with FAILURE status must have message")


@dataclass
class ProcessingJob:
    """Represents a batch processing job for multiple files."""

    start_time: datetime
    end_time: datetime | None = None
    total_files: int = 0
    succeeded: int = 0
    failed: int = 0
    total_chunks_added: int = 0
    results: list[ProcessingResult] = field(default_factory=list)

    @property
    def duration_ms(self) -> int | None:
        """Calculate job duration in milliseconds."""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() * 1000)


# RAG Query Models


@dataclass
class Query:
    """Represents a query to the vector database."""

    text: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate query attributes."""
        if not self.text:
            raise ValueError("text must be non-empty string")


@dataclass
class QueryResponse:
    """Response from a vector database query."""

    answer: str
    retrieved_chunks: int = 0

    def __post_init__(self):
        """Validate query response attributes."""
        if not self.answer:
            raise ValueError("answer must be non-empty string")