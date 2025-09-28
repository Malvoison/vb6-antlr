"""JSON serialization utilities for VB6 IR modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..ir import IRModule


class JsonSerializer:
    """Serialize IR modules into JSON strings or files."""

    def dumps(self, module: IRModule, *, indent: int = 2) -> str:
        """Return a JSON string for the supplied module."""

        payload = {
            "schemaVersion": module.body.get("schemaVersion", "1.0.0"),
            "source": str(module.source_path),
            "body": module.body,
            "diagnostics": [d.to_dict() for d in module.diagnostics],
        }
        return json.dumps(payload, indent=indent)

    def dump_to_path(
        self, module: IRModule, destination: Path, *, indent: int = 2
    ) -> None:
        """Write the serialized module to disk."""

        destination.write_text(self.dumps(module, indent=indent), encoding="utf-8")

    def dump_many(self, modules: Iterable[IRModule], output_dir: Path) -> list[Path]:
        """Serialize multiple modules to the provided directory."""

        output_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for module in modules:
            target = output_dir / f"{module.source_path.stem}.json"
            self.dump_to_path(module, target)
            written.append(target)
        return written
