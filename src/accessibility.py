from dataclasses import dataclass
from enum import Enum


class AccessibilityProfile(str, Enum):
    DEFAULT = "default"
    SCREEN_READER = "screen_reader"  # без emoji, розгорнутий текст
    COLOR_BLIND = "color_blind"      # без кольорових індикаторів, символьні маркери
    DYSLEXIA = "dyslexia"           # короткі речення, більше пробілів


@dataclass
class AccessibilityFormatter:
    profile: AccessibilityProfile = AccessibilityProfile.DEFAULT

    def format_question(self, text: str, index: int, total: int) -> str:
        """Форматує питання з урахуванням профілю."""
        if self.profile == AccessibilityProfile.SCREEN_READER:
            return f"Question {index} of {total}. {text}"
        if self.profile == AccessibilityProfile.DYSLEXIA:
            return f"Питання {index} / {total}\n\n{text}"
        # DEFAULT і COLOR_BLIND — однаковий формат
        return f"Питання {index}/{total}: {text}"

    def format_option(self, letter: str, text: str, is_correct: bool | None = None) -> str:
        """Форматує варіант відповіді з урахуванням профілю та стану відповіді.

        is_correct=None → ще не відповіли
        is_correct=True/False → після відповіді
        """
        if self.profile == AccessibilityProfile.SCREEN_READER:
            base = f"{letter}. {text}"
            if is_correct is None:
                return base
            return f"CORRECT: {base}" if is_correct else f"WRONG: {base}"

        if self.profile == AccessibilityProfile.COLOR_BLIND:
            base = f"{letter}) {text}"
            if is_correct is None:
                return base
            return f"[+] {base}" if is_correct else f"[-] {base}"

        if self.profile == AccessibilityProfile.DYSLEXIA:
            base = f"{letter})  {text}"
            if is_correct is None:
                return base
            return f"✓ {base}" if is_correct else f"✗ {base}"

        # DEFAULT
        base = f"{letter}) {text}"
        if is_correct is None:
            return base
        return f"✅ {base}" if is_correct else f"❌ {base}"

    def format_result(self, is_correct: bool, explanation: str) -> str:
        """Форматує результат відповіді з поясненням."""
        if self.profile == AccessibilityProfile.SCREEN_READER:
            verdict = "CORRECT" if is_correct else "INCORRECT"
            return f"{verdict}. {explanation}"

        if self.profile == AccessibilityProfile.COLOR_BLIND:
            verdict = "[CORRECT]" if is_correct else "[INCORRECT]"
            return f"{verdict} {explanation}"

        if self.profile == AccessibilityProfile.DYSLEXIA:
            verdict = "Так!" if is_correct else "Ні."
            return f"{verdict}\n\n{explanation}"

        # DEFAULT
        verdict = "✅ Правильно!" if is_correct else "❌ Неправильно."
        return f"{verdict} {explanation}"

    def format_score(self, correct: int, total: int) -> str:
        """Форматує підсумковий результат квізу."""
        percent = round(correct / total * 100) if total > 0 else 0

        if self.profile == AccessibilityProfile.SCREEN_READER:
            return f"Score: {correct} out of {total}. {percent} percent."

        if self.profile == AccessibilityProfile.COLOR_BLIND:
            return f"Result: {correct}/{total} ({percent}%)"

        if self.profile == AccessibilityProfile.DYSLEXIA:
            return f"Результат:\n{correct} з {total}\n{percent}%"

        # DEFAULT
        return f"🏆 Результат: {correct}/{total} ({percent}%)"


def get_formatter(profile: AccessibilityProfile) -> AccessibilityFormatter:
    """Factory function."""
    return AccessibilityFormatter(profile=profile)
