"""Tests for RetentionTracker (closes #30)."""
from __future__ import annotations

from datetime import date

import pytest

from src.retention import RetentionRecord, RetentionTracker


# ── fixtures ────────────────────────────────────────────────────────────────

INITIAL_DATE = date(2026, 5, 1)
RETEST_DATE = date(2026, 5, 15)  # 14 days later


def tracker_with_initial() -> RetentionTracker:
    t = RetentionTracker()
    t.record_initial(quiz_id=1, user_id=10, accuracy=0.8, on=INITIAL_DATE)
    return t


# ── 1. record_initial ────────────────────────────────────────────────────────

def test_record_initial_stores_data():
    t = tracker_with_initial()
    rec = t.get_retention(quiz_id=1, user_id=10)
    # initial recorded, no retest yet → None
    assert rec is None


def test_record_initial_duplicate_overwrites():
    """Second record_initial for same (quiz, user) replaces the first."""
    t = RetentionTracker()
    t.record_initial(quiz_id=1, user_id=10, accuracy=0.5, on=INITIAL_DATE)
    t.record_initial(quiz_id=1, user_id=10, accuracy=0.9, on=INITIAL_DATE)
    # After retest we should see initial=0.9, not 0.5
    rec = t.record_retest(quiz_id=1, user_id=10, accuracy=0.9, on=RETEST_DATE)
    assert rec.initial_score == pytest.approx(0.9)


# ── 2. record_retest → RetentionRecord ──────────────────────────────────────

def test_record_retest_returns_record():
    t = tracker_with_initial()
    rec = t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    assert isinstance(rec, RetentionRecord)


def test_record_retest_correct_fields():
    t = tracker_with_initial()
    rec = t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    assert rec.quiz_id == 1
    assert rec.user_id == 10
    assert rec.initial_score == pytest.approx(0.8)
    assert rec.retest_score == pytest.approx(0.6)
    assert rec.tested_on == RETEST_DATE


def test_record_retest_retention_rate_calculated():
    t = tracker_with_initial()
    rec = t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    # 0.6 / 0.8 = 0.75
    assert rec.retention_rate == pytest.approx(0.75)


def test_record_retest_without_initial_raises():
    t = RetentionTracker()
    with pytest.raises(ValueError):
        t.record_retest(quiz_id=1, user_id=99, accuracy=0.5, on=RETEST_DATE)


def test_retention_rate_zero_initial_score():
    """When initial_score == 0, retention_rate should be 0.0 (no division by zero)."""
    t = RetentionTracker()
    t.record_initial(quiz_id=1, user_id=5, accuracy=0.0, on=INITIAL_DATE)
    rec = t.record_retest(quiz_id=1, user_id=5, accuracy=0.0, on=RETEST_DATE)
    assert rec.retention_rate == pytest.approx(0.0)


# ── 3. get_retention ────────────────────────────────────────────────────────

def test_get_retention_after_retest():
    t = tracker_with_initial()
    t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    rec = t.get_retention(quiz_id=1, user_id=10)
    assert rec is not None
    assert rec.retest_score == pytest.approx(0.6)


def test_get_retention_unknown_user_returns_none():
    t = tracker_with_initial()
    assert t.get_retention(quiz_id=1, user_id=999) is None


# ── 4. class_retention_rate ──────────────────────────────────────────────────

def test_class_retention_rate_single_user():
    t = tracker_with_initial()
    t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    rate = t.class_retention_rate(quiz_id=1)
    assert rate == pytest.approx(0.75)


def test_class_retention_rate_multiple_users():
    t = RetentionTracker()
    # user 1: initial=1.0, retest=0.8 → rate=0.8
    t.record_initial(quiz_id=2, user_id=1, accuracy=1.0, on=INITIAL_DATE)
    t.record_retest(quiz_id=2, user_id=1, accuracy=0.8, on=RETEST_DATE)
    # user 2: initial=0.5, retest=0.5 → rate=1.0
    t.record_initial(quiz_id=2, user_id=2, accuracy=0.5, on=INITIAL_DATE)
    t.record_retest(quiz_id=2, user_id=2, accuracy=0.5, on=RETEST_DATE)
    # average: (0.8 + 1.0) / 2 = 0.9
    rate = t.class_retention_rate(quiz_id=2)
    assert rate == pytest.approx(0.9)


def test_class_retention_rate_no_retests_returns_none():
    t = tracker_with_initial()
    assert t.class_retention_rate(quiz_id=1) is None


def test_class_retention_rate_unknown_quiz_returns_none():
    t = RetentionTracker()
    assert t.class_retention_rate(quiz_id=999) is None


# ── 5. due_for_retest ────────────────────────────────────────────────────────

def test_due_for_retest_returns_user_after_14_days():
    t = tracker_with_initial()
    # as_of = 14 days after initial → user is due
    result = t.due_for_retest(quiz_id=1, as_of=RETEST_DATE)
    assert 10 in result


def test_due_for_retest_not_due_before_14_days():
    t = tracker_with_initial()
    early = date(2026, 5, 8)  # only 7 days after initial
    result = t.due_for_retest(quiz_id=1, as_of=early)
    assert 10 not in result


def test_due_for_retest_excludes_already_retested():
    t = tracker_with_initial()
    t.record_retest(quiz_id=1, user_id=10, accuracy=0.6, on=RETEST_DATE)
    result = t.due_for_retest(quiz_id=1, as_of=RETEST_DATE)
    assert 10 not in result


def test_due_for_retest_empty_when_no_initials():
    t = RetentionTracker()
    result = t.due_for_retest(quiz_id=5, as_of=date.today())
    assert result == []


# ── 6. format_summary ────────────────────────────────────────────────────────

def test_format_summary_correct_format():
    t = RetentionTracker()
    for uid in range(1, 13):
        t.record_initial(quiz_id=3, user_id=uid, accuracy=0.8, on=INITIAL_DATE)
    # 9 out of 12 have retested
    for uid in range(1, 10):
        t.record_retest(quiz_id=3, user_id=uid, accuracy=0.73 * 0.8 / 0.8, on=RETEST_DATE)
    # avg retention ≈ 0.73 → 73%
    # but let's use exact values: retest=0.8*0.73 → rate=0.73 each → avg=73%
    summary = t.format_summary(quiz_id=3)
    assert "9/12" in summary
    assert "📊" in summary


def test_format_summary_no_data():
    t = RetentionTracker()
    summary = t.format_summary(quiz_id=99)
    assert "0/0" in summary or "даних немає" in summary.lower() or "немає" in summary.lower()
