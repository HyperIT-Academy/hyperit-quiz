"""Tests for peer teaching — student question submission (TDD)."""
import pytest
from src.session import Question
from src.peer_questions import (
    SubmissionStatus,
    QuestionSubmission,
    PeerQuestionBank,
    validate_question,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_question(
    id=1,
    text="Що таке змінна?",
    options=("Контейнер даних", "Функція", "Клас"),
    correct_index=0,
    explanation="Змінна зберігає значення.",
    code_language=None,
) -> Question:
    return Question(
        id=id,
        text=text,
        options=list(options),
        correct_index=correct_index,
        explanation=explanation,
        code_language=code_language,
    )


# ── validate_question ─────────────────────────────────────────────────────────

def test_validate_valid_question_returns_no_errors():
    q = make_question()
    assert validate_question(q) == []


def test_validate_empty_text_returns_error():
    q = make_question(text="")
    errors = validate_question(q)
    assert any("text" in e.lower() for e in errors)


def test_validate_single_option_returns_error():
    q = make_question(options=("Тільки один",))
    errors = validate_question(q)
    assert any("option" in e.lower() or "варіант" in e.lower() for e in errors)


def test_validate_correct_index_out_of_range_returns_error():
    q = make_question(options=("A", "B"), correct_index=5)
    errors = validate_question(q)
    assert any("correct_index" in e.lower() or "index" in e.lower() for e in errors)


def test_validate_empty_explanation_returns_error():
    q = make_question(explanation="")
    errors = validate_question(q)
    assert any("explanation" in e.lower() for e in errors)


def test_validate_multiple_errors_returned_together():
    q = make_question(text="", explanation="")
    errors = validate_question(q)
    assert len(errors) >= 2


# ── PeerQuestionBank.submit ───────────────────────────────────────────────────

def test_submit_returns_submission_with_pending_status():
    bank = PeerQuestionBank()
    q = make_question()
    sub = bank.submit(author_id=42, question=q)
    assert sub.status == SubmissionStatus.PENDING
    assert sub.author_id == 42
    assert sub.question is q


def test_submit_assigns_unique_ids():
    bank = PeerQuestionBank()
    s1 = bank.submit(author_id=1, question=make_question(id=1))
    s2 = bank.submit(author_id=1, question=make_question(id=2))
    assert s1.id != s2.id


def test_submit_increments_id_sequentially():
    bank = PeerQuestionBank()
    s1 = bank.submit(author_id=1, question=make_question(id=1))
    s2 = bank.submit(author_id=2, question=make_question(id=2))
    assert s2.id == s1.id + 1


# ── approve / reject ──────────────────────────────────────────────────────────

def test_approve_changes_status_to_approved():
    bank = PeerQuestionBank()
    sub = bank.submit(author_id=1, question=make_question())
    bank.approve(sub.id)
    pending = bank.get_pending()
    assert all(s.id != sub.id for s in pending)
    approved = bank.get_approved()
    assert make_question() in approved


def test_reject_changes_status_to_rejected_with_reason():
    bank = PeerQuestionBank()
    sub = bank.submit(author_id=1, question=make_question())
    bank.reject(sub.id, reason="Некоректна відповідь")
    # rejected submission is no longer pending
    assert all(s.id != sub.id for s in bank.get_pending())
    # rejected question is not in approved
    assert make_question() not in bank.get_approved()


def test_approve_nonexistent_id_raises():
    bank = PeerQuestionBank()
    with pytest.raises((KeyError, ValueError)):
        bank.approve(999)


def test_reject_nonexistent_id_raises():
    bank = PeerQuestionBank()
    with pytest.raises((KeyError, ValueError)):
        bank.reject(999, reason="причина")


# ── get_approved / get_pending ────────────────────────────────────────────────

def test_get_pending_returns_only_pending_submissions():
    bank = PeerQuestionBank()
    s1 = bank.submit(author_id=1, question=make_question(id=1))
    s2 = bank.submit(author_id=2, question=make_question(id=2))
    bank.approve(s1.id)
    pending = bank.get_pending()
    ids = [s.id for s in pending]
    assert s1.id not in ids
    assert s2.id in ids


def test_get_approved_returns_questions_of_approved_submissions():
    bank = PeerQuestionBank()
    q = make_question()
    sub = bank.submit(author_id=1, question=q)
    bank.approve(sub.id)
    assert q in bank.get_approved()


def test_get_approved_excludes_pending_and_rejected():
    bank = PeerQuestionBank()
    q1 = make_question(id=1)
    q2 = make_question(id=2)
    s1 = bank.submit(author_id=1, question=q1)
    s2 = bank.submit(author_id=2, question=q2)
    bank.approve(s1.id)
    bank.reject(s2.id, reason="погане питання")
    approved = bank.get_approved()
    assert q1 in approved
    assert q2 not in approved


# ── author_stats ──────────────────────────────────────────────────────────────

def test_author_stats_initial_zeros():
    bank = PeerQuestionBank()
    stats = bank.author_stats(author_id=99)
    assert stats == {"submitted": 0, "approved": 0, "rejected": 0}


def test_author_stats_counts_correctly():
    bank = PeerQuestionBank()
    s1 = bank.submit(author_id=7, question=make_question(id=1))
    s2 = bank.submit(author_id=7, question=make_question(id=2))
    s3 = bank.submit(author_id=7, question=make_question(id=3))
    bank.approve(s1.id)
    bank.reject(s2.id, reason="причина")
    stats = bank.author_stats(author_id=7)
    assert stats == {"submitted": 3, "approved": 1, "rejected": 1}


def test_author_stats_does_not_count_other_authors():
    bank = PeerQuestionBank()
    s1 = bank.submit(author_id=1, question=make_question(id=1))
    bank.submit(author_id=2, question=make_question(id=2))
    bank.approve(s1.id)
    assert bank.author_stats(author_id=2)["approved"] == 0
