import os
import yt_dlp
import asyncio
from core.progress import ProgressUpdater
def yt_dlp_download_sync(url: str, quality: str, updater: ProgressUpdater, tmp_dir: str):
    format_map = {
        "best": "bestvideo+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "audio": "bestaudio/best"
    }
    ydl_format = format_map.get(quality, "best")
    def my_hook(d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
                speed_str = d.get('_speed_str', 'N/A').replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()
                eta_str = d.get('_eta_str', 'N/A').replace('\x1b[0;33m', '').replace('\x1b[0m', '').strip()
                percent = float(percent_str.replace('%', ''))
                updater.update_sync(percent, speed_str, eta_str)
            except Exception:
                pass
    ydl_opts = {
        'format': ydl_format,
        'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4' if quality != "audio" else None,
        'postprocessors':[{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if quality == "audio" else [],
        'progress_hooks': [my_hook],
        'quiet': True,
        'nocheckcertificate': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if quality == "audio":
            filename = filename.rsplit('.', 1)[0] + '.mp3'
        return filename
async def download_media(url: str, quality: str, updater: ProgressUpdater):
    tmp_dir = "tmp_downloads"
    os.makedirs(tmp_dir, exist_ok=True)
    loop = asyncio.get_running_loop()
    downloaded_file = await loop.run_in_executor(
        None, yt_dlp_download_sync, url, quality, updater, tmp_dir
    )
    return downloaded_file