from __future__ import annotations

from vb6_antlr.cli import main


def test_cli_runs_with_single_file(tmp_path) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text('Attribute VB_Name = "Module1"\n', encoding="utf-8")

    exit_code = main([str(vb_file)])

    assert exit_code == 0
