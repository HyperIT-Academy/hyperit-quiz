"""Tests for team mode scoring (closes #3) — RED phase."""
from __future__ import annotations

import pytest
from src.teams import Team, TeamSession, assign_teams_auto


# ── Team dataclass ───────────────────────────────────────────────────────────

def test_team_starts_zero():
    t = Team(name="Дракони", member_ids={1, 2, 3})
    assert t.score == 0


def test_team_add_score():
    t = Team(name="Дракони", member_ids={1, 2, 3})
    t.add_score(2)
    assert t.score == 2


# ── auto-assign ──────────────────────────────────────────────────────────────

def test_assign_teams_auto_two_teams():
    teams = assign_teams_auto(user_ids=[1, 2, 3, 4], n_teams=2)
    assert len(teams) == 2
    all_members = set().union(*(t.member_ids for t in teams))
    assert all_members == {1, 2, 3, 4}


def test_assign_teams_no_overlap():
    teams = assign_teams_auto(user_ids=list(range(10)), n_teams=3)
    all_ids = [uid for t in teams for uid in t.member_ids]
    assert len(all_ids) == len(set(all_ids))


def test_assign_teams_balanced():
    teams = assign_teams_auto(user_ids=list(range(6)), n_teams=2)
    sizes = [len(t.member_ids) for t in teams]
    assert max(sizes) - min(sizes) <= 1


# ── TeamSession ──────────────────────────────────────────────────────────────

def test_team_session_team_of_user():
    teams = [
        Team(name="A", member_ids={1, 2}),
        Team(name="B", member_ids={3, 4}),
    ]
    ts = TeamSession(teams=teams)
    assert ts.team_of(user_id=1).name == "A"
    assert ts.team_of(user_id=3).name == "B"


def test_team_session_unknown_user_returns_none():
    ts = TeamSession(teams=[Team(name="A", member_ids={1})])
    assert ts.team_of(user_id=99) is None


def test_team_session_record_correct_adds_to_team():
    teams = [Team(name="A", member_ids={1, 2}), Team(name="B", member_ids={3})]
    ts = TeamSession(teams=teams)
    ts.record_answer(user_id=1, is_correct=True)
    ts.record_answer(user_id=2, is_correct=False)
    assert ts.team_of(1).score == 1
    assert ts.team_of(3).score == 0


def test_team_leaderboard_sorted():
    teams = [
        Team(name="A", member_ids={1}),
        Team(name="B", member_ids={2}),
    ]
    ts = TeamSession(teams=teams)
    ts.record_answer(user_id=2, is_correct=True)
    ts.record_answer(user_id=2, is_correct=True)
    ts.record_answer(user_id=1, is_correct=True)
    board = ts.leaderboard()
    assert board[0].name == "B"
    assert board[1].name == "A"


def test_team_leaderboard_format():
    teams = [Team(name="Дракони", member_ids={1})]
    ts = TeamSession(teams=teams)
    ts.record_answer(user_id=1, is_correct=True)
    text = ts.format_leaderboard()
    assert "Дракони" in text
    assert "1" in text
