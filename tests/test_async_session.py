"""Tests for AsyncQuizSession — homework/async mode (closes #4)."""
from __future__ import annotations

import pytest
from datetime import date

from src.session import Question
from src.async_session import AsyncQuizSession, AsyncSessionState


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_question(qid: int, correct: int = 0) -> Question:
    return Question(
        id=qid,
        text=f"Question {qid}",
        options=["A", "B", "C"],
        correct_index=correct,
        explanation="explanation",
    )


def make_session(deadline: date = date(2030, 1, 1)) -> AsyncQuizSession:
    questions = [make_question(1, correct=0), make_question(2, correct=1)]
    return AsyncQuizSession(quiz_id=42, questions=questions, deadline=deadline)


# ── is_expired ────────────────────────────────────────────────────────────────

def test_not_expired_before_deadline():
    s = make_session(deadline=date(2030, 6, 1))
    assert s.is_expired(as_of=date(2030, 5, 31)) is False


def test_not_expired_on_deadline_day():
    s = make_session(deadline=date(2030, 6, 1))
    assert s.is_expired(as_of=date(2030, 6, 1)) is False


def test_expired_after_deadline():
    s = make_session(deadline=date(2030, 6, 1))
    assert s.is_expired(as_of=date(2030, 6, 2)) is True


# ── submit_answer — happy path ────────────────────────────────────────────────

def test_submit_answer_stores_answer():
    s = make_session()
    s.submit_answer(user_id=1, question_index=0, chosen_index=2, as_of=date(2029, 1, 1))
    assert s.answers[1][0] == 2


def test_submit_multiple_users():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    s.submit_answer(2, 0, 1, as_of=date(2029, 1, 1))
    assert s.answers[1][0] == 0
    assert s.answers[2][0] == 1


def test_duplicate_answer_ignored_first_is_final():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    s.submit_answer(1, 0, 2, as_of=date(2029, 1, 1))  # duplicate — should be ignored
    assert s.answers[1][0] == 0


# ── submit_answer — error cases ───────────────────────────────────────────────

def test_submit_raises_when_closed():
    s = make_session()
    s.close()
    with pytest.raises(RuntimeError):
        s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))


def test_submit_raises_when_expired():
    s = make_session(deadline=date(2020, 1, 1))
    with pytest.raises(RuntimeError):
        s.submit_answer(1, 0, 0, as_of=date(2020, 1, 2))


def test_submit_raises_on_invalid_chosen_index():
    s = make_session()
    with pytest.raises(ValueError):
        s.submit_answer(1, 0, 99, as_of=date(2029, 1, 1))


# ── close ────────────────────────────────────────────────────────────────────

def test_close_changes_state():
    s = make_session()
    assert s.state == AsyncSessionState.OPEN
    s.close()
    assert s.state == AsyncSessionState.CLOSED


# ── score ─────────────────────────────────────────────────────────────────────

def test_score_all_correct():
    s = make_session()
    # q0 correct=0, q1 correct=1
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    s.submit_answer(1, 1, 1, as_of=date(2029, 1, 1))
    assert s.score(1) == 2


def test_score_none_correct():
    s = make_session()
    s.submit_answer(1, 0, 2, as_of=date(2029, 1, 1))
    s.submit_answer(1, 1, 2, as_of=date(2029, 1, 1))
    assert s.score(1) == 0


def test_score_user_with_no_answers():
    s = make_session()
    assert s.score(999) == 0


# ── leaderboard ───────────────────────────────────────────────────────────────

def test_leaderboard_sorted_desc():
    s = make_session()
    s.submit_answer(1, 0, 2, as_of=date(2029, 1, 1))  # 0 correct
    s.submit_answer(2, 0, 0, as_of=date(2029, 1, 1))  # 1 correct
    s.submit_answer(2, 1, 1, as_of=date(2029, 1, 1))  # 2 correct total
    board = s.leaderboard()
    assert board[0] == (2, 2)
    assert board[1] == (1, 0)


def test_leaderboard_empty_when_no_answers():
    s = make_session()
    assert s.leaderboard() == []


# ── completion_rate ───────────────────────────────────────────────────────────

def test_completion_rate_all_submitted():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    s.submit_answer(2, 0, 0, as_of=date(2029, 1, 1))
    assert s.completion_rate(expected_participants=2) == 1.0


def test_completion_rate_partial():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    assert s.completion_rate(expected_participants=4) == pytest.approx(0.25)


def test_completion_rate_zero_expected():
    s = make_session()
    assert s.completion_rate(expected_participants=0) == 0.0


# ── pending_participants ──────────────────────────────────────────────────────

def test_pending_participants_all_pending():
    s = make_session()
    result = s.pending_participants({1, 2, 3})
    assert result == {1, 2, 3}


def test_pending_participants_some_submitted():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    result = s.pending_participants({1, 2, 3})
    assert result == {2, 3}


def test_pending_participants_all_submitted():
    s = make_session()
    s.submit_answer(1, 0, 0, as_of=date(2029, 1, 1))
    s.submit_answer(2, 1, 0, as_of=date(2029, 1, 1))
    result = s.pending_participants({1, 2})
    assert result == set()
