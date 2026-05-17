"""Tests for post-game analysis — weak questions, repeat pack (#29)."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession


def _session_with_answers() -> QuizSession:
    questions = [
        Question(id=0, text="Q0", options=["A","B","C","D"], correct_index=0, explanation="E0"),
        Question(id=1, text="Q1", options=["A","B","C","D"], correct_index=1, explanation="E1"),
        Question(id=2, text="Q2", options=["A","B","C","D"], correct_index=2, explanation="E2"),
    ]
    s = QuizSession(quiz_id=1, questions=questions)
    s.start()

    # Q0: 3 users — 1 correct, 2 wrong → 33% accuracy
    s.answer(user_id=1, chosen_index=0)  # correct
    s.answer(user_id=2, chosen_index=1)  # wrong
    s.answer(user_id=3, chosen_index=1)  # wrong
    s.next_question()

    # Q1: 3 users — 3 correct → 100% accuracy
    s.answer(user_id=1, chosen_index=1)
    s.answer(user_id=2, chosen_index=1)
    s.answer(user_id=3, chosen_index=1)
    s.next_question()

    # Q2: 3 users — 2 correct, 1 wrong → 67% accuracy
    s.answer(user_id=1, chosen_index=2)
    s.answer(user_id=2, chosen_index=2)
    s.answer(user_id=3, chosen_index=0)  # wrong
    s.next_question()

    return s


def test_question_accuracy_correct():
    s = _session_with_answers()
    acc = s.question_accuracy(question_index=0)
    assert abs(acc - 1/3) < 0.01


def test_question_accuracy_all_correct():
    s = _session_with_answers()
    assert s.question_accuracy(question_index=1) == 1.0


def test_question_accuracy_no_answers_returns_none():
    s = QuizSession(quiz_id=1, questions=[
        Question(id=0, text="Q", options=["A","B"], correct_index=0, explanation="E")
    ])
    s.start()
    assert s.question_accuracy(question_index=0) is None


def test_weak_questions_below_threshold():
    s = _session_with_answers()
    weak = s.weak_questions(threshold=0.6)
    assert len(weak) == 1
    assert weak[0].id == 0


def test_weak_questions_empty_when_all_pass():
    s = _session_with_answers()
    weak = s.weak_questions(threshold=0.0)
    assert weak == []


def test_weak_questions_default_threshold_60():
    s = _session_with_answers()
    # Q0=33%, Q2=67% — only Q0 below 60%
    weak = s.weak_questions()
    assert len(weak) == 1
    assert weak[0].id == 0


def test_repeat_pack_returns_weak_questions():
    s = _session_with_answers()
    pack = s.repeat_pack()
    assert all(isinstance(q, Question) for q in pack)
    assert len(pack) == 1
    assert pack[0].id == 0
