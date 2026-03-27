"""
word.py - Word / WPS 适配器（热火朝天版）
优化：
- 窗口不存在直接跳过（不等待）
- type_paragraph 改为真正流式打字（去掉 use_clipboard）
- 新增"连续写作"动作：快速打多段
- 停顿大幅缩短，节奏更快
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


_PARAGRAPH_TEMPLATES = [
    "根据本季度{kw}分析，整体呈现稳步增长态势，",
    "针对{kw}工作，我们制定了以下改进方案，",
    "综合以上数据，{kw}目标完成情况如下，",
    "就{kw}问题，经过深入研究和讨论，建议如下，",
    "本报告主要就{kw}方面进行系统性总结，",
    "从数据来看，{kw}环比增长明显，原因分析如下，",
    "针对{kw}提出以下三点优化建议，",
]


class WordAdapter(BaseAdapter):

    def _find_window(self):
        for win in gw.getAllWindows():
            t = win.title.lower()
            if ('word' in t or '.docx' in t or '.doc' in t
                    or ('wps' in t and 'writer' in t)):
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            # 尝试创建临时文档，但只等 2.5s
            self._create_temp_doc()
            time.sleep(2.5)
            win = self._find_window()
        if not win:
            return False
        try:
            win.activate()
            time.sleep(random.uniform(0.3, 0.6))
            return True
        except Exception:
            return False

    def _create_temp_doc(self):
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False,
                                          prefix='look_busy_', dir=tempfile.gettempdir())
        tmp.close()
        os.startfile(tmp.name)

    def _get_template_text(self):
        kws = self._get_task_keywords()
        kw = random.choice(kws) if kws else '工作'
        tmpl = random.choice(_PARAGRAPH_TEMPLATES)
        return tmpl.format(kw=kw)

    def _generate_behavior_chain(self) -> list:
        """生成一套零极高仿真的文档查阅与审视动作链（零真实输入修改）"""
        chains = [
            # 剧本1: 沉浸式审读 - 上下翻阅 -> 划选某段文字高亮 -> 停滞思考
            ['scroll', 'select_text', 'stay_and_think'],
            # 剧本2: 全文检索找错 - Ctrl+F 搜索关键词 -> 上下文比对 -> 关掉搜素
            ['search_document', 'scroll', 'scroll'],
            # 剧本3: 摸鱼翻页 - 连续上下滚动查阅之前写的 -> 偶尔进行一次微滑动
            ['scroll', 'scroll', 'stay_and_think'],
            # 剧本4: 缝合怪 - 切去别的地方找资料 -> 回来快速划选对比
            ['navigate', 'scroll', 'select_text']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return   # ✅ 跳过

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'search_document':
                self._action_search_document()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'select_text':
                self._action_select_text()
            elif action == 'stay_and_think':
                self._action_stay_and_think()
            else:
                self._action_navigate()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Word] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_search_document(self):
        """假装按 Ctrl+F 搜索某个关键词，没有任何物理修改破坏"""
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(random.uniform(0.3, 0.6))
        # 随机抽取本工作域内的词或随意打几个词
        keywords = self._get_task_keywords()
        query = random.choice(keywords) if keywords else random.choice(['报告', '总结', '数据', '分析'])
        be.human_type(query)
        be.short_pause(1.5, 3.0)
        pyautogui.press('escape')  # 退出搜索框

    def _action_stay_and_think(self):
        """发呆思考"""
        time.sleep(random.uniform(1.5, 3.5))

    def _action_select_text(self):
        """安全动作：按住 Shift 和方向键假装在高亮划选重点段落"""
        pyautogui.keyDown('shift')
        for _ in range(random.randint(4, 15)):
            pyautogui.press(random.choice(['down', 'right', 'right']))
            time.sleep(random.uniform(0.05, 0.15))
        pyautogui.keyUp('shift')
        time.sleep(random.uniform(1.0, 2.5))
        pyautogui.press('left')  # 取消选区
        count = random.randint(1, 2)   # 从2-4减为1-2
        for i in range(count):
            text = self._get_paragraph() if random.random() < 0.4 else self._get_template_text()
            be.human_type(text)
            time.sleep(0.1)
            pyautogui.press('enter')
            if i < count - 1:
                be.short_pause(0.3, 0.8)

    def _action_review_and_edit(self):
        """向上滚动回顾，然后选中一行修改（模拟审稿）"""
        be.human_scroll(clicks=random.randint(5, 12), direction='up')
        be.short_pause(0.5, 1.5)
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
        key = random.choice(['pagedown', 'pageup', 'ctrl+end', 'ctrl+home'])
        if '+' in key:
            pyautogui.hotkey(*key.split('+'))
        else:
            pyautogui.press(key)
        be.short_pause(0.5, 1.5)
