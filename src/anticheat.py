"""Anti-cheat monitor — виявлення підозрілої активності (#11)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class SuspicionReason(str, Enum):
    TOO_FAST = "too_fast"
    PERFECT_TIMING = "perfect_timing"
    DUPLICATE_SUBMIT = "duplicate_submit"
    ANSWER_FLOOD = "answer_flood"


@dataclass
class SuspicionEvent:
    user_id: int
    reason: SuspicionReason
    detail: str


class AntiCheatMonitor:
    """Аналізує паттерни відповідей для виявлення підозрілої активності."""

    MIN_RESPONSE_MS: int = 500
    FLOOD_WINDOW_MS: int = 2000
    FLOOD_THRESHOLD: int = 3

    def __init__(self) -> None:
        self._events: list[SuspicionEvent] = []
        # (user_id, q_idx, timestamp_ms)
        self._submit_log: list[tuple[int, int, int]] = []

    def check_response_time(
        self, user_id: int, question_index: int, response_time_ms: int
    ) -> SuspicionEvent | None:
        """Повертає SuspicionEvent(TOO_FAST) або None."""
        if response_time_ms < self.MIN_RESPONSE_MS:
            event = SuspicionEvent(
                user_id=user_id,
                reason=SuspicionReason.TOO_FAST,
                detail=(
                    f"Відповідь за {response_time_ms} мс на питання {question_index} "
                    f"— менше порогу {self.MIN_RESPONSE_MS} мс"
                ),
            )
            self._events.append(event)
            return event
        return None

    def check_flood(
        self, user_id: int, question_index: int, timestamp_ms: int
    ) -> SuspicionEvent | None:
        """Логує submit. Повертає ANSWER_FLOOD якщо >FLOOD_THRESHOLD у FLOOD_WINDOW_MS."""
        self._submit_log.append((user_id, question_index, timestamp_ms))

        # Рахуємо submits цього user у вікні [timestamp_ms - FLOOD_WINDOW_MS, timestamp_ms]
        window_start = timestamp_ms - self.FLOOD_WINDOW_MS
        recent = [
            ts
            for uid, _, ts in self._submit_log
            if uid == user_id and window_start <= ts <= timestamp_ms
        ]

        if len(recent) > self.FLOOD_THRESHOLD:
            event = SuspicionEvent(
                user_id=user_id,
                reason=SuspicionReason.ANSWER_FLOOD,
                detail=(
                    f"{len(recent)} відповідей за {self.FLOOD_WINDOW_MS} мс "
                    f"(ліміт: {self.FLOOD_THRESHOLD})"
                ),
            )
            self._events.append(event)
            return event
        return None

    def check_duplicate(
        self, user_id: int, question_index: int, already_answered: bool
    ) -> SuspicionEvent | None:
        """Повертає DUPLICATE_SUBMIT або None."""
        if already_answered:
            event = SuspicionEvent(
                user_id=user_id,
                reason=SuspicionReason.DUPLICATE_SUBMIT,
                detail=(
                    f"Повторна відповідь на питання {question_index} "
                    f"від користувача {user_id}"
                ),
            )
            self._events.append(event)
            return event
        return None

    def events_for(self, user_id: int) -> list[SuspicionEvent]:
        """Всі підозрілі події для конкретного користувача."""
        return [e for e in self._events if e.user_id == user_id]

    def suspicious_users(self) -> list[int]:
        """user_id із >=2 подіями (відсортовано)."""
        counts: dict[int, int] = defaultdict(int)
        for event in self._events:
            counts[event.user_id] += 1
        return sorted(uid for uid, cnt in counts.items() if cnt >= 2)

    def format_report(self) -> str:
        """Короткий текстовий звіт: '⚠️ Підозрілі: N юзерів, M подій'."""
        n_users = len(self.suspicious_users())
        n_events = len(self._events)
        return f"⚠️ Підозрілі: {n_users} юзерів, {n_events} подій"
