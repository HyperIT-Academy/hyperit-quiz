"""Tests for teacher onboarding flow (#27)."""
import pytest
from datetime import datetime, timezone

from src.onboarding import (
    OnboardingStep,
    OnboardingProgress,
    OnboardingManager,
    STEP_ORDER,
)


# ---------------------------------------------------------------------------
# OnboardingProgress — unit tests
# ---------------------------------------------------------------------------

class TestOnboardingProgress:
    def _make_progress(self, teacher_id: int = 1) -> OnboardingProgress:
        return OnboardingProgress(teacher_id=teacher_id)

    def test_initial_completion_pct_is_zero(self):
        p = self._make_progress()
        assert p.completion_pct == 0.0

    def test_completion_pct_after_one_step(self):
        p = self._make_progress()
        p.completed_steps.append(OnboardingStep.WELCOME)
        assert p.completion_pct == pytest.approx(1 / 5)

    def test_completion_pct_full(self):
        p = self._make_progress()
        p.completed_steps = list(STEP_ORDER)
        assert p.completion_pct == pytest.approx(1.0)

    def test_is_complete_false_when_empty(self):
        p = self._make_progress()
        assert p.is_complete is False

    def test_is_complete_true_when_all_steps_done(self):
        p = self._make_progress()
        p.completed_steps = list(STEP_ORDER)
        assert p.is_complete is True

    def test_is_complete_false_when_partial(self):
        p = self._make_progress()
        p.completed_steps = [OnboardingStep.WELCOME, OnboardingStep.CREATE_FIRST_QUIZ]
        assert p.is_complete is False

    def test_next_step_returns_first_when_none_done(self):
        p = self._make_progress()
        assert p.next_step() == OnboardingStep.WELCOME

    def test_next_step_returns_correct_next(self):
        p = self._make_progress()
        p.completed_steps = [OnboardingStep.WELCOME, OnboardingStep.CREATE_FIRST_QUIZ]
        assert p.next_step() == OnboardingStep.RUN_DEMO_SESSION

    def test_next_step_returns_none_when_all_done(self):
        p = self._make_progress()
        p.completed_steps = list(STEP_ORDER)
        assert p.next_step() is None

    def test_completed_at_is_none_initially(self):
        p = self._make_progress()
        assert p.completed_at is None

    def test_started_at_is_set_on_creation(self):
        before = datetime.now(tz=timezone.utc)
        p = self._make_progress()
        after = datetime.now(tz=timezone.utc)
        assert before <= p.started_at <= after


# ---------------------------------------------------------------------------
# OnboardingManager — unit tests
# ---------------------------------------------------------------------------

class TestOnboardingManagerStart:
    def test_start_creates_progress(self):
        mgr = OnboardingManager()
        progress = mgr.start(teacher_id=10)
        assert progress.teacher_id == 10
        assert progress.completed_steps == []

    def test_start_idempotent_returns_existing(self):
        mgr = OnboardingManager()
        first = mgr.start(teacher_id=10)
        first.completed_steps.append(OnboardingStep.WELCOME)
        second = mgr.start(teacher_id=10)
        assert second is first
        assert second.completed_steps == [OnboardingStep.WELCOME]

    def test_start_different_teachers_independent(self):
        mgr = OnboardingManager()
        p1 = mgr.start(teacher_id=1)
        p2 = mgr.start(teacher_id=2)
        assert p1 is not p2


class TestOnboardingManagerCompleteStep:
    def test_complete_step_marks_step_done(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=5)
        progress = mgr.complete_step(5, OnboardingStep.WELCOME)
        assert OnboardingStep.WELCOME in progress.completed_steps

    def test_complete_step_idempotent(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=5)
        mgr.complete_step(5, OnboardingStep.WELCOME)
        mgr.complete_step(5, OnboardingStep.WELCOME)
        progress = mgr.get(5)
        assert progress is not None
        assert progress.completed_steps.count(OnboardingStep.WELCOME) == 1

    def test_complete_step_raises_if_not_started(self):
        mgr = OnboardingManager()
        with pytest.raises(ValueError):
            mgr.complete_step(99, OnboardingStep.WELCOME)

    def test_complete_all_steps_sets_completed_at(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=7)
        for step in STEP_ORDER:
            mgr.complete_step(7, step)
        progress = mgr.get(7)
        assert progress.completed_at is not None
        assert isinstance(progress.completed_at, datetime)

    def test_completed_at_not_set_until_all_done(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=8)
        mgr.complete_step(8, OnboardingStep.WELCOME)
        assert mgr.get(8).completed_at is None


class TestOnboardingManagerGet:
    def test_get_returns_none_for_unknown(self):
        mgr = OnboardingManager()
        assert mgr.get(999) is None

    def test_get_returns_progress_after_start(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=3)
        assert mgr.get(3) is not None
        assert mgr.get(3).teacher_id == 3


class TestOnboardingManagerIncompleteTeachers:
    def test_incomplete_returns_started_but_not_finished(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=1)
        mgr.start(teacher_id=2)
        # Complete teacher 2 fully
        for step in STEP_ORDER:
            mgr.complete_step(2, step)
        incomplete = mgr.incomplete_teachers()
        assert incomplete == [1]
        assert 2 not in incomplete

    def test_incomplete_sorted(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=5)
        mgr.start(teacher_id=2)
        mgr.start(teacher_id=8)
        assert mgr.incomplete_teachers() == [2, 5, 8]

    def test_incomplete_empty_when_all_done(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=1)
        for step in STEP_ORDER:
            mgr.complete_step(1, step)
        assert mgr.incomplete_teachers() == []


class TestOnboardingManagerFormatProgress:
    def test_format_progress_returns_none_for_unknown(self):
        mgr = OnboardingManager()
        assert mgr.format_progress(999) is None

    def test_format_progress_complete(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=1)
        for step in STEP_ORDER:
            mgr.complete_step(1, step)
        result = mgr.format_progress(1)
        assert result == "🎉 Онбординг завершено!"

    def test_format_progress_partial(self):
        mgr = OnboardingManager()
        mgr.start(teacher_id=2)
        mgr.complete_step(2, OnboardingStep.WELCOME)
        mgr.complete_step(2, OnboardingStep.CREATE_FIRST_QUIZ)
        result = mgr.format_progress(2)
        # Completed 2 of 5, next is RUN_DEMO_SESSION
        assert "✅ Крок 2/5" in result
        assert "Run Demo Session" in result
        assert "➡️ Далі: Invite Students" in result
