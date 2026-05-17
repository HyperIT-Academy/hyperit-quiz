"""Tests for teacher analytics summary (closes #6) — RED phase."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession
from src.analytics import SessionSummary, build_summary


def _finished_session() -> QuizSession:
    questions = [
        Question(id=i, text=f"Q{i}", options=["A","B","C","D"],
                 correct_index=0, explanation=f"E{i}")
        for i in range(4)
    ]
    s = QuizSession(quiz_id=42, questions=questions)
    s.start()
    # Q0: 3/3 correct — 100%
    for uid in (1, 2, 3):
        s.answer(uid, 0, response_time_ms=2000)
    s.next_question()
    # Q1: 1/3 correct — 33%
    s.answer(1, 0, response_time_ms=1000)
    s.answer(2, 1, response_time_ms=9000)
    s.answer(3, 1, response_time_ms=11000)
    s.next_question()
    # Q2: 2/3 correct — 67%
    s.answer(1, 0, response_time_ms=4000)
    s.answer(2, 0, response_time_ms=3000)
    s.answer(3, 1, response_time_ms=5000)
    s.next_question()
    # Q3: 0/3 correct — 0%
    for uid in (1, 2, 3):
        s.answer(uid, 1, response_time_ms=8000)
    s.next_question()
    return s


def test_build_summary_returns_summary():
    s = _finished_session()
    summary = build_summary(s)
    assert isinstance(summary, SessionSummary)


def test_summary_total_participants():
    summary = build_summary(_finished_session())
    assert summary.total_participants == 3


def test_summary_class_accuracy():
    summary = build_summary(_finished_session())
    # (100 + 33 + 67 + 0) / 4 = 50%
    assert abs(summary.class_accuracy - 0.5) < 0.01


def test_summary_weak_questions_ids():
    summary = build_summary(_finished_session())
    weak_ids = {q.id for q in summary.weak_questions}
    assert weak_ids == {1, 3}  # Q1=33%, Q3=0%


def test_summary_top_mistake_is_worst_question():
    summary = build_summary(_finished_session())
    # Q3 has 0% accuracy — worst
    assert summary.top_mistake.id == 3


def test_summary_avg_response_ms():
    summary = build_summary(_finished_session())
    assert summary.avg_response_ms is not None
    assert summary.avg_response_ms > 0


def test_summary_format_text_contains_key_info():
    summary = build_summary(_finished_session())
    text = summary.format_text()
    assert "3" in text           # participants
    assert "%" in text           # accuracy shown as percent
    assert "⚠️" in text          # weak questions marker
