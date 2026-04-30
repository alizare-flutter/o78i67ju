from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from database.crud import create_or_update_user, get_user


router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    create_or_update_user(message.from_user.id)

    welcome_text = (
        "👋 **Welcome to RGit uploader!**\n\n"
        "I'm here to bypass restrictions and upload files directly to your GitHub repository.\n\n"
        "⚙️ **Setup Instructions:**\n"
        "1️⃣ `/set_token <YOUR_GITHUB_PAT>` - Set your Personal Access Token.\n"
        "2️⃣ `/set_repo <username/repo>` - Set your target repository.\n\n"
        "💡 *Once configured, just send me any direct link or supported media URL to start!*"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("set_token"))
async def set_token(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ **Usage:** `/set_token <YOUR_GITHUB_PAT>`\n*Example:* `/set_token ghp_123456789...`", parse_mode="Markdown")
        return

    token = args[1].strip()
    create_or_update_user(message.from_user.id, github_token=token)
    await message.answer("✅ **GitHub Token saved successfully!**", parse_mode="Markdown")

@router.message(Command("set_repo"))
async def set_repo(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ **Usage:** `/set_repo <username/repo>`\n*Example:* `/set_repo myuser/sandbox`", parse_mode="Markdown")
        return

    repo = args[1].strip()
    create_or_update_user(message.from_user.id, github_repo=repo)
    await message.answer(f"✅ **Target repository set to:** `{repo}`", parse_mode="Markdown")

@router.message(Command("status"))
async def cmd_status(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("⚠️ You are not registered yet. Please send /start first.")
        return

    token_status = "✅ `Set` (Hidden for security)" if user.github_token else "❌ `Not set`"
    repo_status = f"✅ `{user.github_repo}`" if user.github_repo else "❌ `Not set`"

    text = (
        "📊 **Your Current Status:**\n\n"
        f"🔑 **Token:** {token_status}\n"
        f"📁 **Repository:** {repo_status}\n\n"
        "*(Both must be set before sending links!)*"
    )
    await message.answer(text, parse_mode="Markdown")