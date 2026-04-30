import re
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.crud import get_user

router = Router()

@router.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_url(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if not user or not user.github_token or not user.github_repo:
        await message.answer(
            "⚠️ **Setup Incomplete:**\n"
            "Please set your GitHub Token and Repository first using `/set_token` and `/set_repo`.",
            parse_mode="Markdown"
        )
        return

    url = message.text.strip()

    await state.update_data(target_url=url)


    media_domains =["youtube.com", "youtu.be", "twitch.tv", "reddit.com", "vimeo.com", "soundcloud.com"]
    is_media = any(domain in url for domain in media_domains)

    if is_media:

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Best Quality", callback_data="qual_best")],[InlineKeyboardButton(text="📺 720p (MP4)", callback_data="qual_720p"),
             InlineKeyboardButton(text="📱 480p (MP4)", callback_data="qual_480p")],[InlineKeyboardButton(text="🎵 Audio Only (MP3)", callback_data="qual_audio")]
        ])
        await message.answer("🎬 **Media link detected!**\nPlease select the desired quality:", reply_markup=keyboard, parse_mode="Markdown")
    else:
        await state.update_data(quality="default")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📄 Raw (No Zip)", callback_data="comp_raw")],[InlineKeyboardButton(text="📦 Zip (Max Compression)", callback_data="comp_zip")],[InlineKeyboardButton(text="🔐 Zip with Password", callback_data="comp_pass")]
        ])
        await message.answer("🔗 **Direct link detected!**\nHow should I process and upload this file?", reply_markup=keyboard, parse_mode="Markdown")