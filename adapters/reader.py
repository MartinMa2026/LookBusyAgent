"""
reader.py - PDF/长文档/笔记阅读器 代跑适配器（热火朝天版）
新增：支持 Acrobat, SumatraPDF, Notion, Obsidian, Epub 等窗口的上下翻页、精读与沉浸式划选。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be

class ReaderAdapter(BaseAdapter):

    def _find_window(self):
        keywords = ['acrobat', 'sumatra', 'pdf', 'notion', 'obsidian', 'foxit', '阅读', '笔记']
        for win in gw.getAllWindows():
            t = win.title.lower()
            if any(k in t for k in keywords):
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            time.sleep(random.uniform(1.0, 2.0))
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
        """生成连贯的长文阅读动作链"""
        chains = [
            # 剧本1: 沉浸大阅读 - 仔细阅读往下滚 -> 偶尔划选高亮文字 -> 阅读往下翻页
            ['read_and_scroll', 'highlight_text', 'read_and_scroll'],
            # 剧本2: 快速略读 - page_down 一页一页看 -> 滑动查看上下文
            ['page_down', 'page_down', 'read_and_scroll'],
            # 剧本3: 盯着看并记录 - 单纯发呆看并划线
            ['read_and_scroll', 'highlight_text', 'highlight_text']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'read_and_scroll':
                self._action_read_and_scroll()
            elif action == 'page_down':
                self._action_page_down()
            else:
                self._action_highlight_text()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Reader] {action} failed: {e}")

        be.short_pause(0.5, 2.0)

    def _action_read_and_scroll(self):
        """仔细阅读当前页，并滚轮向下"""
        time.sleep(random.uniform(1.5, 4.0))
        be.human_scroll(random.randint(4, 12))

    def _action_page_down(self):
        """模拟看长文直接按 PageDown 或者空格键翻页"""
        time.sleep(random.uniform(0.5, 2.0))
        key = random.choice(['pagedown', 'space'])
        pyautogui.press(key)
        time.sleep(random.uniform(1.0, 3.0))

    def _action_highlight_text(self):
        """假装在文档上划选一下文字或者发呆点两下左键"""
        be.human_click(double=random.choice([True, False]))
        time.sleep(random.uniform(0.5, 1.5))
