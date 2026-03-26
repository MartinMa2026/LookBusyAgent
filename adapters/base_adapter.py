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
                 stop_event: threading.Event, llm=None):
        self.app_name = app_name
        self.task_description = task_description
        self.stop_event = stop_event
        self.llm = llm  # LLMGenerator 实例（可为 None，降级到模板）

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
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', self.task_description)
        return words if words else ["工作", "报告", "数据", "分析"]

    def _get_reply(self) -> str:
        """获取 LLM 生成的即时回复（微信场景）"""
        if self.llm:
            return self.llm.get_reply()
        import random
        return random.choice(["好的，我看一下", "收到，稍等", "了解，跟进一下"])

    def _get_paragraph(self) -> str:
        """获取 LLM 生成的文档段落（Word 场景）"""
        if self.llm:
            return self.llm.get_paragraph()
        import random
        return random.choice(["本季度整体数据稳步增长，", "根据分析，建议优化以下流程，"])

    def _get_search_query(self) -> str:
        """获取 LLM 生成的搜索词（浏览器场景）"""
        if self.llm:
            return self.llm.get_search_query()
        import random
        return random.choice(["季度报告模板", "数据分析方法", "工作计划表"])
