"""Tests for in-memory session store."""
from __future__ import annotations

from src.store import create_session, get_session, remove_session
from src.session import SessionState


def test_create_returns_session():
    s = create_session(chat_id=100)
    assert s is not None


def test_get_returns_same_session():
    create_session(chat_id=200)
    s = get_session(200)
    assert s is not None


def test_get_unknown_returns_none():
    assert get_session(99999) is None


def test_remove_cleans_up():
    create_session(chat_id=300)
    remove_session(300)
    assert get_session(300) is None


def test_new_session_has_demo_questions():
    s = create_session(chat_id=400)
    assert len(s.questions) == 3


def test_session_starts_waiting():
    s = create_session(chat_id=500)
    assert s.state == SessionState.WAITING
