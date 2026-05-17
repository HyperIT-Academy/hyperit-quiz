"""Async (homework) quiz session — closes #4."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto

from src.session import Question


class AsyncSessionState(Enum):
    OPEN = auto()    # учні можуть відповідати
    CLOSED = auto()  # дедлайн минув або вчитель закрив


@dataclass
class AsyncQuizSession:
    quiz_id: int
    questions: list[Question]
    deadline: date
    state: AsyncSessionState = AsyncSessionState.OPEN
    # answers[user_id][question_index] = chosen_index
    answers: dict[int, dict[int, int]] = field(default_factory=dict)

    def is_expired(self, as_of: date = None) -> bool:
        """True якщо as_of > deadline."""
        check = as_of if as_of is not None else date.today()
        return check > self.deadline

    def submit_answer(
        self,
        user_id: int,
        question_index: int,
        chosen_index: int,
        as_of: date = None,
    ) -> None:
        """Зберегти відповідь учня.

        Raises:
            RuntimeError: якщо сесія CLOSED або дедлайн минув.
            ValueError: якщо chosen_index виходить за межі варіантів.
        """
        if self.state == AsyncSessionState.CLOSED or self.is_expired(as_of):
            raise RuntimeError("Session is closed or deadline has passed")

        question = self.questions[question_index]
        if chosen_index < 0 or chosen_index >= len(question.options):
            raise ValueError(
                f"chosen_index {chosen_index} out of range "
                f"(question has {len(question.options)} options)"
            )

        user_answers = self.answers.setdefault(user_id, {})
        if question_index in user_answers:
            return  # дублікат — перша відповідь фінальна

        user_answers[question_index] = chosen_index

    def close(self) -> None:
        """Вчитель закриває сесію вручну."""
        self.state = AsyncSessionState.CLOSED

    def completion_rate(self, expected_participants: int) -> float:
        """% учнів що відповіли хоча б на одне питання."""
        if expected_participants == 0:
            return 0.0
        submitted = sum(1 for qa in self.answers.values() if qa)
        return submitted / expected_participants

    def score(self, user_id: int) -> int:
        """Кількість правильних відповідей для учня."""
        user_answers = self.answers.get(user_id, {})
        return sum(
            1
            for q_idx, chosen in user_answers.items()
            if self.questions[q_idx].correct_index == chosen
        )

    def leaderboard(self) -> list[tuple[int, int]]:
        """[(user_id, score)] відсортовано за спаданням."""
        return sorted(
            ((uid, self.score(uid)) for uid in self.answers),
            key=lambda x: x[1],
            reverse=True,
        )

    def pending_participants(self, all_user_ids: set[int]) -> set[int]:
        """Хто ще не відповів жодного разу."""
        submitted = {uid for uid, qa in self.answers.items() if qa}
        return all_user_ids - submitted
