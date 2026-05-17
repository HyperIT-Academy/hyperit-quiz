"""Spaced repetition scheduler (SM-2 simplified) — closes #8."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class RepeatSchedule:
    quiz_id: int
    question_ids: list[int]   # питання що потребують повторення
    due_date: date             # коли повторити


class SpacedScheduler:
    # SM-2 спрощений: інтервали 1, 3, 7, 14, 30 днів
    INTERVALS = [1, 3, 7, 14, 30]

    def __init__(self) -> None:
        # (quiz_id, question_id) → consecutive correct streak
        self._streaks: dict[tuple[int, int], int] = {}
        # (quiz_id, question_id) → date when last result was recorded
        self._last_recorded: dict[tuple[int, int], date] = {}

    def record_result(self, quiz_id: int, question_id: int, correct: bool) -> None:
        """Відстежує кількість правильних відповідей підряд per question."""
        key = (quiz_id, question_id)
        if correct:
            self._streaks[key] = self._streaks.get(key, 0) + 1
        else:
            self._streaks[key] = 0
        self._last_recorded[key] = date.today()

    def next_review_date(
        self,
        quiz_id: int,
        question_id: int,
        from_date: date | None = None,
    ) -> date:
        """Повертає дату наступного повторення за SM-2 інтервалами.

        0 correct → +1 day, 1 → +3, 2 → +7, 3 → +14, 4+ → +30
        """
        if from_date is None:
            from_date = date.today()
        key = (quiz_id, question_id)
        streak = self._streaks.get(key, 0)
        interval_index = min(streak, len(self.INTERVALS) - 1)
        interval = self.INTERVALS[interval_index]
        return from_date + timedelta(days=interval)

    def due_questions(self, quiz_id: int, as_of: date | None = None) -> list[int]:
        """Повертає question_ids що потрібно повторити сьогодні або раніше."""
        if as_of is None:
            as_of = date.today()
        result = []
        for (qid, question_id), last_date in self._last_recorded.items():
            if qid != quiz_id:
                continue
            streak = self._streaks.get((qid, question_id), 0)
            interval_index = min(streak, len(self.INTERVALS) - 1)
            interval = self.INTERVALS[interval_index]
            next_review = last_date + timedelta(days=interval)
            if next_review <= as_of:
                result.append(question_id)
        return result

    def build_schedule(
        self,
        quiz_id: int,
        question_ids: list[int],
    ) -> RepeatSchedule:
        """Генерує розклад повторення для списку питань."""
        today = date.today()
        earliest = min(
            self.next_review_date(quiz_id, qid, from_date=today)
            for qid in question_ids
        )
        return RepeatSchedule(
            quiz_id=quiz_id,
            question_ids=question_ids,
            due_date=earliest,
        )
