# Look-Busy Agent 🎭
Git地址：[github.com/MartinMa2026/LookBusyAgent](https://github.com/MartinMa2026/LookBusyAgent)

假装很忙Agent，体如其名，一个能让你安心摸鱼的工作流(开源、免费、绿色免安装)

这个Agent没有什么玄乎的东西，就是接管你的屏幕、鼠标和键盘，结合你的工作岗位、工作目标，努力地假装在工作，但什么都不产出。最近听说Meta会抓取员工的鼠标按键，炼化员工，训练AI。这就巧了，这个Agent竟然可以有效对抗炼化。

（上面是人写的）

下面的是AI写的，比我写的全面但AI味儿太重，我改了一些实在改不动了，大家脱敏看看吧⬇⬇⬇

---

## 🔥 核心功能
- **👀 瞒天过海的真人操作**：鼠标移动采用了讲究的贝塞尔曲线，还会随机发呆、点击、偶尔来回翻滚网页，完美还原人类“边思考边发呆”的边缘状态。
- **🤖 高端废话生成器**：只要你输入自己的岗位和今天要做什么，接上 AI 大脑后，它会在你的 Word 或代码编辑器里疯狂敲击出诸如“赋能、架构、闭环”的高深段落，然后边打边立刻删，主打一个“我很纠结、我在深度修改”。
- **💨 纯净无痛，随时待命**：如果你不懂 Python，直接去 [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases) 下载打包好的 `LookBusyAgent-windows-x64.zip` 或 `LookBusyAgent.exe`，双击就能跑，无任何流氓弹窗和多余残留。
- **🌍 打工人跨国共识**：自带 中/英/日 语言一键热切。摸鱼的需求是没有国界的！
- **🚨 救命老板键 (F12)**：遇到突发情况一键拍下 `F12`，屏幕立刻切回给你自己。
- **⏱️ 摸鱼计时器**：统计你偷偷赚回了多少青春，帮你记录“反吸血”收益。

## 🏄‍♂️ 怎么开启？

### 步骤 1：领装备
不想折腾环境的话，直接去 [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases) 下载 `LookBusyAgent-windows-x64.zip` 或 `LookBusyAgent.exe` 就行。

当然，喜欢看源码的大佬可以这样跑：

注意：下面命令请在 **Windows 原生 PowerShell / CMD** 中执行，不要在 WSL / Linux / macOS 里直接跑。

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

如果你的机器没有 `py` 命令，也可以把上面的 `py -3` 换成 `python`。

### 步骤 2：启动欺诈仪式
1. 告诉面板“你是谁 / 在做啥”（没想好的话不填也行）。
2. 在列表里勾选你平时常用的软件（网页、IDE、Word 都可以）。
3. 填入你自己的 LLM API Key（如果嫌麻烦不填，它也会用内置的弱智降级废话模板撑场面；现在项目默认**不再内置任何 API Key**）。
4. 点击右下角闪烁的「▶ START FISHING」。
5. **现在，你可以放开双手，安心去刷手机、喝咖啡了。**

如果你之前用过旧版本，建议顺手看一眼程序目录下的 `lookbusy_config.json`；老版本生成的本地配置里可能还留着旧 key，删掉后重新启动就会恢复为空配置。

---

## 🛡️ 免责与保命声明

本工具的开发初衷坚持一个极其严肃的底线：**绝对不干涉你的真实业务代码与文件！**
- **不留痕迹**（输入框打完字后，一定会做全选删除操作，绝不主动保存修改废话）
- **不传数据**（无后门，纯净开源，甚至不需要联网也能跑降级模式）
- **只图一乐**（一切逻辑仅操作你的当前前台窗口）

*⚠️ 警告：请在合理合规的范围内使用。如果因为本软件演技太差（或者太好）被老板揪住扣了本月绩效，作者概不负责* 💸

---
<br>

# 🛠️ 极客专区：一起构建“世界级摸鱼生态”！

嫌这就完了？独带薪不如众带薪！目前 Look-Busy 的底层已经被我们彻底重构成了**即插即用 (Plug-and-Play)** 的完全动态架构。原生已支持浏览器、代码编辑器和诸多办公套件。

> 🤝 **贡献召唤！**
> 如果你正被钉钉、飞书、WhatsApp、或者你们公司某个反人类的内部自研系统折磨，非常欢迎顺手写个小适配器提 PR！

### 🔌 1 分钟就能写完的接入规则：
你**不需要**修改现有的任何控制逻辑，引擎会自动靠反射把你的脚本加载进 UI 里，只需两步：

1. 在 `adapters/` 目录下新建个脚本，比如 `your_app_name.py`。
2. 继承基类，画好你的专属 `META` 属性名牌：

```python
from adapters.base_adapter import BaseAdapter

class WhatsAppAdapter(BaseAdapter):
    # 填好这个名牌，程序启动时就会自动把它加进面板！
    META = {
        "names": ["WhatsApp"],                  # UI 上显示的别名
        "processes": ["whatsapp.exe"],          # 要挂钩监听的系统进程名
        "icon": "💬",                           # 随便配个顺眼的 emoji
        "priority": 1                           # 权重
    }
    
    def run_action(self):
        # 在这里写你希望鼠标和键盘在这个软件里做的各种“花里胡哨”的动作吧！
        pass
```

### 📦 怎么打包发行版？
如果你自己改了代码并想打包扔给同事，千万别去死磕复杂的 PyInstaller 参数和环境坑（比如 Anaconda 动不动丢 DLL 的老毛病）。
我们提供了一个自动修补依赖防坑的构建脚本，但现在请按下面这组命令来，别直接裸跑：

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller
py -3 build.py
```

同样，这组命令也请在 **Windows 原生终端** 里执行，不要在 WSL 里跑。

喝口水，崭新打包好的 `LookBusyAgent.exe` 就会老老实实呆在 `dist/` 目录里了。

如果你准备发 GitHub Release，建议顺手再压一个 zip：

```powershell
Compress-Archive -Force -Path .\dist\LookBusyAgent.exe -DestinationPath .\dist\LookBusyAgent-windows-x64.zip
```

**致敬每一个热爱生活的打工人！🍻**

---

# README (English)

GitHub: [github.com/MartinMa2026/LookBusyAgent](https://github.com/MartinMa2026/LookBusyAgent)

Look-Busy Agent is exactly what the name suggests: an open-source, free, portable workflow toy that simulates “being busy” on your computer.

It takes control of your screen, mouse, and keyboard, then combines that with your role and your current task to act like you are working hard while intentionally producing nothing meaningful.

## Core Features
- **Human-like activity simulation**: bezier-style mouse movement, pauses, clicks, scrolling, and random hesitation to make behavior feel more natural.
- **LLM-powered filler content**: if you enter your role and today’s task, it can generate office-style text for Word or code editors, then type and delete it like someone constantly revising.
- **Portable release build**: if you do not want to touch Python, just download `LookBusyAgent-windows-x64.zip` or `LookBusyAgent.exe` from [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases) and run it.
- **Multilingual UI**: built-in Chinese / English / Japanese switching.
- **Boss key (`F12`)**: instantly pause and regain control.
- **Fishing timer**: keeps track of how much “life time” you have reclaimed.

## How To Start

### Step 1: Get Equipped
If you just want to use it, download the packaged build from [GitHub Releases](https://github.com/MartinMa2026/LookBusyAgent/releases).

If you want to run from source, use native Windows PowerShell or CMD:

```bash
py -3 -m pip install -r requirements.txt
py -3 main.py
```

If your system does not have `py`, replace `py -3` with `python`.

Please do not run the desktop app directly from WSL / Linux / macOS.

### Step 2: Start The Ritual
1. Tell the panel who you are and what you are doing.
2. Select the apps you want it to operate on.
3. Fill in your own LLM API Key if you want smarter filler content.
4. Click `START FISHING`.
5. Done. Go get coffee.

Notes:
- The project no longer ships with any bundled default API key.
- If you used an older build before, check `lookbusy_config.json` in the app directory. Old local config may still contain previous values.

## Build A Release
If you modified the code and want to package it for someone else, use these commands in a **native Windows terminal**:

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pip install pyinstaller
py -3 build.py
```

The built executable will be placed in `dist/LookBusyAgent.exe`.

If you want a zip for GitHub Releases:

```powershell
Compress-Archive -Force -Path .\dist\LookBusyAgent.exe -DestinationPath .\dist\LookBusyAgent-windows-x64.zip
```

## Disclaimer
This project is for learning, experimentation, and fun. Please use it responsibly and at your own risk.
