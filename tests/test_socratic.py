"""Tests for Socratic mode — challenge wrong options, explain & rate."""
import pytest

from src.socratic import (
    ExplanationRating,
    ExplanationSubmission,
    SocraticChallenge,
    SocraticSession,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_session() -> SocraticSession:
    return SocraticSession()


# ── SocraticChallenge creation ────────────────────────────────────────────────

def test_create_challenge_returns_instance():
    session = make_session()
    challenge = session.create_challenge(
        question_id=1,
        wrong_option_index=2,
        wrong_option_text="Python — компільована мова",
    )
    assert isinstance(challenge, SocraticChallenge)


def test_create_challenge_fields():
    session = make_session()
    challenge = session.create_challenge(
        question_id=5,
        wrong_option_index=0,
        wrong_option_text="Java не має GC",
    )
    assert challenge.question_id == 5
    assert challenge.wrong_option_index == 0
    assert challenge.wrong_option_text == "Java не має GC"
    assert "Java не має GC" in challenge.prompt


def test_create_challenge_ids_are_sequential():
    session = make_session()
    c1 = session.create_challenge(1, 0, "A")
    c2 = session.create_challenge(2, 1, "B")
    assert c2.question_id != c1.question_id or c2.wrong_option_index != c1.wrong_option_index
    assert c1.question_id == 1
    assert c2.question_id == 2


# ── format_challenge ─────────────────────────────────────────────────────────

def test_format_challenge_contains_header():
    session = make_session()
    challenge = session.create_challenge(1, 0, "Неправильний варіант")
    formatted = session.format_challenge(challenge)
    assert "Socratic Challenge" in formatted


def test_format_challenge_contains_wrong_option_text():
    session = make_session()
    challenge = session.create_challenge(1, 0, "Земля пласка")
    formatted = session.format_challenge(challenge)
    assert "Земля пласка" in formatted


def test_format_challenge_contains_max_chars_hint():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    formatted = session.format_challenge(challenge)
    assert "300" in formatted


# ── submit_explanation ────────────────────────────────────────────────────────

def test_submit_explanation_returns_submission():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    sub = session.submit_explanation(challenge.question_id, author_id=42, text="Тому що...")
    assert isinstance(sub, ExplanationSubmission)
    assert sub.author_id == 42
    assert sub.text == "Тому що..."
    assert sub.rating is None


def test_submit_explanation_empty_text_raises():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    with pytest.raises(ValueError, match="порожн"):
        session.submit_explanation(challenge.question_id, author_id=1, text="")


def test_submit_explanation_whitespace_only_raises():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    with pytest.raises(ValueError):
        session.submit_explanation(challenge.question_id, author_id=1, text="   ")


def test_submit_explanation_over_300_chars_raises():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    long_text = "а" * 301
    with pytest.raises(ValueError, match="300"):
        session.submit_explanation(challenge.question_id, author_id=1, text=long_text)


def test_submit_explanation_exactly_300_chars_ok():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    text = "а" * 300
    sub = session.submit_explanation(challenge.question_id, author_id=1, text=text)
    assert len(sub.text) == 300


# ── rate_explanation ──────────────────────────────────────────────────────────

def test_rate_explanation_sets_rating():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    sub = session.submit_explanation(challenge.question_id, author_id=10, text="Пояснення")
    session.rate_explanation(sub.id, rated_by=99, rating=ExplanationRating.GOOD)
    assert sub.rating == ExplanationRating.GOOD
    assert sub.rated_by == 99


def test_rate_explanation_self_rating_raises():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    sub = session.submit_explanation(challenge.question_id, author_id=7, text="Пояснення")
    with pytest.raises(ValueError, match="(?i)автор"):
        session.rate_explanation(sub.id, rated_by=7, rating=ExplanationRating.FAIR)


def test_rate_explanation_unknown_submission_raises():
    session = make_session()
    with pytest.raises(KeyError):
        session.rate_explanation(submission_id=999, rated_by=1, rating=ExplanationRating.POOR)


# ── get_submissions ───────────────────────────────────────────────────────────

def test_get_submissions_empty_for_new_challenge():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    assert session.get_submissions(challenge.question_id) == []


def test_get_submissions_returns_all_for_challenge():
    session = make_session()
    c = session.create_challenge(1, 0, "X")
    session.submit_explanation(c.question_id, author_id=1, text="Перше")
    session.submit_explanation(c.question_id, author_id=2, text="Друге")
    subs = session.get_submissions(c.question_id)
    assert len(subs) == 2


def test_get_submissions_isolates_by_challenge():
    session = make_session()
    c1 = session.create_challenge(1, 0, "A")
    c2 = session.create_challenge(2, 1, "B")
    session.submit_explanation(c1.question_id, author_id=1, text="Для першого")
    subs_c2 = session.get_submissions(c2.question_id)
    assert subs_c2 == []


# ── best_explanation ──────────────────────────────────────────────────────────

def test_best_explanation_none_when_no_submissions():
    session = make_session()
    challenge = session.create_challenge(1, 0, "X")
    assert session.best_explanation(challenge.question_id) is None


def test_best_explanation_none_when_no_rated():
    session = make_session()
    c = session.create_challenge(1, 0, "X")
    session.submit_explanation(c.question_id, author_id=1, text="Без рейтингу")
    assert session.best_explanation(c.question_id) is None


def test_best_explanation_returns_highest_rated():
    session = make_session()
    c = session.create_challenge(1, 0, "X")
    s1 = session.submit_explanation(c.question_id, author_id=1, text="Погане")
    s2 = session.submit_explanation(c.question_id, author_id=2, text="Гарне")
    session.rate_explanation(s1.id, rated_by=99, rating=ExplanationRating.POOR)
    session.rate_explanation(s2.id, rated_by=98, rating=ExplanationRating.GOOD)
    best = session.best_explanation(c.question_id)
    assert best is s2


# ── ExplanationRating enum ────────────────────────────────────────────────────

def test_rating_enum_values():
    assert ExplanationRating.POOR.value == 1
    assert ExplanationRating.FAIR.value == 2
    assert ExplanationRating.GOOD.value == 3
