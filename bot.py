#python bot.py
import asyncio
import os
from dotenv import load_dotenv
import aiosqlite
from aiogram import Bot, Dispatcher
from tg_bot_folder.handlers import router

load_dotenv()

TOKEN = os.getenv('TOKEN')
from tg_bot_folder.handlers import DB_NAME

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS users ('
                         'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                         'user_id INTEGER,'
                         'cities_db TEXT,'
                         'latitude_db TEXT,'
                         'longitude_db TEXT,'
                         'time_db TEXT'
                         ')')
        await db.commit()



async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
