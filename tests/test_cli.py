from __future__ import annotations

import json

from vb6_antlr.cli import main


def test_cli_runs_with_single_file(tmp_path, capsys) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text(
        'Attribute VB_Name = "Module1"\nOption Explicit\nPublic Sub Foo()\nEnd Sub\n',
        encoding="utf-8",
    )

    exit_code = main([str(vb_file)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())

    assert exit_code == 0
    assert payload["body"]["module"]["name"] == "Module1"
