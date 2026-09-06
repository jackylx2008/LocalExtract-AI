"""集中加载项目配置与本地环境变量。"""

from __future__ import annotations

import os
import platform
import re
from pathlib import Path
from collections.abc import Iterable
from typing import Any

import yaml

ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def load_config(
    config_file: Path,
    env_file: Path | Iterable[Path] | None = None,
) -> dict[str, Any]:
    """读取 YAML 配置，展开环境变量并返回字典。"""
    if env_file:
        env_files = (env_file,) if isinstance(env_file, Path) else env_file
        for path in env_files:
            _load_env_file(path)
    _alias_local_ai_api_key()
    _select_cloudstation_root()
    path = config_file.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    raw = path.read_text(encoding="utf-8")
    expanded = ENV_PATTERN.sub(_replace_env, raw)
    data = yaml.safe_load(expanded)
    if not isinstance(data, dict):
        raise ValueError("配置文件根节点必须是映射")
    return data


def _replace_env(match: re.Match[str]) -> str:
    name, default = match.group(1), match.group(2)
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"缺少环境变量: {name}")
    return value.replace("\\", "\\\\")


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _select_cloudstation_root() -> None:
    if os.environ.get("CLOUDSTATION_ROOT"):
        return
    suffix = {"Windows": "WINDOWS", "Darwin": "MACOS", "Linux": "LINUX"}.get(platform.system())
    if suffix:
        value = os.environ.get(f"CLOUDSTATION_ROOT_{suffix}")
        if value:
            os.environ["CLOUDSTATION_ROOT"] = str(Path(value).expanduser())


def _alias_local_ai_api_key() -> None:
    """将常见的本地 AI 密钥变量名映射为项目统一变量。"""
    if os.environ.get("LOCAL_AI_API_KEY"):
        return
    for alias in ("LLAMACPP_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(alias)
        if value:
            os.environ["LOCAL_AI_API_KEY"] = value
            return
