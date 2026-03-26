"""
scheduler.py
多软件任务调度器：按时间槽轮转执行各软件适配器。
"""

import threading
import random
import time
import json
import os
from core import behavior_engine
from core.llm_generator import LLMGenerator


def _load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    config_path = os.path.normpath(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class Scheduler:
    """
    调度多个软件适配器，按随机时间槽轮转执行。

    用法：
        scheduler = Scheduler(
            selected_apps=["微信", "Chrome"],
            task_description="做Q1销售报告",
            stop_event=hotkey_manager.get_stop_event()
        )
        scheduler.start()
    """

    def __init__(
        self,
        selected_apps: list[str],
        task_description: str = "",
        stop_event: threading.Event = None,
    ):
        self.selected_apps = selected_apps
        self.task_description = task_description
        self.stop_event = stop_event or threading.Event()
        self.config = _load_config()
        self._thread = None
        self._adapters = {}
        # 共享 LLM 生成器（异步预热）
        self._llm = LLMGenerator(task_description=task_description)

    def _load_adapters(self):
        """动态加载所需适配器"""
        from adapters.wechat import WeChatAdapter
        from adapters.browser import BrowserAdapter
        from adapters.excel import ExcelAdapter
        from adapters.word import WordAdapter

        adapter_map = {
            "微信": WeChatAdapter,
            "企业微信": WeChatAdapter,
            "Chrome": BrowserAdapter,
            "Edge": BrowserAdapter,
            "Excel": ExcelAdapter,
            "Word": WordAdapter,
            "WPS": WordAdapter,
        }

        self._adapters = {}
        for app in self.selected_apps:
            cls = adapter_map.get(app)
            if cls:
                self._adapters[app] = cls(
                    app_name=app,
                    task_description=self.task_description,
                    stop_event=self.stop_event,
                    llm=self._llm,
                )

    def start(self):
        """在后台线程中启动调度循环"""
        behavior_engine.set_stop_event(self.stop_event)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止调度（stop_event 会传递到所有适配器）"""
        self.stop_event.set()

    def _run_loop(self):
        """主调度循环：随机轮转各软件"""
        self._load_adapters()

        if not self._adapters:
            return

        app_queue = list(self._adapters.keys())
        random.shuffle(app_queue)
        idx = 0

        interval_min, interval_max = self.config.get('switch_interval_minutes', [5, 15])

        while not self.stop_event.is_set():
            app_name = app_queue[idx % len(app_queue)]
            adapter = self._adapters[app_name]
            slot_duration = random.uniform(
                interval_min * 60,
                interval_max * 60
            )

            slot_end = time.time() + slot_duration
            try:
                # 用时间槽机制：在 slot_duration 内反复执行该软件的动作
                while time.time() < slot_end and not self.stop_event.is_set():
                    adapter.run_action()
                    # 偶发长停顿（模拟被打断）
                    behavior_engine.maybe_long_pause(probability=0.01)
            except InterruptedError:
                break
            except Exception as e:
                # 单个适配器出错，记录后继续
                print(f"[Scheduler] {app_name} 适配器异常: {e}")
                time.sleep(2)

            idx += 1

    def wait(self):
        """等待调度线程结束"""
        if self._thread:
            self._thread.join()
