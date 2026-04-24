from core.utils import get_config_path, get_resource_path
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

_LANGUAGE_NAMES = {
    "ZH": "Simplified Chinese",
    "EN": "English",
    "JA": "Japanese",
}

_DEFAULT_CONTEXT = {
    "ZH": "日常办公工作",
    "EN": "day-to-day office work",
    "JA": "日常のオフィス業務",
}

_FALLBACK_REPLIES = {
    "ZH": [
        "好的，我看一下",
        "稍等，我确认一下",
        "收到，我处理一下",
        "了解，我这边跟进一下",
    ],
    "EN": [
        "On it, checking now.",
        "Give me a minute, I'm confirming.",
        "Got it, I'm handling this.",
        "Understood, I'll follow up.",
    ],
    "JA": [
        "了解です、確認します。",
        "少々お待ちください、確認中です。",
        "承知しました、対応します。",
        "把握しました、引き続き進めます。",
    ],
}

_FALLBACK_PARAGRAPHS = {
    "ZH": [
        "本阶段整体数据保持稳定增长，后续重点将放在节奏控制与细节优化上。",
        "基于现有信息，下一步建议优先梳理关键问题并同步推进相关动作。",
        "结合当前进展，阶段性目标已基本明确，后续需要继续补齐支撑材料。",
    ],
    "EN": [
        "Overall progress remains stable, and the next step is to tighten execution and refine the supporting details.",
        "Based on the current information, the priority is to clarify the key issues and move the follow-up items forward in parallel.",
        "At this stage, the main direction is clear, and the remaining work is focused on filling in the supporting material.",
    ],
    "JA": [
        "現時点の進捗は安定しており、次の段階では実行精度と補足資料の整理が重要です。",
        "現在の情報を踏まえると、主要課題を明確にしつつ関連対応を並行して進める必要があります。",
        "ここまでで全体方針は固まっており、今後は根拠資料と細部の整理を進めます。",
    ],
}

_FALLBACK_SEARCH_QUERIES = {
    "ZH": [
        "季度报告模板",
        "数据分析方法",
        "项目进度管理",
        "会议纪要模板",
    ],
    "EN": [
        "quarterly report template",
        "data analysis methods",
        "project progress tracking",
        "meeting notes template",
    ],
    "JA": [
        "四半期報告 テンプレート",
        "データ分析 手法",
        "進捗管理 テンプレート",
        "議事録 テンプレート",
    ],
}


def _load_llm_config() -> dict:
    config_path = os.path.normpath(
        get_config_path())
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('llm', {})
    except Exception:
        return {}


def _resolve_base_url(config: dict) -> str:
    return (config.get('base_url') or 'https://api.openai.com').rstrip('/')


def _build_chat_completions_url(config: dict) -> str:
    """
    Accept a plain API host, a /v1 base URL, or a fully specified endpoint.
    """
    base_url = _resolve_base_url(config)
    if base_url.endswith('/chat/completions'):
        return base_url
    if base_url.endswith('/v1'):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


class LLMGenerator:
    """
    LLM 内容生成器（v2）
    - 首次异步预热，生成个性化内容缓存
    - 防重复队列：最近用过的 N 条不重复
    - 每 refresh_interval 分钟自动刷新一次
    """

    def __init__(self, task_description: str = "", identity: str = "",
                 refresh_interval_min: float = 10.0, language: str = "ZH"):
        self.task_description    = task_description
        self.identity            = identity
        self.refresh_interval    = refresh_interval_min * 60
        self.language            = language if language in _LANGUAGE_NAMES else "ZH"
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

    def set_language(self, language: str):
        if language in _LANGUAGE_NAMES:
            self.language = language
            self.refresh_async()

    # ── LLM 调用 ─────────────────────────────────────────────

    def _call_llm(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        try:
            import urllib.request
            api_key  = self.config.get('api_key', '')
            model    = self.config.get('model', 'gpt-4o-mini')

            url = _build_chat_completions_url(self.config)
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
            parts.append(self.identity)
        if self.task_description:
            parts.append(self.task_description)
        return " / ".join(parts) if parts else _DEFAULT_CONTEXT[self.language]

    def _warm_up(self):
        ctx = self._build_context()
        language_name = _LANGUAGE_NAMES[self.language]

        reply_prompt = (
            f"Context: {ctx}\n"
            f"Generate 12 short workplace instant-message replies in {language_name}.\n"
            f"Each line should be one natural reply with no numbering.\n"
            f"Keep them concise, professional, and varied, showing that the user is actively working or checking something."
        )
        para_prompt = (
            f"Context: {ctx}\n"
            f"Generate 10 professional document sentences in {language_name}.\n"
            f"Each line should be one sentence suitable for Word or document editing, with no numbering.\n"
            f"Make them realistic, specific to the work context, and not repetitive."
        )
        search_prompt = (
            f"Context: {ctx}\n"
            f"Generate 10 realistic web search queries in {language_name}.\n"
            f"Each line should be one practical search phrase related to the work context, with no numbering.\n"
            f"Keep them useful and varied."
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
        return self._pick('reply', _FALLBACK_REPLIES[self.language])

    def get_paragraph(self) -> str:
        return self._pick('paragraph', _FALLBACK_PARAGRAPHS[self.language])

    def get_search_query(self) -> str:
        return self._pick('search', _FALLBACK_SEARCH_QUERIES[self.language])

    def refresh_async(self):
        """手动触发异步刷新"""
        if self._enabled:
            self._ready.clear()
            threading.Thread(target=self._warm_up, daemon=True).start()
