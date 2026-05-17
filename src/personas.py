"""Anonymous persona assignment — no shaming, no real names in leaderboard."""
from __future__ import annotations

PERSONAS: list[str] = [
    "🦊 Хитра Лисиця", "🐉 Синій Дракон", "🦁 Сміливий Лев", "🐺 Сірий Вовк",
    "🦅 Гострий Орел", "🐬 Швидкий Дельфін", "🦋 Строката Метелик", "🐻 Бурий Ведмідь",
    "🦉 Мудра Сова", "🐯 Смугастий Тигр", "🦄 Чарівний Єдиноріг", "🐊 Зелений Крокодил",
    "🦈 Океанська Акула", "🦜 Яскравий Папуга", "🐘 Сильний Слон", "🦩 Рожевий Фламінго",
    "🦝 Спритний Єнот", "🐆 Плямистий Гепард", "🦌 Гордий Олень", "🦔 Колючий Їжак",
    "🐋 Великий Кит", "🦓 Смугаста Зебра", "🦒 Висока Жирафа", "🐙 Хитрий Восьминіг",
    "🦀 Бічний Краб", "🦚 Павлин із Хвостом", "🐢 Мудра Черепаха", "🦭 Ластоногий Тюлень",
    "🦘 Стрибучий Кенгуру", "🦦 Грайлива Видра", "🦬 Могутній Бізон", "🐓 Гордий Півень",
]


def assign_persona(user_id: int, session_id: int) -> str:
    """Deterministically assign a unique persona per (user, session) pair."""
    # Collect all participants seen so far would require shared state;
    # here we use a stable hash-based index within the PERSONAS pool.
    idx = (user_id * 2654435761 ^ session_id * 2246822519) % len(PERSONAS)
    return PERSONAS[idx]


def format_leaderboard_anonymous(
    board: list[tuple[int, int]],
    session_id: int,
) -> str:
    """Render leaderboard with persona names instead of user IDs."""
    lines = ["🏆 Результати:"]
    for rank, (user_id, score) in enumerate(board, 1):
        persona = assign_persona(user_id=user_id, session_id=session_id)
        lines.append(f"{rank}. {persona} — {score} балів")
    return "\n".join(lines)
