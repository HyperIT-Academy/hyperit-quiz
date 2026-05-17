"""Quiz sharing library — вчителі діляться квізами між собою (#28)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QuizMetadata:
    quiz_id: int
    title: str
    author_id: int
    tags: list[str] = field(default_factory=list)
    question_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_public: bool = False


class QuizLibrary:
    """In-memory бібліотека квізів для обміну між вчителями."""

    def __init__(self) -> None:
        self._quizzes: dict[int, QuizMetadata] = {}

    def publish(self, quiz_id: int, title: str, author_id: int,
                tags: list[str], question_count: int) -> QuizMetadata:
        """Публікує квіз у бібліотеку (is_public=True). Якщо вже є — оновлює."""
        existing = self._quizzes.get(quiz_id)
        if existing is not None:
            existing.title = title
            existing.author_id = author_id
            existing.tags = tags
            existing.question_count = question_count
            existing.is_public = True
            return existing
        meta = QuizMetadata(
            quiz_id=quiz_id,
            title=title,
            author_id=author_id,
            tags=tags,
            question_count=question_count,
            is_public=True,
        )
        self._quizzes[quiz_id] = meta
        return meta

    def unpublish(self, quiz_id: int, author_id: int) -> bool:
        """Знімає з публікації. Повертає False якщо не знайдено або не автор."""
        meta = self._quizzes.get(quiz_id)
        if meta is None or meta.author_id != author_id:
            return False
        meta.is_public = False
        return True

    def search(self, tag: str | None = None,
               author_id: int | None = None) -> list[QuizMetadata]:
        """Повертає тільки публічні квізи, відфільтровані за параметрами.
        tag: None = всі теги. author_id: None = всі автори.
        Відсортовано: новіші першими."""
        results = [
            m for m in self._quizzes.values()
            if m.is_public
            and (tag is None or tag in m.tags)
            and (author_id is None or m.author_id == author_id)
        ]
        return sorted(results, key=lambda m: m.created_at, reverse=True)

    def get(self, quiz_id: int) -> QuizMetadata | None:
        """Повертає метадані або None якщо не знайдено."""
        return self._quizzes.get(quiz_id)

    def clone(self, quiz_id: int, new_author_id: int,
              new_quiz_id: int) -> QuizMetadata | None:
        """Клонує публічний квіз для нового автора (is_public=False за замовчуванням).
        Повертає None якщо оригінал не знайдено або не публічний."""
        original = self._quizzes.get(quiz_id)
        if original is None or not original.is_public:
            return None
        clone = QuizMetadata(
            quiz_id=new_quiz_id,
            title=original.title,
            author_id=new_author_id,
            tags=list(original.tags),
            question_count=original.question_count,
            is_public=False,
        )
        self._quizzes[new_quiz_id] = clone
        return clone

    def author_quizzes(self, author_id: int) -> list[QuizMetadata]:
        """Всі квізи автора (публічні та приватні), новіші першими."""
        results = [m for m in self._quizzes.values() if m.author_id == author_id]
        return sorted(results, key=lambda m: m.created_at, reverse=True)
