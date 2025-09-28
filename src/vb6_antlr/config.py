"""Configuration primitives for the VB6 parser toolchain."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_SCHEMA_VERSION = "1.0.0"


@dataclass(slots=True)
class ConverterConfig:
    """High-level configuration for a conversion run."""

    inputs: Sequence[Path]
    output_dir: Path | None = None
    schema_version: str = DEFAULT_SCHEMA_VERSION
    fail_fast: bool = False
    include_forms: bool = True
    include_comments: bool = True
    extra_options: dict[str, str] = field(default_factory=dict)

    def resolve_inputs(self) -> list[Path]:
        """Expand provided inputs into a sorted list of VB6 source files."""

        files: list[Path] = []
        allowed_suffixes = {".bas", ".cls", ".frm"}
        for path in self.inputs:
            if path.is_dir():
                files.extend(
                    sorted(
                        p
                        for p in path.rglob("*")
                        if p.suffix.lower() in allowed_suffixes
                    )
                )
            elif path.suffix.lower() in allowed_suffixes:
                files.append(path)
        return sorted({p.resolve() for p in files})

    @classmethod
    def from_paths(
        cls,
        inputs: Iterable[str | Path],
        *,
        output_dir: str | Path | None = None,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
    ) -> "ConverterConfig":
        """Convenience constructor used by CLI/bootstrap code."""

        resolved_inputs = [Path(p) for p in inputs]
        resolved_output = Path(output_dir) if output_dir is not None else None
        return cls(
            inputs=resolved_inputs,
            output_dir=resolved_output,
            schema_version=schema_version,
        )

    def with_updates(self, **overrides: object) -> "ConverterConfig":
        """Return a copy of the configuration with selective overrides."""

        data = asdict(self)
        data.update(overrides)
        return ConverterConfig(**data)  # type: ignore[arg-type]
