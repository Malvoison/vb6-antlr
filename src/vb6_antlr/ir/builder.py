"""Placeholder IR builder that will translate parse trees into JSON-ready nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..parser import ParserOutput


@dataclass(slots=True)
class IRModule:
    """Minimal IR stub capturing the parsed module and metadata."""

    source_path: Path
    body: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


class IRBuilder:
    """Transforms raw parser output into the intermediate representation."""

    def build(self, output: ParserOutput) -> IRModule:
        """Translate a single parser output into an IR module."""

        body = {
            "schemaVersion": "1.0.0",
            "notes": "IR generation not yet implemented",
        }
        return IRModule(
            source_path=output.source_path, body=body, diagnostics=output.diagnostics
        )
