"""Tests for question_types module — TDD RED phase."""
import pytest
from src.question_types import (
    QuestionType,
    ShortAnswerQuestion,
    OrderingQuestion,
    MatchingQuestion,
)


# ── QuestionType enum ────────────────────────────────────────────────────────

def test_question_type_values():
    assert QuestionType.MULTIPLE_CHOICE == "multiple_choice"
    assert QuestionType.SHORT_ANSWER == "short_answer"
    assert QuestionType.ORDERING == "ordering"
    assert QuestionType.MATCHING == "matching"


def test_question_type_is_str_enum():
    assert isinstance(QuestionType.ORDERING, str)


# ── ShortAnswerQuestion ──────────────────────────────────────────────────────

def make_short(correct_answers=None, case_sensitive=False):
    return ShortAnswerQuestion(
        id=1,
        text="What is 2+2?",
        correct_answers=correct_answers or ["4", "four"],
        explanation="Basic arithmetic",
        case_sensitive=case_sensitive,
    )


def test_short_answer_exact_match():
    q = make_short()
    assert q.check("4") is True


def test_short_answer_exact_match_strips_whitespace():
    q = make_short()
    assert q.check("  4  ") is True


def test_short_answer_case_insensitive_by_default():
    q = make_short(correct_answers=["Python"])
    assert q.check("python") is True
    assert q.check("PYTHON") is True


def test_short_answer_case_sensitive_rejects_wrong_case():
    q = make_short(correct_answers=["Python"], case_sensitive=True)
    assert q.check("python") is False
    assert q.check("Python") is True


def test_short_answer_multiple_synonyms():
    q = make_short(correct_answers=["4", "four", "IV"])
    assert q.check("four") is True
    assert q.check("IV") is True


def test_short_answer_wrong_answer():
    q = make_short()
    assert q.check("5") is False


def test_short_answer_fuzzy_close_match():
    q = make_short(correct_answers=["Python"])
    # "Pythn" — одна пропущена літера, ~0.91 ratio
    assert q.check_fuzzy("Pythn", threshold=0.8) is True


def test_short_answer_fuzzy_too_different():
    q = make_short(correct_answers=["Python"])
    assert q.check_fuzzy("Java", threshold=0.8) is False


def test_short_answer_fuzzy_exact_is_true():
    q = make_short(correct_answers=["Python"])
    assert q.check_fuzzy("Python", threshold=1.0) is True


def test_short_answer_fuzzy_uses_best_match():
    # якщо хоча б один з correct_answers дає ratio >= threshold — True
    q = make_short(correct_answers=["Java", "Python"])
    assert q.check_fuzzy("Pythn", threshold=0.8) is True


# ── OrderingQuestion ─────────────────────────────────────────────────────────

def make_ordering():
    return OrderingQuestion(
        id=2,
        text="Sort: HTML, CSS, JS",
        correct_order=["HTML", "CSS", "JS"],
        explanation="Standard web stack order",
    )


def test_ordering_correct():
    q = make_ordering()
    assert q.check(["HTML", "CSS", "JS"]) is True


def test_ordering_wrong():
    q = make_ordering()
    assert q.check(["CSS", "HTML", "JS"]) is False


def test_ordering_partial_score_all_correct():
    q = make_ordering()
    assert q.partial_score(["HTML", "CSS", "JS"]) == pytest.approx(1.0)


def test_ordering_partial_score_all_wrong():
    q = make_ordering()
    # повністю зворотній порядок
    assert q.partial_score(["JS", "CSS", "HTML"]) == pytest.approx(1 / 3)


def test_ordering_partial_score_one_correct():
    q = make_ordering()
    # тільки перший елемент правильний
    assert q.partial_score(["HTML", "JS", "CSS"]) == pytest.approx(1 / 3)


def test_ordering_partial_score_empty():
    q = make_ordering()
    assert q.partial_score([]) == pytest.approx(0.0)


# ── MatchingQuestion ─────────────────────────────────────────────────────────

def make_matching():
    return MatchingQuestion(
        id=3,
        text="Match language to creator",
        pairs={"Python": "Guido", "Ruby": "Matz", "Java": "Gosling"},
        explanation="Programming language creators",
    )


def test_matching_all_correct():
    q = make_matching()
    assert q.check({"Python": "Guido", "Ruby": "Matz", "Java": "Gosling"}) is True


def test_matching_one_wrong():
    q = make_matching()
    assert q.check({"Python": "Guido", "Ruby": "Gosling", "Java": "Matz"}) is False


def test_matching_partial_score_all_correct():
    q = make_matching()
    result = q.partial_score({"Python": "Guido", "Ruby": "Matz", "Java": "Gosling"})
    assert result == pytest.approx(1.0)


def test_matching_partial_score_two_of_three():
    q = make_matching()
    result = q.partial_score({"Python": "Guido", "Ruby": "Matz", "Java": "WRONG"})
    assert result == pytest.approx(2 / 3)


def test_matching_partial_score_none_correct():
    q = make_matching()
    result = q.partial_score({"Python": "Matz", "Ruby": "Gosling", "Java": "Guido"})
    assert result == pytest.approx(0.0)


def test_matching_partial_score_empty_submission():
    q = make_matching()
    assert q.partial_score({}) == pytest.approx(0.0)


def test_matching_partial_score_missing_keys():
    q = make_matching()
    # тільки один ключ поданий, два — відсутні
    result = q.partial_score({"Python": "Guido"})
    assert result == pytest.approx(1 / 3)
