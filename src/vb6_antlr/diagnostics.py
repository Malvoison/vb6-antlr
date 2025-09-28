"""Common diagnostic structures shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Severity = Literal["info", "warning", "error"]


@dataclass(slots=True)
class Diagnostic:
    """Represents a message produced during parsing or transformation."""

    severity: Severity
    message: str
    source_path: Path | None = None
    line: int | None = None
    column: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly dictionary representation."""

        return {
            "severity": self.severity,
            "message": self.message,
            "sourcePath": str(self.source_path) if self.source_path else None,
            "line": self.line,
            "column": self.column,
        }
