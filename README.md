# Look-Busy Agent

[GitHub Repository](https://github.com/MartinMa2026/LookBusyAgent)

## 中文

假装很忙 Agent。它会接管你的鼠标、键盘和前台窗口，模拟一些看起来像真人办公的操作节奏，比如浏览网页、切换窗口、输入再删除、停顿、滚动和搜索。

### 功能

- 真人感操作节奏：鼠标移动、停顿、滚动、输入和删除都带随机性。
- 多应用切换：浏览器、办公软件、编辑器等适配器可按权重轮换。
- LLM 可选：你可以填写自己的 API Key，让内容更贴近你的岗位和任务。
- 无 Key 也可运行：不填 Key 时会自动退回内建模板。
- 老板键：默认 `F12` 暂停/恢复。
- 多语言界面：支持中文、英文、日文。

### 直接使用

1. 前往 [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases) 下载 `LookBusyAgent-windows-x64.zip` 或 `LookBusyAgent.exe`
2. 解压后双击 `LookBusyAgent.exe`

说明：

- 当前项目按 Windows 桌面环境设计和验证。
- 不要在 WSL、Linux 或 macOS 里直接运行这个桌面包。
- 发布包里不再包含任何默认 API Key。

### 从源码运行

请在 Windows 原生 PowerShell 或 CMD 中执行：

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

如果你的机器没有 `py`，可以把命令中的 `py -3` 换成 `python`。

### LLM 配置

- `API Key`：填写你自己的 key
- `Base URL`：留空时默认使用 `https://api.openai.com`
- `Model`：默认是 `gpt-4o-mini`
- 不填写 `API Key` 时，程序会自动使用内建模板

### 安全说明

- 仓库默认配置不再内置任何 API Key。
- 旧版本如果已经在本地生成过配置文件，可能仍然保留旧值。
- 打包版第一次启动后，会在可执行文件同目录生成 `lookbusy_config.json`。
- 如果你之前用过带默认 key 的旧包，建议删除同目录下的 `lookbusy_config.json`，再重新启动。

### 打包 Release

请在 Windows 原生终端中执行，不要在 WSL 里运行：

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller
py -3 build.py
```

打包完成后产物位于：

- `dist/LookBusyAgent.exe`

如果你要上传 GitHub Release，建议同时生成 zip：

```powershell
Compress-Archive -Force -Path .\dist\LookBusyAgent.exe -DestinationPath .\dist\LookBusyAgent-windows-x64.zip
```

### 适配器扩展

你可以在 `adapters/` 目录里新增适配器脚本并继承 `BaseAdapter`。程序启动时会自动扫描并加载。

### 免责声明

本项目仅供学习、研究和娱乐，请在合法合规范围内使用。由使用本项目产生的后果需自行承担。

---

## English

Look-Busy Agent is a desktop automation toy that simulates “busy at work” behavior by controlling the mouse, keyboard, and foreground window. It can browse, type and delete text, scroll, pause, switch apps, and mimic light office activity patterns.

### Features

- Human-like interaction rhythm with randomized mouse movement, pauses, scrolling, typing, and deleting
- Multi-app rotation through adapters with configurable weights
- Optional LLM support using your own API key
- Built-in fallback templates when no API key is provided
- Panic hotkey: `F12` by default
- Multilingual UI: Chinese, English, and Japanese

### Download And Run

1. Go to [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases)
2. Download `LookBusyAgent-windows-x64.zip` or `LookBusyAgent.exe`
3. Extract it and double-click `LookBusyAgent.exe`

Notes:

- The project is currently designed and validated for Windows desktop usage.
- Do not try to run the packaged desktop app directly inside WSL, Linux, or macOS.
- The release package no longer ships with any default API key.

### Run From Source

Run these commands in native Windows PowerShell or CMD:

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

If your system does not have `py`, replace `py -3` with `python`.

### LLM Settings

- `API Key`: use your own key
- `Base URL`: leave empty to use `https://api.openai.com`
- `Model`: defaults to `gpt-4o-mini`
- If `API Key` is empty, the app falls back to built-in templates

### Security Notes

- The repository default config no longer contains any bundled API key.
- Older builds may already have written a local config file that still contains previous values.
- The packaged app creates `lookbusy_config.json` next to the executable on first launch.
- If you used an older package with a bundled key, delete `lookbusy_config.json` and start the app again.

### Build A Release

Run the following commands in a native Windows terminal, not inside WSL:

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller
py -3 build.py
```

The output file will be:

- `dist/LookBusyAgent.exe`

To prepare a GitHub Release zip:

```powershell
Compress-Archive -Force -Path .\dist\LookBusyAgent.exe -DestinationPath .\dist\LookBusyAgent-windows-x64.zip
```

### Extending Adapters

You can add new adapter scripts under `adapters/` by inheriting from `BaseAdapter`. The app scans and loads them automatically at startup.

### Disclaimer

This project is provided for learning, experimentation, and entertainment purposes only. Please use it responsibly and at your own risk.
