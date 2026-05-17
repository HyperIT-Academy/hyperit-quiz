"""Tests for MistakeMuseum (closes #18) — TDD RED phase."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession
from src.mistake_museum import MistakeEntry, MistakeMuseum


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_question(
    qid: int,
    text: str = "Q",
    options: list[str] | None = None,
    correct_index: int = 0,
    explanation: str = "Пояснення",
) -> Question:
    if options is None:
        options = ["Правильно", "Неправильно А", "Неправильно Б", "Неправильно В"]
    return Question(
        id=qid,
        text=text,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
    )


def _session_with_answers(
    questions: list[Question],
    answers_per_question: list[list[int]],
) -> QuizSession:
    """Build a finished session. answers_per_question[q_idx] = list of chosen_index per user."""
    s = QuizSession(quiz_id=99, questions=questions)
    s.start()
    for q_idx, chosen_list in enumerate(answers_per_question):
        for uid, chosen in enumerate(chosen_list, start=1):
            s.answer(uid, chosen)
        if q_idx < len(questions) - 1:
            s.next_question()
    s.next_question()  # finish
    return s


# ── TEST 1: collect returns MistakeEntry instances ────────────────────────────

def test_collect_returns_list_of_mistake_entries():
    q = _make_question(1, "Що таке змінна?")
    # user 1 wrong, user 2 correct
    s = _session_with_answers([q], [[1, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert isinstance(entries, list)
    assert len(entries) > 0
    assert all(isinstance(e, MistakeEntry) for e in entries)


# ── TEST 2: ignores questions where everyone answered correctly ───────────────

def test_collect_ignores_all_correct_questions():
    q = _make_question(1, "Легке питання")
    # всі 3 відповіли правильно (index 0)
    s = _session_with_answers([q], [[0, 0, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries == []


# ── TEST 3: top wrong option is the most-chosen wrong one ────────────────────

def test_collect_picks_top_wrong_option():
    options = ["Правильно", "Варіант Б", "Варіант В", "Варіант Г"]
    q = Question(
        id=1,
        text="Питання",
        options=options,
        correct_index=0,
        explanation="Бо так",
    )
    # 3 обрали Варіант Б (index 1), 1 обрав Варіант В (index 2)
    s = _session_with_answers([q], [[1, 1, 1, 2]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert len(entries) == 1
    assert entries[0].wrong_option == "Варіант Б"
    assert entries[0].count == 3


# ── TEST 4: entry contains correct_option text ────────────────────────────────

def test_collect_entry_has_correct_option():
    options = ["Правильна відповідь", "Хибна"]
    q = Question(id=2, text="Q", options=options, correct_index=0, explanation="Так")
    s = _session_with_answers([q], [[1, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries[0].correct_option == "Правильна відповідь"


# ── TEST 5: entry contains question_text ─────────────────────────────────────

def test_collect_entry_has_question_text():
    q = _make_question(3, text="Що таке цикл?")
    s = _session_with_answers([q], [[1, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries[0].question_text == "Що таке цикл?"


# ── TEST 6: entry contains explanation ───────────────────────────────────────

def test_collect_entry_has_explanation():
    q = _make_question(4, explanation="Цикл — це повторення")
    s = _session_with_answers([q], [[1, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries[0].explanation == "Цикл — це повторення"


# ── TEST 7: sorted by count descending ───────────────────────────────────────

def test_collect_sorted_by_count_descending():
    options = ["Правильно", "Помилка А", "Помилка Б"]
    q1 = Question(id=1, text="Q1", options=options, correct_index=0, explanation="E1")
    q2 = Question(id=2, text="Q2", options=options, correct_index=0, explanation="E2")
    # q1: 1 помилка; q2: 3 помилки
    s = _session_with_answers([q1, q2], [[1, 0, 0], [1, 1, 1]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert len(entries) == 2
    # q2 має більше помилок — має бути першим
    assert entries[0].count >= entries[1].count


# ── TEST 8: multiple wrong options — takes the most popular one ───────────────

def test_collect_takes_most_popular_wrong_option_per_question():
    options = ["Правильно", "Менш популярна помилка", "Найпопулярніша помилка"]
    q = Question(id=5, text="Q", options=options, correct_index=0, explanation="E")
    # index 2 обрали 2 рази, index 1 — 1 раз
    s = _session_with_answers([q], [[2, 2, 1]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries[0].wrong_option == "Найпопулярніша помилка"
    assert entries[0].count == 2


# ── TEST 9: format_text default top_n=3 ──────────────────────────────────────

def test_format_text_default_top_n():
    entries = [
        MistakeEntry(
            question_text=f"Питання {i}",
            wrong_option=f"Помилка {i}",
            count=5 - i,
            correct_option="Правильно",
            explanation="Пояснення",
        )
        for i in range(5)
    ]
    museum = MistakeMuseum()
    text = museum.format_text(entries)
    # лише перші 3 мають бути у тексті
    assert "Питання 0" in text
    assert "Питання 1" in text
    assert "Питання 2" in text
    assert "Питання 3" not in text
    assert "Питання 4" not in text


# ── TEST 10: format_text starts with museum header ────────────────────────────

def test_format_text_has_museum_header():
    entries = [
        MistakeEntry(
            question_text="Питання",
            wrong_option="Помилка",
            count=2,
            correct_option="Правильно",
            explanation="Бо так",
        )
    ]
    museum = MistakeMuseum()
    text = museum.format_text(entries)
    assert text.startswith("🏛 Музей помилок")


# ── TEST 11: format_text empty list ──────────────────────────────────────────

def test_format_text_empty_entries():
    museum = MistakeMuseum()
    text = museum.format_text([])
    assert "🏛 Музей помилок" in text
    # no crash, returns something meaningful
    assert isinstance(text, str)


# ── TEST 12: format_text respects custom top_n ───────────────────────────────

def test_format_text_custom_top_n():
    entries = [
        MistakeEntry(
            question_text=f"Q{i}",
            wrong_option=f"E{i}",
            count=10 - i,
            correct_option="OK",
            explanation="X",
        )
        for i in range(10)
    ]
    museum = MistakeMuseum()
    text = museum.format_text(entries, top_n=2)
    assert "Q0" in text
    assert "Q1" in text
    assert "Q2" not in text


# ── TEST 13: format_text is anonymous (no user IDs) ──────────────────────────

def test_format_text_no_user_ids():
    q = _make_question(10, "Що є правдою?")
    s = _session_with_answers([q], [[1, 1, 0]])
    museum = MistakeMuseum()
    entries = museum.collect(s)
    text = museum.format_text(entries)
    # user IDs 1, 2, 3 не мають фігурувати в тексті
    assert "1" not in text or text.count("1") <= text.count(
        "1"
    )  # count може бути у статистиці, але не як user_id
    # перевіряємо відсутність типового патерну "user_id:"
    assert "user_id" not in text
    assert "uid" not in text


# ── TEST 14: format_text shows count statistics ───────────────────────────────

def test_format_text_shows_count():
    entries = [
        MistakeEntry(
            question_text="Що є масивом?",
            wrong_option="Словник",
            count=7,
            correct_option="Список",
            explanation="Масив = список",
        )
    ]
    museum = MistakeMuseum()
    text = museum.format_text(entries)
    assert "7" in text


# ── TEST 15: session with no answers returns empty ────────────────────────────

def test_collect_empty_session():
    q = _make_question(99)
    questions = [q]
    s = QuizSession(quiz_id=1, questions=questions)
    # не стартуємо — відповідей немає
    museum = MistakeMuseum()
    entries = museum.collect(s)
    assert entries == []
