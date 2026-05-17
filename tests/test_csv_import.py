"""Tests for CSV question import (closes #22) — RED phase."""
from __future__ import annotations

import io
import pytest
from src.csv_import import parse_csv, CsvImportError


VALID_CSV = """\
text,option_a,option_b,option_c,option_d,correct,explanation
Що виведе print(type(1))?,<class 'int'>,<class 'str'>,<class 'float'>,None,a,type() повертає тип об'єкту
Що означає DRY?,Don't Repeat Yourself,Do Run Yearly,Debug Refactor Yield,Data Runs Yesterday,a,DRY = Don't Repeat Yourself
"""

MINIMAL_CSV = """\
text,option_a,option_b,correct,explanation
Скільки 2+2?,3,4,b,Арифметика
"""


def test_parse_valid_csv_returns_questions():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert len(questions) == 2


def test_parsed_question_text():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert "print(type(1))" in questions[0].text


def test_parsed_correct_index_a():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert questions[0].correct_index == 0


def test_parsed_explanation():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert "type()" in questions[0].explanation


def test_parsed_options_count():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert len(questions[0].options) == 4


def test_minimal_two_options():
    questions = parse_csv(io.StringIO(MINIMAL_CSV))
    assert len(questions[0].options) == 2
    assert questions[0].correct_index == 1   # 'b' → index 1


def test_ids_are_sequential():
    questions = parse_csv(io.StringIO(VALID_CSV))
    assert [q.id for q in questions] == [0, 1]


def test_missing_text_raises():
    bad = "text,option_a,option_b,correct,explanation\n,A,B,a,Exp\n"
    with pytest.raises(CsvImportError, match="text"):
        parse_csv(io.StringIO(bad))


def test_invalid_correct_letter_raises():
    bad = "text,option_a,option_b,correct,explanation\nQ,A,B,z,Exp\n"
    with pytest.raises(CsvImportError, match="correct"):
        parse_csv(io.StringIO(bad))


def test_correct_index_out_of_options_raises():
    # correct=c but only option_a and option_b provided
    bad = "text,option_a,option_b,correct,explanation\nQ,A,B,c,Exp\n"
    with pytest.raises(CsvImportError):
        parse_csv(io.StringIO(bad))


def test_empty_csv_returns_empty_list():
    empty = "text,option_a,option_b,correct,explanation\n"
    assert parse_csv(io.StringIO(empty)) == []
