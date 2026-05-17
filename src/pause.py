"""Pause controller for quiz sessions — Ticket #7."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PauseReason(Enum):
    TEACHER_MANUAL = "teacher_manual"
    LOW_ACCURACY = "low_accuracy"


@dataclass
class PauseEvent:
    question_index: int
    reason: PauseReason
    accuracy_at_pause: float | None  # None for manual pauses


class PauseController:
    def __init__(self, auto_pause_threshold: float = 0.4) -> None:
        self._threshold = auto_pause_threshold
        self._paused = False
        self._history: list[PauseEvent] = []

    # ── Queries ───────────────────────────────────────────────────────────────

    def should_auto_pause(self, correct_count: int, total_answers: int) -> bool:
        """True when accuracy is strictly below the threshold."""
        if total_answers == 0:
            return False
        return (correct_count / total_answers) < self._threshold

    def is_paused(self) -> bool:
        return self._paused

    def pause_history(self) -> list[PauseEvent]:
        """Returns a copy of the pause history list."""
        return list(self._history)

    # ── Commands ──────────────────────────────────────────────────────────────

    def record_pause(
        self,
        question_index: int,
        reason: PauseReason,
        accuracy: float | None = None,
    ) -> PauseEvent:
        event = PauseEvent(
            question_index=question_index,
            reason=reason,
            accuracy_at_pause=accuracy,
        )
        self._paused = True
        self._history.append(event)
        return event

    def manual_pause(self, question_index: int) -> PauseEvent:
        return self.record_pause(
            question_index=question_index,
            reason=PauseReason.TEACHER_MANUAL,
            accuracy=None,
        )

    def resume(self) -> None:
        self._paused = False

    def check_and_auto_pause(
        self,
        question_index: int,
        correct_count: int,
        total_answers: int,
    ) -> PauseEvent | None:
        """Auto-pause if accuracy is below threshold; returns event or None."""
        if not self.should_auto_pause(correct_count, total_answers):
            return None
        accuracy = correct_count / total_answers
        return self.record_pause(
            question_index=question_index,
            reason=PauseReason.LOW_ACCURACY,
            accuracy=accuracy,
        )
