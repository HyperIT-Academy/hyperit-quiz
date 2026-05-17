"""Adaptive difficulty — #23."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.session import Question


class Difficulty(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"


_WEIGHTS: dict[Difficulty, int] = {
    Difficulty.BASIC: 1,
    Difficulty.ADVANCED: 2,
    Difficulty.EXPERT: 3,
}


@dataclass
class AdaptiveQuestion:
    question: Question
    difficulty: Difficulty


class AdaptivePool:
    def __init__(self) -> None:
        # difficulty → ordered list of questions
        self._buckets: dict[Difficulty, list[Question]] = {}

    def add(self, question: Question, difficulty: Difficulty) -> None:
        self._buckets.setdefault(difficulty, []).append(question)

    def questions_for(self, difficulty: Difficulty) -> list[Question]:
        return list(self._buckets.get(difficulty, []))

    def all_difficulties(self) -> list[Difficulty]:
        return list(self._buckets.keys())


class AdaptiveSession:
    def __init__(self) -> None:
        # user_id → Difficulty
        self._tracks: dict[int, Difficulty] = {}
        # user_id → set of question ids already shown
        self._seen: dict[int, set[int]] = {}
        # user_id → list of (question_id, Difficulty) in order shown
        self._history: dict[int, list[tuple[int, Difficulty]]] = {}

    def assign(self, user_id: int, difficulty: Difficulty) -> None:
        self._tracks[user_id] = difficulty

    def track_of(self, user_id: int) -> Difficulty:
        return self._tracks[user_id]  # raises KeyError if unknown

    def next_question(self, user_id: int, pool: AdaptivePool) -> Question | None:
        difficulty = self._tracks[user_id]
        seen = self._seen.setdefault(user_id, set())
        for q in pool.questions_for(difficulty):
            if q.id not in seen:
                seen.add(q.id)
                self._history.setdefault(user_id, []).append((q.id, difficulty))
                return q
        return None

    def weighted_score(self, user_id: int, answers: dict[int, bool]) -> float:
        history = self._history.get(user_id, [])
        if not history:
            return 0.0
        max_possible = sum(_WEIGHTS[diff] for _, diff in history)
        if max_possible == 0:
            return 0.0
        earned = sum(
            _WEIGHTS[diff]
            for qid, diff in history
            if answers.get(qid, False)
        )
        return earned / max_possible
