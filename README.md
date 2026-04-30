<div align="center">
  <h1>🚀 RGit Uploader Bot</h1>
  <p>A powerful Telegram bot that acts as an ultimate download and bypass tool. It downloads direct links, videos, and media, processes them, and pushes them directly to your GitHub repository to generate filter-free raw direct links.</p>
</div>

---

## ✨ Features
- ⚡ **Blazing Fast Downloads:** Uses `Aria2c` (up to 4 concurrent connections) for direct links.
- 🎬 **Media Extraction:** Integrated with `yt-dlp` to download videos from YouTube, Twitch, Bunkr, Vimeo, Reddit, and more.
- 🗜️ **Smart Archiving & Splitting:** Automatically uses `7-Zip` to compress files and splits them into 95MB parts to bypass GitHub's strict file size limit. Password protection is supported.
- 🔄 **GitHub Automation:** Pushes the downloaded files directly to a designated GitHub repository without storing them on your device permanently.
- 📊 **Live Progress Bar:** Clean and non-spammy progress updates inside Telegram.

## 🛠️ Prerequisites
Before running the bot, ensure you have Python 3.9+ and the required CLI tools installed on your Linux machine or server:

```bash
sudo apt-get update
sudo apt-get install -y aria2 ffmpeg p7zip-full git unzip
```

## ⚙️ Setup & Installation

You can download the bot using either **Git** or **Wget**.

### Option 1: Using Git (Recommended)
```bash
git clone https://github.com/YOUR_USERNAME/sandbox.git
cd sandbox
```

### Option 2: Using Wget
```bash
wget https://github.com/YOUR_USERNAME/sandbox/archive/refs/heads/main.zip -O sandbox.zip
unzip sandbox.zip
cd sandbox-main
```

---

**1. Create the Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Install Python Dependencies:**
```bash
pip install -r requirements.txt
```

**3. Environment Variables (.env):**
Create a `.env` file in the root directory and add your bot credentials:
```env
# Get this from @BotFather in Telegram
BOT_TOKEN=123456789:YOUR_BOT_TOKEN_HERE

# Database URI (SQLite is default)
DB_URL=sqlite:///database/bot.db
```

## 🚀 Running the Bot
Once everything is set up, run the bot using:
```bash
python bot.py
```

## 🤖 Usage (Telegram Commands)
Open your bot in Telegram and use the following commands to get started:
- `/start` - Initialize the bot.
- `/set_token <PAT>` - Securely link your GitHub Personal Access Token. *(Requires `Contents: Write` permission).*
- `/set_repo <username/repo>` - Set the target repository for uploading.
- `/status` - Check your configuration status.
- Just send any **URL** to the bot, choose your quality/compression settings via Inline Keyboards, and receive your direct raw links!