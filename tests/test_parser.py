from __future__ import annotations


from vb6_antlr.config import ConverterConfig
from vb6_antlr.parser import VB6ParserService


def test_parser_generates_parse_tree(tmp_path) -> None:
    source = tmp_path / "module.bas"
    source.write_text(
        """
Attribute VB_Name = "Module1"
Option Explicit
Public Sub Foo()
    Dim x As Integer
End Sub
""".strip(),
        encoding="utf-8",
    )

    config = ConverterConfig.from_paths([source])
    service = VB6ParserService(config)

    jobs = service.build_jobs()
    outputs = service.parse(jobs)

    assert len(outputs) == 1
    result = outputs[0]
    assert result.parse_tree is not None
    assert result.diagnostics == []
