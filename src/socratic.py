"""Socratic mode: challenge wrong options, collect and rate explanations."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class ExplanationRating(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3


@dataclass
class SocraticChallenge:
    question_id: int
    wrong_option_index: int
    wrong_option_text: str
    prompt: str


@dataclass
class ExplanationSubmission:
    id: int
    challenge_id: int
    author_id: int
    text: str
    rating: ExplanationRating | None = None
    rated_by: int | None = None


class SocraticSession:
    def __init__(self) -> None:
        # challenge_id → SocraticChallenge
        self._challenges: dict[int, SocraticChallenge] = {}
        # submission_id → ExplanationSubmission
        self._submissions: dict[int, ExplanationSubmission] = {}
        self._next_challenge_id: int = 1
        self._next_submission_id: int = 1

    def create_challenge(
        self,
        question_id: int,
        wrong_option_index: int,
        wrong_option_text: str,
    ) -> SocraticChallenge:
        prompt = f"Поясни чому варіант '{wrong_option_text}' неправильний"
        challenge = SocraticChallenge(
            question_id=question_id,
            wrong_option_index=wrong_option_index,
            wrong_option_text=wrong_option_text,
            prompt=prompt,
        )
        self._challenges[self._next_challenge_id] = challenge
        self._next_challenge_id += 1
        return challenge

    def submit_explanation(
        self,
        challenge_id: int,
        author_id: int,
        text: str,
    ) -> ExplanationSubmission:
        if not text or not text.strip():
            raise ValueError("Текст пояснення не може бути порожнім")
        if len(text) > 300:
            raise ValueError(
                f"Текст пояснення не може перевищувати 300 символів (отримано {len(text)})"
            )
        sub = ExplanationSubmission(
            id=self._next_submission_id,
            challenge_id=challenge_id,
            author_id=author_id,
            text=text,
        )
        self._submissions[self._next_submission_id] = sub
        self._next_submission_id += 1
        return sub

    def rate_explanation(
        self,
        submission_id: int,
        rated_by: int,
        rating: ExplanationRating,
    ) -> None:
        if submission_id not in self._submissions:
            raise KeyError(f"Submission {submission_id} not found")
        sub = self._submissions[submission_id]
        if rated_by == sub.author_id:
            raise ValueError(
                "Автор не може оцінювати власне пояснення"
            )
        sub.rating = rating
        sub.rated_by = rated_by

    def get_submissions(self, challenge_id: int) -> list[ExplanationSubmission]:
        return [
            s for s in self._submissions.values()
            if s.challenge_id == challenge_id
        ]

    def best_explanation(self, challenge_id: int) -> ExplanationSubmission | None:
        rated = [
            s for s in self.get_submissions(challenge_id)
            if s.rating is not None
        ]
        if not rated:
            return None
        return max(rated, key=lambda s: s.rating.value)

    def format_challenge(self, challenge: SocraticChallenge) -> str:
        return (
            "🧠 Socratic Challenge\n\n"
            f"Поясни чому варіант '{challenge.wrong_option_text}' неправильний.\n"
            "(max 300 символів)"
        )
