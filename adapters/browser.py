"""
browser.py - Chrome / Edge 适配器（热火朝天版）
优化：
- 不自动打开浏览器（避免暴露风险）
- 窗口不存在直接跳过
- 新增"研究循环"：反复搜索+滚动，像在查资料
- 停顿大幅缩短，节奏更快
"""

import random
import time
import json
import os
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


def _load_browser_urls():
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f).get('browser_urls', ['https://www.google.com'])


class BrowserAdapter(BaseAdapter):

    def __init__(self, app_name: str, task_description: str, stop_event, llm=None):
        super().__init__(app_name, task_description, stop_event, llm)
        self.browser_urls = _load_browser_urls()
        self._window_kws = {"Chrome": ["Chrome", "Google Chrome"],
                            "Edge": ["Edge", "Microsoft Edge"]}
        self.action_queue = []

    def _find_window(self):
        kws = self._window_kws.get(self.app_name, ["Chrome"])
        for win in gw.getAllWindows():
            if any(k.lower() in win.title.lower() for k in kws):
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            return False   # ✅ 直接跳过，不自动打开浏览器
        try:
            win.activate()
            time.sleep(random.uniform(0.3, 0.6))
            return True
        except Exception:
            return False

    def _generate_behavior_chain(self) -> list:
        """生成一套具有连贯逻辑的上网行为链（剧本）"""
        chains = [
            # 剧本1: 查阅资料 - 新开标签页 -> 尝试搜索 -> 滚动查阅结果 -> 点击进入页面留在文章页细看 -> 继续滚动
            ['new_tab', 'fake_search', 'scroll_read', 'stay_and_read', 'scroll_read'],
            # 剧本2: 主动导航 - 去常去网站 -> 滚动看咨询 -> 停在一篇里面细看 -> 再次进入深度研究
            ['navigate', 'scroll_read', 'stay_and_read', 'research_loop'],
            # 剧本3: 沉浸调研 - 直接开始一轮深度搜索和查阅 -> 发呆或者逐字看文章 -> 上下滚动
            ['research_loop', 'stay_and_read', 'scroll_read'],
            # 剧本4: 轻度摸鱼 - 随便搜点什么就一直停在那看
            ['fake_search', 'stay_and_read', 'scroll_read', 'stay_and_read'],
            # 剧本5: 重度阅读 - 连着滚然后一直看
            ['scroll_read', 'stay_and_read', 'scroll_read', 'stay_and_read', 'scroll_read']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return   # ✅ 跳过，不等待

        if not self.action_queue:
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'research_loop':
                self._action_research_loop()
            elif action == 'scroll_read':
                self._action_scroll_read()
            elif action == 'stay_and_read':
                self._action_stay_and_read()
            elif action == 'fake_search':
                self._action_fake_search()
            elif action == 'navigate':
                self._action_navigate()
            else:
                self._action_new_tab()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Browser] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_research_loop(self):
        """搜索+阅读（只执行 1 轮，避免过多连续搜索）"""
        rounds = 1
        for _ in range(rounds):
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(random.uniform(0.2, 0.4))
            be.human_type_burst(self._get_search_query())
            time.sleep(0.15)
            pyautogui.press('enter')
            be.medium_pause(1.0, 2.5)
            screen_w, screen_h = pyautogui.size()
            be.human_move(
                random.randint(int(screen_w * 0.2), int(screen_w * 0.8)),
                random.randint(int(screen_h * 0.3), int(screen_h * 0.6))
            )
            for _ in range(random.randint(2, 3)):
                be.human_scroll(clicks=random.randint(3, 6), direction='down')
                be.short_pause(0.3, 0.6)
            if random.random() < 0.3:
                be.human_scroll(clicks=random.randint(2, 4), direction='up')
            be.short_pause(0.2, 0.5)

    def _action_stay_and_read(self):
        """停留在当前页面认真阅读（鼠标跟随文字移动）"""
        screen_w, screen_h = pyautogui.size()
        y = int(screen_h * 0.25)
        for _ in range(random.randint(3, 6)):
            x = random.randint(int(screen_w * 0.1), int(screen_w * 0.85))
            y = min(int(screen_h * 0.82), y + random.randint(15, 45))
            be.human_move(x, y, duration=random.uniform(0.5, 1.2))
            be.short_pause(0.4, 1.2)
        if random.random() < 0.4:
            be.human_scroll(clicks=random.randint(3, 6), direction='up')
            be.short_pause(0.5, 1.5)

    def _action_scroll_read(self):
        """快速阅读当前页面"""
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.2), int(screen_w * 0.8))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y)
        for _ in range(random.randint(3, 6)):
            be.human_scroll(clicks=random.randint(2, 6), direction='down')
            be.short_pause(0.2, 0.6)
        if random.random() < 0.3:
            be.human_scroll(clicks=random.randint(3, 8), direction='up')

    def _action_fake_search(self):
        """在地址栏输入搜索词"""
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.2, 0.4))
        query = self._get_search_query()
        be.human_type(query)
        time.sleep(random.uniform(0.3, 0.8))
        if random.random() < 0.7:   # ✅ 提高真搜索概率
            pyautogui.press('enter')
            be.medium_pause(1.0, 2.5)
        else:
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            pyautogui.press('escape')

    def _action_navigate(self):
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.2, 0.4))
        be.human_type_burst(random.choice(self.browser_urls))
        time.sleep(0.15)
        pyautogui.press('enter')
        be.medium_pause(1.0, 2.5)

    def _action_new_tab(self):
        pyautogui.hotkey('ctrl', 't')
        time.sleep(random.uniform(0.4, 0.8))
        be.human_type_burst(random.choice(self.browser_urls))
        time.sleep(0.15)
        pyautogui.press('enter')
        be.medium_pause(1.0, 2.0)
