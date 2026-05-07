import os
import asyncio
import html
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.crud import get_user
from core.ytdlp_engine import download_media
from core.downloader import download_direct
from core.bunkr_engine import is_bunkr_url, download_bunkr
from core.progress import ProgressUpdater
from core.archiver import process_archive
from github_integration.git_manager import push_to_github
from config import YOUTUBE_COOKIES
router = Router()
task_store = {}
class DownloadWorkflow(StatesGroup):
    waiting_for_password = State()
@router.callback_query(F.data.startswith("qual_"))
async def process_quality(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    quality = parts[1]
    task_id = parts[2] if len(parts) > 2 else ""
    if task_id not in task_store:
        await callback.answer("⚠️ Session expired! Please send the link again.", show_alert=True)
        return
    task_store[task_id]["quality"] = quality
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📄 Raw (No Zip)", callback_data=f"comp_raw_{task_id}")],[InlineKeyboardButton(text="📦 Zip (Max Compression)", callback_data=f"comp_zip_{task_id}")],[InlineKeyboardButton(text="🔐 Zip with Password", callback_data=f"comp_pass_{task_id}")]
    ])
    await callback.message.edit_text("⚙️ **Quality selected!**\nHow should I process this?", reply_markup=keyboard, parse_mode="Markdown")
@router.callback_query(F.data.startswith("comp_"))
async def process_compression(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    comp_type = parts[1]
    task_id = parts[2] if len(parts) > 2 else ""
    if task_id not in task_store:
        await callback.answer("⚠️ Session expired! Please send the link again.", show_alert=True)
        return
    if comp_type == "pass":
        await callback.message.edit_text("🔐 **Send password for the Zip file:**", parse_mode="Markdown")
        await state.set_state(DownloadWorkflow.waiting_for_password)
        await state.update_data(task_id=task_id)
        return
    task_store[task_id]["compression"] = comp_type
    status_msg = await callback.message.edit_text("⏳ **Initializing...**", parse_mode="Markdown")
    asyncio.create_task(prepare_download_task(status_msg, task_id, callback.message.chat.id))
@router.message(DownloadWorkflow.waiting_for_password)
async def handle_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    task_id = data.get("task_id")
    await state.clear()
    if not task_id or task_id not in task_store:
        await message.answer("❌ Session expired or invalid.")
        return
    task_store[task_id]["compression"] = "zip_pass"
    task_store[task_id]["zip_password"] = password
    status_msg = await message.answer("⏳ **Initializing...**", parse_mode="Markdown")
    asyncio.create_task(prepare_download_task(status_msg, task_id, message.chat.id))
async def prepare_download_task(status_msg: Message, task_id: str, chat_id: int):
    data = task_store.pop(task_id, {})
    urls = data.get("urls") or [data.get("target_url")]
    quality = data.get("quality")
    comp_mode = data.get("compression")
    password = data.get("zip_password", "None")
    user = get_user(chat_id)
    updater = ProgressUpdater(
        status_msg,
        action_text="Processing"
    )
    success_links = []
    failed_links = []
    media_domains = [
        "youtube.com",
        "youtu.be",
        "twitch.tv",
        "reddit.com",
        "vimeo.com",
        "soundcloud.com"
    ]
    total = len(urls)
    for index, url in enumerate(urls, start=1):
        is_local = data.get("is_local_file", False)
        downloaded_file = None
        final_files = []
        try:
            await status_msg.edit_text(
                f"🔄 Processing [{index}/{total}]\n\n`{url[:70]}`",
                parse_mode="Markdown"
            )
            updater.action_text = f"[{index}/{total}] Downloading"
            if is_local:

                downloaded_file = url

            elif is_bunkr_url(url):
                downloaded_file = await download_bunkr(
                    url,
                    updater
                )
            elif any(domain in url for domain in media_domains):
                downloaded_file = await download_media(
                    url,
                    quality,
                    updater,
                    YOUTUBE_COOKIES
                )
            else:
                downloaded_file = await download_direct(
                    url,
                    updater
                )
            if not downloaded_file or not os.path.exists(downloaded_file):
                raise Exception("File not downloaded.")
            final_files = await process_archive(
                downloaded_file,
                comp_mode,
                password,
                updater
            )
            raw_links = await push_to_github(
                chat_id,
                user,
                final_files,
                updater
            )
            success_links.extend(raw_links)
        except Exception as e:
            failed_links.append(
                f"❌ {url}\n{str(e)}"
            )
        finally:
            try:
                if downloaded_file and os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
            except:
                pass
            for f in final_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
    result_text = "✅ <b>Batch Completed!</b>\n\n"
    if success_links:
        result_text += (
            f"📥 <b>Success:</b> {len(success_links)}\n\n"
        )
        result_text += "\n\n".join(
            success_links[:15]
        )
    if failed_links:
        result_text += (
            f"\n\n❌ <b>Failed:</b> {len(failed_links)}\n"
        )
        short_errors = failed_links[:5]
        result_text += "\n\n".join(
            f"<code>{html.escape(err[:300])}</code>"
            for err in short_errors
        )
    await status_msg.edit_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )