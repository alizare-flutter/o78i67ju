import time
import asyncio
from aiogram.types import Message
class ProgressUpdater:
    def __init__(self, message: Message, action_text="Downloading"):
        self.message = message
        self.action_text = action_text
        self.last_update_time = 0
        self.update_interval = 3.0
        self.loop = asyncio.get_running_loop()
    async def _edit_message(self, text):
        try:
            await self.message.edit_text(text, parse_mode="Markdown")
        except Exception:
            pass
    def update_sync(self, percentage: float, speed: str, eta: str):
        """Called by synchronous libraries like yt-dlp"""
        now = time.time()
        if now - self.last_update_time < self.update_interval or percentage == 100:
            self.last_update_time = now
            filled = int(percentage / 10)
            bar = '█' * filled + '░' * (10 - filled)
            text = (
                f"⏳ **{self.action_text}... {percentage:.1f}%**\n"
                f"`[{bar}]`\n"
                f"🚀 **Speed:** {speed} | ⏱ **ETA:** {eta}"
            )
            asyncio.run_coroutine_threadsafe(self._edit_message(text), self.loop)