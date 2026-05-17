"""Tests for IT vertical: code questions + misconception labels (#35, #37)."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession
from src.analytics import build_summary


# ── Question with code_language ──────────────────────────────────────────────

def test_question_default_no_code():
    q = Question(id=1, text="Q", options=["A","B"], correct_index=0, explanation="E")
    assert q.code_language is None


def test_question_with_python_code():
    q = Question(
        id=1, text="for i in range(3):\n    print(i)",
        options=["0 1 2", "1 2 3"], correct_index=0, explanation="E",
        code_language="python",
    )
    assert q.code_language == "python"


def test_question_is_code_question():
    q = Question(id=1, text="Q", options=["A"], correct_index=0, explanation="E",
                 code_language="python")
    assert q.is_code_question is True


def test_question_not_code_question_by_default():
    q = Question(id=1, text="Q", options=["A"], correct_index=0, explanation="E")
    assert q.is_code_question is False


# ── Option misconception labels ──────────────────────────────────────────────

def test_question_option_misconceptions_default_empty():
    q = Question(id=1, text="Q", options=["A","B"], correct_index=0, explanation="E")
    assert q.option_misconceptions == {}


def test_question_with_misconception():
    q = Question(
        id=1, text="Q", options=["A","B"], correct_index=0, explanation="E",
        option_misconceptions={1: "off-by-one у range()"},
    )
    assert q.option_misconceptions[1] == "off-by-one у range()"


# ── Misconception detection in analytics ────────────────────────────────────

def _session_with_misconceptions() -> QuizSession:
    questions = [
        Question(
            id=0, text="range(3) виводить?",
            options=["0 1 2", "1 2 3", "0 1 2 3"],
            correct_index=0, explanation="0-indexed",
            option_misconceptions={1: "off-by-one: range починається з 0"},
        ),
    ]
    s = QuizSession(quiz_id=1, questions=questions)
    s.start()
    s.answer(user_id=1, chosen_index=0)   # correct
    s.answer(user_id=2, chosen_index=1)   # wrong → misconception
    s.answer(user_id=3, chosen_index=1)   # wrong → misconception
    s.next_question()
    return s


def test_summary_detects_misconceptions():
    s = _session_with_misconceptions()
    summary = build_summary(s)
    assert len(summary.top_misconceptions) >= 1
    assert "off-by-one" in summary.top_misconceptions[0][1]


def test_summary_misconception_count():
    s = _session_with_misconceptions()
    summary = build_summary(s)
    label, count = summary.top_misconceptions[0][1], summary.top_misconceptions[0][0]
    assert count == 2


def test_summary_format_includes_misconceptions():
    s = _session_with_misconceptions()
    text = build_summary(s).format_text()
    assert "off-by-one" in text or "misconception" in text.lower() or "🧠" in text
