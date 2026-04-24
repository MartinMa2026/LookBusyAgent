"""
word.py - Word / WPS 适配器（热火朝天版）
优化：
- 窗口不存在直接跳过（不等待）
- type_paragraph 改为真正流式打字（去掉 use_clipboard）
- 新增"连续写作"动作：快速打多段
- 停顿大幅缩短，节奏更快
"""

import os
import random
import subprocess
import time
from pathlib import Path
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


_PARAGRAPH_TEMPLATES = {
    "ZH": [
        "根据当前{kw}分析，整体进展保持稳定，后续重点如下。",
        "围绕{kw}工作，现阶段整理出以下推进思路。",
        "结合现有信息，{kw}相关结论和建议如下。",
    ],
    "EN": [
        "Based on the current {kw} review, overall progress remains stable and the next focus areas are listed below.",
        "For the ongoing {kw} work, the current draft can be organized around the following actions.",
        "Taking the available information into account, the key findings and recommendations for {kw} are as follows.",
    ],
    "JA": [
        "現時点の{kw}整理を踏まえると、全体の進捗は安定しており今後の重点は以下の通りです。",
        "{kw}対応については、現段階では次の進め方で整理するのが適切です。",
        "現状の情報をもとに、{kw}に関する要点と対応方針を以下にまとめます。",
    ],
}


class WordAdapter(BaseAdapter):
    META = {
        "names": ["Word"],
        "processes": ["WINWORD.EXE"],
        "icon": "📝",
        "priority": 1
    }

    def _is_word_window(self, title: str) -> bool:
        t = title.lower()
        return ('wps' not in t) and (
            'word' in t or '.docx' in t or '.doc' in t or 'winword' in t
        )


    def _activate_window(self) -> bool:
        def attempt_activation():
            for win in gw.getAllWindows():
                if not self._is_word_window(win.title):
                    continue
                        
                try:
                    if getattr(win, 'isMinimized', False):
                        win.restore()
                        time.sleep(0.2)
                    pyautogui.press('alt')
                    win.activate()
                except Exception:
                    pass
                
                time.sleep(random.uniform(0.3, 0.6))
                if getattr(win, 'isActive', False):
                    self.current_window = win
                    return True
            return False

        if attempt_activation():
            return True
            
        # 尝试创建临时文档，挂起寻找
        self._launch_blank_document()
        time.sleep(2.5)
        
        return attempt_activation()

    def _get_word_executable(self):
        candidates = [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\root\Office15\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office15\WINWORD.EXE",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path

        office_roots = [
            Path(r"C:\Program Files\Microsoft Office"),
            Path(r"C:\Program Files (x86)\Microsoft Office"),
        ]
        for root in office_roots:
            if not root.exists():
                continue
            matches = list(root.rglob("WINWORD.EXE"))
            if matches:
                return str(matches[0])
        return None

    def _launch_blank_document(self):
        exe = self._get_word_executable()
        try:
            if exe:
                subprocess.Popen([exe, "/q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["winword"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[Word] launch failed: {e}")
            return False

    def _get_template_text(self):
        kws = self._get_task_keywords()
        defaults = {"ZH": "工作", "EN": "work", "JA": "作業"}
        kw = random.choice(kws) if kws else defaults.get(self.language, defaults["ZH"])
        tmpl = random.choice(_PARAGRAPH_TEMPLATES.get(self.language, _PARAGRAPH_TEMPLATES["ZH"]))
        return tmpl.format(kw=kw)

    def _generate_behavior_chain(self) -> list:
        """生成一套不仅查阅还会当面大段敲字的动作链（绝对不触发 Ctrl+S）"""
        chains = [
            ['type_paragraph', 'scroll', 'continuous_write', 'mouse_review'],
            ['continuous_write', 'scroll', 'type_paragraph'],
            ['mouse_review', 'type_paragraph', 'continuous_write'],
            ['type_paragraph', 'continuous_write', 'mouse_review'],
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'continuous_write':
                self._action_continuous_write()
            elif action == 'type_paragraph':
                self._action_type_paragraph()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'mouse_review':
                self._action_mouse_review()
            elif action == 'stay_and_think':
                self._action_stay_and_think()
            else:
                self._action_navigate()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Word] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_stay_and_think(self):
        """发呆思考"""
        time.sleep(random.uniform(1.5, 3.5))

    def _action_mouse_review(self):
        """用鼠标审阅文档，减少快捷键干扰"""
        screen_w, screen_h = pyautogui.size()
        for _ in range(random.randint(2, 4)):
            be.human_move(
                random.randint(int(screen_w * 0.35), int(screen_w * 0.8)),
                random.randint(int(screen_h * 0.25), int(screen_h * 0.75)),
                duration=random.uniform(0.2, 0.6),
            )
            be.short_pause(0.2, 0.6)
        if random.random() < 0.5:
            be.human_click()
            be.short_pause(0.2, 0.5)

    def _action_continuous_write(self):
        """连续写入文字（绝不执行保存指令）"""
        count = random.randint(1, 2)
        for i in range(count):
            text = self._get_paragraph() if random.random() < 0.4 else self._get_template_text()
            be.human_type(text)
            if i < count - 1:
                be.short_pause(0.3, 0.8)

    def _action_type_paragraph(self):
        """流式打字一段文字（仅敲打不保存）"""
        text = self._get_paragraph() if random.random() < 0.4 else self._get_template_text()
        be.human_type(text)
        be.short_pause(0.4, 1.2)
        pyautogui.press('enter')
    def _action_review_and_edit(self):
        """向上滚动回顾，然后选中一行修改（模拟审稿）"""
        be.human_scroll(clicks=random.randint(5, 12), direction='up')
        time.sleep(random.uniform(0.5, 1.2))
        # 移动光标到某行
        for _ in range(random.randint(2, 5)):
            pyautogui.press('down')
            time.sleep(random.uniform(0.1, 0.25))
        # 选中当前行并重新打几个字（模拟修改）
        pyautogui.press('home')
        pyautogui.hotkey('shift', 'end')
        time.sleep(0.2)
        kw = random.choice(self._get_task_keywords() or ['数据', '分析', '报告'])
        be.human_type(f"（已更新）{kw}相关内容如下，")
        pyautogui.press('enter')

    def _action_format_text(self):
        pyautogui.press('home')
        time.sleep(0.15)
        pyautogui.hotkey('shift', 'end')
        time.sleep(0.2)
        fmt = random.choice(['bold', 'italic', 'underline'])
        key = {'bold': 'b', 'italic': 'i', 'underline': 'u'}[fmt]
        pyautogui.hotkey('ctrl', key)
        be.short_pause(0.3, 0.8)
        pyautogui.hotkey('ctrl', key)   # 取消格式
        pyautogui.press('end')

    def _action_scroll(self):
        screen_w, screen_h = pyautogui.size()
        be.human_move(
            random.randint(int(screen_w * 0.3), int(screen_w * 0.8)),
            random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        )
        be.human_scroll(clicks=random.randint(3, 10),
                        direction=random.choice(['down', 'down', 'up']))
        be.short_pause(0.3, 1.0)

    def _action_navigate(self):
        for _ in range(random.randint(2, 5)):
            pyautogui.press(random.choice(['up', 'down', 'down', 'pageup', 'pagedown']))
            time.sleep(random.uniform(0.08, 0.2))
        be.short_pause(0.5, 1.0)
