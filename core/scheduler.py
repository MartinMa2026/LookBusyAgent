"""
scheduler.py
多软件任务调度器：按权重加权随机选择并执行各软件适配器。
"""

import threading
import random
import time
import json
import os
from core import behavior_engine
from core.llm_generator import LLMGenerator


def _load_config():
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class Scheduler:
    """
    调度多个软件适配器，按权重随机抽取执行。

    app_weights: {app_name: weight}，weight 为正整数，总和不必为 100。
    """

    def __init__(
        self,
        app_weights: dict,
        task_description: str = "",
        stop_event: threading.Event = None,
        identity: str = "",
        selected_apps: list = None,   # 旧接口兼容
    ):
        if selected_apps is not None and not app_weights:
            app_weights = {app: 1 for app in selected_apps}

        self.app_weights      = {k: v for k, v in app_weights.items() if v > 0}
        self.task_description = task_description
        self.identity         = identity
        self.stop_event       = stop_event or threading.Event()
        self.config           = _load_config()
        self._thread          = None
        self._adapters        = {}
        self._llm             = LLMGenerator(task_description=task_description,
                                             identity=identity)

    # ── 适配器加载 ──────────────────────────────────────────

    def _load_adapters(self):
        from adapters.wechat  import WeChatAdapter
        from adapters.browser import BrowserAdapter
        from adapters.excel   import ExcelAdapter
        from adapters.word    import WordAdapter
        from adapters.coder   import CoderAdapter
        from adapters.reader  import ReaderAdapter

        adapter_map = {
            "微信":   WeChatAdapter,
            "企业微信": WeChatAdapter,
            "Chrome": BrowserAdapter,
            "Edge":   BrowserAdapter,
            "Excel":  ExcelAdapter,
            "Word":   WordAdapter,
            "WPS":    WordAdapter,
            "IDE/编辑器": CoderAdapter,
            "VSCode": CoderAdapter,
            "代码": CoderAdapter,
            "阅读器": ReaderAdapter,
            "PDF": ReaderAdapter,
            "笔记": ReaderAdapter,
        }

        self._adapters = {}
        for app in self.app_weights:
            cls = adapter_map.get(app)
            if cls:
                self._adapters[app] = cls(
                    app_name=app,
                    task_description=self.task_description,
                    stop_event=self.stop_event,
                    llm=self._llm,
                )

    # ── 加权随机选择 ────────────────────────────────────────

    def _weighted_choice(self) -> str:
        """按 app_weights 加权随机抽取一个可用 app"""
        apps = [a for a in self._adapters if a in self.app_weights]
        if not apps:
            return ""
        weights = [self.app_weights[a] for a in apps]
        return random.choices(apps, weights=weights, k=1)[0]

    # ── 调度循环 ────────────────────────────────────────────

    def start(self):
        behavior_engine.set_stop_event(self.stop_event)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.stop_event.set()

    def _run_loop(self):
        self._load_adapters()
        if not self._adapters:
            return

        interval_min, interval_max = self.config.get('switch_interval_minutes', [0.5, 2])

        while not self.stop_event.is_set():
            app_name = self._weighted_choice()
            if not app_name:
                time.sleep(1)
                continue
            adapter  = self._adapters[app_name]
            slot_duration = random.uniform(interval_min * 60, interval_max * 60)
            slot_end = time.time() + slot_duration

            try:
                while not self.stop_event.is_set():
                    adapter.run_action()
                    behavior_engine.maybe_long_pause(probability=0.005)
                    
                    if random.random() < 0.1:
                        behavior_engine.anti_sleep_jitter()
                    if random.random() < 0.01:
                        behavior_engine.dismiss_notification_popup()

                    # 当随机分配的时间片耗尽 时刻，并且当前软件的连贯剧本刚好执行完毕（队列为空）才允许切换软件
                    queue = getattr(adapter, 'action_queue', [])
                    if time.time() >= slot_end and not queue:
                        break

            except InterruptedError:
                break
            except Exception as e:
                print(f"[Scheduler] {app_name} 适配器异常: {e}")
                import traceback; traceback.print_exc()
                time.sleep(2)

    def wait(self):
        if self._thread:
            self._thread.join()
