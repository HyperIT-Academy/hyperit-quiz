"""Corporate compliance tracking for onboarding and training quizzes."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class ComplianceStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class ComplianceRecord:
    user_id: int
    quiz_id: int
    status: ComplianceStatus
    score: float          # 0.0–1.0
    passed_at: date | None = None
    expires_at: date | None = None  # None = ніколи не закінчується

    @property
    def is_expired(self) -> bool:
        """True якщо expires_at існує і менший або рівний today."""
        if self.expires_at is None:
            return False
        return self.expires_at <= date.today()


class ComplianceTracker:
    """Відстежує проходження compliance квізів у корпоративному контексті."""

    PASS_THRESHOLD: float = 0.8   # мінімальний score для PASSED

    def __init__(self) -> None:
        self._records: dict[tuple[int, int], ComplianceRecord] = {}

    def record_attempt(
        self,
        user_id: int,
        quiz_id: int,
        score: float,
        on: date | None = None,
        expires_after_days: int | None = None,
    ) -> ComplianceRecord:
        """Записує спробу. score >= PASS_THRESHOLD → PASSED, інакше FAILED.
        expires_after_days: якщо вказано — проставляє expires_at = on + delta.
        on: None → date.today()"""
        attempt_date = on if on is not None else date.today()
        passed = score >= self.PASS_THRESHOLD

        expires_at: date | None = None
        if expires_after_days is not None:
            expires_at = attempt_date + timedelta(days=expires_after_days)

        record = ComplianceRecord(
            user_id=user_id,
            quiz_id=quiz_id,
            status=ComplianceStatus.PASSED if passed else ComplianceStatus.FAILED,
            score=score,
            passed_at=attempt_date if passed else None,
            expires_at=expires_at,
        )
        self._records[(user_id, quiz_id)] = record
        return record

    def status(
        self,
        user_id: int,
        quiz_id: int,
        as_of: date | None = None,
    ) -> ComplianceStatus:
        """Повертає статус. Якщо PASSED але expires_at < as_of → EXPIRED.
        as_of: None → date.today(). Немає запису → PENDING."""
        check_date = as_of if as_of is not None else date.today()
        record = self._records.get((user_id, quiz_id))

        if record is None:
            return ComplianceStatus.PENDING

        if record.status == ComplianceStatus.PASSED:
            if record.expires_at is not None and record.expires_at <= check_date:
                return ComplianceStatus.EXPIRED
            return ComplianceStatus.PASSED

        return record.status

    def compliant_users(
        self,
        quiz_id: int,
        as_of: date | None = None,
    ) -> list[int]:
        """user_id з діючим PASSED статусом (не EXPIRED). Відсортовано."""
        check_date = as_of if as_of is not None else date.today()
        result = [
            user_id
            for (user_id, qid) in self._records
            if qid == quiz_id
            and self.status(user_id, quiz_id, as_of=check_date) == ComplianceStatus.PASSED
        ]
        return sorted(result)

    def non_compliant_users(
        self,
        quiz_id: int,
        all_user_ids: list[int],
        as_of: date | None = None,
    ) -> list[int]:
        """user_id з all_user_ids хто не має діючого PASSED. Відсортовано."""
        check_date = as_of if as_of is not None else date.today()
        result = [
            uid
            for uid in all_user_ids
            if self.status(uid, quiz_id, as_of=check_date) != ComplianceStatus.PASSED
        ]
        return sorted(result)

    def compliance_rate(
        self,
        quiz_id: int,
        all_user_ids: list[int],
        as_of: date | None = None,
    ) -> float:
        """Частка compliant users від загальної кількості. 0.0 якщо порожній список."""
        if not all_user_ids:
            return 0.0
        check_date = as_of if as_of is not None else date.today()
        compliant = self.compliant_users(quiz_id, as_of=check_date)
        compliant_set = set(compliant) & set(all_user_ids)
        return len(compliant_set) / len(all_user_ids)

    def format_report(self, quiz_id: int, all_user_ids: list[int]) -> str:
        """'📋 Compliance: X/N (Y%)\\nНе пройшли: Z осіб'"""
        n = len(all_user_ids)
        compliant = self.compliant_users(quiz_id)
        compliant_in_list = [uid for uid in compliant if uid in set(all_user_ids)]
        x = len(compliant_in_list)
        z = n - x
        pct = round(x / n * 100) if n > 0 else 0
        return f"📋 Compliance: {x}/{n} ({pct}%)\nНе пройшли: {z} осіб"
