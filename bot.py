import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import init_db
from handlers import client, common, driver


async def main():
    logging.basicConfig(level=logging.INFO)

    if not config.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylini yarating (.env.example'dan nusxa oling) "
            "va BotFather'dan olingan tokenni kiriting."
        )

    await init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(driver.router)
    dp.include_router(client.router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
