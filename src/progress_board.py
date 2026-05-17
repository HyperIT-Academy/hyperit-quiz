"""Progress leaderboard — growth-ranking by improvement (closes #17)."""
from __future__ import annotations

from dataclasses import dataclass

from src.personas import assign_persona


@dataclass
class PlayerProgress:
    user_id: int
    current_score: int
    previous_score: int | None
    improvement: int | None


class ProgressBoard:
    def __init__(self) -> None:
        # quiz_id → {user_id: [score, ...]}  (chronological)
        self._history: dict[int, dict[int, list[int]]] = {}

    def record_session(self, quiz_id: int, user_id: int, score: int) -> None:
        self._history.setdefault(quiz_id, {}).setdefault(user_id, []).append(score)

    def leaderboard(self, quiz_id: int) -> list[PlayerProgress]:
        users = self._history.get(quiz_id, {})
        result: list[PlayerProgress] = []
        for user_id, scores in users.items():
            current = scores[-1]
            previous = scores[-2] if len(scores) >= 2 else None
            improvement = (current - previous) if previous is not None else None
            result.append(PlayerProgress(
                user_id=user_id,
                current_score=current,
                previous_score=previous,
                improvement=improvement,
            ))

        # Players with improvement come first (desc), then None-improvement players.
        # Tiebreak within each group: current_score desc.
        def sort_key(p: PlayerProgress) -> tuple[int, int, int]:
            if p.improvement is not None:
                return (0, -p.improvement, -p.current_score)
            return (1, 0, -p.current_score)

        result.sort(key=sort_key)
        return result

    def format_text(self, quiz_id: int, session_id: int) -> str:
        lines: list[str] = []
        for rank, player in enumerate(self.leaderboard(quiz_id), 1):
            persona = assign_persona(player.user_id, session_id)
            if player.improvement is not None:
                sign = "+" if player.improvement >= 0 else ""
                detail = (
                    f"{sign}{player.improvement} "
                    f"(було {player.previous_score}, стало {player.current_score})"
                )
            else:
                detail = f"{player.current_score} балів"
            lines.append(f"{rank}. {persona} {detail}")
        return "\n".join(lines)
