import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import admin, review, start, tokens, top
from bot.handlers.start import fallback_router
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все хэндлеры
    dp.include_router(start.router)
    dp.include_router(review.router)
    dp.include_router(top.router)
    dp.include_router(tokens.router)
    dp.include_router(admin.router)
    dp.include_router(fallback_router)  # must be last

    logger.info("Bot started")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
