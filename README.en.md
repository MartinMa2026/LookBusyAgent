<div align="right">

**English** | [简体中文](./README.md)

</div>

# Look-Busy Agent 🎭
GitHub: [github.com/MartinMa2026/LookBusyAgent](https://github.com/MartinMa2026/LookBusyAgent)

Look-Busy Agent is exactly what the name suggests: an open-source, free, portable workflow toy that helps you look busy at work.

There is nothing mystical going on here. The app takes over your mouse, keyboard, and foreground windows, combines that with your role and your current task, and tries very hard to act like you are working while intentionally producing nothing meaningful.

---

## 🔥 Core Features
- **👀 Human-like activity simulation**: bezier-style mouse movement, random pauses, clicks, scrolling, and hesitation to make behavior feel more natural.
- **🤖 LLM-powered filler content**: once you provide your role and what you are “working on” today, it can generate office-style text for Word or code editors, then type and delete it like someone constantly revising.
- **💨 Portable and easy to run**: if you do not want to deal with Python, just download the `.exe` or zip package from [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases) and launch it directly.
- **🌍 Multilingual UI**: built-in Chinese / English / Japanese switching.
- **🚨 Boss key (F12)**: hit `F12` to instantly pause and take control back.
- **⏱️ Fishing timer**: tracks how much “life time” you have reclaimed.

## 🏄‍♂️ How To Start

### Step 1: Get Equipped
If you just want to use it, download `LookBusyAgent.exe` or `LookBusyAgent-windows-x64.zip` from [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases).

If you prefer running from source, use native **Windows PowerShell / CMD**:

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

If your system does not have `py`, replace `py -3` with `python`.

Please do not run the desktop app directly from WSL / Linux / macOS.

### Step 2: Start The Ritual
1. Tell the panel who you are and what you are doing.
2. Select the apps you want it to operate on.
3. Fill in your own LLM API Key if you want smarter filler content. If you leave it empty, the app falls back to built-in template text. The project no longer ships with any bundled default API key.
4. Click the flashing `START FISHING` button.
5. Done. Go get coffee.

---

## 🛡️ Disclaimer And Safety Notes

The core principle of this tool is simple: **it should not interfere with your real business files or code.**
- **No persistent edits**: after typing text into a field, it is designed to select-all and delete instead of saving anything.
- **No forced uploads**: there is no built-in backdoor, and it can still run in fallback mode without network access.
- **Just for fun**: all behavior only targets the current foreground window.

Please use it responsibly and at your own risk.

---

# 🛠️ Hacker Corner: Build Your Own Adapters

Look-Busy now uses a plug-and-play architecture. Browsers, code editors, and several office tools are already supported.

> 🤝 **Contributions welcome!**
> If you suffer from DingTalk, Feishu, WhatsApp, or some painful internal enterprise software, feel free to add an adapter and open a PR.

### 🔌 Add A New Adapter
You do **not** need to modify the control engine. The app auto-loads adapters by reflection. You only need two steps:

1. Create a new file under `adapters/`, for example `your_app_name.py`
2. Inherit from the base class and define the `META` card:

```python
from adapters.base_adapter import BaseAdapter

class WhatsAppAdapter(BaseAdapter):
    META = {
        "names": ["WhatsApp"],
        "processes": ["whatsapp.exe"],
        "icon": "💬",
        "priority": 1
    }
    
    def run_action(self):
        pass
```

### 📦 Build A Release
If you changed the code and want to package it for someone else, use the provided build flow instead of manually fighting PyInstaller flags:

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller
py -3 build.py
```

Run those commands in a **native Windows terminal**, not in WSL.

The generated executable will appear in `dist/LookBusyAgent.exe`.

If you want a zip for GitHub Releases:

```powershell
Compress-Archive -Force -Path .\dist\LookBusyAgent.exe -DestinationPath .\dist\LookBusyAgent-windows-x64.zip
```

Cheers to every worker who still loves life. 🍻
