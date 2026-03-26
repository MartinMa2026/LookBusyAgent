"""
word.py
Word / WPS 适配器。
模拟：打字、选中文字、修改格式、滚动、不自动保存。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


# 模板段落（根据用户任务描述混入关键词）
_PARAGRAPH_TEMPLATES = [
    "根据本季度{kw}分析，整体呈现稳步增长态势，",
    "针对{kw}工作，我们制定了以下改进方案，",
    "综合以上数据，{kw}目标完成情况如下，",
    "就{kw}问题，经过深入研究和讨论，建议如下，",
    "本报告主要就{kw}方面进行系统性总结，",
]


class WordAdapter(BaseAdapter):
    """Word / WPS 行为适配器"""

    def _find_window(self):
        for win in gw.getAllWindows():
            title = win.title.lower()
            if ('word' in title or '.docx' in title or '.doc' in title
                    or 'wps' in title or 'writer' in title):
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            self._create_temp_doc()
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

    def _create_temp_doc(self):
        """创建临时 Word 文档"""
        import subprocess
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False,
                                          prefix='look_busy_temp_', dir=tempfile.gettempdir())
        tmp.close()
        os.startfile(tmp.name)

    def run_action(self):
        if not self._activate_window():
            be.medium_pause(10, 30)
            return

        action = random.choices(
            ['type_paragraph', 'format_text', 'scroll', 'navigate', 'select_text'],
            weights=[30, 20, 25, 15, 10]
        )[0]

        try:
            if action == 'type_paragraph':
                self._action_type_paragraph()
            elif action == 'format_text':
                self._action_format_text()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'navigate':
                self._action_navigate()
            else:
                self._action_select_text()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Word] 动作 {action} 失败: {e}")

        be.short_pause(1, 6)

    def _action_type_paragraph(self):
        """输入一段工作相关文字（LLM 生成或降级模板）"""
        text = self._get_paragraph()
        be.human_type(text, use_clipboard=True)
        be.short_pause(1.0, 3.0)
        pyautogui.press('end')
        pyautogui.press('enter')

    def _action_format_text(self):
        """选中一段文字并应用格式（粗体/斜体）"""
        # Home → Shift+End 选中当前行
        pyautogui.press('home')
        time.sleep(0.2)
        pyautogui.hotkey('shift', 'end')
        time.sleep(0.3)

        fmt = random.choice(['bold', 'italic', 'underline'])
        if fmt == 'bold':
            pyautogui.hotkey('ctrl', 'b')
        elif fmt == 'italic':
            pyautogui.hotkey('ctrl', 'i')
        else:
            pyautogui.hotkey('ctrl', 'u')

        be.short_pause(0.5, 1.5)
        # 取消格式（再按一次）
        if fmt == 'bold':
            pyautogui.hotkey('ctrl', 'b')
        elif fmt == 'italic':
            pyautogui.hotkey('ctrl', 'i')
        else:
            pyautogui.hotkey('ctrl', 'u')

        # 取消选中
        pyautogui.press('end')

    def _action_scroll(self):
        """在文档中滚动"""
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.3), int(screen_w * 0.8))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y)
        be.human_scroll(clicks=random.randint(3, 10),
                        direction=random.choice(['down', 'down', 'up']))
        be.short_pause(1, 4)

    def _action_navigate(self):
        """用 PageUp/PageDown 或方向键翻页"""
        key = random.choice(['pagedown', 'pageup', 'ctrl+end', 'ctrl+home'])
        if '+' in key:
            parts = key.split('+')
            pyautogui.hotkey(*parts)
        else:
            pyautogui.press(key)
        be.short_pause(1.0, 3.0)

    def _action_select_text(self):
        """用 Ctrl+A 全选后取消（模拟查看全文）"""
        pyautogui.hotkey('ctrl', 'a')
        be.short_pause(0.5, 1.5)
        # 取消选择
        pyautogui.press('escape')
        time.sleep(0.2)
        # 如果 Escape 无效，点一下文档内容区
        screen_w, screen_h = pyautogui.size()
        be.human_click(int(screen_w * 0.5), int(screen_h * 0.5))
