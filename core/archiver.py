import os
import asyncio
import re
import glob

def sanitize_filename(name):
    return re.sub(r'[^\w\.\-\s]', '_', name)

async def process_archive(file_path: str, comp_mode: str, password: str, updater):
    updater.action_text = "📦 Processing File"
    file_path = os.path.abspath(file_path)
    dir_name = os.path.dirname(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    raw_base = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1].lower()
    new_base = sanitize_filename(raw_base)


    if comp_mode == "raw" and file_size_mb <= 90:
        final_path = os.path.join(dir_name, f"{new_base}{ext}")
        if file_path != final_path:
            os.rename(file_path, final_path)
        return [final_path]

    zip_path = os.path.join(dir_name, f"{new_base}.zip")
    has_password = password and password != "None"


    cmd = ["7z", "a", "-tzip"]

    if has_password:
        cmd.extend([f"-p{password}", "-mx=9"])
    elif comp_mode == "raw":

        cmd.append("-mx=0")
    else:

        cmd.append("-mx=9")


    if file_size_mb > 90:
        cmd.append("-v90m")
        updater.action_text = "✂️ Zipping & Splitting (7z)"
    else:
        updater.action_text = "📦 Zipping File"

    cmd.extend([zip_path, file_path])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise Exception(f"Archiving failed!\n{stderr.decode('utf-8', 'ignore')}")


    if os.path.exists(file_path):
        os.remove(file_path)


    if file_size_mb > 90:
        parts = sorted(glob.glob(os.path.join(dir_name, f"{new_base}.zip.*")))
        if not parts:
            raise Exception("Archiving failed: output parts not found.")
        return parts
    else:
        if not os.path.exists(zip_path):
            raise Exception("Archiving failed: output zip not found.")
        return [zip_path]