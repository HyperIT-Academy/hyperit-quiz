"""Mistake Museum — aggregate wrong answers across a quiz session (closes #18)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .session import QuizSession


@dataclass
class MistakeEntry:
    question_text: str
    wrong_option: str        # текст хибного варіанту
    count: int               # скільки учнів обрали його
    correct_option: str      # правильний варіант
    explanation: str


class MistakeMuseum:
    def collect(self, session: QuizSession) -> list[MistakeEntry]:
        """Для кожного питання — топ хибний варіант (найбільше обраний).

        Ігнорує питання де всі відповіли правильно.
        Сортує за count desc.
        """
        entries: list[MistakeEntry] = []

        for q_idx, question in enumerate(session.questions):
            wrong_counts: Counter[int] = Counter()

            for uid_answers in session.answers.values():
                chosen = uid_answers.get(q_idx)
                if chosen is not None and chosen != question.correct_index:
                    wrong_counts[chosen] += 1

            if not wrong_counts:
                continue  # всі правильно або без відповідей

            top_wrong_idx, top_count = wrong_counts.most_common(1)[0]
            entries.append(
                MistakeEntry(
                    question_text=question.text,
                    wrong_option=question.options[top_wrong_idx],
                    count=top_count,
                    correct_option=question.options[question.correct_index],
                    explanation=question.explanation,
                )
            )

        entries.sort(key=lambda e: e.count, reverse=True)
        return entries

    def format_text(self, entries: list[MistakeEntry], top_n: int = 3) -> str:
        """Форматує для Telegram: анонімно, без імен, лише статистика."""
        lines = ["🏛 Музей помилок"]

        top = entries[:top_n]
        if not top:
            lines.append("Помилок не зафіксовано — всі відповіли правильно! 🎉")
            return "\n".join(lines)

        for rank, entry in enumerate(top, start=1):
            lines.append(
                f"\n{rank}. {entry.question_text}\n"
                f"   ❌ Хибна відповідь: «{entry.wrong_option}» — {entry.count} уч.\n"
                f"   ✅ Правильно: «{entry.correct_option}»\n"
                f"   💡 {entry.explanation}"
            )

        return "\n".join(lines)
