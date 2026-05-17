"""Tests for response time tracking (#31) — RED phase."""
from __future__ import annotations

import time
import pytest
from src.session import Question, QuizSession


def make_q(n: int = 2) -> list[Question]:
    return [
        Question(id=i, text=f"Q{i}", options=["A","B","C","D"],
                 correct_index=0, explanation=f"Exp {i}")
        for i in range(n)
    ]


def test_answer_with_time_stored():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=1500)
    assert s.response_times[1][0] == 1500


def test_answer_without_time_defaults_none():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0)
    assert s.response_times[1][0] is None


def test_avg_response_time_for_question():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=1000)
    s.answer(user_id=2, chosen_index=1, response_time_ms=3000)
    avg = s.avg_response_time(question_index=0)
    assert avg == 2000.0


def test_avg_response_time_ignores_none():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=2000)
    s.answer(user_id=2, chosen_index=1)  # no time
    avg = s.avg_response_time(question_index=0)
    assert avg == 2000.0


def test_avg_response_time_all_none_returns_none():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0)
    assert s.avg_response_time(question_index=0) is None


def test_confidence_category_quick():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=1500)
    assert s.confidence_category(user_id=1, question_index=0) == "quick"


def test_confidence_category_thoughtful():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=5000)
    assert s.confidence_category(user_id=1, question_index=0) == "thoughtful"


def test_confidence_category_uncertain():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0, response_time_ms=12000)
    assert s.confidence_category(user_id=1, question_index=0) == "uncertain"


def test_confidence_category_no_time_returns_none():
    s = QuizSession(quiz_id=1, questions=make_q())
    s.start()
    s.answer(user_id=1, chosen_index=0)
    assert s.confidence_category(user_id=1, question_index=0) is None
