"""Follow-up question engine — ticket #33."""
from __future__ import annotations

from dataclasses import dataclass

from src.session import Question


@dataclass
class FollowUpQuestion:
    trigger_option_index: int  # хибний варіант що тригерить питання
    text: str                  # уточнюючий текст
    hint: str                  # підказка (чому саме ця помилка типова)


@dataclass
class FollowUpResult:
    shown: bool
    follow_up: FollowUpQuestion | None
    original_question: Question
    is_correct: bool = False   # True коли chosen_index == correct_index


class FollowUpEngine:
    def __init__(self) -> None:
        # _followups[question_id][option_index] = FollowUpQuestion
        self._followups: dict[int, dict[int, FollowUpQuestion]] = {}

    def register(self, question_id: int, follow_up: FollowUpQuestion) -> None:
        self._followups.setdefault(question_id, {})[follow_up.trigger_option_index] = follow_up

    def get_followup(self, question: Question, chosen_index: int) -> FollowUpResult:
        if chosen_index == question.correct_index:
            return FollowUpResult(
                shown=False,
                follow_up=None,
                original_question=question,
                is_correct=True,
            )
        registered = self._followups.get(question.id, {})
        fq = registered.get(chosen_index)
        if fq is not None:
            return FollowUpResult(
                shown=True,
                follow_up=fq,
                original_question=question,
                is_correct=False,
            )
        return FollowUpResult(
            shown=False,
            follow_up=None,
            original_question=question,
            is_correct=False,
        )

    def has_followup(self, question_id: int, option_index: int) -> bool:
        return option_index in self._followups.get(question_id, {})

    def format_response(self, result: FollowUpResult) -> str:
        if result.shown and result.follow_up is not None:
            return f"🤔 {result.follow_up.text}\n💡 Підказка: {result.follow_up.hint}"
        if result.is_correct:
            return f"✅ Правильно!\n💡 {result.original_question.explanation}"
        return f"❌ Не вірно.\n💡 {result.original_question.explanation}"
