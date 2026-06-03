#python bot.py
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from tg_bot_folder.handlers import router

load_dotenv()

TOKEN = os.getenv('TOKEN')


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
