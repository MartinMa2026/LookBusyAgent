"""
llm_generator.py
基于 LLM 生成与工作主题贴合的文字内容。
支持 OpenAI 兼容 API（含 Ollama 本地模型）。
LLM 不可用时自动降级到模板。
"""

import json
import os
import random
import threading
from typing import Optional

# 降级用的内置模板
_FALLBACK_REPLIES = [
    "好的，我看一下",
    "稍等，我确认一下",
    "收到，我处理一下",
    "嗯嗯，明白了",
    "好的，待我查一查",
    "正在整理，稍后发给你",
    "了解，我这边跟进一下",
    "收到！稍等",
]

_FALLBACK_PARAGRAPHS = [
    "本季度整体情况来看，数据呈稳步增长趋势，各项指标均达预期。",
    "根据现有数据，我们对下一阶段工作提出以下几点建议和改进思路。",
    "经过详细分析，目前问题的主要原因在于流程衔接不畅，需要优化。",
    "综合以上信息，本次会议的核心议题可以归纳为以下三个方面。",
    "就本周工作进展而言，主要完成了资料整理、数据核对和方案讨论。",
]

_FALLBACK_SEARCH_QUERIES = [
    "季度报告模板",
    "数据分析方法论",
    "工作计划表格",
    "PPT汇报技巧",
    "项目进度管理",
]


def _load_llm_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    config_path = os.path.normpath(config_path)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('llm', {})
    except Exception:
        return {}


class LLMGenerator:
    """
    LLM 内容生成器。
    - 首次调用时异步预热，生成一批内容缓存
    - 后续调用直接从缓存随机取
    - LLM 不可用时降级到内置模板
    """

    def __init__(self, task_description: str = ""):
        self.task_description = task_description
        self.config = _load_llm_config()
        self._cache: dict[str, list[str]] = {
            'reply': [],
            'paragraph': [],
            'search': [],
        }
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._enabled = bool(self.config.get('api_key') or self.config.get('base_url'))

        if self._enabled:
            # 后台预热
            threading.Thread(target=self._warm_up, daemon=True).start()
        else:
            self._ready.set()  # 直接可用（使用降级）

    def _call_llm(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        """调用 LLM API（OpenAI 兼容格式）"""
        try:
            import urllib.request
            base_url = self.config.get('base_url', 'https://api.openai.com').rstrip('/')
            api_key = self.config.get('api_key', '')
            model = self.config.get('model', 'gpt-4o-mini')

            url = f"{base_url}/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.8,
            }).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"[LLM] API 调用失败: {e}，将使用降级内容")
            return None

    def _warm_up(self):
        """预生成内容池"""
        task = self.task_description or "日常办公工作"

        # 生成即时回复
        reply_prompt = (
            f"我正在{task}。请生成10条自然的中文工作即时回复短句（微信/企业微信风格），"
            f"每条不超过15个汉字，不带序号，每行一条。"
            f"这些回复表达正在忙于工作、需要稍等、已收到等语气。"
        )
        # 生成段落内容
        para_prompt = (
            f"我今天的工作是：{task}。请生成8条适合在Word文档中出现的中文工作段落开头句，"
            f"每条20-40个汉字，不带序号，每行一条。"
            f"内容要符合该工作主题，看起来像真实的工作文档。"
        )
        # 生成搜索词
        search_prompt = (
            f"我今天的工作是：{task}。请生成8个相关的中文搜索关键词或短语，"
            f"像是正在搜索工作资料时会输入的词，不带序号，每行一条。"
        )

        with self._lock:
            for key, prompt in [('reply', reply_prompt), ('paragraph', para_prompt), ('search', search_prompt)]:
                content = self._call_llm(prompt)
                if content:
                    lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
                    self._cache[key] = lines

        self._ready.set()

    def get_reply(self) -> str:
        """获取一条即时回复（微信打字场景）"""
        self._ready.wait(timeout=10)
        with self._lock:
            pool = self._cache.get('reply') or _FALLBACK_REPLIES
        return random.choice(pool)

    def get_paragraph(self) -> str:
        """获取一段工作文字（Word 打字场景）"""
        self._ready.wait(timeout=10)
        with self._lock:
            pool = self._cache.get('paragraph') or _FALLBACK_PARAGRAPHS
        return random.choice(pool)

    def get_search_query(self) -> str:
        """获取一个搜索词（浏览器搜索场景）"""
        self._ready.wait(timeout=10)
        with self._lock:
            pool = self._cache.get('search') or _FALLBACK_SEARCH_QUERIES
        return random.choice(pool)

    def refresh_async(self):
        """异步刷新内容池（适合长时间运行后定期刷新）"""
        if self._enabled:
            self._ready.clear()
            threading.Thread(target=self._warm_up, daemon=True).start()
