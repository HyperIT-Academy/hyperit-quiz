"""Tests for GDPR/COPPA consent management (TDD RED phase)."""
import hashlib
from datetime import datetime

import pytest

from src.consent import (
    ConsentManager,
    ConsentRecord,
    ConsentStatus,
    DataCategory,
)


# ---------------------------------------------------------------------------
# ConsentStatus / DataCategory enum sanity
# ---------------------------------------------------------------------------

def test_consent_status_values():
    assert ConsentStatus.PENDING == "pending"
    assert ConsentStatus.GRANTED == "granted"
    assert ConsentStatus.DENIED == "denied"
    assert ConsentStatus.REVOKED == "revoked"


def test_data_category_values():
    assert DataCategory.ANSWERS == "answers"
    assert DataCategory.RESPONSE_TIMES == "response_times"
    assert DataCategory.PROGRESS == "progress"
    assert DataCategory.ANALYTICS == "analytics"


# ---------------------------------------------------------------------------
# grant()
# ---------------------------------------------------------------------------

def test_grant_creates_granted_record():
    mgr = ConsentManager()
    rec = mgr.grant(user_id=1)
    assert rec.user_id == 1
    assert rec.status == ConsentStatus.GRANTED
    assert rec.granted_at is not None
    assert isinstance(rec.granted_at, datetime)


def test_grant_non_minor_defaults():
    mgr = ConsentManager()
    rec = mgr.grant(user_id=2)
    assert rec.is_minor is False
    assert rec.guardian_id is None


def test_grant_minor_requires_guardian_id():
    mgr = ConsentManager()
    with pytest.raises(ValueError):
        mgr.grant(user_id=3, is_minor=True)


def test_grant_minor_with_guardian():
    mgr = ConsentManager()
    rec = mgr.grant(user_id=4, is_minor=True, guardian_id=99)
    assert rec.is_minor is True
    assert rec.guardian_id == 99
    assert rec.status == ConsentStatus.GRANTED


def test_grant_idempotent_overwrites():
    """Повторний grant оновлює запис (не кидає)."""
    mgr = ConsentManager()
    mgr.grant(user_id=5)
    rec2 = mgr.grant(user_id=5)
    assert rec2.status == ConsentStatus.GRANTED


# ---------------------------------------------------------------------------
# deny()
# ---------------------------------------------------------------------------

def test_deny_creates_denied_record():
    mgr = ConsentManager()
    rec = mgr.deny(user_id=10)
    assert rec.status == ConsentStatus.DENIED


def test_deny_when_no_record():
    mgr = ConsentManager()
    rec = mgr.deny(user_id=20)
    assert rec.user_id == 20
    assert rec.status == ConsentStatus.DENIED


def test_deny_existing_granted():
    mgr = ConsentManager()
    mgr.grant(user_id=30)
    rec = mgr.deny(user_id=30)
    assert rec.status == ConsentStatus.DENIED


# ---------------------------------------------------------------------------
# revoke()
# ---------------------------------------------------------------------------

def test_revoke_granted_sets_revoked():
    mgr = ConsentManager()
    mgr.grant(user_id=40)
    rec = mgr.revoke(user_id=40)
    assert rec.status == ConsentStatus.REVOKED
    assert rec.revoked_at is not None


def test_revoke_non_granted_raises():
    mgr = ConsentManager()
    mgr.deny(user_id=50)
    with pytest.raises(ValueError):
        mgr.revoke(user_id=50)


def test_revoke_missing_user_raises():
    mgr = ConsentManager()
    with pytest.raises(ValueError):
        mgr.revoke(user_id=999)


# ---------------------------------------------------------------------------
# has_consent()
# ---------------------------------------------------------------------------

def test_has_consent_true_when_granted():
    mgr = ConsentManager()
    mgr.grant(user_id=60)
    assert mgr.has_consent(60) is True


def test_has_consent_false_when_denied():
    mgr = ConsentManager()
    mgr.deny(user_id=61)
    assert mgr.has_consent(61) is False


def test_has_consent_false_when_revoked():
    mgr = ConsentManager()
    mgr.grant(user_id=62)
    mgr.revoke(user_id=62)
    assert mgr.has_consent(62) is False


def test_has_consent_false_when_no_record():
    mgr = ConsentManager()
    assert mgr.has_consent(9999) is False


# ---------------------------------------------------------------------------
# allow_category() / is_allowed()
# ---------------------------------------------------------------------------

def test_allow_category_requires_consent():
    mgr = ConsentManager()
    mgr.deny(user_id=70)
    with pytest.raises(ValueError):
        mgr.allow_category(70, DataCategory.ANSWERS)


def test_allow_category_and_is_allowed():
    mgr = ConsentManager()
    mgr.grant(user_id=80)
    mgr.allow_category(80, DataCategory.ANSWERS)
    assert mgr.is_allowed(80, DataCategory.ANSWERS) is True


def test_is_allowed_false_for_not_added_category():
    mgr = ConsentManager()
    mgr.grant(user_id=81)
    mgr.allow_category(81, DataCategory.ANSWERS)
    assert mgr.is_allowed(81, DataCategory.ANALYTICS) is False


def test_is_allowed_false_without_consent():
    mgr = ConsentManager()
    assert mgr.is_allowed(82, DataCategory.PROGRESS) is False


def test_is_allowed_false_after_revoke():
    mgr = ConsentManager()
    mgr.grant(user_id=83)
    mgr.allow_category(83, DataCategory.ANSWERS)
    mgr.revoke(user_id=83)
    assert mgr.is_allowed(83, DataCategory.ANSWERS) is False


# ---------------------------------------------------------------------------
# anonymize()
# ---------------------------------------------------------------------------

def test_anonymize_returns_hashed_user_id_and_status():
    mgr = ConsentManager()
    mgr.grant(user_id=90)
    result = mgr.anonymize(90)
    expected_hash = hashlib.sha256(str(90).encode()).hexdigest()
    assert result["user_id"] == expected_hash
    assert result["status"] == ConsentStatus.GRANTED


def test_anonymize_does_not_delete_record():
    mgr = ConsentManager()
    mgr.grant(user_id=91)
    mgr.anonymize(91)
    assert mgr.has_consent(91) is True


def test_anonymize_missing_user_raises():
    mgr = ConsentManager()
    with pytest.raises(KeyError):
        mgr.anonymize(9999)


# ---------------------------------------------------------------------------
# minors()
# ---------------------------------------------------------------------------

def test_minors_returns_only_granted_minors():
    mgr = ConsentManager()
    mgr.grant(user_id=100, is_minor=True, guardian_id=200)
    mgr.grant(user_id=101)  # adult
    mgr.grant(user_id=102, is_minor=True, guardian_id=201)
    mgr.deny(user_id=103)   # denied — не враховується

    result = mgr.minors()
    ids = [r.user_id for r in result]
    assert 100 in ids
    assert 102 in ids
    assert 101 not in ids
    assert 103 not in ids


def test_minors_empty_when_none():
    mgr = ConsentManager()
    assert mgr.minors() == []
