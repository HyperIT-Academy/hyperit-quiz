"""Tests for offline queue and connection quality classification (ticket #12)."""
import pytest
from src.offline import (
    ConnectionQuality,
    ConnectionSample,
    OfflineQueue,
    PendingAnswer,
    classify_connection,
)


# ── classify_connection ──────────────────────────────────────────────────────

class TestClassifyConnection:
    def test_good_low_latency_no_drops(self):
        sample = ConnectionSample(latency_ms=100, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.GOOD

    def test_good_boundary_latency_199(self):
        sample = ConnectionSample(latency_ms=199, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.GOOD

    def test_degraded_latency_at_boundary_200(self):
        sample = ConnectionSample(latency_ms=200, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.DEGRADED

    def test_degraded_latency_500(self):
        sample = ConnectionSample(latency_ms=500, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.DEGRADED

    def test_degraded_latency_at_boundary_1000(self):
        sample = ConnectionSample(latency_ms=1000, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.DEGRADED

    def test_poor_latency_above_1000(self):
        sample = ConnectionSample(latency_ms=1001, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.POOR

    def test_poor_very_high_latency(self):
        sample = ConnectionSample(latency_ms=5000, packet_loss_pct=0.0)
        assert classify_connection(sample) == ConnectionQuality.POOR

    def test_degraded_packet_loss_below_5pct(self):
        sample = ConnectionSample(latency_ms=50, packet_loss_pct=4.9)
        assert classify_connection(sample) == ConnectionQuality.DEGRADED

    def test_poor_packet_loss_above_5pct(self):
        sample = ConnectionSample(latency_ms=50, packet_loss_pct=5.1)
        assert classify_connection(sample) == ConnectionQuality.POOR

    def test_poor_packet_loss_exactly_100(self):
        sample = ConnectionSample(latency_ms=0, packet_loss_pct=100.0)
        assert classify_connection(sample) == ConnectionQuality.OFFLINE

    def test_offline_zero_latency_full_loss(self):
        """100% packet loss = offline regardless of latency value."""
        sample = ConnectionSample(latency_ms=0, packet_loss_pct=100.0)
        assert classify_connection(sample) == ConnectionQuality.OFFLINE

    def test_poor_wins_over_degraded_latency_when_loss_above_5(self):
        """High latency AND >5% loss → POOR."""
        sample = ConnectionSample(latency_ms=1500, packet_loss_pct=10.0)
        assert classify_connection(sample) == ConnectionQuality.POOR


# ── OfflineQueue – basic state ────────────────────────────────────────────────

class TestOfflineQueueInitialState:
    def test_initial_quality_is_good(self):
        q = OfflineQueue()
        assert q.quality == ConnectionQuality.GOOD

    def test_initial_pending_count_zero(self):
        q = OfflineQueue()
        assert q.pending_count == 0

    def test_should_queue_false_when_good(self):
        q = OfflineQueue()
        assert q.should_queue() is False


class TestOfflineQueueUpdate:
    def test_update_quality_returns_new_quality(self):
        q = OfflineQueue()
        sample = ConnectionSample(latency_ms=500, packet_loss_pct=0.0)
        result = q.update_quality(sample)
        assert result == ConnectionQuality.DEGRADED

    def test_update_quality_stores_quality(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=2000, packet_loss_pct=0.0))
        assert q.quality == ConnectionQuality.POOR

    def test_should_queue_true_when_poor(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=2000, packet_loss_pct=0.0))
        assert q.should_queue() is True

    def test_should_queue_true_when_offline(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=0, packet_loss_pct=100.0))
        assert q.should_queue() is True

    def test_should_queue_false_when_degraded(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=500, packet_loss_pct=0.0))
        assert q.should_queue() is False


class TestOfflineQueueEnqueueFlush:
    def _make_answer(self, question_index: int = 0) -> PendingAnswer:
        return PendingAnswer(
            user_id=1,
            question_index=question_index,
            chosen_index=2,
            timestamp_ms=1000,
        )

    def test_enqueue_increases_pending_count(self):
        q = OfflineQueue()
        q.enqueue(self._make_answer())
        assert q.pending_count == 1

    def test_enqueue_multiple(self):
        q = OfflineQueue()
        q.enqueue(self._make_answer(0))
        q.enqueue(self._make_answer(1))
        assert q.pending_count == 2

    def test_flush_returns_all_answers(self):
        q = OfflineQueue()
        a1 = self._make_answer(0)
        a2 = self._make_answer(1)
        q.enqueue(a1)
        q.enqueue(a2)
        result = q.flush()
        assert result == [a1, a2]

    def test_flush_clears_queue(self):
        q = OfflineQueue()
        q.enqueue(self._make_answer())
        q.flush()
        assert q.pending_count == 0

    def test_flush_empty_returns_empty_list(self):
        q = OfflineQueue()
        assert q.flush() == []

    def test_flush_is_atomic_second_flush_empty(self):
        q = OfflineQueue()
        q.enqueue(self._make_answer())
        q.flush()
        assert q.flush() == []


class TestOfflineQueueFormatStatus:
    def test_format_good_no_pending(self):
        q = OfflineQueue()
        assert q.format_status() == "📶 Зв'язок: хороший"

    def test_format_degraded_with_pending(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=500, packet_loss_pct=0.0))
        q.enqueue(PendingAnswer(user_id=1, question_index=0, chosen_index=0, timestamp_ms=0))
        assert q.format_status() == "Нестабільний зв'язок (1 у черзі)"

    def test_format_degraded_zero_pending(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=500, packet_loss_pct=0.0))
        assert q.format_status() == "Нестабільний зв'язок (0 у черзі)"

    def test_format_offline(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=0, packet_loss_pct=100.0))
        q.enqueue(PendingAnswer(user_id=2, question_index=1, chosen_index=3, timestamp_ms=999))
        q.enqueue(PendingAnswer(user_id=2, question_index=2, chosen_index=1, timestamp_ms=1000))
        assert q.format_status() == "📵 Офлайн (2 у черзі)"

    def test_format_poor(self):
        q = OfflineQueue()
        q.update_quality(ConnectionSample(latency_ms=2000, packet_loss_pct=0.0))
        assert q.format_status() == "📵 Офлайн (0 у черзі)"
