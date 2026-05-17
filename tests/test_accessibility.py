"""
Тести для src/accessibility.py — тікет #14.
~24 тести, по 6 на профіль (DEFAULT, SCREEN_READER, COLOR_BLIND, DYSLEXIA)
для кожного методу (format_question, format_option, format_result, format_score).
"""

import pytest
from src.accessibility import (
    AccessibilityProfile,
    AccessibilityFormatter,
    get_formatter,
)


# ---------------------------------------------------------------------------
# format_question
# ---------------------------------------------------------------------------


class TestFormatQuestionDefault:
    def test_basic(self):
        f = AccessibilityFormatter()
        assert f.format_question("Що таке Python?", 3, 10) == "Питання 3/10: Що таке Python?"

    def test_first_question(self):
        f = AccessibilityFormatter()
        assert f.format_question("Текст", 1, 5) == "Питання 1/5: Текст"

    def test_last_question(self):
        f = AccessibilityFormatter()
        assert f.format_question("Кінець", 5, 5) == "Питання 5/5: Кінець"

    def test_color_blind_same_as_default(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_question("Текст", 2, 8) == "Питання 2/8: Текст"

    def test_color_blind_first(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_question("Старт", 1, 1) == "Питання 1/1: Старт"

    def test_default_profile_enum(self):
        f = get_formatter(AccessibilityProfile.DEFAULT)
        result = f.format_question("Q", 7, 20)
        assert result == "Питання 7/20: Q"


class TestFormatQuestionScreenReader:
    def test_basic(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_question("What is Python?", 3, 10) == "Question 3 of 10. What is Python?"

    def test_first_question(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_question("Intro", 1, 5) == "Question 1 of 5. Intro"

    def test_last_question(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_question("Final", 5, 5) == "Question 5 of 5. Final"

    def test_no_emoji_in_output(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_question("Test", 1, 1)
        # screen reader profile не повинен мати emoji
        assert "🏆" not in result and "✅" not in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.SCREEN_READER)
        assert "of" in f.format_question("Текст", 2, 4)

    def test_period_after_number(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_question("X", 3, 10)
        assert result.startswith("Question 3 of 10.")


class TestFormatQuestionDyslexia:
    def test_basic(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_question("Що таке Python?", 3, 10) == "Питання 3 / 10\n\nЩо таке Python?"

    def test_first_question(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_question("Текст", 1, 5) == "Питання 1 / 5\n\nТекст"

    def test_double_newline_separator(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_question("Q", 1, 1)
        assert "\n\n" in result

    def test_spaces_around_slash(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_question("Q", 2, 5)
        assert " / " in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DYSLEXIA)
        result = f.format_question("Test", 3, 9)
        assert result == "Питання 3 / 9\n\nTest"

    def test_last_question(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_question("Фінал", 10, 10) == "Питання 10 / 10\n\nФінал"


# ---------------------------------------------------------------------------
# format_option
# ---------------------------------------------------------------------------


class TestFormatOptionDefault:
    def test_no_answer(self):
        f = AccessibilityFormatter()
        assert f.format_option("A", "Варіант 1") == "A) Варіант 1"

    def test_correct(self):
        f = AccessibilityFormatter()
        assert f.format_option("B", "Варіант 2", is_correct=True) == "✅ B) Варіант 2"

    def test_wrong(self):
        f = AccessibilityFormatter()
        assert f.format_option("C", "Варіант 3", is_correct=False) == "❌ C) Варіант 3"

    def test_none_explicit(self):
        f = AccessibilityFormatter()
        assert f.format_option("D", "Текст", is_correct=None) == "D) Текст"

    def test_letter_d(self):
        f = AccessibilityFormatter()
        result = f.format_option("D", "Останній", is_correct=True)
        assert result == "✅ D) Останній"

    def test_factory_default(self):
        f = get_formatter(AccessibilityProfile.DEFAULT)
        assert f.format_option("A", "x", is_correct=False) == "❌ A) x"


class TestFormatOptionScreenReader:
    def test_no_answer(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_option("A", "Option text") == "A. Option text"

    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_option("B", "Option text", is_correct=True) == "CORRECT: B. Option text"

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_option("C", "Option text", is_correct=False) == "WRONG: C. Option text"

    def test_no_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_option("A", "x", is_correct=True)
        assert "✅" not in result and "❌" not in result

    def test_dot_separator(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_option("A", "text")
        assert "A. text" == result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.SCREEN_READER)
        assert f.format_option("D", "last", is_correct=False) == "WRONG: D. last"


class TestFormatOptionColorBlind:
    def test_no_answer(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_option("A", "Варіант") == "A) Варіант"

    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_option("B", "Варіант", is_correct=True) == "[+] B) Варіант"

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_option("C", "Варіант", is_correct=False) == "[-] C) Варіант"

    def test_no_color_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        result = f.format_option("A", "x", is_correct=True)
        assert "✅" not in result and "❌" not in result

    def test_bracket_markers(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        correct = f.format_option("A", "x", is_correct=True)
        wrong = f.format_option("B", "y", is_correct=False)
        assert correct.startswith("[+]") and wrong.startswith("[-]")

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.COLOR_BLIND)
        assert f.format_option("A", "z") == "A) z"


class TestFormatOptionDyslexia:
    def test_no_answer(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_option("A", "Варіант") == "A)  Варіант"

    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_option("B", "Варіант", is_correct=True) == "✓ B)  Варіант"

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_option("C", "Варіант", is_correct=False) == "✗ C)  Варіант"

    def test_double_space(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_option("A", "text")
        assert "A)  text" == result

    def test_checkmark_not_full_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_option("A", "x", is_correct=True)
        # ✓ (U+2713) не ✅ (U+2705)
        assert "✓" in result and "✅" not in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DYSLEXIA)
        assert f.format_option("D", "last", is_correct=False) == "✗ D)  last"


# ---------------------------------------------------------------------------
# format_result
# ---------------------------------------------------------------------------


class TestFormatResultDefault:
    def test_correct(self):
        f = AccessibilityFormatter()
        result = f.format_result(True, "Тому що Python — мова програмування.")
        assert result == "✅ Правильно! Тому що Python — мова програмування."

    def test_wrong(self):
        f = AccessibilityFormatter()
        result = f.format_result(False, "Пояснення.")
        assert result == "❌ Неправильно. Пояснення."

    def test_explanation_included(self):
        f = AccessibilityFormatter()
        result = f.format_result(True, "Деталі тут.")
        assert "Деталі тут." in result

    def test_correct_has_checkmark(self):
        f = AccessibilityFormatter()
        assert "✅" in f.format_result(True, "x")

    def test_wrong_has_cross(self):
        f = AccessibilityFormatter()
        assert "❌" in f.format_result(False, "x")

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DEFAULT)
        result = f.format_result(False, "exp")
        assert result == "❌ Неправильно. exp"


class TestFormatResultScreenReader:
    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_result(True, "Because Python is a language.")
        assert result == "CORRECT. Because Python is a language."

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_result(False, "Explanation here.")
        assert result == "INCORRECT. Explanation here."

    def test_no_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_result(True, "x")
        assert "✅" not in result and "❌" not in result

    def test_uppercase_verdict(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_result(True, "x").startswith("CORRECT")
        assert f.format_result(False, "x").startswith("INCORRECT")

    def test_explanation_after_dot(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_result(True, "Detail.")
        assert "CORRECT. Detail." == result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.SCREEN_READER)
        assert f.format_result(False, "exp") == "INCORRECT. exp"


class TestFormatResultColorBlind:
    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        result = f.format_result(True, "Пояснення.")
        assert result == "[CORRECT] Пояснення."

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        result = f.format_result(False, "Пояснення.")
        assert result == "[INCORRECT] Пояснення."

    def test_no_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        result = f.format_result(True, "x")
        assert "✅" not in result

    def test_bracket_format(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_result(True, "x").startswith("[CORRECT]")
        assert f.format_result(False, "x").startswith("[INCORRECT]")

    def test_explanation_included(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        result = f.format_result(False, "detail")
        assert "detail" in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.COLOR_BLIND)
        assert f.format_result(True, "ok") == "[CORRECT] ok"


class TestFormatResultDyslexia:
    def test_correct(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_result(True, "Пояснення тут.")
        assert result == "Так!\n\nПояснення тут."

    def test_wrong(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_result(False, "Пояснення тут.")
        assert result == "Ні.\n\nПояснення тут."

    def test_double_newline(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_result(True, "exp")
        assert "\n\n" in result

    def test_short_verdict(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_result(True, "x").startswith("Так!")
        assert f.format_result(False, "x").startswith("Ні.")

    def test_explanation_after_newlines(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_result(False, "detail")
        parts = result.split("\n\n")
        assert parts[1] == "detail"

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DYSLEXIA)
        assert f.format_result(True, "ok") == "Так!\n\nok"


# ---------------------------------------------------------------------------
# format_score
# ---------------------------------------------------------------------------


class TestFormatScoreDefault:
    def test_basic(self):
        f = AccessibilityFormatter()
        assert f.format_score(7, 10) == "🏆 Результат: 7/10 (70%)"

    def test_perfect(self):
        f = AccessibilityFormatter()
        assert f.format_score(5, 5) == "🏆 Результат: 5/5 (100%)"

    def test_zero(self):
        f = AccessibilityFormatter()
        assert f.format_score(0, 10) == "🏆 Результат: 0/10 (0%)"

    def test_rounding(self):
        f = AccessibilityFormatter()
        # 1/3 = 33.33... → 33%
        result = f.format_score(1, 3)
        assert "33%" in result

    def test_trophy_emoji(self):
        f = AccessibilityFormatter()
        assert f.format_score(3, 5).startswith("🏆")

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DEFAULT)
        assert f.format_score(7, 10) == "🏆 Результат: 7/10 (70%)"


class TestFormatScoreScreenReader:
    def test_basic(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_score(7, 10) == "Score: 7 out of 10. 70 percent."

    def test_perfect(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_score(5, 5) == "Score: 5 out of 5. 100 percent."

    def test_zero(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert f.format_score(0, 10) == "Score: 0 out of 10. 0 percent."

    def test_no_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        assert "🏆" not in f.format_score(3, 5)

    def test_out_of_wording(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.SCREEN_READER)
        result = f.format_score(2, 4)
        assert "out of" in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.SCREEN_READER)
        assert f.format_score(7, 10) == "Score: 7 out of 10. 70 percent."


class TestFormatScoreColorBlind:
    def test_basic(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_score(7, 10) == "Result: 7/10 (70%)"

    def test_perfect(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_score(5, 5) == "Result: 5/5 (100%)"

    def test_zero(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_score(0, 10) == "Result: 0/10 (0%)"

    def test_no_emoji(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert "🏆" not in f.format_score(3, 5)

    def test_result_prefix(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.COLOR_BLIND)
        assert f.format_score(1, 4).startswith("Result:")

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.COLOR_BLIND)
        assert f.format_score(7, 10) == "Result: 7/10 (70%)"


class TestFormatScoreDyslexia:
    def test_basic(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_score(7, 10) == "Результат:\n7 з 10\n70%"

    def test_perfect(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_score(5, 5) == "Результат:\n5 з 5\n100%"

    def test_zero(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        assert f.format_score(0, 10) == "Результат:\n0 з 10\n0%"

    def test_newline_separated(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_score(3, 6)
        lines = result.split("\n")
        assert len(lines) == 3

    def test_z_wording(self):
        f = AccessibilityFormatter(profile=AccessibilityProfile.DYSLEXIA)
        result = f.format_score(2, 8)
        assert "з" in result

    def test_factory(self):
        f = get_formatter(AccessibilityProfile.DYSLEXIA)
        assert f.format_score(7, 10) == "Результат:\n7 з 10\n70%"


# ---------------------------------------------------------------------------
# get_formatter factory
# ---------------------------------------------------------------------------


class TestGetFormatter:
    def test_returns_formatter(self):
        f = get_formatter(AccessibilityProfile.DEFAULT)
        assert isinstance(f, AccessibilityFormatter)

    def test_profile_set_correctly(self):
        f = get_formatter(AccessibilityProfile.SCREEN_READER)
        assert f.profile == AccessibilityProfile.SCREEN_READER

    def test_all_profiles(self):
        for profile in AccessibilityProfile:
            f = get_formatter(profile)
            assert f.profile == profile
