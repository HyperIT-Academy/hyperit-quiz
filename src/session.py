"""Quiz session state machine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple


class SessionState(Enum):
    WAITING = auto()
    QUESTION = auto()
    FINISHED = auto()


@dataclass(frozen=True)
class Question:
    id: int
    text: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizSession:
    def __init__(self, quiz_id: int, questions: list[Question]) -> None:
        self.quiz_id = quiz_id
        self.questions = questions
        self.state = SessionState.WAITING
        self.current_index = 0
        # answers[user_id][question_index] = chosen_index
        self.answers: dict[int, dict[int, int]] = {}

    # ── transitions ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if self.state != SessionState.WAITING:
            raise RuntimeError("Session already started")
        self.state = SessionState.QUESTION

    def next_question(self) -> None:
        self.current_index += 1
        if self.current_index >= len(self.questions):
            self.state = SessionState.FINISHED
        else:
            self.state = SessionState.QUESTION

    # ── actions ─────────────────────────────────────────────────────────────

    def answer(self, user_id: int, chosen_index: int) -> None:
        if self.state != SessionState.QUESTION:
            raise RuntimeError("Cannot answer outside of QUESTION state")
        user_answers = self.answers.setdefault(user_id, {})
        if self.current_index in user_answers:
            return  # duplicate — ignored
        user_answers[self.current_index] = chosen_index

    # ── queries ─────────────────────────────────────────────────────────────

    def current_question(self) -> Question:
        if self.state != SessionState.QUESTION:
            raise RuntimeError("No active question")
        return self.questions[self.current_index]

    def score(self, user_id: int) -> int:
        user_answers = self.answers.get(user_id, {})
        return sum(
            1
            for q_idx, chosen in user_answers.items()
            if self.questions[q_idx].correct_index == chosen
        )

    def leaderboard(self) -> list[tuple[int, int]]:
        """Returns [(user_id, score), ...] sorted descending."""
        all_users = set(self.answers)
        return sorted(
            ((uid, self.score(uid)) for uid in all_users),
            key=lambda x: x[1],
            reverse=True,
        )
