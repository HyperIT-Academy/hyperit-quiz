"""Tests for thinking time mode — all answer, then reveal (RED phase)."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession, SessionState


def make_q(n: int = 2) -> list[Question]:
    return [
        Question(id=i, text=f"Q{i}", options=["A","B","C","D"],
                 correct_index=0, explanation=f"Exp {i}")
        for i in range(n)
    ]


# ── reveal_mode flag ─────────────────────────────────────────────────────────

def test_default_mode_is_auto_advance():
    s = QuizSession(quiz_id=1, questions=make_q())
    assert s.reveal_mode is False


def test_reveal_mode_can_be_set():
    s = QuizSession(quiz_id=1, questions=make_q(), reveal_mode=True)
    assert s.reveal_mode is True


# ── in reveal_mode: next_question only via explicit reveal ───────────────────

def test_reveal_mode_does_not_auto_advance_on_answer():
    s = QuizSession(quiz_id=1, questions=make_q(2), reveal_mode=True)
    s.start()
    s.answer(user_id=1, chosen_index=0)
    # still on question 0
    assert s.current_index == 0
    assert s.state == SessionState.QUESTION


def test_reveal_advances_to_next():
    s = QuizSession(quiz_id=1, questions=make_q(2), reveal_mode=True)
    s.start()
    s.answer(user_id=1, chosen_index=0)
    s.reveal()
    assert s.current_index == 1


def test_reveal_on_last_question_finishes():
    s = QuizSession(quiz_id=1, questions=make_q(1), reveal_mode=True)
    s.start()
    s.reveal()
    assert s.state == SessionState.FINISHED


def test_reveal_not_available_in_auto_mode():
    s = QuizSession(quiz_id=1, questions=make_q(), reveal_mode=False)
    s.start()
    with pytest.raises(RuntimeError):
        s.reveal()


# ── all_answered helper ──────────────────────────────────────────────────────

def test_all_answered_false_when_none():
    s = QuizSession(quiz_id=1, questions=make_q(), reveal_mode=True)
    s.start()
    assert s.all_answered(participant_ids={1, 2}) is False


def test_all_answered_true_when_all_responded():
    s = QuizSession(quiz_id=1, questions=make_q(), reveal_mode=True)
    s.start()
    s.answer(user_id=1, chosen_index=0)
    s.answer(user_id=2, chosen_index=1)
    assert s.all_answered(participant_ids={1, 2}) is True


def test_all_answered_false_when_partial():
    s = QuizSession(quiz_id=1, questions=make_q(), reveal_mode=True)
    s.start()
    s.answer(user_id=1, chosen_index=0)
    assert s.all_answered(participant_ids={1, 2}) is False
