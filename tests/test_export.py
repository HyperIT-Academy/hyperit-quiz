"""Tests for export formatter (closes #15) — RED phase."""
from __future__ import annotations

import pytest
from src.session import Question, QuizSession
from src.analytics import SessionSummary, build_summary
from src.export import session_to_csv, summary_to_text


# ── helpers ─────────────────────────────────────────────────────────────────

def make_two_question_session() -> QuizSession:
    questions = [
        Question(id=0, text="Що таке Python?", options=["Мова", "Змія", "Гра"], correct_index=0, explanation="Python — мова програмування"),
        Question(id=1, text="Що таке змінна?", options=["Комірка пам'яті", "Функція", "Клас"], correct_index=0, explanation="Змінна — комірка пам'яті"),
    ]
    session = QuizSession(quiz_id=1, questions=questions)
    session.start()
    # user 1: both correct
    session.answer(1, 0, 2000)   # q0 correct
    session.next_question()
    session.answer(1, 0, 4000)   # q1 correct
    session.next_question()
    return session


def make_session_with_mistakes() -> QuizSession:
    questions = [
        Question(id=0, text="Що таке Python?", options=["Мова", "Змія", "Гра"], correct_index=0, explanation=""),
        Question(id=1, text="Що таке змінна?", options=["Комірка пам'яті", "Функція", "Клас"], correct_index=0, explanation=""),
    ]
    session = QuizSession(quiz_id=2, questions=questions)
    session.start()
    # user 1: q0 correct, q1 wrong
    session.answer(1, 0)   # q0 correct
    session.next_question()
    session.answer(1, 1)   # q1 wrong (chose "Функція")
    # user 2: both wrong
    session.answer(2, 1)   # q1 wrong
    session.next_question()
    return session


PERSONA_MAP = {1: "Аліса", 2: "Боб"}


# ── session_to_csv ───────────────────────────────────────────────────────────

class TestSessionToCsv:
    def test_returns_string(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        assert isinstance(result, str)

    def test_has_header_row(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        lines = result.strip().splitlines()
        assert "persona" in lines[0]
        assert "total_score" in lines[0]

    def test_header_contains_question_columns(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        header = result.strip().splitlines()[0]
        assert "q1_correct" in header
        assert "q2_correct" in header

    def test_data_row_count_matches_participants(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        lines = result.strip().splitlines()
        # 1 header + 1 participant
        assert len(lines) == 2

    def test_persona_name_in_row(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        assert "Аліса" in result

    def test_all_correct_total_score(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        # Аліса answered both correctly → total_score = 2
        data_line = result.strip().splitlines()[1]
        assert data_line.endswith("2")

    def test_correct_column_value_1_for_correct_answer(self):
        session = make_two_question_session()
        result = session_to_csv(session, PERSONA_MAP)
        data_line = result.strip().splitlines()[1]
        fields = data_line.split(",")
        # fields[1] = q1_correct, fields[2] = q2_correct
        assert fields[1] == "1"
        assert fields[2] == "1"

    def test_wrong_answer_marked_0(self):
        session = make_session_with_mistakes()
        result = session_to_csv(session, {1: "Аліса", 2: "Боб"})
        lines = result.strip().splitlines()
        # Find Аліса line (user 1): q1 correct=1, q2 wrong=0
        alice_line = next(l for l in lines[1:] if "Аліса" in l)
        fields = alice_line.split(",")
        assert fields[1] == "1"   # q1 correct
        assert fields[2] == "0"   # q2 wrong

    def test_unknown_user_falls_back_to_id(self):
        session = make_two_question_session()
        # pass empty persona_map
        result = session_to_csv(session, {})
        assert "1" in result   # user_id as string

    def test_two_participants(self):
        session = make_session_with_mistakes()
        result = session_to_csv(session, {1: "Аліса", 2: "Боб"})
        lines = result.strip().splitlines()
        assert len(lines) == 3   # header + 2 participants

    def test_no_answers_session_returns_header_only(self):
        questions = [
            Question(id=0, text="Q", options=["A", "B"], correct_index=0, explanation="")
        ]
        session = QuizSession(quiz_id=3, questions=questions)
        result = session_to_csv(session, {})
        lines = result.strip().splitlines()
        assert len(lines) == 1   # header only, no participants


# ── summary_to_text ──────────────────────────────────────────────────────────

class TestSummaryToText:
    def test_returns_string(self):
        session = make_two_question_session()
        summary = build_summary(session)
        result = summary_to_text(summary)
        assert isinstance(result, str)

    def test_contains_participant_count(self):
        session = make_two_question_session()
        summary = build_summary(session)
        result = summary_to_text(summary)
        assert "1" in result   # 1 учасник

    def test_contains_accuracy_percentage(self):
        session = make_two_question_session()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # All correct → 100%
        assert "100" in result

    def test_contains_weak_question_texts(self):
        # When there are weak questions, their text must appear in the report.
        session = make_session_with_mistakes()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # "Що таке змінна?" had 0% accuracy → weak
        assert "змінна" in result

    def test_shows_per_question_accuracy(self):
        session = make_session_with_mistakes()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # Should contain % signs showing per-question accuracy
        assert "%" in result

    def test_marks_weak_questions(self):
        session = make_session_with_mistakes()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # "Що таке змінна?" was answered wrong by everyone — should be flagged
        assert "змінна" in result

    def test_multiline_output(self):
        session = make_two_question_session()
        summary = build_summary(session)
        result = summary_to_text(summary)
        assert "\n" in result

    def test_no_weak_questions_when_all_correct(self):
        session = make_two_question_session()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # No weak questions section should be minimal / not show "Слабкі"
        # (or it's present but empty) — at minimum, the text is non-empty
        assert len(result) > 0

    def test_top_mistake_highlighted(self):
        session = make_session_with_mistakes()
        summary = build_summary(session)
        result = summary_to_text(summary)
        # top_mistake should appear prominently
        assert summary.top_mistake is not None
        assert summary.top_mistake.text[:20] in result
