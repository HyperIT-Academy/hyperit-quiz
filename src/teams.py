"""Team mode scoring (closes #3)."""
from __future__ import annotations

from dataclasses import dataclass, field


TEAM_NAMES = [
    "🐉 Дракони", "🦁 Леви", "🦅 Орли", "🐺 Вовки",
    "🦊 Лисиці", "🐯 Тигри", "🦈 Акули", "🦉 Сови",
]


@dataclass
class Team:
    name: str
    member_ids: set[int]
    score: int = field(default=0, compare=False)

    def add_score(self, points: int = 1) -> None:
        self.score += points


class TeamSession:
    def __init__(self, teams: list[Team]) -> None:
        self.teams = teams
        self._user_team: dict[int, Team] = {
            uid: team
            for team in teams
            for uid in team.member_ids
        }

    def team_of(self, user_id: int) -> Team | None:
        return self._user_team.get(user_id)

    def record_answer(self, user_id: int, is_correct: bool) -> None:
        team = self.team_of(user_id)
        if team and is_correct:
            team.add_score(1)

    def leaderboard(self) -> list[Team]:
        return sorted(self.teams, key=lambda t: t.score, reverse=True)

    def format_leaderboard(self) -> str:
        lines = ["🏆 Командний рейтинг:"]
        for rank, team in enumerate(self.leaderboard(), 1):
            lines.append(f"{rank}. {team.name} — {team.score} балів")
        return "\n".join(lines)


def assign_teams_auto(user_ids: list[int], n_teams: int) -> list[Team]:
    """Round-robin distribution into n_teams balanced teams."""
    teams = [
        Team(name=TEAM_NAMES[i % len(TEAM_NAMES)], member_ids=set())
        for i in range(n_teams)
    ]
    for i, uid in enumerate(user_ids):
        teams[i % n_teams].member_ids.add(uid)
    return teams
