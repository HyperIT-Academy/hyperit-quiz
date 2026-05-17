"""Session history + progress delta tracking (closes #36)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProgressDelta:
    change: float    # signed, e.g. +0.22 or -0.15
    direction: str   # "up" | "down" | "same"

    def format_text(self) -> str:
        pct = round(abs(self.change) * 100)
        if self.direction == "up":
            return f"📈 +{pct}% — клас покращився!"
        if self.direction == "down":
            return f"📉 -{pct}% — потрібно повторити"
        return f"➡️ {pct}% — без змін"


class SessionHistory:
    """In-memory store of per-quiz accuracy history."""

    def __init__(self) -> None:
        self._records: dict[int, list[float]] = {}

    def record(self, quiz_id: int, accuracy: float) -> None:
        self._records.setdefault(quiz_id, []).append(accuracy)

    def get_last(self, quiz_id: int) -> float | None:
        records = self._records.get(quiz_id, [])
        return records[-1] if records else None

    def progress_delta(self, quiz_id: int) -> ProgressDelta | None:
        records = self._records.get(quiz_id, [])
        if len(records) < 2:
            return None
        prev, current = records[-2], records[-1]
        change = round(current - prev, 4)
        if change > 0.005:
            direction = "up"
        elif change < -0.005:
            direction = "down"
        else:
            direction = "same"
        return ProgressDelta(change=change, direction=direction)
