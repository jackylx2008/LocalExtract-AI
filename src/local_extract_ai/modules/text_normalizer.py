"""AI 提取文本规范化。"""

from __future__ import annotations


def normalize_extracted_text(raw: str, separator: str = "\n") -> str:
    """去掉模型常见的 Markdown 包装、空行和项目符号。"""
    text = raw.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()[1:-1]
    else:
        lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        value = line.strip()
        if value.startswith(("- ", "* ", "• ")):
            value = value[2:].strip()
        if value and value not in cleaned:
            cleaned.append(value)
    return separator.join(cleaned)
