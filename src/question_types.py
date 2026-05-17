"""Question type definitions beyond basic multiple choice."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ORDERING = "ordering"
    MATCHING = "matching"


@dataclass
class ShortAnswerQuestion:
    id: int
    text: str
    correct_answers: list[str]
    explanation: str
    case_sensitive: bool = False

    def _normalise(self, s: str) -> str:
        s = s.strip()
        return s if self.case_sensitive else s.lower()

    def check(self, response: str) -> bool:
        """Exact match (strip + optional lower)."""
        normalised = self._normalise(response)
        return any(self._normalise(a) == normalised for a in self.correct_answers)

    def check_fuzzy(self, response: str, threshold: float = 0.8) -> bool:
        """Return True if best ratio among correct_answers >= threshold.

        Ratio = 2 * |common chars| / (|a| + |b|)  (simple character-level).
        """
        normalised = self._normalise(response)
        for answer in self.correct_answers:
            if self._ratio(self._normalise(answer), normalised) >= threshold:
                return True
        return False

    @staticmethod
    def _ratio(a: str, b: str) -> float:
        """Sequence-match ratio: 2*matching / (len(a)+len(b))."""
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        # count matching chars using a simple two-pointer approach on sorted bags
        from collections import Counter
        ca, cb = Counter(a), Counter(b)
        common = sum((ca & cb).values())
        return 2 * common / (len(a) + len(b))


@dataclass
class OrderingQuestion:
    id: int
    text: str
    correct_order: list[str]
    explanation: str

    def check(self, submitted_order: list[str]) -> bool:
        return submitted_order == self.correct_order

    def partial_score(self, submitted_order: list[str]) -> float:
        """Fraction of elements at the correct position (0.0–1.0)."""
        if not self.correct_order:
            return 0.0
        correct = sum(
            1
            for i, item in enumerate(submitted_order)
            if i < len(self.correct_order) and item == self.correct_order[i]
        )
        return correct / len(self.correct_order)


@dataclass
class MatchingQuestion:
    id: int
    text: str
    pairs: dict[str, str]  # key → correct_value
    explanation: str

    def check(self, submitted: dict[str, str]) -> bool:
        """All pairs must be correct."""
        return all(submitted.get(k) == v for k, v in self.pairs.items())

    def partial_score(self, submitted: dict[str, str]) -> float:
        """Fraction of correct pairs out of all expected pairs (0.0–1.0)."""
        if not self.pairs:
            return 0.0
        correct = sum(1 for k, v in self.pairs.items() if submitted.get(k) == v)
        return correct / len(self.pairs)
