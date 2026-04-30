import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.commands import router as commands_router
from handlers.messages import router as messages_router
from handlers.callbacks import router as callbacks_router

#  ? Setup logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(commands_router)
dp.include_router(messages_router)
dp.include_router(callbacks_router)

async def main():
    print("🚀 RGit uploader Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot stopped.")