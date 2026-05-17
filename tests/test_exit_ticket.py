"""Tests for ExitTicketSession (closes #19)."""
from __future__ import annotations

import pytest

from src.exit_ticket import ExitTicketResult, ExitTicketSession


# ── submit & all_results ─────────────────────────────────────────────────────

def test_submit_returns_result():
    session = ExitTicketSession("loops")
    result = session.submit(1, "for loops", "while edge case", "when to use while?")
    assert isinstance(result, ExitTicketResult)


def test_result_fields_match_input():
    session = ExitTicketSession("loops")
    result = session.submit(42, "understood A", "confused B", "question C")
    assert result.user_id == 42
    assert result.understood == "understood A"
    assert result.confused == "confused B"
    assert result.question == "question C"


def test_all_results_empty_on_init():
    session = ExitTicketSession("loops")
    assert session.all_results() == []


def test_all_results_grows_with_submits():
    session = ExitTicketSession("loops")
    session.submit(1, "a", "b", "c")
    session.submit(2, "d", "e", "f")
    assert len(session.all_results()) == 2


def test_all_results_returns_correct_order():
    session = ExitTicketSession("loops")
    r1 = session.submit(1, "a", "b", "c")
    r2 = session.submit(2, "d", "e", "f")
    results = session.all_results()
    assert results[0] is r1
    assert results[1] is r2


# ── completion_rate ──────────────────────────────────────────────────────────

def test_completion_rate_zero_when_no_submits():
    session = ExitTicketSession("loops")
    assert session.completion_rate(10) == 0.0


def test_completion_rate_full_when_all_submitted():
    session = ExitTicketSession("loops")
    for uid in range(1, 6):
        session.submit(uid, "ok", "nothing", "none")
    assert session.completion_rate(5) == 1.0


def test_completion_rate_partial():
    session = ExitTicketSession("loops")
    session.submit(1, "ok", "nothing", "none")
    session.submit(2, "ok", "nothing", "none")
    rate = session.completion_rate(4)
    assert abs(rate - 0.5) < 1e-9


def test_completion_rate_over_expected_capped_or_gt_one():
    # якщо більше людей здали ніж expected — rate > 1.0 або == 1.0 (не падати)
    session = ExitTicketSession("loops")
    session.submit(1, "a", "b", "c")
    session.submit(2, "a", "b", "c")
    session.submit(3, "a", "b", "c")
    rate = session.completion_rate(2)
    assert rate >= 1.0  # не падає, повертає >= 1.0


# ── common_confusions ────────────────────────────────────────────────────────

def test_common_confusions_empty_when_no_submits():
    session = ExitTicketSession("loops")
    assert session.common_confusions() == []


def test_common_confusions_sorted_by_frequency():
    session = ExitTicketSession("loops")
    session.submit(1, "ok", "recursion", "q1")
    session.submit(2, "ok", "recursion", "q2")
    session.submit(3, "ok", "closures", "q3")
    confusions = session.common_confusions()
    assert confusions[0] == "recursion"
    assert confusions[1] == "closures"


def test_common_confusions_unique_strings():
    session = ExitTicketSession("loops")
    for uid in range(1, 4):
        session.submit(uid, "ok", "same confusion", "q")
    confusions = session.common_confusions()
    assert len(confusions) == 1
    assert confusions[0] == "same confusion"


# ── teacher_summary ──────────────────────────────────────────────────────────

def test_teacher_summary_contains_topic():
    session = ExitTicketSession("Recursion Basics")
    session.submit(1, "base case", "stack overflow", "how deep?")
    summary = session.teacher_summary()
    assert "Recursion Basics" in summary


def test_teacher_summary_contains_questions():
    session = ExitTicketSession("loops")
    session.submit(1, "ok", "nothing", "when to use for vs while?")
    summary = session.teacher_summary()
    assert "when to use for vs while?" in summary


def test_teacher_summary_contains_confusion():
    session = ExitTicketSession("loops")
    session.submit(1, "ok", "off-by-one errors", "q?")
    summary = session.teacher_summary()
    assert "off-by-one errors" in summary


def test_teacher_summary_no_crash_when_empty():
    session = ExitTicketSession("loops")
    summary = session.teacher_summary()
    assert isinstance(summary, str)
    assert len(summary) > 0
