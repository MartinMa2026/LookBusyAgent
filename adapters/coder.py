"""
coder.py - 程序员/IDE 代跑适配器（热火朝天版）
新增：支持 VSCode, PyCharm, Cursor 等常见编辑器的窗口捕获与代码书写、查阅、格式化动作。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


class CoderAdapter(BaseAdapter):

    def _find_window(self):
        for win in gw.getAllWindows():
            t = win.title.lower()
            if 'visual studio code' in t or 'vscode' in t or 'pycharm' in t or 'intellij' in t or 'cursor' in t:
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            # 等待时间中掺杂随机极短抖动模拟寻找
            time.sleep(random.uniform(1.0, 3.0))
            # 再次寻找
            win = self._find_window()
            if not win:
                return False
        try:
            if not win.isActive:
                win.activate()
                time.sleep(random.uniform(0.3, 0.6))
            return True
        except Exception:
            return False

    def _generate_behavior_chain(self) -> list:
        """生成连贯的写代码动作链"""
        chains = [
            # 剧本1: 正常撸代码 - 思考审阅 -> 连敲代码 -> 随手保存 -> 切文件
            ['scroll_read', 'type_code', 'format_code', 'switch_file'],
            # 剧本2: 写错重构 - 写着写着 -> 翻页看下 -> 删掉重写
            ['type_code', 'scroll_read', 'type_code', 'format_code'],
            # 剧本3: 看查阅代码 - 切来翻去只读不写
            ['switch_file', 'scroll_read', 'scroll_read'],
            # 剧本4: 极速开发 - 一直写一直存
            ['type_code', 'format_code', 'type_code', 'format_code']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'type_code':
                self._action_type_code()
            elif action == 'scroll_read':
                self._action_scroll_read()
            elif action == 'switch_file':
                self._action_switch_file()
            else:
                self._action_format_code()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Coder] {action} failed: {e}")

        be.short_pause(0.2, 0.8)

    def _action_type_code(self):
        """拉取真实代码段并写入"""
        code_snippet = self._get_code_snippet()
        be.human_type(code_snippet)

    def _action_scroll_read(self):
        """假装在思考和上下滚动审视代码"""
        time.sleep(random.uniform(1.0, 3.0))
        be.human_scroll(random.randint(6, 15))
        time.sleep(random.uniform(0.5, 1.5))

    def _action_switch_file(self):
        """模拟 Ctrl + Tab 或者 Ctrl+P 等快捷键查阅其它源文件"""
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(random.uniform(0.5, 1.0))
        be.human_scroll()

    def _action_format_code(self):
        """好习惯：随手 Ctrl+S 保存或调用格式化快捷键"""
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.0)
