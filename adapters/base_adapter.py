"""
base_adapter.py
所有软件适配器的抽象基类。
"""

import threading
from abc import ABC, abstractmethod
from typing import Optional


class BaseAdapter(ABC):
    """
    软件适配器基类。
    每个子类实现 run_action()，调度器会反复调用它。
    """

    def __init__(self, app_name: str, task_description: str,
                 stop_event: threading.Event, llm=None, language: str = "ZH"):
        self.app_name = app_name
        self.task_description = task_description
        self.stop_event = stop_event
        self.llm = llm  # LLMGenerator 实例（可为 None，降级到模板）
        self.language = language if language in {"ZH", "EN", "JA"} else "ZH"

    def set_language(self, language: str):
        if language in {"ZH", "EN", "JA"}:
            self.language = language

    def is_stopped(self) -> bool:
        return self.stop_event.is_set()

    @abstractmethod
    def run_action(self):
        """
        执行一次模拟动作序列。
        调度器会在时间槽内反复调用此方法。
        """
        pass

    def _get_task_keywords(self) -> list[str]:
        """从任务描述中提取关键词"""
        import re
        words = re.findall(r'[\u4e00-\u9fff\u3040-\u30ffA-Za-z0-9]+', self.task_description)
        if words:
            return words
        fallbacks = {
            "ZH": ["工作", "报告", "数据", "分析"],
            "EN": ["work", "report", "data", "analysis"],
            "JA": ["作業", "報告", "データ", "分析"],
        }
        return fallbacks.get(self.language, fallbacks["ZH"])

    def _get_reply(self) -> str:
        """获取 LLM 生成的即时回复（聊天场景）"""
        if self.llm:
            return self.llm.get_reply()
        import random
        replies = {
            "ZH": ["好的，我看一下", "收到，稍等", "了解，我跟进一下"],
            "EN": ["On it, checking now.", "Got it, give me a moment.", "Understood, I'll follow up."],
            "JA": ["了解です、確認します。", "承知しました、少々お待ちください。", "把握しました、進めます。"],
        }
        return random.choice(replies.get(self.language, replies["ZH"]))

    def _get_paragraph(self) -> str:
        """获取 LLM 生成的文档段落（Word 场景）"""
        if self.llm:
            return self.llm.get_paragraph()
        import random
        paragraphs = {
            "ZH": ["本季度整体数据稳步增长，", "根据分析，建议优化以下流程，"],
            "EN": ["Overall results remain on a steady upward trend,", "Based on the analysis, the next workflow improvements are as follows,"],
            "JA": ["今期の全体データは安定して伸びており、", "分析結果を踏まえると、次の工程改善が必要です。"],
        }
        return random.choice(paragraphs.get(self.language, paragraphs["ZH"]))

    def _get_search_query(self) -> str:
        """获取 LLM 生成的搜索词（浏览器场景）"""
        if self.llm:
            return self.llm.get_search_query()
        import random
        queries = {
            "ZH": ["季度报告模板", "数据分析方法", "工作计划表"],
            "EN": ["quarterly report template", "data analysis methods", "work plan template"],
            "JA": ["四半期報告 テンプレート", "データ分析 手法", "業務計画 テンプレート"],
        }
        return random.choice(queries.get(self.language, queries["ZH"]))

    def _get_code_snippet(self) -> str:
        """获取 LLM 生成的代码片段（IDE/编辑器场景）"""
        if self.llm and hasattr(self.llm, "get_code_snippet"):
            return self.llm.get_code_snippet()
        import random
        return random.choice([
            "def process_data(data):\n    result = []\n    for item in data:\n        if item.is_valid():\n            result.append(item.transform())\n    return result\n",
            "class TaskScheduler:\n    def __init__(self):\n        self.tasks = []\n    def add_task(self, task):\n        self.tasks.append(task)\n",
            "import re\nimport json\n\ndef parse_response(body: str) -> dict:\n    try:\n        return json.loads(body)\n    except Exception as e:\n        return {}\n"
        ])
