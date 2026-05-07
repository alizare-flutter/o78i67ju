import os
import asyncio
import subprocess
import re
import uuid
from core.progress import ProgressUpdater

async def download_direct(url: str, updater: ProgressUpdater):
    unique_id = uuid.uuid4().hex[:8]
    tmp_dir = os.path.join("tmp_downloads", f"aria_{unique_id}")
    os.makedirs(tmp_dir, exist_ok=True)

    cmd =[
        "aria2c",
        "--split=4",
        "--max-connection-per-server=4",
        "--summary-interval=3",

        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--dir", tmp_dir,
        url
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    filename = None
    error_log =[]

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line_str = line.decode('utf-8', errors='ignore').strip()

        if line_str:
            error_log.append(line_str)

        if "Saving to" in line_str:
            parts = line_str.split("Saving to ")
            if len(parts) > 1:
                filename = parts[1].strip(" '")

        progress_match = re.search(r'\((\d+)%\).*DL:([^\s]+).*ETA:([^\s\]]+)', line_str)
        if progress_match:
            percent = float(progress_match.group(1))
            speed = progress_match.group(2)
            eta = progress_match.group(3)
            updater.update_sync(percent, speed, eta)

    await process.wait()


    if process.returncode != 0:
        log_text = "\n".join(error_log[-10:])
        raise Exception(f"Download Engine Failed! The site might be blocking the request.\nLogs:\n{log_text}")

    files = os.listdir(tmp_dir)

    files_paths =[
        os.path.join(tmp_dir, f) for f in files
        if os.path.isfile(os.path.join(tmp_dir, f)) and not f.endswith('.aria2')
    ]

    if files_paths:
        final_file = max(files_paths, key=os.path.getmtime)


        if os.path.getsize(final_file) == 0:
            os.remove(final_file)
            raise Exception("The downloaded file is 0 bytes (Empty). The server blocked the request (e.g., 403 Forbidden).")

        return final_file

    raise Exception("Download finished but no valid file was found.")