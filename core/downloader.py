import os
import asyncio
import subprocess
import re
from core.progress import ProgressUpdater
async def download_direct(url: str, updater: ProgressUpdater):
    tmp_dir = "tmp_downloads"
    os.makedirs(tmp_dir, exist_ok=True)
    cmd =[
        "aria2c",
        "--split=4",
        "--max-connection-per-server=4",
        "--summary-interval=3",
        "--dir", tmp_dir,
        url
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    filename = None
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line_str = line.decode('utf-8').strip()
        if "Saving to" in line_str:
            filename = line_str.split("Saving to ")[1].strip("'")
        progress_match = re.search(r'\((\d+)%\).*DL:([^\s]+).*ETA:([^\s\]]+)', line_str)
        if progress_match:
            percent = float(progress_match.group(1))
            speed = progress_match.group(2)
            eta = progress_match.group(3)
            updater.update_sync(percent, speed, eta)
    await process.wait()
    if filename and os.path.exists(filename):
        return filename
    else:
        files = os.listdir(tmp_dir)
        if files:
            files_paths =[os.path.join(tmp_dir, f) for f in files]
            return max(files_paths, key=os.path.getmtime)
        return None