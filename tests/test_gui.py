from local_extract_ai.gui import format_result_log


def test_format_result_log_contains_recognized_content():
    formatted = format_result_log("ABC-123\nXYZ-9", 800, 600)

    assert "识别结果（截图 800×600）" in formatted
    assert "ABC-123\nXYZ-9" in formatted
