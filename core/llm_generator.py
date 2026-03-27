"""
llm_generator.py  (v2)
基于 LLM 生成与「我是谁 + 今天做什么」贴合的个性化内容。
改进：
- 将 identity（我是谁）加入 prompt 上下文
- 防重复队列：最近用过的内容不重复出现
- 定期自动刷新缓存（默认 10 分钟），保持内容新鲜
"""

import json
import os
import random
import threading
import time
from collections import deque
from typing import Optional


# ── 降级模板（LLM 不可用时使用）────────────────────────────

_FALLBACK_REPLIES = [
    "好的，我看一下", "稍等，我确认一下", "收到，我处理一下",
    "嗯嗯，明白了", "好的，待我查一查", "正在整理，稍后发给你",
    "了解，我这边跟进一下", "收到！稍等", "好的，我来想一下",
    "这个我核实一下", "明白，处理完告诉你", "没问题，我这边查",
]

_FALLBACK_PARAGRAPHS = [
    "本季度整体情况来看，数据呈稳步增长趋势，各项指标均达预期。",
    "根据现有数据，我们对下一阶段工作提出以下几点建议和改进思路。",
    "经过详细分析，目前问题的主要原因在于流程衔接不畅，需要优化。",
    "综合以上信息，本次会议的核心议题可以归纳为以下三个方面。",
    "就本周工作进展而言，主要完成了资料整理、数据核对和方案讨论。",
    "针对客户提出的问题，我们制定了详细的解决方案和跟进计划。",
    "基于现有资源和时间节点，建议按照以下优先级推进各项工作。",
]

_FALLBACK_SEARCH_QUERIES = [
    "季度报告模板", "数据分析方法论", "工作计划表格",
    "PPT汇报技巧", "项目进度管理", "Excel数据透视表",
    "工作汇报格式", "会议纪要模板",
]


def _load_llm_config() -> dict:
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('llm', {})
    except Exception:
        return {}


class LLMGenerator:
    """
    LLM 内容生成器（v2）
    - 首次异步预热，生成个性化内容缓存
    - 防重复队列：最近用过的 N 条不重复
    - 每 refresh_interval 分钟自动刷新一次
    """

    def __init__(self, task_description: str = "", identity: str = "",
                 refresh_interval_min: float = 10.0):
        self.task_description    = task_description
        self.identity            = identity
        self.refresh_interval    = refresh_interval_min * 60
        self.config              = _load_llm_config()

        self._cache: dict[str, list[str]] = {
            'reply': [], 'paragraph': [], 'search': []
        }
        # 防重复队列：记录最近使用过的条目
        self._recent: dict[str, deque] = {
            'reply': deque(maxlen=4),
            'paragraph': deque(maxlen=3),
            'search': deque(maxlen=4),
        }
        self._ready  = threading.Event()
        self._lock   = threading.Lock()
        self._enabled = bool(self.config.get('api_key') or self.config.get('base_url'))

        if self._enabled:
            threading.Thread(target=self._warm_up, daemon=True).start()
            threading.Thread(target=self._auto_refresh_loop, daemon=True).start()
        else:
            self._ready.set()

    # ── LLM 调用 ─────────────────────────────────────────────

    def _call_llm(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        try:
            import urllib.request
            base_url = self.config.get('base_url', 'https://api.openai.com').rstrip('/')
            api_key  = self.config.get('api_key', '')
            model    = self.config.get('model', 'gpt-4o-mini')

            url = f"{base_url}/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.9,   # 提高多样性
            }).encode('utf-8')

            req = urllib.request.Request(
                url, data=payload,
                headers={'Content-Type': 'application/json',
                         'Authorization': f'Bearer {api_key}'}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result['choices'][0]['message']['content']
                if content:
                    import re
                    content = re.sub(r'<think>.*?(</think>|$)', '', content, flags=re.DOTALL)
                    content = re.sub(r'```[a-zA-Z]*\n', '', content)
                    content = re.sub(r'```', '', content)
                    content = content.strip()
                return content
        except Exception as e:
            print(f"[LLM] API 调用失败: {e}，将使用降级内容")
            return None

    # ── 预热 & 刷新 ──────────────────────────────────────────

    def _build_context(self) -> str:
        """构建身份+任务上下文描述"""
        parts = []
        if self.identity:
            parts.append(f"我是：{self.identity}")
        if self.task_description:
            parts.append(f"今天在做：{self.task_description}")
        return "。".join(parts) if parts else "日常办公工作"

    def _warm_up(self):
        ctx = self._build_context()

        reply_prompt = (
            f"背景：{ctx}。\n"
            f"请生成12条自然的中文工作即时消息回复短句（微信/企业微信风格），"
            f"每条不超过20个汉字，不带序号，每行一条，内容多样化，"
            f"体现正在忙于该工作、需稍等、已处理中等语气，避免重复。"
        )
        para_prompt = (
            f"背景：{ctx}。\n"
            f"请生成10条适合在Word工作文档中出现的中文段落开头句，"
            f"每条25-45个汉字，不带序号，每行一条，"
            f"内容要紧扣该职位和工作主题，看起来像真实的专业工作文档，避免重复。"
        )
        search_prompt = (
            f"背景：{ctx}。\n"
            f"请生成10个真实工作中会搜索的中文关键词或短语，"
            f"像在百度/谷歌搜索工作资料时输入的词，不带序号，每行一条，"
            f"要与该职位和工作内容密切相关，避免重复。"
        )

        new_cache = {}
        for key, prompt in [('reply', reply_prompt),
                             ('paragraph', para_prompt),
                             ('search', search_prompt)]:
            content = self._call_llm(prompt)
            # 大模型可能会因为任务描述有“摸鱼”、“黑客”等词汇触发安全警报并返回“抱歉，无法提供”之类的拒绝语
            if content and not any(r in content.lower() for r in ['sorry', '抱歉', '无法提供', '无法协助', '不能提供', "can't help"]):
                lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
                # 通常正常生成的列表至少会有多行，如果是单句且过短通常不正常
                if len(lines) >= 3:
                    new_cache[key] = lines

        with self._lock:
            for key, lines in new_cache.items():
                if lines:
                    self._cache[key] = lines
        self._ready.set()
        print(f"[LLM] 内容池刷新完成：reply×{len(self._cache.get('reply', []))}"
              f" para×{len(self._cache.get('paragraph', []))}"
              f" search×{len(self._cache.get('search', []))}")

    def _auto_refresh_loop(self):
        """后台定期刷新内容池，保持内容新鲜"""
        while True:
            time.sleep(self.refresh_interval)
            print(f"[LLM] 定时刷新内容池...")
            self._ready.clear()
            self._warm_up()

    # ── 防重复取值 ────────────────────────────────────────────

    def _pick(self, key: str, fallback: list) -> str:
        """从 cache 中取一条，如果还未生成好（预热中）则不再死等，直接用降级数据。"""
        # 最多等0.5秒，避免"点击Start后鼠标不动"长达十几秒的卡死感
        is_ready = self._ready.wait(timeout=0.5)
        
        with self._lock:
            # 如果没准备好，强制用 fallback
            pool = list(self._cache.get(key) or fallback) if is_ready else list(fallback)

        # 过滤掉最近用过的
        recent = self._recent[key]
        candidates = [x for x in pool if x not in recent]
        if not candidates:
            candidates = pool   # 全部都用过了，就重置

        chosen = random.choice(candidates)
        self._recent[key].append(chosen)
        return chosen

    # ── 公开接口 ─────────────────────────────────────────────

    def get_reply(self) -> str:
        return self._pick('reply', _FALLBACK_REPLIES)

    def get_paragraph(self) -> str:
        return self._pick('paragraph', _FALLBACK_PARAGRAPHS)

    def get_search_query(self) -> str:
        return self._pick('search', _FALLBACK_SEARCH_QUERIES)

    def refresh_async(self):
        """手动触发异步刷新"""
        if self._enabled:
            self._ready.clear()
            threading.Thread(target=self._warm_up, daemon=True).start()
