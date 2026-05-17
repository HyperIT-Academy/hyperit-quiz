"""Flashcard generator — converts quiz mistakes into Anki-compatible cards."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.session import QuizSession


@dataclass
class Flashcard:
    front: str
    back: str
    tags: list[str]


@dataclass
class FlashcardDeck:
    cards: list[Flashcard] = field(default_factory=list)

    def to_csv(self) -> str:
        """Anki-compatible CSV: front,back,tags (space-separated tags)."""
        rows = ["front,back,tags"]
        for card in self.cards:
            tags_str = " ".join(card.tags)
            # Escape double-quotes inside fields
            front = card.front.replace('"', '""')
            back = card.back.replace('"', '""')
            rows.append(f'"{front}","{back}","{tags_str}"')
        return "\n".join(rows)

    def to_text(self) -> str:
        """Human-readable text for Telegram messages."""
        if not self.cards:
            return ""
        parts = []
        for i, card in enumerate(self.cards, 1):
            parts.append(f"{i}. {card.front}\n{card.back}")
        return "\n\n".join(parts)


def _make_card(question_index: int, session: QuizSession) -> Flashcard:
    question = session.questions[question_index]
    correct_answer = question.options[question.correct_index]
    back = f"✅ {correct_answer}\n💡 {question.explanation}"
    tags: list[str] = ["wrong_answer"]
    if question.code_language is not None:
        tags.append(question.code_language)
    return Flashcard(front=question.text, back=back, tags=tags)


def generate_deck(session: QuizSession, user_id: int) -> FlashcardDeck:
    """Cards only for questions where user_id answered incorrectly."""
    user_answers = session.answers.get(user_id, {})
    cards: list[Flashcard] = []
    for q_idx, chosen in user_answers.items():
        question = session.questions[q_idx]
        if chosen != question.correct_index:
            cards.append(_make_card(q_idx, session))
    return FlashcardDeck(cards=cards)


def generate_class_deck(session: QuizSession) -> FlashcardDeck:
    """Cards for all questions where at least one participant answered incorrectly."""
    wrong_indices: set[int] = set()
    for user_answers in session.answers.values():
        for q_idx, chosen in user_answers.items():
            if chosen != session.questions[q_idx].correct_index:
                wrong_indices.add(q_idx)

    cards = [_make_card(q_idx, session) for q_idx in sorted(wrong_indices)]
    return FlashcardDeck(cards=cards)
