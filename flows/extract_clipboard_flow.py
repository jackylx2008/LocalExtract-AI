"""剪贴板截图识别工作流。"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Callable

from local_extract_ai.context import AppContext
from local_extract_ai.modules.ai_client import AISettings, LocalAIClient
from local_extract_ai.modules.clipboard import read_image, write_text
from local_extract_ai.modules.text_normalizer import normalize_extracted_text
from logging_config import get_logger

logger = get_logger(__name__)


class TaskCancelled(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    width: int
    height: int


def build_client(context: AppContext) -> LocalAIClient:
    config = context.config["ai"]
    return LocalAIClient(AISettings(
        base_url=str(config["base_url"]),
        api_key=str(config["api_key"]),
        model=str(config["model"]),
        timeout_seconds=float(config.get("timeout_seconds", 60)),
    ))


def verify_ai(context: AppContext) -> str:
    return build_client(context).verify()


def run(
    context: AppContext,
    cancel_event: Event,
    progress: Callable[[int, str], None] | None = None,
) -> ExtractionResult:
    report = progress or (lambda _value, _message: None)
    report(10, "读取剪贴板截图")
    image = read_image()
    logger.info("已读取剪贴板截图：%sx%s", image.width, image.height)
    _check_cancel(cancel_event)

    report(35, "调用本地 AI 识别")
    flow_config = context.config["flows"]["extract_clipboard"]
    raw = build_client(context).extract(image.png_bytes, str(flow_config["prompt"]))
    _check_cancel(cancel_event)

    report(85, "整理并写入剪贴板")
    text = normalize_extracted_text(raw, str(flow_config.get("output_separator", "\n")))
    if not text:
        raise ValueError("识别完成，但没有可写入剪贴板的特征字符串")
    write_text(text)
    report(100, "提取结果已写入剪贴板")
    logger.info("已向剪贴板写入 %s 个字符", len(text))
    return ExtractionResult(text=text, width=image.width, height=image.height)


def _check_cancel(cancel_event: Event) -> None:
    if cancel_event.is_set():
        raise TaskCancelled("任务已取消")
