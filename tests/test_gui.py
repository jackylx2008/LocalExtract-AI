import logging

from local_extract_ai.gui import format_result_log, log_task_failure
from local_extract_ai.modules.clipboard import ClipboardError


def test_format_result_log_contains_recognized_content():
    formatted = format_result_log("ABC-123\nXYZ-9", 800, 600)

    assert "识别结果（截图 800×600）" in formatted
    assert "ABC-123\nXYZ-9" in formatted


def test_log_task_failure_shows_reason_without_traceback(caplog):
    error = ClipboardError("剪贴板中没有截图，请先复制一张图片")

    with caplog.at_level(logging.ERROR):
        log_task_failure(error)

    assert [record.getMessage() for record in caplog.records] == [
        "截图识别失败",
        "剪贴板中没有截图，请先复制一张图片",
    ]
    assert all(record.exc_info is None for record in caplog.records)
