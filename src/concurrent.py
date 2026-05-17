"""Thread-safe concurrent answer handling (closes #13)."""
from __future__ import annotations

import threading
from dataclasses import dataclass

from src.session import QuizSession, SessionState


@dataclass
class AnswerResult:
    accepted: bool        # чи прийнято відповідь
    duplicate: bool       # True якщо user вже відповів на це питання
    is_correct: bool      # чи правильна
    question_index: int


class ConcurrentQuizSession:
    """Thread-safe обгортка. Гарантує що дублікати відповідей відкидаються."""

    def __init__(self, session: QuizSession) -> None:
        self._session = session
        self._lock = threading.Lock()
        self._answered: dict[int, set[int]] = {}  # question_index → set of user_ids

    def submit_answer(
        self,
        user_id: int,
        question_index: int,
        chosen_index: int,
    ) -> AnswerResult:
        """Потокобезпечний submit. Дублікат відкидається (accepted=False, duplicate=True)."""
        with self._lock:
            answered_users = self._answered.setdefault(question_index, set())
            if user_id in answered_users:
                return AnswerResult(
                    accepted=False,
                    duplicate=True,
                    is_correct=False,
                    question_index=question_index,
                )
            answered_users.add(user_id)
            # Делегуємо у QuizSession тільки якщо сесія у стані QUESTION
            # і питання відповідає поточному індексу
            if (
                self._session.state == SessionState.QUESTION
                and self._session.current_index == question_index
            ):
                self._session.answer(user_id, chosen_index)

            question = self._session.questions[question_index]
            is_correct = question.correct_index == chosen_index

        return AnswerResult(
            accepted=True,
            duplicate=False,
            is_correct=is_correct,
            question_index=question_index,
        )

    def advance_question(self) -> bool:
        """Потокобезпечний перехід до наступного питання.
        Повертає False якщо сесія вже закінчена."""
        with self._lock:
            if self._session.state == SessionState.FINISHED:
                return False
            self._session.next_question()
            return True

    @property
    def current_question_index(self) -> int:
        with self._lock:
            return self._session.current_index

    def answered_count(self, question_index: int) -> int:
        """Кількість унікальних відповідей на дане питання."""
        with self._lock:
            return len(self._answered.get(question_index, set()))


class AnswerQueue:
    """FIFO черга відповідей для burst scenarios. Thread-safe."""

    def __init__(self) -> None:
        self._queue: list[tuple[int, int, int]] = []  # (user_id, q_idx, chosen_idx)
        self._lock = threading.Lock()

    def push(self, user_id: int, question_index: int, chosen_index: int) -> None:
        with self._lock:
            self._queue.append((user_id, question_index, chosen_index))

    def drain(self) -> list[tuple[int, int, int]]:
        """Атомарно забирає всі елементи з черги і повертає їх."""
        with self._lock:
            items = self._queue.copy()
            self._queue.clear()
            return items

    def size(self) -> int:
        with self._lock:
            return len(self._queue)
