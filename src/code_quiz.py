"""IT vertical: code completion and code output question types."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SQL = "sql"
    HTML = "html"
    CSS = "css"


@dataclass
class CodeCompletionQuestion:
    id: int
    text: str                       # опис що треба заповнити
    template: str                   # код з плейсхолдером "___"
    correct_completions: list[str]  # один або кілька правильних варіантів
    language: ProgrammingLanguage
    explanation: str
    hints: list[str] = field(default_factory=list)

    def check(self, submitted: str) -> bool:
        """Exact match після strip. Case-sensitive для коду."""
        stripped = submitted.strip()
        return stripped in self.correct_completions

    def render(self) -> str:
        """Повертає template як є (для відображення в Telegram)."""
        return self.template

    def hint_at(self, index: int) -> str | None:
        """Повертає hints[index] або None якщо index out of range."""
        if index < 0 or index >= len(self.hints):
            return None
        return self.hints[index]


@dataclass
class CodeOutputQuestion:
    id: int
    text: str               # "Що виведе цей код?"
    code_snippet: str       # код для показу
    correct_output: str     # очікуваний output
    language: ProgrammingLanguage
    explanation: str

    def check(self, submitted: str) -> bool:
        """Exact match після strip (output може бути multiline)."""
        return submitted.strip() == self.correct_output.strip()

    def render_code(self) -> str:
        """Повертає code_snippet у backtick блоці з мовою."""
        return f"```{self.language.value}\n{self.code_snippet}\n```"


class CodeQuizBuilder:
    """Утиліта для побудови квізів з code питань."""

    def __init__(self) -> None:
        self._questions: list = []

    def add_completion(
        self,
        id: int,
        text: str,
        template: str,
        correct_completions: list[str],
        language: ProgrammingLanguage,
        explanation: str,
        hints: list[str] | None = None,
    ) -> "CodeQuizBuilder":
        """Додає CodeCompletionQuestion і повертає self (builder pattern)."""
        self._questions.append(
            CodeCompletionQuestion(
                id=id,
                text=text,
                template=template,
                correct_completions=correct_completions,
                language=language,
                explanation=explanation,
                hints=hints or [],
            )
        )
        return self

    def add_output(
        self,
        id: int,
        text: str,
        code_snippet: str,
        correct_output: str,
        language: ProgrammingLanguage,
        explanation: str,
    ) -> "CodeQuizBuilder":
        """Додає CodeOutputQuestion і повертає self (builder pattern)."""
        self._questions.append(
            CodeOutputQuestion(
                id=id,
                text=text,
                code_snippet=code_snippet,
                correct_output=correct_output,
                language=language,
                explanation=explanation,
            )
        )
        return self

    def build(self) -> list:
        """Повертає список питань у порядку додавання."""
        return list(self._questions)
