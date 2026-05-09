import time
import asyncio
from aiogram.types import Message

class ProgressUpdater:
    def __init__(self, message: Message, action_text="Downloading"):
        self.message = message
        self.action_text = action_text
        self.last_action_text = action_text
        self.last_update_time = 0
        self.update_interval = 3.0
        self.loop = asyncio.get_running_loop()

    async def _edit_message(self, text):
        try:
            await self.message.edit_text(text, parse_mode="HTML")
        except Exception:
            pass

    def update_sync(self, percentage: float, speed: str, eta: str):
        now = time.time()

        force_update = (percentage == 100) or (self.action_text != getattr(self, 'last_action_text', ''))

        if not force_update and (now - self.last_update_time < self.update_interval):
            return

        self.last_update_time = now
        self.last_action_text = self.action_text

        filled = int(percentage / 10)
        bar = '█' * filled + '░' * (10 - filled)
        text = (
            f"⏳ <b>{self.action_text}... {percentage:.1f}%</b>\n"
            f"<code>[{bar}]</code>\n"
            f"🚀 <b>Speed:</b> {speed} | ⏱ <b>ETA:</b> {eta}"
        )
        asyncio.run_coroutine_threadsafe(self._edit_message(text), self.loop)