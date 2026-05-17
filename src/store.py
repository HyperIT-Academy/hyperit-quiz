"""In-memory store of active quiz sessions keyed by chat_id."""
from __future__ import annotations

from .session import Question, QuizSession


_sessions: dict[int, QuizSession] = {}

DEMO_QUESTIONS = [
    Question(
        id=1,
        text="Що виведе цей код?\n\n```python\nfor i in range(3):\n    print(i)\n```",
        options=["0 1 2", "1 2 3", "0 1 2 3", "Помилка"],
        correct_index=0,
        explanation="range(3) генерує 0, 1, 2 — три числа починаючи з 0.",
    ),
    Question(
        id=2,
        text="Яка структура даних зберігає пари ключ→значення?",
        options=["Список (list)", "Словник (dict)", "Кортеж (tuple)", "Множина (set)"],
        correct_index=1,
        explanation="dict (словник) — це хеш-таблиця ключ→значення.",
    ),
    Question(
        id=3,
        text="Що означає DRY у програмуванні?",
        options=[
            "Don't Repeat Yourself",
            "Do Run Yearly",
            "Debug, Refactor, Yield",
            "Data Runs Yesterday",
        ],
        correct_index=0,
        explanation="DRY = Don't Repeat Yourself — уникати дублювання коду.",
    ),
]


def create_session(chat_id: int) -> QuizSession:
    session = QuizSession(quiz_id=chat_id, questions=list(DEMO_QUESTIONS))
    _sessions[chat_id] = session
    return session


def get_session(chat_id: int) -> QuizSession | None:
    return _sessions.get(chat_id)


def remove_session(chat_id: int) -> None:
    _sessions.pop(chat_id, None)
