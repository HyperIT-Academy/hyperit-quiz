"""Teacher analytics summary — post-game insights for closes #6."""
from __future__ import annotations

from dataclasses import dataclass

from .session import Question, QuizSession


@dataclass
class SessionSummary:
    total_participants: int
    class_accuracy: float          # 0.0–1.0 mean across all questions
    weak_questions: list[Question] # accuracy < 60%
    top_mistake: Question | None   # lowest accuracy question
    avg_response_ms: float | None  # mean across all timed answers

    def format_text(self) -> str:
        pct = round(self.class_accuracy * 100)
        lines = [
            f"📊 Підсумок сесії",
            f"👥 Учасників: {self.total_participants}",
            f"✅ Середня точність класу: {pct}%",
        ]
        if self.weak_questions:
            titles = ", ".join(f'"{q.text[:30]}"' for q in self.weak_questions)
            lines.append(f"⚠️ Слабкі теми: {titles}")
        if self.top_mistake:
            lines.append(f"💀 Найпроблемніше: \"{self.top_mistake.text[:40]}\"")
        if self.avg_response_ms is not None:
            lines.append(f"⏱ Середній час відповіді: {round(self.avg_response_ms / 1000, 1)}с")
        return "\n".join(lines)


def build_summary(session: QuizSession) -> SessionSummary:
    participants = len(session.answers)

    accuracies = [
        acc
        for idx in range(len(session.questions))
        if (acc := session.question_accuracy(idx)) is not None
    ]
    class_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

    weak = session.weak_questions()

    top_mistake: Question | None = None
    worst_acc = 1.1
    for idx, q in enumerate(session.questions):
        acc = session.question_accuracy(idx)
        if acc is not None and acc < worst_acc:
            worst_acc = acc
            top_mistake = q

    all_times = [
        t
        for uid_times in session.response_times.values()
        for t in uid_times.values()
        if t is not None
    ]
    avg_ms = sum(all_times) / len(all_times) if all_times else None

    return SessionSummary(
        total_participants=participants,
        class_accuracy=class_accuracy,
        weak_questions=weak,
        top_mistake=top_mistake,
        avg_response_ms=avg_ms,
    )
