"""
wechat.py - 微信／企业微信 适配器（热火朝天版）
优化：
- 窗口不存在直接跳过（不等待）
- 权重调整为更多打字/切换（更忙碌）
- 新增"连续回复多条"动作
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


_FALLBACK_REPLIES = [
    "好的，我看一下", "收到，稍等片刻", "没问题，我来跟进",
    "了解，这边马上处理", "好的好的，我知道了", "数据我在整理中",
    "这个问题我查一下", "你说得对，我这边确认一下",
    "嗯嗯，我这边已经在看了", "可以，今天内给你回复",
]


class WeChatAdapter(BaseAdapter):

    def __init__(self, app_name: str, task_description: str, stop_event, llm=None):
        super().__init__(app_name, task_description, stop_event, llm)
        self._process_names = {"微信": "WeChat", "企业微信": "WXWork"}

    def _find_window(self):
        for win in gw.getAllWindows():
            t = win.title
            # 黑名单屏蔽部分浏览器和文件夹包含该关键词的情况
            if any(b in t for b in ['Chrome', 'Edge', 'Firefox', 'LookBusyAgent']):
                continue
            
            if self.app_name == "企业微信":
                # 企业微信的窗口名稳定为 "企业微信"
                if t == "企业微信":
                    return win
            else:
                # 普通微信的窗口名为 "微信" 或 "WeChat"
                if t == "微信" or t.lower() == "wechat":
                    return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            return False   # ✅ 直接跳过，不等待
        try:
            win.activate()
            time.sleep(random.uniform(0.3, 0.6))
            return True
        except Exception:
            return False

    def _generate_behavior_chain(self) -> list:
        """生成连贯的微信沟通动作链"""
        chains = [
            # 剧本1: 沉浸式回复 - 切换一次联系人 -> 快速回两句 -> 思考再回一句 -> 滑动看聊天记录
            ['switch_chat', 'fake_type_burst', 'fake_type', 'scroll_read'],
            # 剧本2: 爬楼看群 - 上下滚动看半天群消息 -> 切换另一个群继续看 -> 偶尔回一句短的
            ['scroll_read', 'scroll_read', 'switch_chat', 'scroll_read', 'fake_type_burst'],
            # 剧本3: 盯着屏幕看 - 啥也不干就在那仔细看某段聊天
            ['scroll_read', 'just_look'],
            # 剧本4: 连续输出长文 - 一直在那敲敲打打（随后全部删掉不发）
            ['fake_type', 'fake_type']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return   # ✅ 窗口不存在直接返回，Scheduler 会切换其他 app

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'fake_type_burst':
                self._action_fake_type_burst()
            elif action == 'fake_type':
                self._action_fake_type()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'switch_chat':
                self._action_switch_chat()
            else:
                self._action_just_look()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[WeChat] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_fake_type_burst(self):
        """快速输入1条回复（减少循环，让其他动作有机会执行）"""
        screen_w, screen_h = pyautogui.size()
        input_x = random.randint(int(screen_w * 0.4), int(screen_w * 0.75))
        input_y = random.randint(int(screen_h * 0.85), int(screen_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.4)

        text = self._get_reply() if random.random() < 0.4 else random.choice(_FALLBACK_REPLIES)
        be.human_type_burst(text)
        be.short_pause(0.3, 0.7)
        # 安全清空（绝不发送）
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_fake_type(self):
        """在输入框流式打字，然后清空"""
        screen_w, screen_h = pyautogui.size()
        input_x = random.randint(int(screen_w * 0.4), int(screen_w * 0.75))
        input_y = random.randint(int(screen_h * 0.85), int(screen_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.5)
        text = self._get_reply()
        be.human_type(text)
        be.short_pause(0.5, 1.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_scroll(self):
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.35), int(screen_w * 0.85))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y)
        be.short_pause(0.1, 0.3)
        be.human_scroll(clicks=random.randint(3, 10),
                        direction=random.choice(['up', 'down', 'down']))
        if random.random() < 0.4:
            be.short_pause(0.2, 0.5)
            be.human_scroll(clicks=random.randint(2, 5), direction='down')

    def _action_switch_chat(self):
        """左侧联系人/群聊快速切换扫视"""
        screen_w, screen_h = pyautogui.size()
        chat_x = random.randint(int(screen_w * 0.1), int(screen_w * 0.25))
        
        # 随机快速切换 3 到 8 个聊天，营造很急切找消息的氛围
        for _ in range(random.randint(3, 8)):
            chat_y = random.randint(int(screen_h * 0.15), int(screen_h * 0.85))
            be.human_click(chat_x, chat_y)
            # 点击后仅扫一眼，极短停顿
            be.short_pause(0.1, 0.4)
            
            # 极速切过去如果有长消息，稍微滚轮扫一下
            if random.random() < 0.3:
                be.human_scroll(clicks=random.randint(2, 5))

    def _action_just_look(self):
        screen_w, screen_h = pyautogui.size()
        for _ in range(random.randint(1, 2)):
            x = random.randint(int(screen_w * 0.3), int(screen_w * 0.85))
            y = random.randint(int(screen_h * 0.25), int(screen_h * 0.8))
            be.human_move(x, y, duration=random.uniform(0.3, 0.8))
            be.short_pause(0.5, 2.0)
