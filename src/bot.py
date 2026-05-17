"""Telegram MVP bot for HyperIT Quiz."""
from __future__ import annotations

import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from .session import SessionState
from .store import create_session, get_session, remove_session

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger(__name__)

bot = Bot(token=os.environ["BOT_TOKEN"])
dp = Dispatcher()

LETTERS = ["A", "B", "C", "D"]


def _question_keyboard(session_id: int, n_options: int) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=LETTERS[i],
            callback_data=f"ans:{session_id}:{i}",
        )
        for i in range(n_options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def _format_question(index: int, total: int, text: str, options: list[str]) -> str:
    header = f"❓ Питання {index + 1}/{total}\n\n{text}\n\n"
    choices = "\n".join(f"{LETTERS[i]}. {opt}" for i, opt in enumerate(options))
    return header + choices


@dp.message(Command("quiz"))
async def cmd_quiz(message: Message) -> None:
    chat_id = message.chat.id
    if get_session(chat_id) is not None:
        await message.answer("Квіз вже йде. /stop щоб зупинити.")
        return

    session = create_session(chat_id)
    session.start()
    q = session.current_question()
    await message.answer(
        _format_question(0, len(session.questions), q.text, q.options),
        reply_markup=_question_keyboard(chat_id, len(q.options)),
    )


@dp.message(Command("stop"))
async def cmd_stop(message: Message) -> None:
    chat_id = message.chat.id
    if get_session(chat_id) is None:
        await message.answer("Немає активного квізу.")
        return
    remove_session(chat_id)
    await message.answer("Квіз зупинено. /quiz — почати новий.")


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привіт! Я HyperIT Quiz Bot.\n\n"
        "/quiz — почати демо-квіз\n"
        "/stop — зупинити квіз"
    )


@dp.callback_query(F.data.startswith("ans:"))
async def on_answer(callback: CallbackQuery) -> None:
    _, raw_chat, raw_idx = callback.data.split(":")
    chat_id = int(raw_chat)
    chosen = int(raw_idx)

    session = get_session(chat_id)
    if session is None or session.state != SessionState.QUESTION:
        await callback.answer("Квіз вже завершено.")
        return

    user_id = callback.from_user.id
    q = session.current_question()
    already_answered = user_id in session.answers.get(user_id, {}) or (
        session.current_index in session.answers.get(user_id, {})
    )

    session.answer(user_id=user_id, chosen_index=chosen)
    await callback.answer(
        "✅ Правильно!" if chosen == q.correct_index else "❌ Не вірно"
    )

    if already_answered:
        return

    # Show explanation only to the answering user (private message hint)
    is_correct = chosen == q.correct_index
    mark = "✅" if is_correct else "❌"
    expl = f"{mark} {LETTERS[chosen]}. {q.options[chosen]}\n\n💡 {q.explanation}"
    await callback.message.answer(expl)

    # Advance to next question (teacher/group flow: auto-advance)
    session.next_question()

    if session.state == SessionState.FINISHED:
        board = session.leaderboard()
        lines = [f"🏆 Результати:"]
        for rank, (uid, score) in enumerate(board, 1):
            lines.append(f"{rank}. user_{uid} — {score}/{len(session.questions)}")
        remove_session(chat_id)
        await callback.message.answer("\n".join(lines))
        await callback.message.answer("/quiz — зіграти ще раз")
    else:
        q = session.current_question()
        idx = session.current_index
        await callback.message.answer(
            _format_question(idx, len(session.questions), q.text, q.options),
            reply_markup=_question_keyboard(chat_id, len(q.options)),
        )
