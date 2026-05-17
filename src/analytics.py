"""Teacher analytics summary — post-game insights for closes #6."""
from __future__ import annotations

from dataclasses import dataclass, field

from .session import Question, QuizSession


@dataclass
class SessionSummary:
    total_participants: int
    class_accuracy: float                    # 0.0–1.0 mean across all questions
    weak_questions: list[Question]           # accuracy < 60%
    top_mistake: Question | None             # lowest accuracy question
    avg_response_ms: float | None            # mean across all timed answers
    # [(count, label), ...] sorted descending
    top_misconceptions: list[tuple[int, str]] = field(default_factory=list)

    def format_text(self) -> str:
        pct = round(self.class_accuracy * 100)
        lines = [
            "📊 Підсумок сесії",
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
        if self.top_misconceptions:
            mc_lines = [f"  • {label} ({count} уч.)" for count, label in self.top_misconceptions[:3]]
            lines.append("🧠 Типові misconceptions:\n" + "\n".join(mc_lines))
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

    # Collect misconceptions: option_misconceptions[chosen_idx] for wrong answers
    mc_counts: dict[str, int] = {}
    for q_idx, q in enumerate(session.questions):
        if not q.option_misconceptions:
            continue
        for uid, qa in session.answers.items():
            chosen = qa.get(q_idx)
            if chosen is not None and chosen != q.correct_index:
                label = q.option_misconceptions.get(chosen)
                if label:
                    mc_counts[label] = mc_counts.get(label, 0) + 1

    top_misconceptions = sorted(
        ((count, label) for label, count in mc_counts.items()),
        reverse=True,
    )

    return SessionSummary(
        total_participants=participants,
        class_accuracy=class_accuracy,
        weak_questions=weak,
        top_mistake=top_mistake,
        avg_response_ms=avg_ms,
        top_misconceptions=top_misconceptions,
    )
