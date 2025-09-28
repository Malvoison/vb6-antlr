from __future__ import annotations

from vb6_antlr.config import ConverterConfig
from vb6_antlr.ir import IRBuilder
from vb6_antlr.parser import ParserOutput, VB6ParserService


def build_ir_for(source_text: str, tmp_path):
    source_file = tmp_path / "module.bas"
    source_file.write_text(source_text, encoding="utf-8")

    config = ConverterConfig.from_paths([source_file])
    service = VB6ParserService(config)
    jobs = service.build_jobs()
    outputs = service.parse(jobs)

    builder = IRBuilder()
    return builder.build(outputs[0])


def test_ir_builder_extracts_module_metadata(tmp_path) -> None:
    ir_module = build_ir_for(
        """
Attribute VB_Name = "SampleModule"
Option Explicit
Option Compare Text

Private Sub Foo(ByVal a As Integer, Optional ByRef b = 5)
End Sub

Public Function Bar() As Integer
    Bar = a
End Function
""",
        tmp_path,
    )

    module = ir_module.body["module"]
    assert module["name"] == "SampleModule"
    assert any(opt for opt in module["options"] if opt["type"] == "explicit")
    assert any(
        opt
        for opt in module["options"]
        if opt["type"] == "compare" and opt.get("value") == "text"
    )

    members = {member["name"]: member for member in module["members"]}
    assert "Foo" in members
    assert "Bar" in members

    foo = members["Foo"]
    assert foo["kind"] == "sub"
    assert foo["visibility"] == "private"
    assert len(foo["parameters"]) == 2
    assert foo["parameters"][0]["name"] == "a"
    assert "ByVal" in foo["parameters"][0]["modifiers"]

    bar = members["Bar"]
    assert bar["kind"] == "function"
    assert bar["returnType"] == "Integer"
    assert bar["visibility"] == "public"


def test_ir_builder_handles_missing_parse_tree(tmp_path) -> None:
    builder = IRBuilder()
    # Simulate parser failure with None parse tree
    output = ParserOutput(
        source_path=tmp_path / "empty.bas", parse_tree=None, diagnostics=[]
    )
    ir_module = builder.build(output)
    assert ir_module.body["module"]["members"] == []
