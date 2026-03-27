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
        """生成结合查阅与输入（无保存操作）的绝对安全写代码动作链"""
        chains = [
            # 剧本1: 全局找Bug后定位修改 - 切文件 -> Ctrl+F搜代码 -> 思考划选 -> 写一行代码
            ['switch_file', 'search_code', 'select_code', 'type_code'],
            # 剧本2: 代码审查并增加注释/逻辑 - 滚动查看 -> 敲几段代码 -> 不保存退出
            ['scroll_read', 'type_code', 'type_code'],
            # 剧本3: 看查阅代码 - 切来翻去只读不写
            ['switch_file', 'scroll_read', 'scroll_read'],
            # 剧本4: 极速开发 - 一直写一直写
            ['type_code', 'type_code', 'scroll_read']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'search_code':
                self._action_search_code()
            elif action == 'type_code':
                self._action_type_code()
            elif action == 'scroll_read':
                self._action_scroll_read()
            elif action == 'switch_file':
                self._action_switch_file()
            else:
                self._action_select_code()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Coder] {action} failed: {e}")

        be.short_pause(0.2, 0.8)

    def _action_type_code(self):
        """拉取真实代码段并写入（绝不按 Ctrl+S 保存破坏文件）"""
        code_snippet = self._get_code_snippet()
        be.human_type(code_snippet)

    def _action_search_code(self):
        """假装按 Ctrl+F 搜索某个变量或函数，不修改文件"""
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(random.uniform(0.2, 0.5))
        be.human_type(random.choice(['process', 'load_data', 'update', 'main', 'config', 'user_id', 'init']))
        be.short_pause(1.0, 2.5)
        pyautogui.press('escape')  # 退出搜索框

    def _action_scroll_read(self):
        """假装在思考和上下滚动审视代码"""
        time.sleep(random.uniform(1.0, 2.5))
        be.human_scroll(random.randint(4, 12))
        time.sleep(random.uniform(0.5, 1.5))

    def _action_switch_file(self):
        """模拟 Ctrl + Tab 或者其他系统级切换键查阅源文件"""
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(random.uniform(0.5, 1.0))
        be.human_scroll(random.randint(2, 5))

    def _action_select_code(self):
        """安全动作：按住 Shift 和方向键假装在高亮划选某几行代码以辅助思考"""
        pyautogui.keyDown('shift')
        for _ in range(random.randint(2, 6)):
            pyautogui.press(random.choice(['down', 'right']))
            time.sleep(random.uniform(0.05, 0.2))
        pyautogui.keyUp('shift')
        time.sleep(random.uniform(0.5, 1.5))
        # 随便点一下取消高亮
        pyautogui.press('left')
