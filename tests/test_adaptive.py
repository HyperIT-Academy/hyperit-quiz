"""Tests for adaptive difficulty — #23."""
from __future__ import annotations

import pytest

from src.adaptive import AdaptivePool, AdaptiveSession, AdaptiveQuestion, Difficulty
from src.session import Question


# ── helpers ──────────────────────────────────────────────────────────────────

def make_question(qid: int, text: str = "Q") -> Question:
    return Question(
        id=qid,
        text=text,
        options=["A", "B", "C", "D"],
        correct_index=0,
        explanation="exp",
    )


# ── AdaptivePool ──────────────────────────────────────────────────────────────

def test_pool_add_and_questions_for():
    pool = AdaptivePool()
    q = make_question(1)
    pool.add(q, Difficulty.BASIC)
    assert pool.questions_for(Difficulty.BASIC) == [q]


def test_pool_questions_for_empty_difficulty():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.BASIC)
    assert pool.questions_for(Difficulty.ADVANCED) == []


def test_pool_questions_for_returns_only_matching_difficulty():
    pool = AdaptivePool()
    b = make_question(1)
    a = make_question(2)
    pool.add(b, Difficulty.BASIC)
    pool.add(a, Difficulty.ADVANCED)
    assert pool.questions_for(Difficulty.BASIC) == [b]
    assert pool.questions_for(Difficulty.ADVANCED) == [a]


def test_pool_all_difficulties_empty():
    pool = AdaptivePool()
    assert pool.all_difficulties() == []


def test_pool_all_difficulties_single():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.EXPERT)
    assert pool.all_difficulties() == [Difficulty.EXPERT]


def test_pool_all_difficulties_multiple_unique():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.BASIC)
    pool.add(make_question(2), Difficulty.EXPERT)
    pool.add(make_question(3), Difficulty.BASIC)  # duplicate difficulty
    result = pool.all_difficulties()
    assert set(result) == {Difficulty.BASIC, Difficulty.EXPERT}
    assert len(result) == 2  # no duplicates


# ── AdaptiveSession.assign / track_of ────────────────────────────────────────

def test_session_assign_and_track_of():
    session = AdaptiveSession()
    session.assign(42, Difficulty.ADVANCED)
    assert session.track_of(42) == Difficulty.ADVANCED


def test_session_track_of_unknown_user_raises():
    session = AdaptiveSession()
    with pytest.raises(KeyError):
        session.track_of(999)


def test_session_assign_overrides_existing_track():
    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)
    session.assign(1, Difficulty.EXPERT)
    assert session.track_of(1) == Difficulty.EXPERT


# ── AdaptiveSession.next_question ────────────────────────────────────────────

def test_next_question_returns_first_unseen():
    pool = AdaptivePool()
    q1, q2 = make_question(1), make_question(2)
    pool.add(q1, Difficulty.BASIC)
    pool.add(q2, Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)

    assert session.next_question(1, pool) == q1


def test_next_question_skips_already_seen():
    pool = AdaptivePool()
    q1, q2 = make_question(1), make_question(2)
    pool.add(q1, Difficulty.BASIC)
    pool.add(q2, Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)

    session.next_question(1, pool)  # consume q1
    assert session.next_question(1, pool) == q2


def test_next_question_returns_none_when_exhausted():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)

    session.next_question(1, pool)  # consume
    assert session.next_question(1, pool) is None


def test_next_question_independent_per_user():
    pool = AdaptivePool()
    q1, q2 = make_question(1), make_question(2)
    pool.add(q1, Difficulty.BASIC)
    pool.add(q2, Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)
    session.assign(2, Difficulty.BASIC)

    session.next_question(1, pool)  # user 1 sees q1
    # user 2 starts fresh
    assert session.next_question(2, pool) == q1


def test_next_question_only_from_user_track():
    pool = AdaptivePool()
    basic_q = make_question(1)
    expert_q = make_question(2)
    pool.add(basic_q, Difficulty.BASIC)
    pool.add(expert_q, Difficulty.EXPERT)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)

    assert session.next_question(1, pool) == basic_q
    assert session.next_question(1, pool) is None  # expert_q not in track


# ── AdaptiveSession.weighted_score ───────────────────────────────────────────

def test_weighted_score_all_correct_basic():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)

    session.next_question(1, pool)
    # answers: question id 1 → correct (True)
    score = session.weighted_score(1, {1: True})
    assert score == pytest.approx(1.0)


def test_weighted_score_all_wrong_returns_zero():
    pool = AdaptivePool()
    pool.add(make_question(1), Difficulty.BASIC)

    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)
    session.next_question(1, pool)

    score = session.weighted_score(1, {1: False})
    assert score == pytest.approx(0.0)


def test_weighted_score_mixed_advanced():
    """2 ADVANCED questions, 1 correct → 2/4 = 0.5."""
    pool = AdaptivePool()
    q1, q2 = make_question(1), make_question(2)
    pool.add(q1, Difficulty.ADVANCED)
    pool.add(q2, Difficulty.ADVANCED)

    session = AdaptiveSession()
    session.assign(1, Difficulty.ADVANCED)
    session.next_question(1, pool)
    session.next_question(1, pool)

    score = session.weighted_score(1, {1: True, 2: False})
    assert score == pytest.approx(0.5)


def test_weighted_score_expert_weights_3():
    """1 EXPERT correct → 3/3 = 1.0."""
    pool = AdaptivePool()
    pool.add(make_question(7), Difficulty.EXPERT)

    session = AdaptiveSession()
    session.assign(1, Difficulty.EXPERT)
    session.next_question(1, pool)

    score = session.weighted_score(1, {7: True})
    assert score == pytest.approx(1.0)


def test_weighted_score_no_questions_seen_returns_zero():
    """User assigned but never fetched any question."""
    session = AdaptiveSession()
    session.assign(1, Difficulty.BASIC)
    score = session.weighted_score(1, {})
    assert score == pytest.approx(0.0)


# ── AdaptiveQuestion dataclass ────────────────────────────────────────────────

def test_adaptive_question_holds_question_and_difficulty():
    q = make_question(99)
    aq = AdaptiveQuestion(question=q, difficulty=Difficulty.EXPERT)
    assert aq.question is q
    assert aq.difficulty == Difficulty.EXPERT
