import os
import asyncio
import aiohttp
import base64
import urllib.parse
import html
from datetime import datetime, timedelta
from database.models import User
from core.progress import ProgressUpdater

git_locks = {}

async def push_to_github(user_id: int, user: User, file_paths: list, updater: ProgressUpdater):
    repo = user.github_repo
    token = user.github_token

    if not repo or not token:
        raise Exception("GitHub Repo or Token is not configured.")

    if user_id not in git_locks:
        git_locks[user_id] = asyncio.Lock()

    updater.action_text = "Waiting in Queue"
    updater.update_sync(5, "-", "-")

    async with git_locks[user_id]:
        updater.action_text = "Connecting to GitHub API"
        updater.update_sync(10, "-", "-")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RGit-Bot"
        }
        api_base = f"https://api.github.com/repos/{repo}"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{api_base}/git/refs/heads/main") as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise Exception(f"Failed to fetch repo refs. Check Token/Repo name.\n{err}")
                ref_data = await resp.json()
                commit_sha = ref_data['object']['sha']

            async with session.get(f"{api_base}/git/commits/{commit_sha}") as resp:
                commit_data = await resp.json()
                base_tree_sha = commit_data['tree']['sha']

            tree_items = []
            links = []
            uploaded_filenames =[]
            total_files = len(file_paths)
            tehran_time = (datetime.utcnow() + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M")
            new_links_content = f"### 📅 {tehran_time} (IR Time)\n"

            for i, fp in enumerate(file_paths):
                fname = os.path.basename(fp)
                updater.action_text = f"Uploading ({i+1}/{total_files})"
                updater.update_sync(20 + (50 * i / total_files), fname[:10], "-")

                with open(fp, "rb") as f:
                    file_data = f.read()

                b64_content = base64.b64encode(file_data).decode('utf-8')

                async with session.post(f"{api_base}/git/blobs", json={
                    "content": b64_content,
                    "encoding": "base64"
                }) as resp:
                    if resp.status != 201:
                        err = await resp.text()
                        raise Exception(f"Failed to upload Blob for {fname}\n{err}")
                    blob_data = await resp.json()
                    blob_sha = blob_data['sha']

                tree_items.append({
                    "path": f"dl/{fname}",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
                uploaded_filenames.append(fname)

                size_mb = len(file_data) / (1024 * 1024)
                size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.2f} MB"
                encoded_name = urllib.parse.quote(fname)
                raw_url = f"https://github.com/{repo}/raw/main/dl/{encoded_name}"

                display_text = f"{fname} `{size_str}`"
                safe_display = html.escape(display_text)
                links.append(f"📥 <b><a href='{raw_url}'>{safe_display}</a></b>")
                new_links_content += f"- 📥 [{fname}]({raw_url}) `{size_str}`\n"

            updater.action_text = "Updating Links.md"
            updater.update_sync(80, "-", "-")

            links_md_path = "Links.md"
            links_md_content = ""

            async with session.get(f"{api_base}/contents/{links_md_path}") as resp:
                if resp.status == 200:
                    file_info = await resp.json()
                    links_md_content = base64.b64decode(file_info['content']).decode('utf-8')

            default_header = "## 🔗 Direct Download Links\n\n"
            if links_md_content:
                split_marker = "### 📅"
                if split_marker in links_md_content:
                    parts = links_md_content.split(split_marker, 1)
                    preserved_header = parts[0]
                    old_links = split_marker + parts[1]
                else:
                    preserved_header = links_md_content if links_md_content.strip() else default_header
                    old_links = ""
            else:
                preserved_header = default_header
                old_links = ""

            if not preserved_header.endswith("\n\n"):
                preserved_header = preserved_header.rstrip() + "\n\n"

            final_links_md = preserved_header + new_links_content + "\n" + old_links

            async with session.post(f"{api_base}/git/blobs", json={
                "content": base64.b64encode(final_links_md.encode('utf-8')).decode('utf-8'),
                "encoding": "base64"
            }) as resp:
                if resp.status == 201:
                    blob_data = await resp.json()
                    tree_items.append({
                        "path": links_md_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_data['sha']
                    })

            updater.action_text = "Committing to GitHub"
            updater.update_sync(90, "-", "-")

            async with session.post(f"{api_base}/git/trees", json={
                "base_tree": base_tree_sha,
                "tree": tree_items
            }) as resp:
                if resp.status != 201:
                    err = await resp.text()
                    raise Exception(f"Failed to create tree.\n{err}")
                tree_data = await resp.json()
                new_tree_sha = tree_data['sha']

            async with session.post(f"{api_base}/git/commits", json={
                "message": "✨ Add new files via API [skip ci]",
                "tree": new_tree_sha,
                "parents": [commit_sha]
            }) as resp:
                if resp.status != 201:
                    err = await resp.text()
                    raise Exception(f"Failed to create commit.\n{err}")
                new_commit_data = await resp.json()
                new_commit_sha = new_commit_data['sha']

            async with session.patch(f"{api_base}/git/refs/heads/main", json={
                "sha": new_commit_sha,
                "force": True
            }) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise Exception(f"Failed to update branch ref.\n{err}")

            updater.action_text = "Upload Complete"
            updater.update_sync(100, "-", "-")
            return links
async def _update_repo_tree(user: User, tree_items: list, commit_message: str):
    repo = user.github_repo
    token = user.github_token
    api_base = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{api_base}/git/refs/heads/main") as resp:
            ref_data = await resp.json()
            commit_sha = ref_data['object']['sha']

        async with session.get(f"{api_base}/git/commits/{commit_sha}") as resp:
            commit_data = await resp.json()
            base_tree_sha = commit_data['tree']['sha']

        async with session.post(f"{api_base}/git/trees", json={
            "base_tree": base_tree_sha,
            "tree": tree_items
        }) as resp:
            tree_data = await resp.json()
            new_tree_sha = tree_data['sha']

        async with session.post(f"{api_base}/git/commits", json={
            "message": commit_message,
            "tree": new_tree_sha,
            "parents":[commit_sha]
        }) as resp:
            new_commit_data = await resp.json()
            new_commit_sha = new_commit_data['sha']

        await session.patch(f"{api_base}/git/refs/heads/main", json={"sha": new_commit_sha, "force": True})

async def delete_file_from_github(user: User, filename: str):
    repo = user.github_repo
    token = user.github_token
    api_base = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}

    async with aiohttp.ClientSession(headers=headers) as session:
        links_md_path = "Links.md"
        async with session.get(f"{api_base}/contents/{links_md_path}") as resp:
            if resp.status != 200:
                raise Exception("Links.md not found.")
            file_info = await resp.json()
            links_md_content = base64.b64decode(file_info['content']).decode('utf-8')

        new_lines =[]
        for line in links_md_content.split('\n'):
            if f"[{filename}]" not in line and f"{filename} `" not in line:
                new_lines.append(line)
        new_links_md = '\n'.join(new_lines)

        tree_items =[
            {"path": f"dl/{filename}", "mode": "100644", "type": "blob", "sha": None}
        ]

        async with session.post(f"{api_base}/git/blobs", json={
            "content": base64.b64encode(new_links_md.encode('utf-8')).decode('utf-8'),
            "encoding": "base64"
        }) as resp:
            blob_data = await resp.json()
            tree_items.append({"path": links_md_path, "mode": "100644", "type": "blob", "sha": blob_data['sha']})

    await _update_repo_tree(user, tree_items, f"🗑️ Delete {filename} [skip ci]")

async def clear_github_repo(user: User):
    repo = user.github_repo
    token = user.github_token
    api_base = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{api_base}/contents/dl") as resp:
            if resp.status != 200:
                raise Exception("Directory `dl/` is already empty or unreachable.")
            files = await resp.json()

        if not isinstance(files, list):
            files = [files]

        tree_items =[]
        for f in files:
            tree_items.append({"path": f"dl/{f['name']}", "mode": "100644", "type": "blob", "sha": None})

        default_header = "## 🔗 Direct Download Links\n\n"
        async with session.post(f"{api_base}/git/blobs", json={
            "content": base64.b64encode(default_header.encode('utf-8')).decode('utf-8'),
            "encoding": "base64"
        }) as resp:
            blob_data = await resp.json()
            tree_items.append({"path": "Links.md", "mode": "100644", "type": "blob", "sha": blob_data['sha']})

    await _update_repo_tree(user, tree_items, "🧹 Clear all files [skip ci]")