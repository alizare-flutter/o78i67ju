import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.commands import router as commands_router
from handlers.messages import router as messages_router
from handlers.callbacks import router as callbacks_router
import os
import time

# ⚙️ Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(commands_router)
dp.include_router(messages_router)
dp.include_router(callbacks_router)

TMP_DIR = "/root/sandbox-main/tmp_downloads/"
CLEANUP_INTERVAL = 3600

async def cleanup_old_files():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        now = time.time()
        cleaned = 0
        try:
            for entry in os.scandir(TMP_DIR):
                if now - entry.stat().st_mtime > CLEANUP_INTERVAL:
                    if entry.is_dir(follow_symlinks=False):
                        import shutil
                        shutil.rmtree(entry.path, ignore_errors=True)
                    else:
                        os.remove(entry.path)
                    cleaned += 1
                    logger.info(f"🗑️ Deleted: {entry.path}")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

        logger.info(f"✅ Cleanup done. {cleaned} item(s) removed.")

async def main():
    print("🚀 RGit Uploader Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(cleanup_old_files())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot stopped.")