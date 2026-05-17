"""CSV question importer (closes #22).

CSV format:
  text, option_a, option_b, [option_c], [option_d], correct, explanation
  correct = one of: a, b, c, d  (case-insensitive)
"""
from __future__ import annotations

import csv
from typing import IO

from .session import Question

LETTER_TO_INDEX = {"a": 0, "b": 1, "c": 2, "d": 3}
OPTION_COLUMNS = ["option_a", "option_b", "option_c", "option_d"]


class CsvImportError(ValueError):
    pass


def parse_csv(file: IO[str]) -> list[Question]:
    reader = csv.DictReader(file)
    questions: list[Question] = []

    for row_num, row in enumerate(reader, start=2):
        text = (row.get("text") or "").strip()
        if not text:
            raise CsvImportError(f"Row {row_num}: 'text' is empty or missing")

        options = [
            row[col].strip()
            for col in OPTION_COLUMNS
            if col in row and row[col].strip()
        ]

        raw_correct = (row.get("correct") or "").strip().lower()
        if raw_correct not in LETTER_TO_INDEX:
            raise CsvImportError(
                f"Row {row_num}: 'correct' must be a/b/c/d, got '{raw_correct}'"
            )

        correct_index = LETTER_TO_INDEX[raw_correct]
        if correct_index >= len(options):
            raise CsvImportError(
                f"Row {row_num}: correct='{raw_correct}' but only {len(options)} options provided"
            )

        explanation = (row.get("explanation") or "").strip()

        questions.append(
            Question(
                id=len(questions),
                text=text,
                options=options,
                correct_index=correct_index,
                explanation=explanation,
            )
        )

    return questions
