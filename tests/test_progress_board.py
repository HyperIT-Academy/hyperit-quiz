"""Tests for ProgressBoard — growth-ranking leaderboard (closes #17) — RED phase."""
from __future__ import annotations

import pytest
from src.progress_board import ProgressBoard, PlayerProgress


# ── PlayerProgress dataclass ─────────────────────────────────────────────────

def test_player_progress_with_improvement():
    p = PlayerProgress(user_id=1, current_score=8, previous_score=5, improvement=3)
    assert p.improvement == 3


def test_player_progress_no_previous():
    p = PlayerProgress(user_id=1, current_score=7, previous_score=None, improvement=None)
    assert p.previous_score is None
    assert p.improvement is None


# ── record_session ────────────────────────────────────────────────────────────

def test_first_session_no_previous():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=10, score=5)
    lb = board.leaderboard(quiz_id=1)
    assert len(lb) == 1
    assert lb[0].user_id == 10
    assert lb[0].current_score == 5
    assert lb[0].previous_score is None
    assert lb[0].improvement is None


def test_second_session_sets_improvement():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=10, score=5)
    board.record_session(quiz_id=1, user_id=10, score=8)
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].previous_score == 5
    assert lb[0].current_score == 8
    assert lb[0].improvement == 3


def test_negative_improvement():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=10, score=9)
    board.record_session(quiz_id=1, user_id=10, score=6)
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].improvement == -3


def test_zero_improvement():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=10, score=7)
    board.record_session(quiz_id=1, user_id=10, score=7)
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].improvement == 0


# ── leaderboard sorting ───────────────────────────────────────────────────────

def test_leaderboard_sorted_by_improvement_desc():
    board = ProgressBoard()
    # user 1: improvement=1, user 2: improvement=5
    board.record_session(quiz_id=1, user_id=1, score=4)
    board.record_session(quiz_id=1, user_id=1, score=5)
    board.record_session(quiz_id=1, user_id=2, score=3)
    board.record_session(quiz_id=1, user_id=2, score=8)
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].user_id == 2  # improvement=5 > 1
    assert lb[1].user_id == 1


def test_leaderboard_tiebreak_by_current_score():
    board = ProgressBoard()
    # both improvement=2, but user 2 has higher current_score
    board.record_session(quiz_id=1, user_id=1, score=5)
    board.record_session(quiz_id=1, user_id=1, score=7)   # +2
    board.record_session(quiz_id=1, user_id=2, score=6)
    board.record_session(quiz_id=1, user_id=2, score=8)   # +2
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].user_id == 2  # same improvement, higher current_score


def test_no_previous_session_goes_to_end():
    board = ProgressBoard()
    # user 1: has improvement, user 2: first session (None)
    board.record_session(quiz_id=1, user_id=1, score=3)
    board.record_session(quiz_id=1, user_id=1, score=5)   # improvement=2
    board.record_session(quiz_id=1, user_id=2, score=10)  # no previous
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].user_id == 1   # improvement=2 → перший
    assert lb[1].user_id == 2   # improvement=None → останній


def test_multiple_none_improvement_sorted_by_current_score():
    board = ProgressBoard()
    # both have None improvement — fall back to current_score desc
    board.record_session(quiz_id=1, user_id=1, score=4)
    board.record_session(quiz_id=1, user_id=2, score=9)
    lb = board.leaderboard(quiz_id=1)
    assert lb[0].user_id == 2   # higher current_score
    assert lb[1].user_id == 1


# ── quiz isolation ────────────────────────────────────────────────────────────

def test_different_quizzes_are_independent():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=1, score=5)
    board.record_session(quiz_id=2, user_id=1, score=10)
    lb1 = board.leaderboard(quiz_id=1)
    lb2 = board.leaderboard(quiz_id=2)
    # quiz 1 history doesn't bleed into quiz 2
    assert lb1[0].previous_score is None
    assert lb2[0].previous_score is None


def test_empty_leaderboard_returns_empty_list():
    board = ProgressBoard()
    assert board.leaderboard(quiz_id=99) == []


# ── format_text ───────────────────────────────────────────────────────────────

def test_format_text_shows_persona_not_user_id():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=42, score=5)
    board.record_session(quiz_id=1, user_id=42, score=8)
    text = board.format_text(quiz_id=1, session_id=100)
    assert "42" not in text  # user_id замінено персонажем
    assert "8" in text       # current_score присутній


def test_format_text_shows_improvement_sign():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=1, score=5)
    board.record_session(quiz_id=1, user_id=1, score=8)
    text = board.format_text(quiz_id=1, session_id=1)
    assert "+3" in text


def test_format_text_rank_prefix():
    board = ProgressBoard()
    board.record_session(quiz_id=1, user_id=1, score=7)
    board.record_session(quiz_id=1, user_id=1, score=9)
    text = board.format_text(quiz_id=1, session_id=1)
    assert text.startswith("1.")
