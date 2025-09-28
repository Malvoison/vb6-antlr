from __future__ import annotations


from vb6_antlr.config import ConverterConfig


def test_config_resolve_inputs(tmp_path) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text('Attribute VB_Name = "Module1"\n', encoding="utf-8")

    config = ConverterConfig.from_paths([vb_file])
    resolved = config.resolve_inputs()

    assert resolved == [vb_file.resolve()]


def test_with_updates_returns_new_instance(tmp_path) -> None:
    vb_file = tmp_path / "module.bas"
    vb_file.write_text("", encoding="utf-8")

    config = ConverterConfig.from_paths([vb_file])
    updated = config.with_updates(fail_fast=True)

    assert updated is not config
    assert updated.fail_fast is True
    assert config.fail_fast is False
