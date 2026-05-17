"""GDPR/COPPA consent management module."""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class DataCategory(str, Enum):
    ANSWERS = "answers"
    RESPONSE_TIMES = "response_times"
    PROGRESS = "progress"
    ANALYTICS = "analytics"


@dataclass
class ConsentRecord:
    user_id: int
    status: ConsentStatus
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    is_minor: bool = False
    guardian_id: int | None = None


class ConsentManager:
    """Управління згодою на обробку даних."""

    def __init__(self) -> None:
        self._records: dict[int, ConsentRecord] = {}
        self._allowed_categories: dict[int, set[DataCategory]] = {}

    def grant(
        self,
        user_id: int,
        is_minor: bool = False,
        guardian_id: int | None = None,
    ) -> ConsentRecord:
        """Реєструє згоду. Для неповнолітніх потрібен guardian_id (інакше ValueError)."""
        if is_minor and guardian_id is None:
            raise ValueError("guardian_id required for minors (COPPA)")
        record = ConsentRecord(
            user_id=user_id,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(),
            is_minor=is_minor,
            guardian_id=guardian_id,
        )
        self._records[user_id] = record
        return record

    def deny(self, user_id: int) -> ConsentRecord:
        """Відмова від згоди. Якщо запису нема — створює зі статусом DENIED."""
        record = ConsentRecord(user_id=user_id, status=ConsentStatus.DENIED)
        self._records[user_id] = record
        return record

    def revoke(self, user_id: int) -> ConsentRecord:
        """Відкликання існуючої згоди (GRANTED → REVOKED). ValueError якщо не GRANTED."""
        record = self._records.get(user_id)
        if record is None or record.status != ConsentStatus.GRANTED:
            raise ValueError(
                f"Cannot revoke: user {user_id} does not have GRANTED consent"
            )
        record.status = ConsentStatus.REVOKED
        record.revoked_at = datetime.now()
        return record

    def has_consent(self, user_id: int) -> bool:
        """True якщо статус GRANTED."""
        record = self._records.get(user_id)
        return record is not None and record.status == ConsentStatus.GRANTED

    def allow_category(self, user_id: int, category: DataCategory) -> None:
        """Дозволяє збір конкретної категорії даних (тільки якщо є consent)."""
        if not self.has_consent(user_id):
            raise ValueError(
                f"Cannot allow category: user {user_id} has no GRANTED consent"
            )
        self._allowed_categories.setdefault(user_id, set()).add(category)

    def is_allowed(self, user_id: int, category: DataCategory) -> bool:
        """True якщо є consent і категорія дозволена."""
        return self.has_consent(user_id) and category in self._allowed_categories.get(
            user_id, set()
        )

    def anonymize(self, user_id: int) -> dict:
        """Повертає мінімізовані дані: {user_id: hash(user_id), status}.
        НЕ видаляє — тільки повертає анонімізовану версію."""
        record = self._records[user_id]  # KeyError if missing
        hashed = hashlib.sha256(str(user_id).encode()).hexdigest()
        return {"user_id": hashed, "status": record.status}

    def minors(self) -> list[ConsentRecord]:
        """Всі неповнолітні зі статусом GRANTED."""
        return [
            r
            for r in self._records.values()
            if r.is_minor and r.status == ConsentStatus.GRANTED
        ]
