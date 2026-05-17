"""Entry point."""
from __future__ import annotations

import asyncio
import logging

from src.bot import bot, dp

log = logging.getLogger(__name__)


async def main() -> None:
    log.info("Starting HyperIT Quiz Bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
