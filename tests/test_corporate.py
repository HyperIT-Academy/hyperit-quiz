"""Tests for corporate compliance tracking module (ticket #25)."""

import pytest
from datetime import date, timedelta

from src.corporate import (
    ComplianceStatus,
    ComplianceRecord,
    ComplianceTracker,
)


# ---------------------------------------------------------------------------
# ComplianceRecord.is_expired
# ---------------------------------------------------------------------------

class TestComplianceRecordIsExpired:
    def _make(self, expires_at=None, status=ComplianceStatus.PASSED, score=1.0):
        return ComplianceRecord(
            user_id=1,
            quiz_id=10,
            status=status,
            score=score,
            passed_at=date(2026, 1, 1),
            expires_at=expires_at,
        )

    def test_no_expiry_never_expired(self):
        rec = self._make(expires_at=None)
        assert rec.is_expired is False

    def test_future_expiry_not_expired(self):
        rec = self._make(expires_at=date.today() + timedelta(days=1))
        assert rec.is_expired is False

    def test_past_expiry_is_expired(self):
        rec = self._make(expires_at=date.today() - timedelta(days=1))
        assert rec.is_expired is True

    def test_today_expiry_is_expired(self):
        # expires_at == today means it expired at start of today
        rec = self._make(expires_at=date.today())
        assert rec.is_expired is True


# ---------------------------------------------------------------------------
# ComplianceTracker.record_attempt
# ---------------------------------------------------------------------------

class TestRecordAttempt:
    def setup_method(self):
        self.tracker = ComplianceTracker()
        self.today = date(2026, 5, 17)

    def test_passing_score_gives_passed_status(self):
        rec = self.tracker.record_attempt(1, 10, score=0.9, on=self.today)
        assert rec.status == ComplianceStatus.PASSED

    def test_exact_threshold_gives_passed_status(self):
        rec = self.tracker.record_attempt(1, 10, score=0.8, on=self.today)
        assert rec.status == ComplianceStatus.PASSED

    def test_below_threshold_gives_failed_status(self):
        rec = self.tracker.record_attempt(1, 10, score=0.79, on=self.today)
        assert rec.status == ComplianceStatus.FAILED

    def test_zero_score_gives_failed_status(self):
        rec = self.tracker.record_attempt(1, 10, score=0.0, on=self.today)
        assert rec.status == ComplianceStatus.FAILED

    def test_passed_at_set_on_passed(self):
        rec = self.tracker.record_attempt(1, 10, score=1.0, on=self.today)
        assert rec.passed_at == self.today

    def test_passed_at_none_on_failed(self):
        rec = self.tracker.record_attempt(1, 10, score=0.5, on=self.today)
        assert rec.passed_at is None

    def test_expires_at_set_when_expires_after_days_given(self):
        rec = self.tracker.record_attempt(1, 10, score=1.0, on=self.today, expires_after_days=30)
        assert rec.expires_at == self.today + timedelta(days=30)

    def test_expires_at_none_when_not_given(self):
        rec = self.tracker.record_attempt(1, 10, score=1.0, on=self.today)
        assert rec.expires_at is None

    def test_later_attempt_overwrites_previous(self):
        self.tracker.record_attempt(1, 10, score=0.5, on=self.today)
        rec = self.tracker.record_attempt(1, 10, score=0.95, on=self.today)
        assert rec.status == ComplianceStatus.PASSED

    def test_on_defaults_to_today(self):
        rec = self.tracker.record_attempt(1, 10, score=1.0)
        assert rec.passed_at == date.today()

    def test_fields_stored_correctly(self):
        rec = self.tracker.record_attempt(42, 99, score=0.85, on=self.today)
        assert rec.user_id == 42
        assert rec.quiz_id == 99
        assert rec.score == pytest.approx(0.85)


# ---------------------------------------------------------------------------
# ComplianceTracker.status
# ---------------------------------------------------------------------------

class TestStatus:
    def setup_method(self):
        self.tracker = ComplianceTracker()
        self.today = date(2026, 5, 17)

    def test_no_record_returns_pending(self):
        assert self.tracker.status(1, 10, as_of=self.today) == ComplianceStatus.PENDING

    def test_failed_record_returns_failed(self):
        self.tracker.record_attempt(1, 10, score=0.5, on=self.today)
        assert self.tracker.status(1, 10, as_of=self.today) == ComplianceStatus.FAILED

    def test_passed_non_expiring_returns_passed(self):
        self.tracker.record_attempt(1, 10, score=0.9, on=self.today)
        assert self.tracker.status(1, 10, as_of=self.today) == ComplianceStatus.PASSED

    def test_passed_but_expired_returns_expired(self):
        self.tracker.record_attempt(1, 10, score=0.9, on=self.today, expires_after_days=10)
        future = self.today + timedelta(days=11)
        assert self.tracker.status(1, 10, as_of=future) == ComplianceStatus.EXPIRED

    def test_passed_not_yet_expired_returns_passed(self):
        self.tracker.record_attempt(1, 10, score=0.9, on=self.today, expires_after_days=30)
        future = self.today + timedelta(days=15)
        assert self.tracker.status(1, 10, as_of=future) == ComplianceStatus.PASSED

    def test_as_of_defaults_to_today(self):
        self.tracker.record_attempt(1, 10, score=0.9, on=self.today)
        assert self.tracker.status(1, 10) == ComplianceStatus.PASSED


# ---------------------------------------------------------------------------
# ComplianceTracker.compliant_users / non_compliant_users / compliance_rate
# ---------------------------------------------------------------------------

class TestCompliantUsers:
    def setup_method(self):
        self.tracker = ComplianceTracker()
        self.today = date(2026, 5, 17)

    def _pass(self, user_id, quiz_id=10, expires_after_days=None):
        self.tracker.record_attempt(user_id, quiz_id, score=1.0, on=self.today,
                                    expires_after_days=expires_after_days)

    def _fail(self, user_id, quiz_id=10):
        self.tracker.record_attempt(user_id, quiz_id, score=0.0, on=self.today)

    def test_compliant_users_sorted(self):
        self._pass(3); self._pass(1); self._pass(2)
        assert self.tracker.compliant_users(10, as_of=self.today) == [1, 2, 3]

    def test_compliant_excludes_failed(self):
        self._pass(1); self._fail(2)
        assert self.tracker.compliant_users(10, as_of=self.today) == [1]

    def test_compliant_excludes_expired(self):
        self._pass(1, expires_after_days=5)
        future = self.today + timedelta(days=10)
        assert self.tracker.compliant_users(10, as_of=future) == []

    def test_non_compliant_users_sorted(self):
        all_users = [1, 2, 3, 4]
        self._pass(1); self._pass(3)
        result = self.tracker.non_compliant_users(10, all_users, as_of=self.today)
        assert result == [2, 4]

    def test_non_compliant_includes_pending(self):
        # user 2 has no record at all → non-compliant
        all_users = [1, 2]
        self._pass(1)
        result = self.tracker.non_compliant_users(10, all_users, as_of=self.today)
        assert result == [2]

    def test_compliance_rate_all_passed(self):
        self._pass(1); self._pass(2)
        rate = self.tracker.compliance_rate(10, [1, 2], as_of=self.today)
        assert rate == pytest.approx(1.0)

    def test_compliance_rate_half(self):
        self._pass(1); self._fail(2)
        rate = self.tracker.compliance_rate(10, [1, 2], as_of=self.today)
        assert rate == pytest.approx(0.5)

    def test_compliance_rate_empty_list(self):
        assert self.tracker.compliance_rate(10, [], as_of=self.today) == 0.0


# ---------------------------------------------------------------------------
# ComplianceTracker.format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def setup_method(self):
        self.tracker = ComplianceTracker()
        self.today = date(2026, 5, 17)

    def test_format_report_all_passed(self):
        self.tracker.record_attempt(1, 10, score=1.0, on=self.today)
        self.tracker.record_attempt(2, 10, score=1.0, on=self.today)
        report = self.tracker.format_report(10, [1, 2])
        assert report == "📋 Compliance: 2/2 (100%)\nНе пройшли: 0 осіб"

    def test_format_report_none_passed(self):
        report = self.tracker.format_report(10, [1, 2])
        assert report == "📋 Compliance: 0/2 (0%)\nНе пройшли: 2 осіб"

    def test_format_report_partial(self):
        self.tracker.record_attempt(1, 10, score=1.0, on=self.today)
        report = self.tracker.format_report(10, [1, 2, 3, 4])
        assert report == "📋 Compliance: 1/4 (25%)\nНе пройшли: 3 осіб"
