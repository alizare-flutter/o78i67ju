import os
import asyncio
import uuid
import re
import glob
import shlex
from core.progress import ProgressUpdater

async def download_media(url: str, quality: str, updater: ProgressUpdater, user_cookies: str = None):
    tmp_dir = "tmp_downloads"
    os.makedirs(tmp_dir, exist_ok=True)


    if quality == "720p":
        ytdlp_args = ["-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best", "--merge-output-format", "mp4"]
    elif quality == "480p":
        ytdlp_args =["-f", "bestvideo[height<=480]+bestaudio/best[height<=480]/best", "--merge-output-format", "mp4"]
    elif quality == "360p":
        ytdlp_args =["-f", "bestvideo[height<=360]+bestaudio/best[height<=360]/best", "--merge-output-format", "mp4"]
    elif quality == "audio":
        ytdlp_args = ["-x", "--audio-format", "mp3"]
    else:
        ytdlp_args =["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    file_id = uuid.uuid4().hex[:8]
    dl_dir = os.path.join(tmp_dir, file_id)
    os.makedirs(dl_dir, exist_ok=True)
    outtmpl = os.path.join(dl_dir, "%(title)s.%(ext)s")


    cookie_path = None
    if user_cookies and os.path.exists(user_cookies):
        cookie_path = user_cookies
    elif user_cookies and len(user_cookies.strip()) > 20:
        cookie_path = os.path.join(tmp_dir, f"cookies_{uuid.uuid4().hex[:6]}.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(user_cookies.strip())

    async def run_ytdlp(use_cookies: bool) -> tuple[int, list[str]]:

        cmd_parts = [
            "yt-dlp", "--no-warnings", "--no-playlist",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "--extractor-args", "youtube:player_client=web"
        ]

        if use_cookies and cookie_path:
            cmd_parts.extend(["--cookies", cookie_path])

        cmd_parts.extend(ytdlp_args)
        cmd_parts.extend(["-o", outtmpl, url])


        cmd_string = " ".join([shlex.quote(c) for c in cmd_parts])

        process = await asyncio.create_subprocess_shell(
            cmd_string,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ
        )

        all_output = []
        while True:
            line = await process.stdout.readline()
            if not line: break
            text = line.decode('utf-8', errors='ignore').strip()
            all_output.append(text)


            if "[download]" in text and "%" in text:
                try:
                    parts = text.split()
                    percent = float(parts[1].replace('%', ''))
                    speed = parts[3] if len(parts) > 3 else "N/A"
                    updater.update_sync(percent, speed, "...")
                except: pass

        await process.wait()
        return process.returncode, all_output

    updater.action_text = "Downloading"


    returncode, all_output = await run_ytdlp(use_cookies=(cookie_path is not None))


    if returncode != 0 and cookie_path:
        updater.action_text = "Retrying (No Cookies)..."
        returncode, all_output = await run_ytdlp(use_cookies=False)

    downloaded_files = glob.glob(os.path.join(dl_dir, "*"))


    if cookie_path and cookie_path.startswith(tmp_dir) and os.path.exists(cookie_path):
        os.remove(cookie_path)

    if downloaded_files and returncode == 0:
        return downloaded_files[0]
    else:

        raise Exception(f"yt-dlp failed:\n" + "\n".join(all_output))