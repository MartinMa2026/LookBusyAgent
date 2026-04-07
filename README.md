# Look-Busy Agent 🎭

> 让你假装很忙，实际啥也没干。开源 · 免费 · 支持一键扩展应用 · Windows 优先

---

## 🌟 最新突破：极简的 "即插即用" 开源插件化系统！

为了给社区开发者极高的扩展自由度，当前版本的架构经历了底层升级：**全面移除硬配置，实现完全动态的本地插件（Adapter）加载架构**。
你不需要修改项目的任何主干代码，只需把编写的 `.py` 脚本丢到 `adapters` 文件夹中并带上 `META` 元信息，程序启动时会自动发现并无缝加载你的自定义“摸鱼软件支持”（展示到 UI，接入控制流）。

> 🤝 **我们热烈邀请每一位极客加入我们的行列**：
> 目前 LookBusyAgent 支持微信、Chrome、Excel 等基础应用。如果你每天被 **WhatsApp**、**Line**、**Discord**、或者各种**炒股系统**和**行业特定开发软件**折磨，**非常欢迎你顺手写一个新适配器提交 Pull Request！** 众人拾柴火焰高，让我们打造支持各种生态的神器吧！

### 👉 怎样编写自己的适配器提交 PR？

只需建立 `adapters/your_app.py`（例如 `whatsapp.py`），继承 `BaseAdapter` 并附加上：

```python
from adapters.base_adapter import BaseAdapter

class WhatsAppAdapter(BaseAdapter):
    META = {
        "names": ["WhatsApp"],                  # UI显示的别名
        "processes": ["whatsapp.exe"],          # 对应的系统进程
        "icon": "💬",                           # UI展示的 emoji 
        "priority": 1
    }
    
    def run_action(self):
        # 你的自动操作逻辑（例如点击页面、鼠标游走）
        pass
```
没有任何复杂的配置文件，随写随用，全自动构建载入！

---

## 核心特性

- **多语言秒切**：内置中文(ZH) / 英文(EN) / 日文(JA) 三语言字典，UI 界面一点即换，无缝热更新。
- **免环境纯净版**：支持直接打包为纯正单文件 `.exe`，内置精致像素风「喝咖啡摸鱼」图标，即查即用，无需配置 Python 依赖。
- **配置持久便携化**：打包后的软件以“U 盘绿色形态”运行。运行目录会自动生成伴生 `lookbusy_config.json` 来保存个人自定义设置，换电脑拷走即用。
- 🔍 **自动扫描**：通过注册表和运行时分析探测系统中已安装的兼容办公软件。
- 🖱️ **完美真人操作模拟**：基于贝塞尔曲线鼠标移动、随机错落打字节奏、仿真停顿模型。
- 🤖 **LLM 智能内容生成**：打出来的字高度贴合你描述的日常工作主题（可选功能）。
- 🚨 **强力老板键急停**（默认 `Ctrl+Shift+Q`），强杀指令，随停随走。

## 支持软件

| 类别 | 软件 |
|------|------|
| 即时通讯 | 微信、企业微信 |
| 浏览器 | Chrome、Edge |
| 办公套件 | Excel、Word、WPS |
| 开发者工具 | Code、Idea、Pycharm 等主流 IDE |
| 文献平台 | Notion、Foxit、AcroBat、WeRead |

## 快速开始

### 1. 源码模式（适用于开发者和爱折腾的朋友）

```bash
pip install -r requirements.txt
python main.py
```

### 2. 免安装单机版使用（一键独立运行版）

如已下载由 PyInstaller 编译好的 `.exe` 实体版本，直接双击运行即可。程序的各项参数和快捷键设置将会自动储存在其同级目录伴生的 `lookbusy_config.json` 里。真正免垃圾的便携使用体验！

## 配置与操作流程

1. 填写"我是谁 / 在做啥"（可选，用于让 LLM 生成更自然顺滑的场景文稿内容）
2. 勾选今天要"接客工作"的软件
3. 填写 LLM API Key（可选，不填就用降级固定模板）
4. 在顶部选择所需的显示用语言配置 `[ZH]` `[EN]` `[JA]`
5. 点击「🚀 开始摸鱼」

## 自己打包为最终 EXE 分发文件

可随时使用下方的 PyInstaller 终极无痛指令编译带图标的全新静默绿色单文件（它将自动收录社区提供的新增模块！）：

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon "assets/icon.ico" --add-data "config;config" --add-data "assets;assets" --collect-submodules adapters main.py -n LookBusyAgent
```

生成的完整可携式单体 EXE 文件位于 `dist/` 目录。

## 安全声明

本工具**坚决不会**：
- 发送任何消息出去（类似微信输入后必将立刻触发安全全选自动清空命令）
- 上传任何您的系统数据或截取后台隐私
- 修改任何真实的文件系统（所有的临时工作区均作废弃清理处理）
- 并不能帮您绕过诸如公司屏幕高频录屏的监控类安全软件

请在合理合规范围内娱乐操作本工具。

## License

MIT
