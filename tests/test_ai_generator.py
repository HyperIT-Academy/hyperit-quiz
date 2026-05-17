"""Tests for AI question generation pipeline (ticket #26)."""
from __future__ import annotations

import pytest

from src.ai_generator import (
    GenerationRequest,
    GenerationResult,
    MockLLMBackend,
    QuestionGenerator,
    parse_questions_from_text,
)
from src.session import Question


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_BLOCK = """\
Q: Що виводить print(len([1, 2, 3]))?
A) 2
B) 3
C) 4
D) 1
CORRECT: B
EXPLANATION: Список містить 3 елементи, тому len повертає 3.
"""

VALID_BLOCK_2 = """\
Q: Яке ключове слово для визначення функції в Python?
A) func
B) function
C) def
D) define
CORRECT: C
EXPLANATION: В Python функції визначаються через ключове слово def.
"""

MULTI_BLOCK = VALID_BLOCK + "---\n" + VALID_BLOCK_2

INVALID_NO_CORRECT = """\
Q: Питання без відповіді?
A) варіант а
B) варіант б
C) варіант в
D) варіант г
EXPLANATION: немає відповіді
"""

INVALID_FEW_OPTIONS = """\
Q: Питання з однією опцією?
A) тільки один варіант
CORRECT: A
EXPLANATION: пояснення
"""

MIXED_BLOCKS = VALID_BLOCK + "---\n" + INVALID_NO_CORRECT + "---\n" + VALID_BLOCK_2

FIVE_BLOCKS = "\n---\n".join([VALID_BLOCK] * 5)
THREE_BLOCKS = "\n---\n".join([VALID_BLOCK] * 3)


def _make_generator(responses: list[str]) -> QuestionGenerator:
    backend = MockLLMBackend(responses=responses)
    return QuestionGenerator(backend=backend)


# ---------------------------------------------------------------------------
# parse_questions_from_text
# ---------------------------------------------------------------------------


class TestParseQuestionsFromText:
    def test_valid_single_block_returns_one_question(self):
        questions = parse_questions_from_text(VALID_BLOCK, topic="Python")
        assert len(questions) == 1

    def test_valid_single_block_question_type(self):
        questions = parse_questions_from_text(VALID_BLOCK, topic="Python")
        assert isinstance(questions[0], Question)

    def test_valid_single_block_fields(self):
        questions = parse_questions_from_text(VALID_BLOCK, topic="Python")
        q = questions[0]
        assert "print" in q.text
        assert len(q.options) == 4
        assert q.correct_index == 1  # B → index 1
        assert "3 елементи" in q.explanation

    def test_multi_block_returns_multiple_questions(self):
        questions = parse_questions_from_text(MULTI_BLOCK, topic="Python")
        assert len(questions) == 2

    def test_invalid_no_correct_skipped(self):
        questions = parse_questions_from_text(INVALID_NO_CORRECT, topic="Python")
        assert len(questions) == 0

    def test_invalid_few_options_skipped(self):
        questions = parse_questions_from_text(INVALID_FEW_OPTIONS, topic="Python")
        assert len(questions) == 0

    def test_mixed_blocks_only_valid_returned(self):
        questions = parse_questions_from_text(MIXED_BLOCKS, topic="Python")
        assert len(questions) == 2

    def test_empty_string_returns_empty_list(self):
        questions = parse_questions_from_text("", topic="Python")
        assert questions == []

    def test_correct_index_mapping_a(self):
        block = VALID_BLOCK.replace("CORRECT: B", "CORRECT: A")
        questions = parse_questions_from_text(block, topic="Python")
        assert questions[0].correct_index == 0

    def test_correct_index_mapping_d(self):
        block = VALID_BLOCK.replace("CORRECT: B", "CORRECT: D")
        questions = parse_questions_from_text(block, topic="Python")
        assert questions[0].correct_index == 3

    def test_ids_are_sequential(self):
        questions = parse_questions_from_text(MULTI_BLOCK, topic="Python")
        assert questions[0].id == 0
        assert questions[1].id == 1


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def setup_method(self):
        self._gen = _make_generator(["dummy"])

    def test_prompt_contains_topic(self):
        req = GenerationRequest(topic="Python list comprehensions")
        prompt = self._gen.build_prompt(req)
        assert "Python list comprehensions" in prompt

    def test_prompt_contains_difficulty(self):
        req = GenerationRequest(topic="loops", difficulty="hard")
        prompt = self._gen.build_prompt(req)
        assert "hard" in prompt

    def test_prompt_contains_count(self):
        req = GenerationRequest(topic="loops", count=7)
        prompt = self._gen.build_prompt(req)
        assert "7" in prompt

    def test_prompt_contains_language(self):
        req = GenerationRequest(topic="loops", language="uk")
        prompt = self._gen.build_prompt(req)
        assert "uk" in prompt

    def test_prompt_contains_source_text_when_provided(self):
        req = GenerationRequest(topic="loops", source_text="Урок про цикли for і while")
        prompt = self._gen.build_prompt(req)
        assert "Урок про цикли for і while" in prompt

    def test_prompt_no_source_text_when_none(self):
        req = GenerationRequest(topic="loops", source_text=None)
        prompt = self._gen.build_prompt(req)
        # source_text section should not contain placeholder noise — just verify no crash
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ---------------------------------------------------------------------------
# MockLLMBackend
# ---------------------------------------------------------------------------


class TestMockLLMBackend:
    def test_returns_first_response(self):
        backend = MockLLMBackend(responses=["response_a", "response_b"])
        assert backend.generate("prompt") == "response_a"

    def test_cycles_through_responses(self):
        backend = MockLLMBackend(responses=["a", "b"])
        backend.generate("p")
        assert backend.generate("p") == "b"

    def test_wraps_around(self):
        backend = MockLLMBackend(responses=["only"])
        backend.generate("p")
        assert backend.generate("p") == "only"

    def test_call_count_increments(self):
        backend = MockLLMBackend(responses=["x"])
        backend.generate("p")
        backend.generate("p")
        assert backend._call_count == 2


# ---------------------------------------------------------------------------
# QuestionGenerator.generate
# ---------------------------------------------------------------------------


class TestQuestionGeneratorGenerate:
    def test_generate_returns_result(self):
        gen = _make_generator([FIVE_BLOCKS])
        req = GenerationRequest(topic="Python", count=5)
        result = gen.generate(req)
        assert isinstance(result, GenerationResult)

    def test_generate_result_has_questions(self):
        gen = _make_generator([FIVE_BLOCKS])
        req = GenerationRequest(topic="Python", count=5)
        result = gen.generate(req)
        assert len(result.questions) == 5

    def test_generate_result_topic_matches(self):
        gen = _make_generator([FIVE_BLOCKS])
        req = GenerationRequest(topic="Python comprehensions", count=5)
        result = gen.generate(req)
        assert result.topic == "Python comprehensions"

    def test_generate_warning_when_fewer_questions(self):
        gen = _make_generator([THREE_BLOCKS])
        req = GenerationRequest(topic="Python", count=5)
        result = gen.generate(req)
        assert len(result.warnings) > 0
        assert "3" in result.warnings[0]
        assert "5" in result.warnings[0]

    def test_generate_no_warning_when_enough_questions(self):
        gen = _make_generator([FIVE_BLOCKS])
        req = GenerationRequest(topic="Python", count=5)
        result = gen.generate(req)
        assert result.warnings == []

    def test_generate_model_used_field_set(self):
        gen = _make_generator([FIVE_BLOCKS])
        req = GenerationRequest(topic="Python", count=5)
        result = gen.generate(req)
        assert isinstance(result.model_used, str)
        assert len(result.model_used) > 0

    def test_generate_calls_backend(self):
        backend = MockLLMBackend(responses=[FIVE_BLOCKS])
        gen = QuestionGenerator(backend=backend)
        req = GenerationRequest(topic="Python", count=5)
        gen.generate(req)
        assert backend._call_count == 1
