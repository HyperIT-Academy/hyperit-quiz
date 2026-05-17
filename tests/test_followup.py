"""Tests for FollowUpEngine (TDD — #33)."""
import pytest
from src.session import Question
from src.followup import FollowUpQuestion, FollowUpResult, FollowUpEngine


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def question():
    return Question(
        id=1,
        text="Що таке list comprehension у Python?",
        options=["Синтаксис для створення списків", "Тип даних", "Функція вбудована", "Клас колекцій"],
        correct_index=0,
        explanation="List comprehension — компактний синтаксис для створення списків.",
    )


@pytest.fixture
def follow_up_for_option_1():
    return FollowUpQuestion(
        trigger_option_index=1,
        text="Чи є list тип даних і list comprehension пов'язані поняття?",
        hint="List comprehension — це синтаксис, а не тип. Результат є списком, але сам механізм — вираз.",
    )


@pytest.fixture
def engine():
    return FollowUpEngine()


# ── 1. register + has_followup ────────────────────────────────────────────────

def test_has_followup_false_before_register(engine, question):
    assert engine.has_followup(question.id, 1) is False


def test_has_followup_true_after_register(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    assert engine.has_followup(question.id, 1) is True


def test_has_followup_correct_index_not_registered(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    assert engine.has_followup(question.id, 0) is False  # correct_index → немає followup


def test_has_followup_other_option_not_registered(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    assert engine.has_followup(question.id, 2) is False


# ── 2. get_followup — correct answer ─────────────────────────────────────────

def test_get_followup_correct_answer_returns_not_shown(engine, question):
    result = engine.get_followup(question, chosen_index=0)
    assert result.shown is False
    assert result.follow_up is None
    assert result.original_question is question


def test_get_followup_correct_answer_with_registered_followup(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    result = engine.get_followup(question, chosen_index=0)  # correct
    assert result.shown is False
    assert result.follow_up is None


# ── 3. get_followup — wrong answer with registered follow-up ──────────────────

def test_get_followup_wrong_with_followup_shown(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    result = engine.get_followup(question, chosen_index=1)
    assert result.shown is True
    assert result.follow_up is follow_up_for_option_1
    assert result.original_question is question


# ── 4. get_followup — wrong answer without registered follow-up ───────────────

def test_get_followup_wrong_without_followup_not_shown(engine, question):
    result = engine.get_followup(question, chosen_index=2)
    assert result.shown is False
    assert result.follow_up is None
    assert result.original_question is question


# ── 5. format_response ────────────────────────────────────────────────────────

def test_format_response_correct(engine, question):
    result = engine.get_followup(question, chosen_index=0)  # correct_index=0
    text = engine.format_response(result)
    assert text.startswith("✅ Правильно!")
    assert question.explanation in text


def test_format_response_wrong_no_followup(engine, question):
    result = FollowUpResult(shown=False, follow_up=None, original_question=question)
    # щоб відрізнити «correct» від «wrong без followup» — shown=False і follow_up=None
    # в обох: format_response дивиться на chosen_index через FollowUpResult
    # але в нашому API FollowUpResult не зберігає chosen_index — логіка: shown=False + follow_up=None
    # перевірим що format_response не падає і повертає ❌ або ✅ залежно від контексту
    # Тест: якщо shown=False і follow_up=None → формат з ❌ НЕ відрізняється від ✅ без dodаткового поля.
    # Тому перевіряємо обидва варіанти через get_followup → format_response
    result_correct = engine.get_followup(question, chosen_index=0)
    result_wrong = engine.get_followup(question, chosen_index=3)  # wrong, no followup
    assert "✅" in engine.format_response(result_correct)
    assert "❌" in engine.format_response(result_wrong)


def test_format_response_followup_shown(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    result = engine.get_followup(question, chosen_index=1)
    text = engine.format_response(result)
    assert "🤔" in text
    assert follow_up_for_option_1.text in text
    assert "💡 Підказка:" in text
    assert follow_up_for_option_1.hint in text


def test_format_response_followup_exact_format(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    result = engine.get_followup(question, chosen_index=1)
    expected = f"🤔 {follow_up_for_option_1.text}\n💡 Підказка: {follow_up_for_option_1.hint}"
    assert engine.format_response(result) == expected


# ── 6. multiple follow-ups for same question ──────────────────────────────────

def test_register_multiple_options_for_same_question(engine, question):
    fq1 = FollowUpQuestion(trigger_option_index=1, text="Питання 1", hint="Підказка 1")
    fq2 = FollowUpQuestion(trigger_option_index=2, text="Питання 2", hint="Підказка 2")
    engine.register(question.id, fq1)
    engine.register(question.id, fq2)
    assert engine.has_followup(question.id, 1) is True
    assert engine.has_followup(question.id, 2) is True
    r1 = engine.get_followup(question, chosen_index=1)
    r2 = engine.get_followup(question, chosen_index=2)
    assert r1.follow_up is fq1
    assert r2.follow_up is fq2


# ── 7. FollowUpResult fields ──────────────────────────────────────────────────

def test_followup_result_stores_original_question(engine, question, follow_up_for_option_1):
    engine.register(question.id, follow_up_for_option_1)
    result = engine.get_followup(question, chosen_index=1)
    assert result.original_question is question


def test_followup_result_is_dataclass(engine, question):
    result = engine.get_followup(question, chosen_index=0)
    assert hasattr(result, "shown")
    assert hasattr(result, "follow_up")
    assert hasattr(result, "original_question")
