from __future__ import annotations

import json

from vb6_antlr.cli import main


VB_SOURCE = """Attribute VB_Name = "Module1"
Option Explicit
Public Sub Foo()
End Sub
"""


def test_cli_prints_json_when_no_output(tmp_path, capsys) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text(VB_SOURCE, encoding="utf-8")

    exit_code = main([str(vb_file)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())

    assert exit_code == 0
    assert payload["body"]["module"]["name"] == "Module1"


def test_cli_writes_files_to_output_directory(tmp_path) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text(VB_SOURCE, encoding="utf-8")

    output_dir = tmp_path / "out"

    exit_code = main([str(vb_file), "--output", str(output_dir)])

    assert exit_code == 0
    written_file = output_dir / "module.json"
    assert written_file.exists()

    payload = json.loads(written_file.read_text(encoding="utf-8"))
    assert payload["body"]["module"]["name"] == "Module1"
