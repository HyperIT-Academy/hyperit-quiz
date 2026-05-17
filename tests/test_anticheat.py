"""Tests for src/anticheat.py — Anti-cheat monitor (#11)."""
from __future__ import annotations

import pytest

from src.anticheat import AntiCheatMonitor, SuspicionEvent, SuspicionReason


# ── SuspicionReason enum ─────────────────────────────────────────────────────

def test_suspicion_reason_values():
    assert SuspicionReason.TOO_FAST == "too_fast"
    assert SuspicionReason.PERFECT_TIMING == "perfect_timing"
    assert SuspicionReason.DUPLICATE_SUBMIT == "duplicate_submit"
    assert SuspicionReason.ANSWER_FLOOD == "answer_flood"


# ── SuspicionEvent dataclass ─────────────────────────────────────────────────

def test_suspicion_event_fields():
    ev = SuspicionEvent(user_id=42, reason=SuspicionReason.TOO_FAST, detail="too fast")
    assert ev.user_id == 42
    assert ev.reason == SuspicionReason.TOO_FAST
    assert ev.detail == "too fast"


# ── check_response_time ──────────────────────────────────────────────────────

def test_check_response_time_too_fast():
    monitor = AntiCheatMonitor()
    event = monitor.check_response_time(user_id=1, question_index=0, response_time_ms=100)
    assert event is not None
    assert event.reason == SuspicionReason.TOO_FAST
    assert event.user_id == 1


def test_check_response_time_exactly_at_threshold_is_not_suspicious():
    monitor = AntiCheatMonitor()
    event = monitor.check_response_time(
        user_id=1, question_index=0, response_time_ms=AntiCheatMonitor.MIN_RESPONSE_MS
    )
    assert event is None


def test_check_response_time_normal_speed():
    monitor = AntiCheatMonitor()
    event = monitor.check_response_time(user_id=1, question_index=0, response_time_ms=1500)
    assert event is None


def test_check_response_time_zero_ms_is_suspicious():
    monitor = AntiCheatMonitor()
    event = monitor.check_response_time(user_id=1, question_index=0, response_time_ms=0)
    assert event is not None
    assert event.reason == SuspicionReason.TOO_FAST


def test_check_response_time_records_event():
    monitor = AntiCheatMonitor()
    monitor.check_response_time(user_id=7, question_index=2, response_time_ms=10)
    events = monitor.events_for(7)
    assert len(events) == 1
    assert events[0].reason == SuspicionReason.TOO_FAST


def test_check_response_time_no_event_not_recorded():
    monitor = AntiCheatMonitor()
    monitor.check_response_time(user_id=7, question_index=0, response_time_ms=2000)
    assert monitor.events_for(7) == []


# ── check_flood ──────────────────────────────────────────────────────────────

def test_check_flood_no_flood_below_threshold():
    monitor = AntiCheatMonitor()
    for i in range(AntiCheatMonitor.FLOOD_THRESHOLD):
        result = monitor.check_flood(user_id=1, question_index=i, timestamp_ms=1000 + i * 100)
    # exactly FLOOD_THRESHOLD submits — не flood (порог >N)
    assert result is None


def test_check_flood_triggers_on_excess():
    monitor = AntiCheatMonitor()
    ts = 1000
    event = None
    for i in range(AntiCheatMonitor.FLOOD_THRESHOLD + 1):
        event = monitor.check_flood(user_id=2, question_index=i, timestamp_ms=ts + i * 10)
    assert event is not None
    assert event.reason == SuspicionReason.ANSWER_FLOOD
    assert event.user_id == 2


def test_check_flood_outside_window_no_flood():
    monitor = AntiCheatMonitor()
    # Submits spread beyond FLOOD_WINDOW_MS
    for i in range(AntiCheatMonitor.FLOOD_THRESHOLD + 1):
        result = monitor.check_flood(
            user_id=3, question_index=i, timestamp_ms=i * (AntiCheatMonitor.FLOOD_WINDOW_MS + 1000)
        )
    assert result is None


def test_check_flood_different_users_independent():
    monitor = AntiCheatMonitor()
    ts = 0
    # User 1 floods
    for i in range(AntiCheatMonitor.FLOOD_THRESHOLD + 1):
        monitor.check_flood(user_id=1, question_index=i, timestamp_ms=ts + i * 10)
    # User 2 sends only 1 submit — should not flood
    result = monitor.check_flood(user_id=2, question_index=0, timestamp_ms=ts)
    assert result is None


# ── check_duplicate ──────────────────────────────────────────────────────────

def test_check_duplicate_returns_event_when_already_answered():
    monitor = AntiCheatMonitor()
    event = monitor.check_duplicate(user_id=5, question_index=0, already_answered=True)
    assert event is not None
    assert event.reason == SuspicionReason.DUPLICATE_SUBMIT
    assert event.user_id == 5


def test_check_duplicate_no_event_first_answer():
    monitor = AntiCheatMonitor()
    event = monitor.check_duplicate(user_id=5, question_index=0, already_answered=False)
    assert event is None


def test_check_duplicate_detail_contains_info():
    monitor = AntiCheatMonitor()
    event = monitor.check_duplicate(user_id=9, question_index=3, already_answered=True)
    assert event is not None
    assert isinstance(event.detail, str) and len(event.detail) > 0


# ── events_for ───────────────────────────────────────────────────────────────

def test_events_for_empty_for_unknown_user():
    monitor = AntiCheatMonitor()
    assert monitor.events_for(999) == []


def test_events_for_only_own_events():
    monitor = AntiCheatMonitor()
    monitor.check_response_time(user_id=1, question_index=0, response_time_ms=10)
    monitor.check_duplicate(user_id=2, question_index=0, already_answered=True)
    assert len(monitor.events_for(1)) == 1
    assert len(monitor.events_for(2)) == 1
    assert monitor.events_for(1)[0].user_id == 1


# ── suspicious_users ─────────────────────────────────────────────────────────

def test_suspicious_users_requires_two_events():
    monitor = AntiCheatMonitor()
    monitor.check_response_time(user_id=10, question_index=0, response_time_ms=10)
    # Only 1 event — not suspicious yet
    assert 10 not in monitor.suspicious_users()

    monitor.check_response_time(user_id=10, question_index=1, response_time_ms=10)
    # 2 events — now suspicious
    assert 10 in monitor.suspicious_users()


def test_suspicious_users_sorted():
    monitor = AntiCheatMonitor()
    for uid in [30, 10, 20]:
        monitor.check_response_time(user_id=uid, question_index=0, response_time_ms=1)
        monitor.check_response_time(user_id=uid, question_index=1, response_time_ms=1)
    assert monitor.suspicious_users() == [10, 20, 30]


# ── format_report ─────────────────────────────────────────────────────────────

def test_format_report_no_events():
    monitor = AntiCheatMonitor()
    report = monitor.format_report()
    assert "0" in report


def test_format_report_contains_counts():
    monitor = AntiCheatMonitor()
    monitor.check_response_time(user_id=1, question_index=0, response_time_ms=10)
    monitor.check_duplicate(user_id=2, question_index=0, already_answered=True)
    monitor.check_duplicate(user_id=2, question_index=1, already_answered=True)
    report = monitor.format_report()
    # 3 events total: 1 TOO_FAST (user 1) + 2 DUPLICATE (user 2)
    # user 2 has 2 events → 1 suspicious user
    assert "3" in report  # total events
    assert "1" in report  # suspicious users


def test_format_report_warning_emoji():
    monitor = AntiCheatMonitor()
    report = monitor.format_report()
    assert "⚠️" in report
