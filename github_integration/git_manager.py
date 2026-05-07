import os
import shutil
import asyncio
import urllib.parse
import uuid
from datetime import datetime, timedelta
from database.models import User
from core.progress import ProgressUpdater

git_locks = {}

async def push_to_github(user_id: int, user: User, file_paths: list, updater: ProgressUpdater):
    repo = user.github_repo

    if repo not in git_locks:
        git_locks[repo] = asyncio.Lock()

    updater.action_text = "⏳ Waiting in Queue"
    updater.update_sync(5, "Queue", "Wait")

    async with git_locks[repo]:
        updater.action_text = "🚀 Uploading to GitHub"
        updater.update_sync(10, "Connecting...", "Wait")

        token = user.github_token
        safe_token = urllib.parse.quote(token)
        auth_url = f"https://{safe_token}@github.com/{repo}.git"

        unique_id = uuid.uuid4().hex[:8]
        repo_dir = f"tmp_downloads/repo_{user_id}_{unique_id}"

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir, ignore_errors=True)


        try:
            updater.update_sync(30, "Cloning...", "Wait")

            clone_cmd = f"git clone --depth 1 {auth_url} {repo_dir}"
            proc = await asyncio.create_subprocess_shell(clone_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()


            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', 'ignore')
                raise Exception(f"Git clone failed! Check your Repo name or Token.\n{error_msg}")

            updater.update_sync(60, "Copying...", "Wait")
            dl_dir = os.path.join(repo_dir, "dl")
            os.makedirs(dl_dir, exist_ok=True)

            uploaded_filenames =[]
            for fp in file_paths:
                shutil.copy(fp, dl_dir)
                uploaded_filenames.append(os.path.basename(fp))

            links_md_path = os.path.join(repo_dir, "Links.md")
            tehran_time = (datetime.utcnow() + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M")

            new_links_content = f"### 📅 {tehran_time} (IR Time)\n"
            links =[]

            for fname in uploaded_filenames:
                file_path = os.path.join(dl_dir, fname)
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)

                if size_mb >= 1024:
                    size_str = f"{size_mb / 1024:.2f} GB"
                else:
                    size_str = f"{size_mb:.2f} MB"

                encoded_name = urllib.parse.quote(fname)
                raw_url = f"https://github.com/{repo}/raw/main/dl/{encoded_name}"
                display_text = f"{fname} [{size_str}]"

                links.append(f"📥 **[{display_text}]({raw_url})**")
                new_links_content += f"- 📥 **[{display_text}]({raw_url})**\n"

            default_header = "## 🔗 Direct Download Links\n\n"

            if os.path.exists(links_md_path):
                with open(links_md_path, "r", encoding="utf-8") as f:
                    full_content = f.read()

                split_marker = "### 📅"
                if split_marker in full_content:
                    parts = full_content.split(split_marker, 1)
                    preserved_header = parts[0]
                    old_links = split_marker + parts[1]
                else:
                    preserved_header = full_content if full_content.strip() else default_header
                    old_links = ""
            else:
                preserved_header = default_header
                old_links = ""

            if not preserved_header.endswith("\n\n"):
                preserved_header = preserved_header.rstrip() + "\n\n"

            with open(links_md_path, "w", encoding="utf-8") as f:
                f.write(preserved_header + new_links_content + "\n" + old_links)

            updater.update_sync(80, "Pushing to GitHub...", "Wait")

            commands =[
                f"cd {repo_dir}",
                "git config user.name 'RGit uploader'",
                "git config user.email 'bot@rgit.local'",
                "git checkout -B main",
                "git add -A",
                "git add -f dl/",
                "git commit -m '✨ Add new files [skip ci]'",
                "git push -u origin main --force"
            ]

            push_cmd = " && ".join(commands)
            proc = await asyncio.create_subprocess_shell(push_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', 'ignore')
                raise Exception(f"Git push failed! Token may lack 'Contents: Write' permission.\n{error_msg}")

            return links

        finally:
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir, ignore_errors=True)