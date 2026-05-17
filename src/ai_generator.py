"""AI question generation pipeline (ticket #26).

Supports any LLMBackend via Protocol — use MockLLMBackend in tests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from src.session import Question


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class GenerationRequest:
    topic: str                        # "Python list comprehensions"
    difficulty: str = "medium"        # "easy"/"medium"/"hard"
    count: int = 5                    # скільки питань генерувати
    language: str = "uk"             # мова питань
    source_text: str | None = None   # текст уроку (опційно)


@dataclass
class GenerationResult:
    questions: list  # list[Question]
    topic: str
    model_used: str
    tokens_used: int = 0
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LLM backend protocol + mock
# ---------------------------------------------------------------------------


class LLMBackend(Protocol):
    """Protocol для підміни реального LLM на mock у тестах."""

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        ...


@dataclass
class MockLLMBackend:
    """Детермінований mock для тестів — повертає заздалегідь задані питання."""

    responses: list[str]  # black-box рядки що повертаються по черзі
    _call_count: int = field(default=0, init=False)

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        idx = self._call_count % len(self.responses)
        self._call_count += 1
        return self.responses[idx]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
_OPTION_RE = re.compile(r"^([A-D])\)\s*(.+)$")


def parse_questions_from_text(raw: str, topic: str) -> list:
    """Парсить питання з LLM-відповіді.

    Формат блоку:
        Q: текст питання
        A) варіант а
        B) варіант б
        C) варіант в
        D) варіант г
        CORRECT: A
        EXPLANATION: пояснення
        ---          (роздільник між блоками, не обов'язковий після останнього)

    Пропускає невалідні блоки (менше 2 опцій або нема CORRECT).
    Повертає list[Question].
    """
    if not raw.strip():
        return []

    questions: list[Question] = []
    # Розбиваємо на блоки по "---" (з довільним пробілом навколо)
    blocks = re.split(r"\n?---\n?", raw)

    for block_idx, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        q_text: str | None = None
        options: list[str] = []
        correct_letter: str | None = None
        explanation: str = ""

        for line in block.splitlines():
            line = line.strip()
            if line.startswith("Q:"):
                q_text = line[2:].strip()
            elif m := _OPTION_RE.match(line):
                options.append(m.group(2).strip())
            elif line.startswith("CORRECT:"):
                correct_letter = line[8:].strip().upper()
            elif line.startswith("EXPLANATION:"):
                explanation = line[12:].strip()

        # Валідація блоку
        if q_text is None:
            continue
        if len(options) < 2:
            continue
        if correct_letter not in _LETTER_TO_INDEX:
            continue

        correct_index = _LETTER_TO_INDEX[correct_letter]
        if correct_index >= len(options):
            continue

        questions.append(
            Question(
                id=len(questions),
                text=q_text,
                options=options,
                correct_index=correct_index,
                explanation=explanation,
            )
        )

    return questions


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class QuestionGenerator:
    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend
        self._call_count = 0

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Формує prompt, викликає backend.generate(), парсить результат.

        warnings: якщо parsed < request.count — додає warning 'Отримано N < M питань'.
        """
        prompt = self.build_prompt(request)
        raw = self._backend.generate(prompt, max_tokens=request.count * 300)
        self._call_count += 1

        questions = parse_questions_from_text(raw, topic=request.topic)

        warnings: list[str] = []
        if len(questions) < request.count:
            warnings.append(
                f"Отримано {len(questions)} < {request.count} питань"
            )

        return GenerationResult(
            questions=questions,
            topic=request.topic,
            model_used="mock",
            tokens_used=0,
            warnings=warnings,
        )

    def build_prompt(self, request: GenerationRequest) -> str:
        """Будує prompt для LLM.

        Містить topic, difficulty, count, language.
        Якщо source_text — додає його до prompt.
        """
        lines = [
            f"Згенеруй {request.count} тестових питань на тему: {request.topic}.",
            f"Складність: {request.difficulty}.",
            f"Мова питань: {request.language}.",
            "",
            "Формат кожного питання:",
            "Q: текст питання",
            "A) варіант",
            "B) варіант",
            "C) варіант",
            "D) варіант",
            "CORRECT: <A|B|C|D>",
            "EXPLANATION: пояснення правильної відповіді",
            "---",
        ]

        if request.source_text:
            lines.append("")
            lines.append("Використай такий текст уроку як основу:")
            lines.append(request.source_text)

        return "\n".join(lines)
