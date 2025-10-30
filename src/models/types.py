"""Data models for PDF-to-Markdown conversion."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ConversionStatus(str, Enum):
    """Status of a PDF conversion operation."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class Document:
    """Represents a source PDF document."""

    filename: str
    path: str
    sizeBytes: Optional[int] = None
    numPages: Optional[int] = None

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
    sizeBytes: Optional[int] = None
    sourceDocument: Optional[Document] = None

    def __post_init__(self):
        """Validate output artifact attributes."""
        if not self.filename.lower().endswith(".md"):
            raise ValueError(f"Output filename must have .md extension: {self.filename}")


@dataclass
class ConversionResult:
    """Result of converting a single PDF document."""

    document: Document
    status: ConversionStatus
    message: Optional[str] = None
    output: Optional[OutputArtifact] = None

    def __post_init__(self):
        """Validate conversion result consistency."""
        if self.status == ConversionStatus.SUCCESS and self.output is None:
            raise ValueError("ConversionResult with SUCCESS status must have output")
        if self.status == ConversionStatus.FAILURE and self.message is None:
            raise ValueError("ConversionResult with FAILURE status must have message")


@dataclass
class ConversionJob:
    """Represents a batch conversion job processing multiple PDFs."""

    startTime: datetime
    endTime: Optional[datetime] = None
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[ConversionResult] = field(default_factory=list)
    doclingVersion: Optional[str] = None

    @property
    def durationMs(self) -> Optional[int]:
        """Calculate job duration in milliseconds."""
        if self.endTime is None:
            return None
        delta = self.endTime - self.startTime
        return int(delta.total_seconds() * 1000)

    def add_result(self, result: ConversionResult) -> None:
        """Add a conversion result and update counters."""
        self.results.append(result)
        self.total += 1
        if result.status == ConversionStatus.SUCCESS:
            self.succeeded += 1
        else:
            self.failed += 1

