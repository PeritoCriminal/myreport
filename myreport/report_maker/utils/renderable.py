# report_maker/utils/renderable.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional


@dataclass(frozen=True)
class ReportSection:
    key: str
    title: str
    fmt: str = "md"   # "md" | "text" | "html"
    level: int = 2


class RenderableExamObjectMixin:
    REPORT_SECTIONS: list[ReportSection] = []

    def get_report_sections(self) -> list[ReportSection]:
        return list(self.REPORT_SECTIONS)


def has_meaningful_value(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, (list, tuple, set, dict)):
        return len(val) > 0
    return True
