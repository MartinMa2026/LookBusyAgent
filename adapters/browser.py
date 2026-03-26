"""
browser.py
Chrome / Edge 浏览器适配器。
模拟：打开标签页、访问预设URL、滚动、假装搜索。
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
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    config_path = os.path.normpath(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('browser_urls', ['https://www.google.com'])


_SEARCH_TEMPLATES = [
    "{kw} 分析报告",
    "{kw} 最新数据",
    "如何做 {kw}",
    "{kw} 模板下载",
    "{kw} 方法论",
    "2024 {kw} 趋势",
]


class BrowserAdapter(BaseAdapter):
    """Chrome / Edge 行为适配器"""

    def __init__(self, app_name: str, task_description: str, stop_event):
        super().__init__(app_name, task_description, stop_event)
        self.browser_urls = _load_browser_urls()
        self._window_titles = {
            "Chrome": ["Chrome", "Google Chrome"],
            "Edge": ["Edge", "Microsoft Edge"],
        }

    def _find_window(self):
        titles = self._window_titles.get(self.app_name, ["Chrome"])
        for title_kw in titles:
            for win in gw.getAllWindows():
                if title_kw.lower() in win.title.lower():
                    return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            # 如果浏览器窗口不存在，尝试打开它
            self._open_browser()
            time.sleep(3)
            win = self._find_window()
        if not win:
            return False
        try:
            win.activate()
            time.sleep(random.uniform(0.5, 1.0))
            return True
        except Exception:
            return False

    def _open_browser(self):
        """尝试打开浏览器"""
        import subprocess
        try:
            if self.app_name == "Chrome":
                subprocess.Popen(["chrome", "--new-window", "https://www.google.com"])
            else:
                subprocess.Popen(["msedge", "--new-window", "https://www.google.com"])
        except Exception:
            pass

    def run_action(self):
        """执行一轮浏览器模拟动作"""
        if not self._activate_window():
            be.medium_pause(10, 30)
            return

        action = random.choices(
            ['scroll', 'new_tab', 'navigate', 'fake_search', 'just_read'],
            weights=[35, 15, 20, 15, 15]
        )[0]

        try:
            if action == 'scroll':
                self._action_scroll()
            elif action == 'new_tab':
                self._action_new_tab()
            elif action == 'navigate':
                self._action_navigate()
            elif action == 'fake_search':
                self._action_fake_search()
            else:
                self._action_just_read()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Browser] 动作 {action} 失败: {e}")

        be.short_pause(2, 10)

    def _action_scroll(self):
        """上下滚动页面"""
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.2), int(screen_w * 0.8))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y)
        # 缓慢向下读页面
        for _ in range(random.randint(2, 5)):
            be.human_scroll(clicks=random.randint(2, 5), direction='down')
            be.short_pause(1.5, 4.0)
        # 有时回滚
        if random.random() < 0.3:
            be.human_scroll(clicks=random.randint(3, 8), direction='up')

    def _action_new_tab(self):
        """打开新标签页并访问 URL"""
        pyautogui.hotkey('ctrl', 't')
        time.sleep(random.uniform(0.8, 1.5))
        url = random.choice(self.browser_urls)
        be.human_type(url, use_clipboard=False)  # URL 全英文，逐字符输入
        time.sleep(0.3)
        pyautogui.press('enter')
        be.medium_pause(3, 8)  # 等待页面加载

    def _action_navigate(self):
        """在地址栏直接导航到工作相关 URL"""
        pyautogui.hotkey('ctrl', 'l')  # 聚焦地址栏
        time.sleep(random.uniform(0.3, 0.6))
        url = random.choice(self.browser_urls)
        be.human_type(url, use_clipboard=False)
        time.sleep(0.3)
        pyautogui.press('enter')
        be.medium_pause(3, 8)

    def _action_fake_search(self):
        """在搜索框输入工作相关内容（不一定回车）"""
        # 使用 LLM 生成的搜索词（或降级模板）
        query = self._get_search_query()

        pyautogui.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.6))
        be.human_type(query, use_clipboard=True)
        time.sleep(random.uniform(0.5, 1.5))
        # 有50%概率真的搜索
        if random.random() < 0.5:
            pyautogui.press('enter')
            be.medium_pause(3, 8)
        else:
            # 不搜索，清空地址栏
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            pyautogui.press('escape')

    def _action_just_read(self):
        """假装在认真阅读：鼠标跟随文字缓慢移动"""
        screen_w, screen_h = pyautogui.size()
        y = int(screen_h * 0.25)
        for _ in range(random.randint(3, 7)):
            x = random.randint(int(screen_w * 0.1), int(screen_w * 0.85))
            y = min(int(screen_h * 0.85), y + random.randint(20, 60))
            be.human_move(x, y, duration=random.uniform(1.0, 3.0))
            be.short_pause(0.5, 2.0)
