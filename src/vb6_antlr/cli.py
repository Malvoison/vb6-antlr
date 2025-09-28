"""Command-line entry point scaffolding."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .config import ConverterConfig
from .ir import IRBuilder
from .parser import VB6ParserService
from .serialization import JsonSerializer


def build_argument_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser used by `main`."""

    parser = argparse.ArgumentParser(description="VB6 to JSON converter")
    parser.add_argument("inputs", nargs="+", help="VB6 files or directories to process")
    parser.add_argument(
        "--output", type=Path, default=None, help="Directory for JSON output"
    )
    parser.add_argument(
        "--schema-version", default="1.0.0", help="Schema version for output JSON"
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop after the first fatal error"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns an exit code for the host process."""

    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    config = ConverterConfig.from_paths(
        args.inputs,
        output_dir=args.output,
        schema_version=args.schema_version,
    ).with_updates(fail_fast=args.fail_fast)

    service = VB6ParserService(config)
    jobs = service.build_jobs()
    parser_outputs = service.parse(jobs)

    builder = IRBuilder()
    modules = [builder.build(output) for output in parser_outputs]

    serializer = JsonSerializer()
    if config.output_dir:
        serializer.dump_many(modules, config.output_dir)
    else:
        for module in modules:
            print(serializer.dumps(module))

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
