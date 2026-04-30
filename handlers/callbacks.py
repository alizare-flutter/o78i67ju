
import os
from database.crud import get_user
from core.ytdlp_engine import download_media
from core.downloader import download_direct
from core.progress import ProgressUpdater
from core.archiver import process_archive
from github_integration.git_manager import push_to_github


async def prepare_download_task(message: Message, state: FSMContext):
    data = await state.get_data()

    url = data.get("target_url")
    quality = data.get("quality")
    comp_mode = data.get("compression")
    password = data.get("zip_password", "None")
    await state.clear()

    user = get_user(message.chat.id)

    status_msg = await message.answer("🔄 **Starting RGit Engine...**", parse_mode="Markdown")
    updater = ProgressUpdater(status_msg, action_text="Downloading File")

    try:

        media_domains =["youtube.com", "youtu.be", "twitch.tv", "reddit.com", "vimeo.com", "soundcloud.com"]
        if any(domain in url for domain in media_domains):
            downloaded_file = await download_media(url, quality, updater)
        else:
            downloaded_file = await download_direct(url, updater)

        if not downloaded_file or not os.path.exists(downloaded_file):
            await status_msg.edit_text("❌ **Download failed.** File could not be retrieved.")
            return


        final_files = await process_archive(downloaded_file, comp_mode, password, updater)


        raw_links = await push_to_github(message.chat.id, user, final_files, updater)


        for f in final_files:
            if os.path.exists(f):
                os.remove(f)


        links_text = "\n\n".join(raw_links)
        success_text = (
            "✅ **Upload Completed Successfully!**\n\n"
            f"🔗 **Your Direct Links:**\n{links_text}\n\n"
            "*(Links bypass network restrictions)*"
        )

        await status_msg.edit_text(success_text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await status_msg.edit_text(f"❌ **Process Failed:**\n`{str(e)}`", parse_mode="Markdown")