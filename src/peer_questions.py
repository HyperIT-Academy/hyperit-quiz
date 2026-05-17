"""Peer teaching: student question submission and review."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from src.session import Question


class SubmissionStatus(Enum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()


@dataclass
class QuestionSubmission:
    id: int
    author_id: int
    question: Question
    status: SubmissionStatus = SubmissionStatus.PENDING
    rejection_reason: str | None = None


def validate_question(q: Question) -> list[str]:
    """Return list of validation error strings (empty = valid)."""
    errors: list[str] = []
    if not q.text or not q.text.strip():
        errors.append("text не може бути пустим")
    if len(q.options) < 2:
        errors.append("мінімум 2 варіанти відповідей (options)")
    if not (0 <= q.correct_index < len(q.options)):
        errors.append(
            f"correct_index ({q.correct_index}) має бути в межах options "
            f"(0..{max(0, len(q.options) - 1)})"
        )
    if not q.explanation or not q.explanation.strip():
        errors.append("explanation не може бути пустим")
    return errors


class PeerQuestionBank:
    def __init__(self) -> None:
        self._submissions: dict[int, QuestionSubmission] = {}
        self._next_id: int = 1

    def submit(self, author_id: int, question: Question) -> QuestionSubmission:
        sub = QuestionSubmission(
            id=self._next_id,
            author_id=author_id,
            question=question,
        )
        self._submissions[sub.id] = sub
        self._next_id += 1
        return sub

    def approve(self, submission_id: int) -> None:
        sub = self._get_or_raise(submission_id)
        sub.status = SubmissionStatus.APPROVED

    def reject(self, submission_id: int, reason: str) -> None:
        sub = self._get_or_raise(submission_id)
        sub.status = SubmissionStatus.REJECTED
        sub.rejection_reason = reason

    def get_approved(self) -> list[Question]:
        return [
            s.question
            for s in self._submissions.values()
            if s.status == SubmissionStatus.APPROVED
        ]

    def get_pending(self) -> list[QuestionSubmission]:
        return [
            s
            for s in self._submissions.values()
            if s.status == SubmissionStatus.PENDING
        ]

    def author_stats(self, author_id: int) -> dict:
        author_subs = [
            s for s in self._submissions.values() if s.author_id == author_id
        ]
        return {
            "submitted": len(author_subs),
            "approved": sum(
                1 for s in author_subs if s.status == SubmissionStatus.APPROVED
            ),
            "rejected": sum(
                1 for s in author_subs if s.status == SubmissionStatus.REJECTED
            ),
        }

    # ── internals ────────────────────────────────────────────────────────────

    def _get_or_raise(self, submission_id: int) -> QuestionSubmission:
        if submission_id not in self._submissions:
            raise KeyError(f"Submission {submission_id} not found")
        return self._submissions[submission_id]
