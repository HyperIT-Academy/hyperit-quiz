"""Tests for sliding window rate limiter (ticket #9)."""
import pytest
from src.rate_limiter import (
    RateLimitResult,
    SlidingWindowRateLimiter,
    PerUserRateLimiter,
    BurstStats,
    BurstMonitor,
)


# ---------------------------------------------------------------------------
# RateLimitResult
# ---------------------------------------------------------------------------

class TestRateLimitResult:
    def test_allowed_result(self):
        r = RateLimitResult(allowed=True, retry_after_ms=0, current_rate=5.0)
        assert r.allowed is True
        assert r.retry_after_ms == 0
        assert r.current_rate == 5.0

    def test_rejected_result(self):
        r = RateLimitResult(allowed=False, retry_after_ms=250, current_rate=10.0)
        assert r.allowed is False
        assert r.retry_after_ms == 250


# ---------------------------------------------------------------------------
# SlidingWindowRateLimiter — check (read-only)
# ---------------------------------------------------------------------------

class TestSlidingWindowCheck:
    def test_empty_window_allows(self):
        lim = SlidingWindowRateLimiter(max_events=5, window_ms=1000)
        result = lim.check(timestamp_ms=1000)
        assert result.allowed is True
        assert result.retry_after_ms == 0

    def test_check_does_not_record(self):
        lim = SlidingWindowRateLimiter(max_events=3, window_ms=1000)
        for _ in range(3):
            lim.check(timestamp_ms=1000)
        # Still 0 recorded
        assert lim.current_count(timestamp_ms=1000) == 0

    def test_check_when_at_limit_after_records(self):
        lim = SlidingWindowRateLimiter(max_events=2, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=0)
        result = lim.check(timestamp_ms=0)
        assert result.allowed is False
        assert result.retry_after_ms > 0

    def test_check_retry_after_is_window_minus_elapsed(self):
        lim = SlidingWindowRateLimiter(max_events=2, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=0)
        # oldest event at 0, window=1000 → retry = 0 + 1000 - 500 = 500
        result = lim.check(timestamp_ms=500)
        assert result.retry_after_ms == 500


# ---------------------------------------------------------------------------
# SlidingWindowRateLimiter — record
# ---------------------------------------------------------------------------

class TestSlidingWindowRecord:
    def test_first_event_allowed(self):
        lim = SlidingWindowRateLimiter(max_events=5, window_ms=1000)
        result = lim.record(timestamp_ms=100)
        assert result.allowed is True

    def test_events_within_limit_all_allowed(self):
        lim = SlidingWindowRateLimiter(max_events=3, window_ms=1000)
        for t in [0, 100, 200]:
            r = lim.record(timestamp_ms=t)
            assert r.allowed is True

    def test_event_over_limit_rejected(self):
        lim = SlidingWindowRateLimiter(max_events=3, window_ms=1000)
        for t in [0, 100, 200]:
            lim.record(timestamp_ms=t)
        result = lim.record(timestamp_ms=300)
        assert result.allowed is False
        assert result.retry_after_ms > 0

    def test_rejected_event_not_recorded(self):
        lim = SlidingWindowRateLimiter(max_events=2, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=0)  # rejected
        assert lim.current_count(timestamp_ms=0) == 2

    def test_old_events_evicted_allow_new(self):
        lim = SlidingWindowRateLimiter(max_events=2, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=100)
        # Both events slide out of the 1000 ms window by t=1100
        result = lim.record(timestamp_ms=1100)
        assert result.allowed is True

    def test_current_rate_nonzero_after_records(self):
        lim = SlidingWindowRateLimiter(max_events=10, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=500)
        result = lim.record(timestamp_ms=999)
        assert result.current_rate > 0

    def test_current_rate_is_zero_on_empty_window(self):
        lim = SlidingWindowRateLimiter(max_events=5, window_ms=1000)
        result = lim.check(timestamp_ms=0)
        assert result.current_rate == 0.0


# ---------------------------------------------------------------------------
# SlidingWindowRateLimiter — current_count
# ---------------------------------------------------------------------------

class TestCurrentCount:
    def test_zero_initially(self):
        lim = SlidingWindowRateLimiter(max_events=5, window_ms=1000)
        assert lim.current_count(timestamp_ms=0) == 0

    def test_counts_events_in_window(self):
        lim = SlidingWindowRateLimiter(max_events=10, window_ms=1000)
        for t in [0, 200, 400, 600]:
            lim.record(timestamp_ms=t)
        assert lim.current_count(timestamp_ms=600) == 4

    def test_does_not_count_expired_events(self):
        lim = SlidingWindowRateLimiter(max_events=10, window_ms=1000)
        lim.record(timestamp_ms=0)
        lim.record(timestamp_ms=100)
        # By t=1100 both are outside the 1000 ms window
        assert lim.current_count(timestamp_ms=1100) == 0


# ---------------------------------------------------------------------------
# PerUserRateLimiter
# ---------------------------------------------------------------------------

class TestPerUserRateLimiter:
    def test_different_users_independent(self):
        lim = PerUserRateLimiter(max_events=2, window_ms=1000)
        lim.record(user_id=1, timestamp_ms=0)
        lim.record(user_id=1, timestamp_ms=0)
        # user 1 at limit — user 2 should still be allowed
        r2 = lim.record(user_id=2, timestamp_ms=0)
        assert r2.allowed is True

    def test_user_throttled_after_limit(self):
        lim = PerUserRateLimiter(max_events=2, window_ms=1000)
        lim.record(user_id=42, timestamp_ms=0)
        lim.record(user_id=42, timestamp_ms=0)
        result = lim.record(user_id=42, timestamp_ms=0)
        assert result.allowed is False

    def test_throttled_users_sorted(self):
        lim = PerUserRateLimiter(max_events=1, window_ms=1000)
        for uid in [5, 1, 3]:
            lim.record(user_id=uid, timestamp_ms=0)
            lim.record(user_id=uid, timestamp_ms=0)  # second → throttled
        throttled = lim.throttled_users(timestamp_ms=0)
        assert throttled == [1, 3, 5]

    def test_throttled_users_empty_initially(self):
        lim = PerUserRateLimiter(max_events=5, window_ms=1000)
        assert lim.throttled_users(timestamp_ms=0) == []

    def test_user_no_longer_throttled_after_window(self):
        lim = PerUserRateLimiter(max_events=1, window_ms=1000)
        lim.record(user_id=7, timestamp_ms=0)
        lim.record(user_id=7, timestamp_ms=0)  # throttled at t=0
        # After window expires
        throttled = lim.throttled_users(timestamp_ms=1001)
        assert 7 not in throttled


# ---------------------------------------------------------------------------
# BurstMonitor
# ---------------------------------------------------------------------------

class TestBurstMonitor:
    def test_initial_stats_all_zero(self):
        m = BurstMonitor()
        s = m.stats()
        assert s.total_events == 0
        assert s.allowed_events == 0
        assert s.rejected_events == 0
        assert s.peak_rate == 0.0

    def test_records_allowed(self):
        m = BurstMonitor()
        m.record_result(RateLimitResult(allowed=True, retry_after_ms=0, current_rate=3.0))
        s = m.stats()
        assert s.total_events == 1
        assert s.allowed_events == 1
        assert s.rejected_events == 0

    def test_records_rejected(self):
        m = BurstMonitor()
        m.record_result(RateLimitResult(allowed=False, retry_after_ms=100, current_rate=10.0))
        s = m.stats()
        assert s.total_events == 1
        assert s.allowed_events == 0
        assert s.rejected_events == 1

    def test_peak_rate_tracks_maximum(self):
        m = BurstMonitor()
        m.record_result(RateLimitResult(allowed=True, retry_after_ms=0, current_rate=5.0))
        m.record_result(RateLimitResult(allowed=True, retry_after_ms=0, current_rate=15.0))
        m.record_result(RateLimitResult(allowed=False, retry_after_ms=50, current_rate=8.0))
        s = m.stats()
        assert s.peak_rate == 15.0

    def test_stats_returns_burst_stats_dataclass(self):
        m = BurstMonitor()
        s = m.stats()
        assert isinstance(s, BurstStats)
