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


def test_loads_dotenv_and_aliases_openai_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("LOCAL_AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    dotenv = tmp_path / ".env"
    dotenv.write_text("OPENAI_API_KEY=test-secret\n", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text('ai:\n  api_key: "${LOCAL_AI_API_KEY}"\n', encoding="utf-8")

    config = load_config(config_file, env_file=(dotenv, tmp_path / "common.env"))

    assert config["ai"]["api_key"] == "test-secret"


def test_aliases_llamacpp_api_key_from_common_env(tmp_path, monkeypatch):
    monkeypatch.delenv("LOCAL_AI_API_KEY", raising=False)
    monkeypatch.delenv("LLAMACPP_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_file = tmp_path / "common.env"
    env_file.write_text("LLAMACPP_API_KEY=llama-secret\n", encoding="utf-8")
    config_file = tmp_path / "config.yaml"
    config_file.write_text('ai:\n  api_key: "${LOCAL_AI_API_KEY}"\n', encoding="utf-8")

    config = load_config(config_file, env_file=env_file)

    assert config["ai"]["api_key"] == "llama-secret"
