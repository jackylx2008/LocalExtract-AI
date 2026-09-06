from __future__ import annotations

from local_extract_ai.config_loader import load_config


def test_load_config_expands_default(tmp_path, monkeypatch):
    monkeypatch.delenv("SAMPLE_SETTING", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text('app:\n  value: "${SAMPLE_SETTING:-demo}"\n', encoding="utf-8")

    assert load_config(config_file)["app"]["value"] == "demo"


def test_env_file_does_not_override_process_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMPLE_SETTING", "process")
    env_file = tmp_path / "common.env"
    env_file.write_text("SAMPLE_SETTING=file\n", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text('app:\n  value: "${SAMPLE_SETTING}"\n', encoding="utf-8")

    assert load_config(config_file, env_file)["app"]["value"] == "process"
