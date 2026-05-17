"""Tests for anonymous persona assignment (RED phase)."""
from __future__ import annotations

import pytest
from src.personas import assign_persona, format_leaderboard_anonymous, PERSONAS


def test_personas_pool_large_enough():
    assert len(PERSONAS) >= 30


def test_assign_returns_string():
    name = assign_persona(user_id=1, session_id=10)
    assert isinstance(name, str)
    assert len(name) > 0


def test_same_user_same_session_stable():
    a = assign_persona(user_id=42, session_id=5)
    b = assign_persona(user_id=42, session_id=5)
    assert a == b


def test_different_users_different_personas():
    names = {assign_persona(user_id=i, session_id=99) for i in range(20)}
    assert len(names) > 1


def test_no_collision_in_small_group():
    names = [assign_persona(user_id=i, session_id=777) for i in range(10)]
    assert len(names) == len(set(names))


def test_format_leaderboard_hides_user_ids():
    board = [(1, 3), (2, 2), (3, 1)]
    text = format_leaderboard_anonymous(board, session_id=1)
    assert "1" not in text or text.count("1") <= 2  # rank numbers ok, user IDs not
    assert "user_id" not in text.lower()


def test_format_leaderboard_shows_scores():
    board = [(10, 5), (20, 3)]
    text = format_leaderboard_anonymous(board, session_id=2)
    assert "5" in text
    assert "3" in text
