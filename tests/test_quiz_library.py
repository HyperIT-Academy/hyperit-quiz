"""Tests for QuizLibrary — sharing бібліотека для вчителів (#28)."""
from __future__ import annotations

from datetime import datetime

import pytest

from src.quiz_library import QuizLibrary, QuizMetadata


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def library() -> QuizLibrary:
    return QuizLibrary()


def _publish(lib: QuizLibrary, quiz_id: int = 1, title: str = "Python Basics",
             author_id: int = 10, tags: list[str] | None = None,
             question_count: int = 5) -> QuizMetadata:
    return lib.publish(quiz_id, title, author_id, tags or ["python"], question_count)


# ── QuizMetadata defaults ──────────────────────────────────────────────────────


def test_metadata_defaults() -> None:
    meta = QuizMetadata(quiz_id=1, title="T", author_id=99)
    assert meta.tags == []
    assert meta.question_count == 0
    assert meta.is_public is False
    assert isinstance(meta.created_at, datetime)


# ── publish ────────────────────────────────────────────────────────────────────


def test_publish_returns_public_metadata(library: QuizLibrary) -> None:
    meta = _publish(library)
    assert meta.is_public is True
    assert meta.quiz_id == 1
    assert meta.title == "Python Basics"
    assert meta.author_id == 10
    assert meta.tags == ["python"]
    assert meta.question_count == 5


def test_publish_stores_quiz(library: QuizLibrary) -> None:
    _publish(library)
    assert library.get(1) is not None


def test_publish_updates_existing(library: QuizLibrary) -> None:
    _publish(library, title="Old Title")
    updated = library.publish(1, "New Title", author_id=10, tags=["js"], question_count=10)
    assert updated.title == "New Title"
    assert updated.tags == ["js"]
    assert updated.question_count == 10
    assert updated.is_public is True


def test_publish_update_keeps_only_one_entry(library: QuizLibrary) -> None:
    _publish(library)
    _publish(library, title="Updated")
    # search має повертати лише 1 запис
    results = library.search()
    assert len(results) == 1


def test_publish_different_quizzes(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    _publish(library, quiz_id=2, author_id=20, title="JS Basics", tags=["js"])
    assert len(library.search()) == 2


# ── unpublish ──────────────────────────────────────────────────────────────────


def test_unpublish_returns_true_for_author(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    result = library.unpublish(1, author_id=10)
    assert result is True


def test_unpublish_makes_quiz_private(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.unpublish(1, author_id=10)
    assert library.get(1) is not None          # запис лишається
    assert library.get(1).is_public is False   # але приватний


def test_unpublish_not_found_returns_false(library: QuizLibrary) -> None:
    result = library.unpublish(999, author_id=10)
    assert result is False


def test_unpublish_wrong_author_returns_false(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    result = library.unpublish(1, author_id=99)
    assert result is False


def test_unpublish_wrong_author_does_not_change_quiz(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.unpublish(1, author_id=99)
    assert library.get(1).is_public is True


# ── search ─────────────────────────────────────────────────────────────────────


def test_search_returns_only_public(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.unpublish(1, author_id=10)  # тепер приватний
    _publish(library, quiz_id=2, author_id=20, title="JS Quiz", tags=["js"])
    results = library.search()
    assert len(results) == 1
    assert results[0].quiz_id == 2


def test_search_no_filters_returns_all_public(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10, tags=["python"])
    _publish(library, quiz_id=2, author_id=20, title="JS", tags=["js"])
    results = library.search()
    assert {r.quiz_id for r in results} == {1, 2}


def test_search_by_tag_filters_correctly(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, tags=["python", "beginner"])
    _publish(library, quiz_id=2, title="JS", author_id=20, tags=["js"])
    results = library.search(tag="python")
    assert len(results) == 1
    assert results[0].quiz_id == 1


def test_search_by_author_filters_correctly(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    _publish(library, quiz_id=2, title="JS", author_id=20, tags=["js"])
    results = library.search(author_id=10)
    assert len(results) == 1
    assert results[0].author_id == 10


def test_search_combined_tag_and_author(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10, tags=["python"])
    _publish(library, quiz_id=2, title="JS", author_id=10, tags=["js"])
    _publish(library, quiz_id=3, title="Py2", author_id=20, tags=["python"])
    results = library.search(tag="python", author_id=10)
    assert len(results) == 1
    assert results[0].quiz_id == 1


def test_search_sorted_newest_first(library: QuizLibrary) -> None:
    meta1 = _publish(library, quiz_id=1, author_id=10)
    meta2 = _publish(library, quiz_id=2, title="Newer", author_id=10, tags=["js"])
    # Щоб гарантувати порядок — патчимо created_at
    meta1.created_at = datetime(2026, 1, 1)
    meta2.created_at = datetime(2026, 6, 1)
    results = library.search()
    assert results[0].quiz_id == 2


# ── get ────────────────────────────────────────────────────────────────────────


def test_get_existing(library: QuizLibrary) -> None:
    _publish(library, quiz_id=42)
    meta = library.get(42)
    assert meta is not None
    assert meta.quiz_id == 42


def test_get_nonexistent_returns_none(library: QuizLibrary) -> None:
    assert library.get(999) is None


# ── clone ──────────────────────────────────────────────────────────────────────


def test_clone_public_quiz(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10, tags=["python"], question_count=8)
    clone = library.clone(quiz_id=1, new_author_id=20, new_quiz_id=100)
    assert clone is not None
    assert clone.quiz_id == 100
    assert clone.author_id == 20
    assert clone.tags == ["python"]
    assert clone.question_count == 8
    assert clone.is_public is False  # клон приватний за замовчуванням


def test_clone_stores_new_quiz(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.clone(quiz_id=1, new_author_id=20, new_quiz_id=100)
    assert library.get(100) is not None


def test_clone_nonexistent_returns_none(library: QuizLibrary) -> None:
    result = library.clone(quiz_id=999, new_author_id=20, new_quiz_id=100)
    assert result is None


def test_clone_private_quiz_returns_none(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.unpublish(1, author_id=10)
    result = library.clone(quiz_id=1, new_author_id=20, new_quiz_id=100)
    assert result is None


def test_clone_does_not_affect_original(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10, title="Original")
    library.clone(quiz_id=1, new_author_id=20, new_quiz_id=100)
    assert library.get(1).author_id == 10
    assert library.get(1).title == "Original"


# ── author_quizzes ─────────────────────────────────────────────────────────────


def test_author_quizzes_returns_all_own(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    _publish(library, quiz_id=2, title="Q2", author_id=10, tags=["js"])
    _publish(library, quiz_id=3, title="Other", author_id=20, tags=["other"])
    results = library.author_quizzes(author_id=10)
    assert {r.quiz_id for r in results} == {1, 2}


def test_author_quizzes_includes_private(library: QuizLibrary) -> None:
    _publish(library, quiz_id=1, author_id=10)
    library.unpublish(1, author_id=10)
    results = library.author_quizzes(author_id=10)
    assert len(results) == 1
    assert results[0].is_public is False


def test_author_quizzes_sorted_newest_first(library: QuizLibrary) -> None:
    meta1 = _publish(library, quiz_id=1, author_id=10)
    meta2 = _publish(library, quiz_id=2, title="Newer", author_id=10, tags=["js"])
    meta1.created_at = datetime(2026, 1, 1)
    meta2.created_at = datetime(2026, 6, 1)
    results = library.author_quizzes(author_id=10)
    assert results[0].quiz_id == 2


def test_author_quizzes_empty_for_unknown_author(library: QuizLibrary) -> None:
    results = library.author_quizzes(author_id=999)
    assert results == []
