from local_extract_ai.modules.text_normalizer import normalize_extracted_text


def test_normalize_removes_markdown_and_duplicates():
    raw = "```text\n- ABC-123\n* XYZ_9\n- ABC-123\n```"

    assert normalize_extracted_text(raw) == "ABC-123\nXYZ_9"


def test_normalize_supports_custom_separator():
    assert normalize_extracted_text("A\nB", ",") == "A,B"
