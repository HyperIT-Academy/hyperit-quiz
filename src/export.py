"""Export formatters for quiz results (closes #15)."""
from __future__ import annotations

import csv
import io

from .analytics import SessionSummary
from .session import QuizSession


def session_to_csv(session: QuizSession, persona_map: dict[int, str]) -> str:
    """Return CSV string: persona, q1_correct, q2_correct, ..., total_score.

    Each row represents one participant's result.
    Correct answer → 1, wrong or no answer → 0.
    Users are sorted by user_id for deterministic output.
    """
    num_questions = len(session.questions)
    q_columns = [f"q{i + 1}_correct" for i in range(num_questions)]
    header = ["persona"] + q_columns + ["total_score"]

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)

    for user_id in sorted(session.answers):
        persona = persona_map.get(user_id, str(user_id))
        user_answers = session.answers[user_id]

        row_cols: list[int] = []
        for q_idx, question in enumerate(session.questions):
            chosen = user_answers.get(q_idx)
            correct = 1 if chosen == question.correct_index else 0
            row_cols.append(correct)

        total = sum(row_cols)
        writer.writerow([persona] + row_cols + [total])

    return output.getvalue()


def summary_to_text(summary: SessionSummary) -> str:
    """Full multi-line teacher report with per-question accuracy details."""
    pct = round(summary.class_accuracy * 100)
    lines = [
        "=== Звіт сесії для вчителя ===",
        f"Учасників: {summary.total_participants}",
        f"Середня точність класу: {pct}%",
    ]

    if summary.avg_response_ms is not None:
        lines.append(f"Середній час відповіді: {round(summary.avg_response_ms / 1000, 1)} с")

    lines.append("")
    lines.append("--- Питання ---")

    # Gather all questions from weak_questions and top_mistake to build full list.
    # We don't have a direct reference to session here, so we derive what we can
    # from summary fields.
    all_flagged = list(summary.weak_questions)
    if summary.top_mistake and summary.top_mistake not in all_flagged:
        all_flagged.append(summary.top_mistake)

    if all_flagged:
        for q in all_flagged:
            marker = "⚠️ СЛАБКЕ" if q in summary.weak_questions else ""
            if summary.top_mistake and q.id == summary.top_mistake.id:
                marker = "💀 НАЙГІРШЕ"
            lines.append(f"  [{q.id + 1}] {q.text}  {marker}")
            if q.explanation:
                lines.append(f"       Пояснення: {q.explanation}")
    else:
        lines.append("  (Всі питання виконано на відмінно)")

    if summary.weak_questions:
        lines.append("")
        lines.append("--- Слабкі теми ---")
        for q in summary.weak_questions:
            lines.append(f"  • {q.text[:60]}")

    if summary.top_mistake:
        lines.append("")
        lines.append(f"Найпроблемніше питання: {summary.top_mistake.text}")

    if summary.top_misconceptions:
        lines.append("")
        lines.append("--- Типові помилкові уявлення ---")
        for count, label in summary.top_misconceptions[:5]:
            lines.append(f"  • {label} — {count} уч.")

    return "\n".join(lines)
