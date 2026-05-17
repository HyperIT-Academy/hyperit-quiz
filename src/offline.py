"""Offline/degradation state tracking for quiz sessions (ticket #12)."""
from dataclasses import dataclass, field
from enum import Enum


class ConnectionQuality(str, Enum):
    GOOD = "good"        # latency < 200ms, 0 drops
    DEGRADED = "degraded"  # latency 200-1000ms або <5% drops
    POOR = "poor"        # latency >1000ms або >5% drops
    OFFLINE = "offline"  # немає зв'язку


@dataclass
class ConnectionSample:
    latency_ms: int
    packet_loss_pct: float  # 0.0–100.0


def classify_connection(sample: ConnectionSample) -> ConnectionQuality:
    """Класифікує якість зв'язку за правилами з enum вище."""
    if sample.packet_loss_pct >= 100.0:
        return ConnectionQuality.OFFLINE
    if sample.packet_loss_pct > 5.0 or sample.latency_ms > 1000:
        return ConnectionQuality.POOR
    if sample.latency_ms >= 200 or sample.packet_loss_pct > 0.0:
        return ConnectionQuality.DEGRADED
    return ConnectionQuality.GOOD


@dataclass
class PendingAnswer:
    user_id: int
    question_index: int
    chosen_index: int
    timestamp_ms: int


class OfflineQueue:
    """Черга відповідей для збереження під час втрати зв'язку."""

    def __init__(self) -> None:
        self._queue: list[PendingAnswer] = []
        self._quality: ConnectionQuality = ConnectionQuality.GOOD

    def update_quality(self, sample: ConnectionSample) -> ConnectionQuality:
        """Оновлює поточну якість зв'язку і повертає її."""
        self._quality = classify_connection(sample)
        return self._quality

    def enqueue(self, answer: PendingAnswer) -> None:
        """Додає відповідь у чергу."""
        self._queue.append(answer)

    def flush(self) -> list[PendingAnswer]:
        """Атомарно повертає і очищає чергу (для відправки коли зв'язок відновився)."""
        result, self._queue = self._queue, []
        return result

    @property
    def quality(self) -> ConnectionQuality:
        return self._quality

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    def should_queue(self) -> bool:
        """True якщо якість POOR або OFFLINE."""
        return self._quality in (ConnectionQuality.POOR, ConnectionQuality.OFFLINE)

    def format_status(self) -> str:
        """'📶 Зв'язок: хороший' / 'Нестабільний зв'язок (N у черзі)' / '📵 Офлайн (N у черзі)'"""
        if self._quality == ConnectionQuality.GOOD:
            return "📶 Зв'язок: хороший"
        if self._quality == ConnectionQuality.DEGRADED:
            return f"Нестабільний зв'язок ({self.pending_count} у черзі)"
        # POOR або OFFLINE
        return f"📵 Офлайн ({self.pending_count} у черзі)"
