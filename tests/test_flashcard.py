"""Tests for FlashcardDeck / generate_deck / generate_class_deck — RED phase."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession
from src.flashcard import Flashcard, FlashcardDeck, generate_deck, generate_class_deck


# ── helpers ─────────────────────────────────────────────────────────────────

def make_question(
    idx: int,
    correct_index: int = 0,
    code_language: str | None = None,
) -> Question:
    return Question(
        id=idx,
        text=f"Питання {idx}?",
        options=["A", "B", "C", "D"],
        correct_index=correct_index,
        explanation=f"Пояснення {idx}",
        code_language=code_language,
    )


def answered_session(
    answers: dict[int, list[int]],  # user_id → [chosen per question]
    code_language: str | None = None,
) -> QuizSession:
    """Build a finished session with given answers."""
    n = max(len(v) for v in answers.values())
    questions = [make_question(i, correct_index=0, code_language=code_language) for i in range(n)]
    session = QuizSession(quiz_id=1, questions=questions)
    session.start()
    for q_idx in range(n):
        for user_id, choices in answers.items():
            if q_idx < len(choices):
                session.answer(user_id=user_id, chosen_index=choices[q_idx])
        session.next_question()
    return session


# ── Flashcard dataclass ──────────────────────────────────────────────────────

def test_flashcard_has_front_back_tags():
    card = Flashcard(front="Q", back="A", tags=["wrong_answer"])
    assert card.front == "Q"
    assert card.back == "A"
    assert "wrong_answer" in card.tags


# ── FlashcardDeck.to_csv ─────────────────────────────────────────────────────

def test_to_csv_header_row():
    deck = FlashcardDeck(cards=[])
    csv = deck.to_csv()
    assert csv.startswith("front,back,tags")


def test_to_csv_single_card():
    card = Flashcard(front="Q1", back="A1", tags=["wrong_answer"])
    deck = FlashcardDeck(cards=[card])
    csv = deck.to_csv()
    lines = csv.strip().splitlines()
    assert len(lines) == 2  # header + 1 data row
    assert "Q1" in lines[1]
    assert "A1" in lines[1]
    assert "wrong_answer" in lines[1]


def test_to_csv_tags_space_separated():
    card = Flashcard(front="Q", back="A", tags=["wrong_answer", "python"])
    deck = FlashcardDeck(cards=[card])
    csv = deck.to_csv()
    data_line = csv.strip().splitlines()[1]
    assert "wrong_answer python" in data_line


def test_to_csv_empty_deck():
    deck = FlashcardDeck(cards=[])
    csv = deck.to_csv()
    lines = csv.strip().splitlines()
    assert len(lines) == 1  # only header


# ── FlashcardDeck.to_text ────────────────────────────────────────────────────

def test_to_text_contains_front():
    card = Flashcard(front="Яке питання?", back="Відповідь", tags=["wrong_answer"])
    deck = FlashcardDeck(cards=[card])
    text = deck.to_text()
    assert "Яке питання?" in text


def test_to_text_contains_back():
    card = Flashcard(front="Q", back="✅ A\n💡 Пояснення", tags=["wrong_answer"])
    deck = FlashcardDeck(cards=[card])
    text = deck.to_text()
    assert "A" in text


def test_to_text_empty_deck():
    deck = FlashcardDeck(cards=[])
    text = deck.to_text()
    assert isinstance(text, str)


# ── generate_deck ────────────────────────────────────────────────────────────

def test_generate_deck_only_wrong_answers():
    # user 10: Q0 → wrong (chosen 1, correct 0), Q1 → correct (chosen 0)
    session = answered_session({10: [1, 0]})
    deck = generate_deck(session, user_id=10)
    assert len(deck.cards) == 1
    assert "Питання 0" in deck.cards[0].front


def test_generate_deck_no_mistakes_empty():
    session = answered_session({5: [0, 0, 0]})
    deck = generate_deck(session, user_id=5)
    assert deck.cards == []


def test_generate_deck_back_format():
    session = answered_session({7: [2]})  # wrong answer
    deck = generate_deck(session, user_id=7)
    assert len(deck.cards) == 1
    back = deck.cards[0].back
    assert back.startswith("✅")
    assert "💡" in back
    assert "Пояснення 0" in back


def test_generate_deck_tag_wrong_answer():
    session = answered_session({3: [1]})
    deck = generate_deck(session, user_id=3)
    assert "wrong_answer" in deck.cards[0].tags


def test_generate_deck_tag_code_language():
    session = answered_session({3: [1]}, code_language="python")
    deck = generate_deck(session, user_id=3)
    assert "python" in deck.cards[0].tags


def test_generate_deck_no_code_language_tag():
    session = answered_session({3: [1]}, code_language=None)
    deck = generate_deck(session, user_id=3)
    tags = deck.cards[0].tags
    # тільки wrong_answer, без мови
    assert tags == ["wrong_answer"]


def test_generate_deck_unknown_user_empty():
    session = answered_session({1: [0]})
    deck = generate_deck(session, user_id=999)
    assert deck.cards == []


# ── generate_class_deck ───────────────────────────────────────────────────────

def test_generate_class_deck_includes_question_any_wrong():
    # Q0: user1 wrong, user2 correct → included
    # Q1: both correct → excluded
    questions = [make_question(0), make_question(1)]
    session = QuizSession(quiz_id=1, questions=questions)
    session.start()
    session.answer(user_id=1, chosen_index=1)  # wrong
    session.answer(user_id=2, chosen_index=0)  # correct
    session.next_question()
    session.answer(user_id=1, chosen_index=0)  # correct
    session.answer(user_id=2, chosen_index=0)  # correct
    session.next_question()

    deck = generate_class_deck(session)
    assert len(deck.cards) == 1
    assert "Питання 0" in deck.cards[0].front


def test_generate_class_deck_all_correct_empty():
    session = answered_session({1: [0, 0], 2: [0, 0]})
    deck = generate_class_deck(session)
    assert deck.cards == []


def test_generate_class_deck_back_format():
    session = answered_session({1: [2]})
    deck = generate_class_deck(session)
    assert len(deck.cards) == 1
    back = deck.cards[0].back
    assert "✅" in back
    assert "💡" in back
