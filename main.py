"""Windows 剪贴板截图特征字符串提取工具

用途：
  读取 Windows 剪贴板中的截图，调用已经运行的本地多模态 AI 提取特征字符串，
  并将提取结果写回剪贴板。本工具不会启动或管理本地 AI 服务。

配置文件：
  默认读取项目根目录的 config.yaml；可由 .env、common.env 或进程环境变量覆盖
  本地 AI 地址、模型、密钥和日志级别。

可选参数：
  --config-file   配置文件路径，默认使用项目根目录下的 config.yaml。

示例：
  python main.py
  python main.py --config-file config.yaml

输出：
  提取结果写入 Windows 剪贴板；运行日志写入项目根目录的 logs/main.log。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from local_extract_ai.config_loader import load_config
from local_extract_ai.context import AppContext
from local_extract_ai.gui import LocalExtractApp
from logging_config import configure_utf8_stdio, get_logger, setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config-file", type=Path, default=PROJECT_ROOT / "config.yaml")
    return parser.parse_args()


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    config = load_config(
        args.config_file,
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / "common.env"),
    )
    setup_logger(config["app"]["log_level"])
    logger = get_logger(__name__)
    logger.info("启动 LocalExtract AI")
    context = AppContext(project_root=PROJECT_ROOT, config=config)
    LocalExtractApp(context).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
