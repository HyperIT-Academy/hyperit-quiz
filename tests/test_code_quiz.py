"""Tests for src/code_quiz.py — IT vertical: code completion & output questions."""
from __future__ import annotations

import pytest
from src.code_quiz import (
    CodeCompletionQuestion,
    CodeOutputQuestion,
    CodeQuizBuilder,
    ProgrammingLanguage,
)


# ── ProgrammingLanguage enum ─────────────────────────────────────────────────

def test_language_enum_values():
    assert ProgrammingLanguage.PYTHON == "python"
    assert ProgrammingLanguage.JAVASCRIPT == "javascript"
    assert ProgrammingLanguage.SQL == "sql"
    assert ProgrammingLanguage.HTML == "html"
    assert ProgrammingLanguage.CSS == "css"


# ── CodeCompletionQuestion.check ─────────────────────────────────────────────

def _make_completion(**kwargs) -> CodeCompletionQuestion:
    defaults = dict(
        id=1,
        text="Заповни порожнечу",
        template="print(___)",
        correct_completions=["'hello'", '"hello"'],
        language=ProgrammingLanguage.PYTHON,
        explanation="Рядок у дужках",
    )
    defaults.update(kwargs)
    return CodeCompletionQuestion(**defaults)


def test_check_correct_exact():
    q = _make_completion()
    assert q.check("'hello'") is True


def test_check_second_correct_variant():
    q = _make_completion()
    assert q.check('"hello"') is True


def test_check_strips_whitespace():
    q = _make_completion()
    assert q.check("  'hello'  ") is True


def test_check_case_sensitive_wrong_case():
    q = _make_completion(correct_completions=["True"])
    assert q.check("true") is False


def test_check_case_sensitive_correct_case():
    q = _make_completion(correct_completions=["True"])
    assert q.check("True") is True


def test_check_wrong_answer():
    q = _make_completion()
    assert q.check("42") is False


def test_check_empty_string():
    q = _make_completion()
    assert q.check("") is False


# ── CodeCompletionQuestion.render ────────────────────────────────────────────

def test_render_returns_template():
    q = _make_completion(template="x = ___")
    assert q.render() == "x = ___"


def test_render_returns_template_with_placeholder():
    template = "for i in range(___):\n    pass"
    q = _make_completion(template=template)
    assert q.render() == template


# ── CodeCompletionQuestion.hint_at ───────────────────────────────────────────

def test_hint_at_valid_index():
    q = _make_completion(hints=["підказка 1", "підказка 2"])
    assert q.hint_at(0) == "підказка 1"
    assert q.hint_at(1) == "підказка 2"


def test_hint_at_out_of_range_returns_none():
    q = _make_completion(hints=["підказка 1"])
    assert q.hint_at(5) is None


def test_hint_at_empty_hints_returns_none():
    q = _make_completion()
    assert q.hint_at(0) is None


def test_hint_at_negative_index_returns_none():
    q = _make_completion(hints=["підказка 1"])
    assert q.hint_at(-1) is None


# ── CodeOutputQuestion.check ──────────────────────────────────────────────────

def _make_output(**kwargs) -> CodeOutputQuestion:
    defaults = dict(
        id=2,
        text="Що виведе цей код?",
        code_snippet="print('hello')",
        correct_output="hello",
        language=ProgrammingLanguage.PYTHON,
        explanation="print виводить рядок без лапок",
    )
    defaults.update(kwargs)
    return CodeOutputQuestion(**defaults)


def test_output_check_correct():
    q = _make_output()
    assert q.check("hello") is True


def test_output_check_strips_whitespace():
    q = _make_output()
    assert q.check("  hello  ") is True


def test_output_check_wrong():
    q = _make_output()
    assert q.check("Hello") is False


def test_output_check_multiline():
    q = _make_output(
        code_snippet="print(1)\nprint(2)",
        correct_output="1\n2",
    )
    assert q.check("1\n2") is True
    assert q.check("1\n2\n") is True


def test_output_check_empty_wrong():
    q = _make_output()
    assert q.check("") is False


# ── CodeOutputQuestion.render_code ────────────────────────────────────────────

def test_render_code_python():
    q = _make_output(code_snippet="print('hi')")
    assert q.render_code() == "```python\nprint('hi')\n```"


def test_render_code_javascript():
    q = _make_output(
        code_snippet="console.log('hi')",
        language=ProgrammingLanguage.JAVASCRIPT,
    )
    assert q.render_code() == "```javascript\nconsole.log('hi')\n```"


def test_render_code_sql():
    q = _make_output(
        code_snippet="SELECT 1",
        language=ProgrammingLanguage.SQL,
        correct_output="1",
    )
    assert q.render_code() == "```sql\nSELECT 1\n```"


# ── CodeQuizBuilder ───────────────────────────────────────────────────────────

def test_builder_empty_build():
    builder = CodeQuizBuilder()
    assert builder.build() == []


def test_builder_add_completion_returns_self():
    builder = CodeQuizBuilder()
    result = builder.add_completion(
        id=1,
        text="Заповни",
        template="x = ___",
        correct_completions=["5"],
        language=ProgrammingLanguage.PYTHON,
        explanation="x дорівнює 5",
    )
    assert result is builder


def test_builder_add_output_returns_self():
    builder = CodeQuizBuilder()
    result = builder.add_output(
        id=2,
        text="Що виведе?",
        code_snippet="print(42)",
        correct_output="42",
        language=ProgrammingLanguage.PYTHON,
        explanation="print виводить число",
    )
    assert result is builder


def test_builder_preserves_order():
    questions = (
        CodeQuizBuilder()
        .add_completion(
            id=1,
            text="Q1",
            template="___",
            correct_completions=["a"],
            language=ProgrammingLanguage.PYTHON,
            explanation="E1",
        )
        .add_output(
            id=2,
            text="Q2",
            code_snippet="pass",
            correct_output="",
            language=ProgrammingLanguage.PYTHON,
            explanation="E2",
        )
        .build()
    )
    assert len(questions) == 2
    assert isinstance(questions[0], CodeCompletionQuestion)
    assert isinstance(questions[1], CodeOutputQuestion)
    assert questions[0].id == 1
    assert questions[1].id == 2


def test_builder_multiple_completions():
    questions = (
        CodeQuizBuilder()
        .add_completion(id=1, text="Q1", template="___", correct_completions=["a"],
                        language=ProgrammingLanguage.PYTHON, explanation="E")
        .add_completion(id=2, text="Q2", template="___", correct_completions=["b"],
                        language=ProgrammingLanguage.JAVASCRIPT, explanation="E")
        .build()
    )
    assert len(questions) == 2
    assert all(isinstance(q, CodeCompletionQuestion) for q in questions)
