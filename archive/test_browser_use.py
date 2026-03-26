import asyncio
from browser_use import Agent, Browser, ChatOpenAI
import re

# 编写自定义大模型拦截器：强制剥离带推理模型返回的 <think> 和 markdown 代码块
class NoThinkChatOpenAI(ChatOpenAI):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        result = await super()._agenerate(messages, stop, run_manager, **kwargs)
        for gen in result.generations:
            text = gen.message.content
            if isinstance(text, str):
                # 剥离 <think>...</think> 或未闭合的 <think>... 
                text = re.sub(r'<think>.*?(</think>|$)', '', text, flags=re.DOTALL)
                # 剥离 markdown json 标签
                text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
                text = re.sub(r'```', '', text)
                gen.message.content = text.strip()
        return result

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        result = super()._generate(messages, stop, run_manager, **kwargs)
        for gen in result.generations:
            text = gen.message.content
            if isinstance(text, str):
                text = re.sub(r'<think>.*?(</think>|$)', '', text, flags=re.DOTALL)
                text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
                text = re.sub(r'```', '', text)
                gen.message.content = text.strip()
        return result

async def main():
    # 使用注入了拦截器的自定义类，而非原始类
    llm = NoThinkChatOpenAI(
        model="MiniMax-M2.5-lightning",
        api_key="sk-cp-s4xXxGy0j94FF5wXFzdteKiCvCdCV2btf2oCUdU09a3zT1DupZFHvZE-MH-ZUREJVcLbgIg1vgKzKWtRwfToVk9MsBM_d9kAbNSJLWAkt94L8DC8ICutFRQ",
        base_url="https://api.minimaxi.com/v1",
    )
    
    # 配置无头/隐身浏览器模拟
    browser = Browser(
        headless=False, # 设置为 False 以便你能亲眼看到它的操作
        disable_security=True,
    )

    # 设定绝对安全、只读的任务！
    # 强调不发送、不录入数据、不修改文件、纯浏览。
    task_instructions = (
        "你是一个正在摸鱼看新闻查资料的普通上班族。"
        "请随意打开一个知名的新闻、视频或资讯网站（如 https://sspai.com/ 或 B站）。"
        "你可以使用网页内部的搜索框搜索你感兴趣的内容，随机点击文章看一看，并自然地上下滚动浏览页面。"
        "【极其重要的安全限制】：\n"
        "1. 绝对不要发送任何真实私人消息（如果不慎点开聊天框，可以随便打几个字假装回复然后立刻清空不发送）。\n"
        "2. 绝对不要上传任何本地数据、文件或涉及隐私的信息。\n"
        "3. 绝对不要修改任何真实文件配置或点击购买/充值按钮。\n"
        "【极其重要的输出格式限制】：\n"
        "你的输出将被程序作为绝对严格的纯 JSON 字典读取。因此：绝对不能包围 ```json 这样的 markdown 代码块！绝对不能返回任何带有 <think> 标签的思考文本！只允许直接输出合法的JSON本身，否则系统会立刻崩溃！\n"
        "请放开手脚自由且安全地浏览探索，查阅资料并阅读文章吧！持续浏览直到我让你停止。"
    )

    print("启动 Browser Use 代理...")
    agent = Agent(
        task=task_instructions,
        llm=llm,
        browser=browser,
        use_thinking=True, # 开启此参数让 browser-use 尝试剥离 <think> 等推理标签
    )

    # 运行代理
    await agent.run()
    
    # 关闭浏览器
    await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
