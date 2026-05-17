"""Tests for quiz session state machine — RED phase."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession, SessionState


# ── fixtures ────────────────────────────────────────────────────────────────

def make_questions(n: int = 3) -> list[Question]:
    return [
        Question(
            id=i,
            text=f"Питання {i}",
            options=["A", "B", "C", "D"],
            correct_index=0,
            explanation=f"Бо A правильно ({i})",
        )
        for i in range(n)
    ]


# ── state transitions ────────────────────────────────────────────────────────

def test_new_session_is_waiting():
    session = QuizSession(quiz_id=1, questions=make_questions())
    assert session.state == SessionState.WAITING


def test_start_moves_to_question():
    session = QuizSession(quiz_id=1, questions=make_questions())
    session.start()
    assert session.state == SessionState.QUESTION
    assert session.current_index == 0


def test_cannot_start_twice():
    session = QuizSession(quiz_id=1, questions=make_questions())
    session.start()
    with pytest.raises(RuntimeError):
        session.start()


def test_answer_records_result():
    session = QuizSession(quiz_id=1, questions=make_questions())
    session.start()
    session.answer(user_id=42, chosen_index=0)
    assert session.answers[42][0] == 0


def test_answer_before_start_raises():
    session = QuizSession(quiz_id=1, questions=make_questions())
    with pytest.raises(RuntimeError):
        session.answer(user_id=42, chosen_index=0)


def test_next_question_advances_index():
    session = QuizSession(quiz_id=1, questions=make_questions(3))
    session.start()
    session.next_question()
    assert session.current_index == 1
    assert session.state == SessionState.QUESTION


def test_next_question_after_last_finishes():
    session = QuizSession(quiz_id=1, questions=make_questions(1))
    session.start()
    session.next_question()
    assert session.state == SessionState.FINISHED


def test_finished_session_rejects_answers():
    session = QuizSession(quiz_id=1, questions=make_questions(1))
    session.start()
    session.next_question()
    with pytest.raises(RuntimeError):
        session.answer(user_id=42, chosen_index=0)


# ── scoring ─────────────────────────────────────────────────────────────────

def test_score_correct_answer():
    session = QuizSession(quiz_id=1, questions=make_questions(2))
    session.start()
    session.answer(user_id=1, chosen_index=0)  # correct
    session.next_question()
    session.answer(user_id=1, chosen_index=1)  # wrong
    session.next_question()
    assert session.score(user_id=1) == 1


def test_score_all_correct():
    session = QuizSession(quiz_id=1, questions=make_questions(3))
    session.start()
    for _ in range(3):
        session.answer(user_id=7, chosen_index=0)
        session.next_question()
    assert session.score(user_id=7) == 3


def test_score_unknown_user_is_zero():
    session = QuizSession(quiz_id=1, questions=make_questions())
    session.start()
    assert session.score(user_id=999) == 0


# ── leaderboard ─────────────────────────────────────────────────────────────

def test_leaderboard_sorted_by_score():
    q = make_questions(2)
    session = QuizSession(quiz_id=1, questions=q)
    session.start()

    session.answer(user_id=1, chosen_index=0)  # correct
    session.answer(user_id=2, chosen_index=1)  # wrong
    session.next_question()

    session.answer(user_id=1, chosen_index=0)  # correct
    session.answer(user_id=2, chosen_index=0)  # correct
    session.next_question()

    board = session.leaderboard()
    assert board[0] == (1, 2)
    assert board[1] == (2, 1)


def test_duplicate_answer_ignored():
    session = QuizSession(quiz_id=1, questions=make_questions())
    session.start()
    session.answer(user_id=42, chosen_index=0)
    session.answer(user_id=42, chosen_index=1)  # second call ignored
    assert session.answers[42][0] == 0


# ── current question helpers ─────────────────────────────────────────────────

def test_current_question_returns_active():
    questions = make_questions(2)
    session = QuizSession(quiz_id=1, questions=questions)
    session.start()
    assert session.current_question() == questions[0]
    session.next_question()
    assert session.current_question() == questions[1]


def test_current_question_after_finish_raises():
    session = QuizSession(quiz_id=1, questions=make_questions(1))
    session.start()
    session.next_question()
    with pytest.raises(RuntimeError):
        session.current_question()
