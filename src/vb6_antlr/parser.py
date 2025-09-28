"""Core parsing orchestrator built on top of the generated ANTLR grammar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from antlr4 import InputStream  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency for scaffolding

    class InputStream:  # type: ignore[no-redef]
        """Minimal stand-in used when the ANTLR runtime is absent."""

        def __init__(self, data: str) -> None:
            self.data = data


from .config import ConverterConfig


@dataclass(slots=True)
class ParseJob:
    """Represents a unit of work for the parser."""

    source_path: Path
    text: str


@dataclass(slots=True)
class ParserOutput:
    """Lightweight wrapper for parser results awaiting IR construction."""

    source_path: Path
    parse_tree: object
    diagnostics: list[str]


class VB6ParserService:
    """Coordinates lexer/parser invocations and collects diagnostics."""

    def __init__(self, config: ConverterConfig) -> None:
        self._config = config

    def build_jobs(self, inputs: Iterable[Path] | None = None) -> list[ParseJob]:
        """Prepare parse jobs from disk or pre-supplied sources."""

        paths = list(inputs) if inputs is not None else self._config.resolve_inputs()
        jobs: list[ParseJob] = []
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            jobs.append(ParseJob(source_path=path, text=text))
        return jobs

    def parse(self, jobs: Iterable[ParseJob]) -> list[ParserOutput]:
        """Execute ANTLR parsing for the provided jobs.

        The actual lexer/parser integration will be fleshed out once the
        generated classes are wired in. For now we hold the raw `InputStream`
        as the parse tree placeholder so downstream layers can be scaffolded
        against a stable interface.
        """

        outputs: list[ParserOutput] = []
        for job in jobs:
            stream = InputStream(job.text)
            outputs.append(
                ParserOutput(
                    source_path=job.source_path,
                    parse_tree=stream,  # TODO: replace with real parse tree
                    diagnostics=[],
                )
            )
        return outputs
