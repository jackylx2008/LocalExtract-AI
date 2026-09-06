"""应用共享上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AppContext:
    project_root: Path
    config: dict[str, Any]
