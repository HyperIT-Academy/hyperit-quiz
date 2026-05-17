"""Tests for session history + progress delta (closes #36) — RED phase."""
from __future__ import annotations

import pytest
from src.history import SessionHistory, ProgressDelta


def test_history_starts_empty():
    h = SessionHistory()
    assert h.get_last(quiz_id=1) is None


def test_history_records_accuracy():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.45)
    assert h.get_last(quiz_id=1) == 0.45


def test_history_get_last_returns_most_recent():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.40)
    h.record(quiz_id=1, accuracy=0.67)
    assert h.get_last(quiz_id=1) == 0.67


def test_history_different_quizzes_independent():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.50)
    h.record(quiz_id=2, accuracy=0.80)
    assert h.get_last(quiz_id=1) == 0.50
    assert h.get_last(quiz_id=2) == 0.80


def test_delta_positive():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.45)
    h.record(quiz_id=1, accuracy=0.67)
    delta = h.progress_delta(quiz_id=1)
    assert delta is not None
    assert abs(delta.change - 0.22) < 0.01
    assert delta.direction == "up"


def test_delta_negative():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.80)
    h.record(quiz_id=1, accuracy=0.60)
    delta = h.progress_delta(quiz_id=1)
    assert delta.direction == "down"
    assert abs(delta.change - (-0.20)) < 0.01


def test_delta_no_previous_returns_none():
    h = SessionHistory()
    h.record(quiz_id=1, accuracy=0.50)
    # only one record — no delta possible
    assert h.progress_delta(quiz_id=1) is None


def test_delta_format_positive():
    delta = ProgressDelta(change=0.22, direction="up")
    text = delta.format_text()
    assert "+" in text or "📈" in text
    assert "22%" in text


def test_delta_format_negative():
    delta = ProgressDelta(change=-0.15, direction="down")
    text = delta.format_text()
    assert "📉" in text or "-" in text
    assert "15%" in text
