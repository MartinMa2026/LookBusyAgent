"""
wechat.py - 私人微信 适配器（碎片化社交版）
定位：生活化、私人化、刷朋友圈、日常聊天。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be

_FALLBACK_REPLIES = [
    "哈哈哈", "可以啊", "我晚点看下", "等下说，这边有点忙",
    "好的我知道了", "收到", "太搞笑了", "那确实",
    "在路上呢", "行，没问题"
]

class WeChatAdapter(BaseAdapter):
    META = {
        "names": ["微信"],
        "processes": ["WeChat.exe"],
        "icon": "💬",
        "priority": 0
    }

    def _activate_window(self) -> bool:
        for win in gw.getAllWindows():
            t = win.title.strip()
            if not t:
                continue
            if any(b in t for b in ['Chrome', 'Edge', 'Firefox', 'LookBusyAgent']):
                continue
            
            if t == "微信" or t.lower() == "wechat":
                if win.width > 50 and win.height > 50:
                    try:
                        if getattr(win, 'isMinimized', False):
                            win.restore()
                        pyautogui.press('alt')
                        win.activate()
                    except Exception:
                        pass
                    
                    time.sleep(random.uniform(0.3, 0.6))
                    self.current_window = win
                    return True
        return False

    def _get_window_rect(self):
        try:
            if getattr(self, 'current_window', None):
                win = self.current_window
                return win.left, win.top, win.width, win.height
        except Exception:
            pass
        w, h = pyautogui.size()
        return 0, 0, w, h

    def _generate_behavior_chain(self) -> list:
        """私人微信更随意，搜生活词，刷朋友圈"""
        chains = [
            ['switch_chat', 'fake_type_burst', 'scroll_read', 'search_chat'],
            ['browse_moments', 'scroll_read', 'switch_chat', 'fake_type_burst'],
            ['scroll_read', 'just_look', 'browse_moments'],
            ['switch_chat', 'fake_type', 'search_chat']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'fake_type_burst':
                self._action_fake_type_burst()
            elif action == 'fake_type':
                self._action_fake_type()
            elif action == 'search_chat':
                self._action_search_chat()
            elif action == 'scroll_read':
                self._action_scroll()
            elif action == 'switch_chat':
                self._action_switch_chat()
            elif action == 'browse_moments':
                self._action_browse_moments()
            else:
                self._action_just_look()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[WeChat] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_fake_type_burst(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        input_x = random.randint(int(win_x + win_w * 0.4), int(win_x + win_w * 0.75))
        input_y = random.randint(int(win_y + win_h * 0.85), int(win_y + win_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.4)

        text = self._get_reply() if random.random() < 0.2 else random.choice(_FALLBACK_REPLIES)
        be.human_type_burst(text)
        be.short_pause(0.3, 0.7)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_fake_type(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        input_x = random.randint(int(win_x + win_w * 0.4), int(win_x + win_w * 0.75))
        input_y = random.randint(int(win_y + win_h * 0.85), int(win_y + win_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.5)
        text = self._get_reply()
        be.human_type(text)
        be.short_pause(0.5, 1.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_search_chat(self):
        time.sleep(random.uniform(0.2, 0.5))
        pyautogui.hotkey('ctrl', 'f')
        be.short_pause(0.3, 0.6)
        query = random.choice(['外卖', '快递', '聚餐', '晚上吃啥', '哈哈', '到了吗', '链接'])
        be.human_type(query)
        be.short_pause(1.5, 3.0)
        pyautogui.press('escape')
        time.sleep(0.3)
        pyautogui.press('escape')

    def _action_scroll(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        x = random.randint(int(win_x + win_w * 0.35), int(win_x + win_w * 0.85))
        y = random.randint(int(win_y + win_h * 0.3), int(win_y + win_h * 0.7))
        be.human_move(x, y)
        be.short_pause(0.1, 0.3)
        be.human_scroll(clicks=random.randint(3, 10), direction=random.choice(['up', 'down', 'down']))

    def _action_switch_chat(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        chat_x = random.randint(int(win_x + win_w * 0.1), int(win_x + win_w * 0.25))
        for _ in range(random.randint(2, 6)):
            chat_y = random.randint(int(win_y + win_h * 0.15), int(win_y + win_h * 0.85))
            be.human_click(chat_x, chat_y)
            be.short_pause(0.1, 0.4)
            if random.random() < 0.3:
                be.human_scroll(clicks=random.randint(2, 5))

    def _action_browse_moments(self):
        """假装在大幅度浏览朋友圈或公众号，连续大量下滚"""
        win_x, win_y, win_w, win_h = self._get_window_rect()
        be.human_move(
            random.randint(int(win_x + win_w * 0.4), int(win_x + win_w * 0.6)), 
            random.randint(int(win_y + win_h * 0.4), int(win_y + win_h * 0.6))
        )
        for _ in range(random.randint(2, 4)):
            be.short_pause(1.0, 2.5)
            be.human_scroll(clicks=random.randint(5, 12), direction='down')

    def _action_just_look(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        for _ in range(random.randint(1, 2)):
            x = random.randint(int(win_x + win_w * 0.3), int(win_x + win_w * 0.85))
            y = random.randint(int(win_y + win_h * 0.25), int(win_y + win_h * 0.8))
            be.human_move(x, y, duration=random.uniform(0.3, 0.8))
            be.short_pause(0.5, 2.0)
