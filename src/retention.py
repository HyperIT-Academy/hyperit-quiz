"""Learning retention metric (closes #30)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

RETEST_INTERVAL_DAYS = 14


@dataclass
class RetentionRecord:
    quiz_id: int
    user_id: int
    initial_score: float    # accuracy відразу після уроку (0.0-1.0)
    retest_score: float     # accuracy через 14 днів
    retention_rate: float   # retest_score / initial_score (якщо initial > 0)
    tested_on: date


@dataclass
class _InitialEntry:
    accuracy: float
    on: date


class RetentionTracker:
    def __init__(self) -> None:
        # (quiz_id, user_id) → _InitialEntry
        self._initials: dict[tuple[int, int], _InitialEntry] = {}
        # (quiz_id, user_id) → RetentionRecord
        self._records: dict[tuple[int, int], RetentionRecord] = {}

    def record_initial(
        self,
        quiz_id: int,
        user_id: int,
        accuracy: float,
        on: date | None = None,
    ) -> None:
        if on is None:
            on = date.today()
        self._initials[(quiz_id, user_id)] = _InitialEntry(accuracy=accuracy, on=on)

    def record_retest(
        self,
        quiz_id: int,
        user_id: int,
        accuracy: float,
        on: date | None = None,
    ) -> RetentionRecord:
        key = (quiz_id, user_id)
        entry = self._initials.get(key)
        if entry is None:
            raise ValueError(
                f"No initial record for quiz_id={quiz_id}, user_id={user_id}"
            )
        if on is None:
            on = date.today()
        initial = entry.accuracy
        retention_rate = accuracy / initial if initial > 0 else 0.0
        rec = RetentionRecord(
            quiz_id=quiz_id,
            user_id=user_id,
            initial_score=initial,
            retest_score=accuracy,
            retention_rate=retention_rate,
            tested_on=on,
        )
        self._records[key] = rec
        return rec

    def get_retention(self, quiz_id: int, user_id: int) -> RetentionRecord | None:
        return self._records.get((quiz_id, user_id))

    def class_retention_rate(self, quiz_id: int) -> float | None:
        rates = [
            rec.retention_rate
            for (q, _), rec in self._records.items()
            if q == quiz_id
        ]
        if not rates:
            return None
        return sum(rates) / len(rates)

    def due_for_retest(self, quiz_id: int, as_of: date | None = None) -> list[int]:
        if as_of is None:
            as_of = date.today()
        result = []
        for (q, u), entry in self._initials.items():
            if q != quiz_id:
                continue
            if (q, u) in self._records:
                continue  # вже retested
            days_since = (as_of - entry.on).days
            if days_since >= RETEST_INTERVAL_DAYS:
                result.append(u)
        return result

    def format_summary(self, quiz_id: int) -> str:
        total_initials = sum(1 for (q, _) in self._initials if q == quiz_id)
        retested = [
            rec for (q, _), rec in self._records.items() if q == quiz_id
        ]
        tested_count = len(retested)

        if total_initials == 0:
            return "📊 Retention через 14 днів: немає даних (0/0 учнів протестовано)"

        if tested_count == 0:
            return f"📊 Retention через 14 днів: немає даних (0/{total_initials} учнів протестовано)"

        avg_rate = sum(r.retention_rate for r in retested) / tested_count
        pct = round(avg_rate * 100)
        return (
            f"📊 Retention через 14 днів: {pct}%"
            f" ({tested_count}/{total_initials} учнів протестовано)"
        )
