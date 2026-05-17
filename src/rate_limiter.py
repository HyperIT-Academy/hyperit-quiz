"""Sliding window rate limiter for WebSocket burst handling (ticket #9)."""
from dataclasses import dataclass
from collections import deque


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_ms: int   # 0 if allowed
    current_rate: float   # events/second in current window


class SlidingWindowRateLimiter:
    """Token bucket / sliding window rate limiter for burst protection."""

    def __init__(self, max_events: int, window_ms: int) -> None:
        """
        max_events: maximum events allowed within window_ms milliseconds.
        window_ms:  sliding window size in milliseconds.
        """
        self._max_events = max_events
        self._window_ms = window_ms
        self._timestamps: deque[int] = deque()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_expired(self, timestamp_ms: int) -> None:
        """Remove events that have fallen outside the sliding window."""
        cutoff = timestamp_ms - self._window_ms
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def _compute_rate(self, count: int) -> float:
        """Events-per-second based on current window size."""
        if count == 0:
            return 0.0
        window_sec = self._window_ms / 1000.0
        return count / window_sec

    def _retry_after(self, timestamp_ms: int) -> int:
        """
        Milliseconds until the oldest event slides out of the window,
        freeing a slot.
        """
        if not self._timestamps:
            return 0
        oldest = self._timestamps[0]
        # oldest + window_ms is when that slot becomes free
        return max(0, oldest + self._window_ms - timestamp_ms)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, timestamp_ms: int) -> RateLimitResult:
        """Check whether an event would be accepted. Does NOT record it."""
        # Build a transient view without modifying internal state.
        cutoff = timestamp_ms - self._window_ms
        active = sum(1 for t in self._timestamps if t > cutoff)
        allowed = active < self._max_events
        if allowed:
            return RateLimitResult(
                allowed=True,
                retry_after_ms=0,
                current_rate=self._compute_rate(active),
            )
        # At limit: compute retry_after from the oldest active timestamp.
        oldest = next(t for t in self._timestamps if t > cutoff)
        retry = max(0, oldest + self._window_ms - timestamp_ms)
        return RateLimitResult(
            allowed=False,
            retry_after_ms=retry,
            current_rate=self._compute_rate(active),
        )

    def record(self, timestamp_ms: int) -> RateLimitResult:
        """
        Record an event if within limit, or reject if limit is exhausted.
        Evicts expired events before checking.
        """
        self._evict_expired(timestamp_ms)
        count = len(self._timestamps)
        allowed = count < self._max_events
        if allowed:
            self._timestamps.append(timestamp_ms)
            new_count = len(self._timestamps)
            return RateLimitResult(
                allowed=True,
                retry_after_ms=0,
                current_rate=self._compute_rate(new_count),
            )
        retry = self._retry_after(timestamp_ms)
        return RateLimitResult(
            allowed=False,
            retry_after_ms=retry,
            current_rate=self._compute_rate(count),
        )

    def current_count(self, timestamp_ms: int) -> int:
        """Number of events recorded within the current window."""
        cutoff = timestamp_ms - self._window_ms
        return sum(1 for t in self._timestamps if t > cutoff)


class PerUserRateLimiter:
    """Separate SlidingWindowRateLimiter per user_id."""

    def __init__(self, max_events: int, window_ms: int) -> None:
        self._max_events = max_events
        self._window_ms = window_ms
        self._limiters: dict[int, SlidingWindowRateLimiter] = {}

    def _get_limiter(self, user_id: int) -> SlidingWindowRateLimiter:
        if user_id not in self._limiters:
            self._limiters[user_id] = SlidingWindowRateLimiter(
                self._max_events, self._window_ms
            )
        return self._limiters[user_id]

    def record(self, user_id: int, timestamp_ms: int) -> RateLimitResult:
        """Lazy-init limiter for user_id, then record the event."""
        return self._get_limiter(user_id).record(timestamp_ms)

    def throttled_users(self, timestamp_ms: int) -> list[int]:
        """user_ids that have reached the limit in the current window. Sorted."""
        result = []
        for user_id, limiter in self._limiters.items():
            if limiter.current_count(timestamp_ms) >= self._max_events:
                result.append(user_id)
        return sorted(result)


@dataclass
class BurstStats:
    total_events: int
    allowed_events: int
    rejected_events: int
    peak_rate: float   # max events/sec seen in any window snapshot


class BurstMonitor:
    """Collects aggregate statistics about burst load."""

    def __init__(self) -> None:
        self._total = 0
        self._allowed = 0
        self._rejected = 0
        self._peak_rate: float = 0.0

    def record_result(self, result: RateLimitResult) -> None:
        self._total += 1
        if result.allowed:
            self._allowed += 1
        else:
            self._rejected += 1
        if result.current_rate > self._peak_rate:
            self._peak_rate = result.current_rate

    def stats(self) -> BurstStats:
        return BurstStats(
            total_events=self._total,
            allowed_events=self._allowed,
            rejected_events=self._rejected,
            peak_rate=self._peak_rate,
        )
