# Look-Busy Agent 🎭

> 让你假装很忙，实际啥也没干。开源 · 免费 · Windows 优先

---

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

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
python main.py
```

### 3. 使用

1. 填写"今天在干什么"（可选，用于生成更贴合的内容）
2. 勾选今天要"工作"的软件
3. 填写 LLM API Key（可选，填了打出来的字更自然）
4. 点击「🚀 开始摸鱼」

## LLM 配置（可选）

在 UI 中填入 API Key 即可，支持：

| 服务 | base_url | model 示例 |
|------|----------|-----------|
| OpenAI | `https://api.openai.com` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Ollama 本地 | `http://localhost:11434` | `qwen2.5` |

> 不填 API Key 时自动使用内置模板，完全离线可用。

也可以直接编辑 `config/default_tasks.json`：

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

## 打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "LookBusyAgent" main.py
```

EXE 文件在 `dist/` 目录。

## 安全声明

本工具**不会**：
- 发送任何消息（微信输入后自动清空）
- 上传任何数据
- 修改任何真实文件（临时文件自动清理）
- 绕过公司监控软件

请在合理范围内使用。

## License

MIT
