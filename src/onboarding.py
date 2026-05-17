"""Teacher onboarding flow — closes #27."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OnboardingStep(str, Enum):
    WELCOME = "welcome"
    CREATE_FIRST_QUIZ = "create_first_quiz"
    RUN_DEMO_SESSION = "run_demo_session"
    INVITE_STUDENTS = "invite_students"
    REVIEW_ANALYTICS = "review_analytics"


STEP_ORDER = [
    OnboardingStep.WELCOME,
    OnboardingStep.CREATE_FIRST_QUIZ,
    OnboardingStep.RUN_DEMO_SESSION,
    OnboardingStep.INVITE_STUDENTS,
    OnboardingStep.REVIEW_ANALYTICS,
]

_STEP_DISPLAY = {
    OnboardingStep.WELCOME: "Welcome",
    OnboardingStep.CREATE_FIRST_QUIZ: "Create First Quiz",
    OnboardingStep.RUN_DEMO_SESSION: "Run Demo Session",
    OnboardingStep.INVITE_STUDENTS: "Invite Students",
    OnboardingStep.REVIEW_ANALYTICS: "Review Analytics",
}


@dataclass
class OnboardingProgress:
    teacher_id: int
    completed_steps: list[OnboardingStep] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def is_complete(self) -> bool:
        return set(STEP_ORDER).issubset(set(self.completed_steps))

    @property
    def completion_pct(self) -> float:
        """0.0–1.0"""
        if not STEP_ORDER:
            return 0.0
        done = len(set(self.completed_steps) & set(STEP_ORDER))
        return done / len(STEP_ORDER)

    def next_step(self) -> OnboardingStep | None:
        """Повертає перший незавершений крок або None якщо всі виконані."""
        done = set(self.completed_steps)
        for step in STEP_ORDER:
            if step not in done:
                return step
        return None


class OnboardingManager:
    def __init__(self) -> None:
        self._progress: dict[int, OnboardingProgress] = {}

    def start(self, teacher_id: int) -> OnboardingProgress:
        """Ініціює онбординг. Якщо вже є — повертає існуючий."""
        if teacher_id not in self._progress:
            self._progress[teacher_id] = OnboardingProgress(teacher_id=teacher_id)
        return self._progress[teacher_id]

    def complete_step(self, teacher_id: int,
                      step: OnboardingStep) -> OnboardingProgress:
        """Позначає крок виконаним. Ідемпотентний (повторний виклик безпечний).
        Якщо всі кроки виконано — проставляє completed_at.
        ValueError якщо teacher_id не знайдено."""
        progress = self._progress.get(teacher_id)
        if progress is None:
            raise ValueError(f"Teacher {teacher_id} has not started onboarding")

        if step not in progress.completed_steps:
            progress.completed_steps.append(step)

        if progress.is_complete and progress.completed_at is None:
            progress.completed_at = datetime.utcnow()

        return progress

    def get(self, teacher_id: int) -> OnboardingProgress | None:
        return self._progress.get(teacher_id)

    def incomplete_teachers(self) -> list[int]:
        """teacher_id хто почав але не завершив онбординг (відсортовано)."""
        return sorted(
            tid for tid, p in self._progress.items() if not p.is_complete
        )

    def format_progress(self, teacher_id: int) -> str | None:
        """Текстовий прогрес: '✅ Крок 3/5: Run Demo Session\\n➡️ Далі: Invite Students'
        або '🎉 Онбординг завершено!' якщо все виконано. None якщо teacher не знайдено."""
        progress = self._progress.get(teacher_id)
        if progress is None:
            return None

        if progress.is_complete:
            return "🎉 Онбординг завершено!"

        total = len(STEP_ORDER)
        done_count = len(set(progress.completed_steps) & set(STEP_ORDER))
        next_step = progress.next_step()
        next_display = _STEP_DISPLAY[next_step]

        # Find what comes after next_step
        next_idx = STEP_ORDER.index(next_step)
        after_idx = next_idx + 1
        if after_idx < total:
            after_display = _STEP_DISPLAY[STEP_ORDER[after_idx]]
            after_line = f"\n➡️ Далі: {after_display}"
        else:
            after_line = ""

        return f"✅ Крок {done_count}/{total}: {next_display}{after_line}"
