import os
import shutil
import asyncio
import urllib.parse
from database.models import User
from core.progress import ProgressUpdater

async def push_to_github(user_id: int, user: User, file_paths: list, updater: ProgressUpdater):
    updater.action_text = "🚀 Uploading to GitHub"
    updater.update_sync(10, "Connecting...", "Wait")

    repo = user.github_repo
    token = user.github_token

    auth_url = f"https://oauth2:{token}@github.com/{repo}.git"
    repo_dir = f"tmp_downloads/repo_{user_id}"


    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)


    updater.update_sync(30, "Cloning...", "Wait")
    clone_cmd = f"git clone --depth 1 {auth_url} {repo_dir}"
    proc = await asyncio.create_subprocess_shell(clone_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.wait()

    if proc.returncode != 0:
        raise Exception("Failed to clone repository. Please check if your Token and Repo name are correct.")


    updater.update_sync(60, "Copying...", "Wait")
    dl_dir = os.path.join(repo_dir, "dl")
    os.makedirs(dl_dir, exist_ok=True)

    uploaded_filenames =[]
    for fp in file_paths:
        shutil.copy(fp, dl_dir)
        uploaded_filenames.append(os.path.basename(fp))


    updater.update_sync(80, "Pushing...", "Wait")
    commands =[
        f"cd {repo_dir}",
        "git config user.name 'RGit uploader'",
        "git config user.email 'bot@rgit.local'",
        "git add dl/",
        "git commit -m '✨ Uploaded via RGit uploader [skip ci]'",
        "git push origin HEAD"
    ]

    push_cmd = " && ".join(commands)
    proc = await asyncio.create_subprocess_shell(push_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.wait()

    if proc.returncode != 0:
        raise Exception("Git push failed. Please ensure your PAT has 'Contents: Write' permissions.")


    shutil.rmtree(repo_dir, ignore_errors=True)


    links =[]
    for fname in uploaded_filenames:
        encoded_name = urllib.parse.quote(fname)
        raw_url = f"https://github.com/{repo}/raw/HEAD/dl/{encoded_name}"
        links.append(f"📥 **[{fname}]({raw_url})**")

    return links