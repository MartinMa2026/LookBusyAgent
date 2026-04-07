# Look-Busy Agent 🎭

> 让你假装很忙，实际啥也没干。开源 · 免费 · Windows 优先

---

## 🌟 最新特性

- **多语言秒切**：内置中文(ZH) / 英文(EN) / 日文(JA) 三语言字典，UI 界面一点即换，无缝热更新。
- **免环境纯净版**：支持直接打包为纯正单文件 `.exe`，内置精致像素风「喝咖啡摸鱼」图标，即查即用，无需配置 Python 依赖。
- **配置持久便携化**：打包后的软件以“U 盘绿色形态”运行。运行目录会自动生成伴生 `lookbusy_config.json` 来保存个人自定义设置，换电脑拷走即用。

## 功能

- 🔍 **自动扫描**系统中已安装的办公软件
- 🖱️ **模拟真人操作**：贝塞尔曲线鼠标、随机打字节奏、思考停顿
- 🤖 **LLM 智能内容生成**：打出来的字贴合你的工作主题（可选）
- 🚨 **老板键一键急停**（默认 `Ctrl+Shift+Q`），再按一次恢复
- ✅ **绝不产生真实操作**：微信输入框打字后自动清空，不发出任何消息

## 支持软件

| 类别 | 软件 |
|------|------|
| 即时通讯 | 微信、企业微信 |
| 浏览器 | Chrome、Edge |
| 办公套件 | Excel、Word、WPS |

## 快速开始

### 1. 源码模式（需依赖）

```bash
pip install -r requirements.txt
python main.py
```

### 2. 免安装单机版使用（独立运行版）

如已下载 `.exe` 版本，直接双击运行即可，配套自定义配置将自动储存在同级目录下的 `lookbusy_config.json` 中。

## 配置与操作流程

1. 填写"我是谁 / 在做啥"（可选，用于让 LLM 生成更贴合场景的内容）
2. 勾选今天要"工作"的软件
3. 填写 LLM API Key（可选，填了打出来的字更自然）
4. 在顶部选择所需的当地语言配置 `[ZH]` `[EN]` `[JA]`
5. 点击「🚀 开始摸鱼」

## LLM 配置（可选）

在 UI 中填入 API Key 即可，支持：

| 服务 | base_url | model 示例 |
|------|----------|-----------|
| OpenAI | `https://api.openai.com` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Ollama 本地 | `http://localhost:11434` | `qwen2.5` |

> 不填 API Key 时自动使用内置模板，完全离线可用。

也可以直接编辑 `config/default_tasks.json` 或 `lookbusy_config.json`（对应单文件版）：

```json
{
  "llm": {
    "api_key": "sk-...",
    "base_url": "https://api.openai.com",
    "model": "gpt-4o-mini"
  }
}
```

## 老板键

默认：**`Ctrl+Shift+Q`**

- 按一次：**立刻停止**所有鼠标/键盘动作，焦点回到原窗口
- 再按一次：**恢复**模拟

可以在 UI 界面自定义快捷键。

## 自己打包为最终 EXE

可随时使用 PyInstaller 编译纯净绿色单文件：

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon "assets/icon.ico" --add-data "config;config" --add-data "assets;assets" --collect-submodules adapters main.py -n LookBusyAgent
```

生成的完整可携式单体 EXE 文件位于 `dist/` 目录。

## 安全声明

本工具**不会**：
- 发送任何消息（微信输入后自动清空）
- 上传任何数据
- 修改任何真实文件（临时文件自动清理）
- 绕过公司监控软件

请在合理范围内使用。

## License

MIT
