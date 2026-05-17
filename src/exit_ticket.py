"""Exit Ticket module — quick post-lesson reflection (closes #19)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ExitTicketResult:
    user_id: int
    understood: str
    confused: str
    question: str


class ExitTicketSession:
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self._results: list[ExitTicketResult] = []

    def submit(
        self,
        user_id: int,
        understood: str,
        confused: str,
        question: str,
    ) -> ExitTicketResult:
        result = ExitTicketResult(
            user_id=user_id,
            understood=understood,
            confused=confused,
            question=question,
        )
        self._results.append(result)
        return result

    def all_results(self) -> list[ExitTicketResult]:
        return list(self._results)

    def completion_rate(self, expected_count: int) -> float:
        if expected_count <= 0:
            return 0.0
        return len(self._results) / expected_count

    def common_confusions(self) -> list[str]:
        counter = Counter(r.confused for r in self._results)
        return [text for text, _ in counter.most_common()]

    def teacher_summary(self) -> str:
        total = len(self._results)
        lines: list[str] = [
            f"Exit Ticket — {self.topic}",
            f"Здали: {total}",
        ]

        if self._results:
            top_confusions = self.common_confusions()[:3]
            lines.append("Топ непорозумінь: " + ", ".join(top_confusions))

            lines.append("Питання до вчителя:")
            for r in self._results:
                if r.question.strip():
                    lines.append(f"  • (user {r.user_id}) {r.question}")

        return "\n".join(lines)
