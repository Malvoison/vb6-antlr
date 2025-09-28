"""Core parsing orchestrator built on top of the generated ANTLR grammar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from antlr4 import CommonTokenStream, InputStream, ParserRuleContext  # type: ignore[import]
from antlr4.error.ErrorListener import ErrorListener  # type: ignore[import]
from antlr4.error.Errors import RecognitionException  # type: ignore[import]

from vb6_grammar.grammars.VisualBasic6Lexer import VisualBasic6Lexer  # type: ignore[import]
from vb6_grammar.grammars.VisualBasic6Parser import VisualBasic6Parser  # type: ignore[import]

from .config import ConverterConfig
from .diagnostics import Diagnostic, Severity


@dataclass(slots=True)
class ParseJob:
    """Represents a unit of work for the parser."""

    source_path: Path
    text: str


@dataclass(slots=True)
class ParserOutput:
    """Lightweight wrapper for parser results awaiting IR construction."""

    source_path: Path
    parse_tree: ParserRuleContext | None
    diagnostics: list[Diagnostic]


class CollectingErrorListener(ErrorListener):
    """Error listener used to accumulate diagnostics produced by ANTLR."""

    def __init__(self, source_path: Path, severity: Severity = "error") -> None:
        super().__init__()
        self._source_path = source_path
        self._severity: Severity = severity
        self.diagnostics: list[Diagnostic] = []

    def syntaxError(  # type: ignore[override]
        self,
        recognizer,
        offendingSymbol,
        line: int,
        column: int,
        msg: str,
        e: RecognitionException | None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(
                severity=self._severity,
                message=msg,
                source_path=self._source_path,
                line=line,
                column=column,
            )
        )


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
        """Execute ANTLR parsing for the provided jobs."""

        outputs: list[ParserOutput] = []
        for job in jobs:
            lexer_listener = CollectingErrorListener(job.source_path)
            parser_listener = CollectingErrorListener(job.source_path)

            input_stream = InputStream(job.text)
            lexer = VisualBasic6Lexer(input_stream)
            lexer.removeErrorListeners()
            lexer.addErrorListener(lexer_listener)

            token_stream = CommonTokenStream(lexer)
            parser = VisualBasic6Parser(token_stream)
            parser.buildParseTrees = True
            parser.removeErrorListeners()
            parser.addErrorListener(parser_listener)

            try:
                tree = parser.startRule()
            except RecognitionException as exc:  # pragma: no cover - defensive guard
                parser_listener.syntaxError(
                    parser, None, exc.line, exc.column, exc.msg or str(exc), exc
                )
                tree = None
            except Exception as exc:  # pragma: no cover - defensive guard
                parser_listener.diagnostics.append(
                    Diagnostic(
                        severity="error",
                        message=str(exc),
                        source_path=job.source_path,
                    )
                )
                tree = None

            diagnostics = lexer_listener.diagnostics + parser_listener.diagnostics
            outputs.append(
                ParserOutput(
                    source_path=job.source_path,
                    parse_tree=tree,
                    diagnostics=diagnostics,
                )
            )
        return outputs
