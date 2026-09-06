from local_extract_ai.modules.text_normalizer import normalize_extracted_text


def test_normalize_removes_markdown_and_duplicates():
    raw = "```text\n- ABC-123\n* XYZ_9\n- ABC-123\n```"

    assert normalize_extracted_text(raw) == "ABC-123\nXYZ_9"


def test_normalize_supports_custom_separator():
    assert normalize_extracted_text("A\nB", ",") == "A,B"


def test_normalize_preserves_name_room_tab_pairs():
    raw = "张三\tA_101\n李四\tB2_203"

    assert normalize_extracted_text(raw) == raw


def test_normalize_converts_literal_tab_markers():
    raw = "张三<TAB>A_101\n李四\\tB2_203"

    assert normalize_extracted_text(raw) == "张三\tA_101\n李四\tB2_203"
