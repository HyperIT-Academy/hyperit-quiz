"""Tests for PauseController — Ticket #7."""
import pytest
from src.pause import PauseController, PauseEvent, PauseReason


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ctrl():
    return PauseController(auto_pause_threshold=0.4)


# ── 1. Initial state ───────────────────────────────────────────────────────────

def test_not_paused_initially(ctrl):
    assert ctrl.is_paused() is False


def test_pause_history_empty_initially(ctrl):
    assert ctrl.pause_history() == []


# ── 2. should_auto_pause ───────────────────────────────────────────────────────

def test_should_auto_pause_below_threshold(ctrl):
    # 1/5 = 0.2 < 0.4 → True
    assert ctrl.should_auto_pause(correct_count=1, total_answers=5) is True


def test_should_auto_pause_at_threshold(ctrl):
    # 2/5 = 0.4 == 0.4 → False (strictly less than)
    assert ctrl.should_auto_pause(correct_count=2, total_answers=5) is False


def test_should_auto_pause_above_threshold(ctrl):
    # 3/5 = 0.6 > 0.4 → False
    assert ctrl.should_auto_pause(correct_count=3, total_answers=5) is False


def test_should_auto_pause_zero_answers(ctrl):
    # 0 answers → cannot determine accuracy → False
    assert ctrl.should_auto_pause(correct_count=0, total_answers=0) is False


def test_custom_threshold():
    ctrl = PauseController(auto_pause_threshold=0.7)
    # 3/5 = 0.6 < 0.7 → True
    assert ctrl.should_auto_pause(correct_count=3, total_answers=5) is True


# ── 3. manual_pause ───────────────────────────────────────────────────────────

def test_manual_pause_sets_paused(ctrl):
    ctrl.manual_pause(question_index=2)
    assert ctrl.is_paused() is True


def test_manual_pause_returns_event(ctrl):
    event = ctrl.manual_pause(question_index=2)
    assert isinstance(event, PauseEvent)
    assert event.question_index == 2
    assert event.reason == PauseReason.TEACHER_MANUAL
    assert event.accuracy_at_pause is None


def test_manual_pause_recorded_in_history(ctrl):
    ctrl.manual_pause(question_index=0)
    history = ctrl.pause_history()
    assert len(history) == 1
    assert history[0].reason == PauseReason.TEACHER_MANUAL


# ── 4. resume ─────────────────────────────────────────────────────────────────

def test_resume_clears_paused(ctrl):
    ctrl.manual_pause(question_index=1)
    ctrl.resume()
    assert ctrl.is_paused() is False


def test_resume_does_not_clear_history(ctrl):
    ctrl.manual_pause(question_index=1)
    ctrl.resume()
    assert len(ctrl.pause_history()) == 1


# ── 5. check_and_auto_pause ───────────────────────────────────────────────────

def test_check_and_auto_pause_triggers(ctrl):
    event = ctrl.check_and_auto_pause(question_index=3, correct_count=1, total_answers=5)
    assert event is not None
    assert event.reason == PauseReason.LOW_ACCURACY
    assert event.question_index == 3
    assert ctrl.is_paused() is True


def test_check_and_auto_pause_no_trigger(ctrl):
    event = ctrl.check_and_auto_pause(question_index=3, correct_count=3, total_answers=5)
    assert event is None
    assert ctrl.is_paused() is False


def test_check_and_auto_pause_accuracy_stored(ctrl):
    ctrl.check_and_auto_pause(question_index=2, correct_count=1, total_answers=5)
    history = ctrl.pause_history()
    assert len(history) == 1
    # 1/5 = 0.2
    assert abs(history[0].accuracy_at_pause - 0.2) < 1e-9


# ── 6. record_pause (direct) ──────────────────────────────────────────────────

def test_record_pause_low_accuracy(ctrl):
    event = ctrl.record_pause(
        question_index=4,
        reason=PauseReason.LOW_ACCURACY,
        accuracy=0.25,
    )
    assert event.accuracy_at_pause == 0.25
    assert event.reason == PauseReason.LOW_ACCURACY
    assert ctrl.is_paused() is True


def test_record_pause_manual_no_accuracy(ctrl):
    event = ctrl.record_pause(
        question_index=0,
        reason=PauseReason.TEACHER_MANUAL,
    )
    assert event.accuracy_at_pause is None


# ── 7. Multiple pauses / history accumulation ─────────────────────────────────

def test_multiple_pauses_accumulate_in_history(ctrl):
    ctrl.manual_pause(question_index=0)
    ctrl.resume()
    ctrl.check_and_auto_pause(question_index=2, correct_count=0, total_answers=5)
    assert len(ctrl.pause_history()) == 2


def test_history_returns_copy(ctrl):
    """Mutating the returned list must not affect internal state."""
    ctrl.manual_pause(question_index=0)
    h = ctrl.pause_history()
    h.clear()
    assert len(ctrl.pause_history()) == 1
