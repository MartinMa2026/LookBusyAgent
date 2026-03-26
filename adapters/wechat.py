"""
wechat.py
微信 / 企业微信 适配器。
模拟：打开聊天、切换对话、滚动记录、假装打字（绝不发送）。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


# wechat.py — 固定模板仅作后备（优先使用 LLM 生成）
_FALLBACK_TYPING_CONTENT = [
    "就这个问题，我觉得需要从几个维度来考虑",
    "数据我这边已经在整理了，大概今天下午能出来",
    "我理解你的意思，不过有几点需要核实一下",
]


class WeChatAdapter(BaseAdapter):
    """微信 / 企业微信 行为适配器"""

    def __init__(self, app_name: str, task_description: str, stop_event):
        super().__init__(app_name, task_description, stop_event)
        self._process_names = {
            "微信": "WeChat",
            "企业微信": "WXWork",
        }

    def _find_window(self):
        """找到微信/企业微信窗口"""
        proc = self._process_names.get(self.app_name, "WeChat")
        windows = gw.getWindowsWithTitle(proc)
        if not windows:
            # 尝试模糊匹配
            all_wins = gw.getAllTitles()
            for title in all_wins:
                if proc.lower() in title.lower() or '微信' in title or 'wechat' in title.lower():
                    windows = gw.getWindowsWithTitle(title)
                    if windows:
                        break
        return windows[0] if windows else None

    def _activate_window(self) -> bool:
        """激活窗口并返回是否成功"""
        win = self._find_window()
        if not win:
            return False
        try:
            win.activate()
            time.sleep(random.uniform(0.5, 1.0))
            return True
        except Exception:
            return False

    def run_action(self):
        """执行一轮微信模拟动作"""
        if not self._activate_window():
            be.medium_pause(10, 30)
            return

        action = random.choices(
            ['scroll', 'fake_type', 'switch_chat', 'just_look'],
            weights=[30, 25, 20, 25]
        )[0]

        try:
            if action == 'scroll':
                self._action_scroll()
            elif action == 'fake_type':
                self._action_fake_type()
            elif action == 'switch_chat':
                self._action_switch_chat()
            else:
                self._action_just_look()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[WeChat] 动作 {action} 失败: {e}")

        be.short_pause(2, 8)

    def _action_scroll(self):
        """滚动聊天记录"""
        # 在聊天内容区域随机移动鼠标后滚动
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.35), int(screen_w * 0.85))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y, duration=random.uniform(0.4, 0.8))
        be.short_pause(0.5, 1.5)
        be.human_scroll(clicks=random.randint(3, 10), direction=random.choice(['up', 'down']))
        be.short_pause(1, 4)
        # 有时候再滚回去
        if random.random() < 0.4:
            be.human_scroll(clicks=random.randint(2, 6), direction='down')

    def _action_fake_type(self):
        """在输入框假装打字，然后清空（绝不发送）"""
        screen_w, screen_h = pyautogui.size()
        input_x = random.randint(int(screen_w * 0.4), int(screen_w * 0.75))
        input_y = random.randint(int(screen_h * 0.85), int(screen_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.5, 1.5)

        # 使用 LLM 生成的内容（或降级模板）
        text = self._get_reply()
        be.human_type(text, use_clipboard=True)
        be.short_pause(1.0, 3.0)

        # ⚠️ 安全清空：Ctrl+A → Delete，确保不会误发
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        be.short_pause(0.5, 1.5)

    def _action_switch_chat(self):
        """点击聊天列表切换对话"""
        screen_w, screen_h = pyautogui.size()
        # 左侧聊天列表区域（约屏幕宽度的 15%~30%）
        list_x = random.randint(int(screen_w * 0.15), int(screen_w * 0.28))
        list_y = random.randint(int(screen_h * 0.2), int(screen_h * 0.75))
        be.human_move(list_x, list_y)
        be.short_pause(0.3, 0.8)
        be.human_click(list_x, list_y)
        be.short_pause(1.0, 3.0)

    def _action_just_look(self):
        """假装在看消息：鼠标缓慢移动，停留"""
        screen_w, screen_h = pyautogui.size()
        for _ in range(random.randint(1, 3)):
            x = random.randint(int(screen_w * 0.3), int(screen_w * 0.85))
            y = random.randint(int(screen_h * 0.25), int(screen_h * 0.8))
            be.human_move(x, y, duration=random.uniform(0.8, 2.0))
            be.short_pause(1.0, 5.0)
