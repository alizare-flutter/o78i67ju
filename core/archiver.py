import os
import asyncio
from core.progress import ProgressUpdater

async def process_archive(file_path: str, comp_mode: str, password: str, updater: ProgressUpdater):
    updater.action_text = "📦 Archiving File"
    updater.update_sync(10, "N/A", "N/A")

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    base_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)


    if comp_mode == "raw" and file_size_mb <= 95:
        return [file_path]

    updater.update_sync(50, "Processing...", "Wait")


    zip_name = f"{base_name}.zip"
    zip_path = os.path.join(dir_name, zip_name)


    cmd =["7z", "a", "-tzip", "-v95m", "-mx=9"]

    if password and password != "None":
        cmd.append(f"-p{password}")

    cmd.extend([zip_path, file_path])


    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.wait()


    generated_files =[]
    for f in os.listdir(dir_name):
        if f.startswith(zip_name):
            generated_files.append(os.path.join(dir_name, f))


    if len(generated_files) > 0 and os.path.exists(file_path):
        os.remove(file_path)

    return sorted(generated_files)