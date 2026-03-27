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

    def _activate_window(self) -> bool:
        for win in gw.getAllWindows():
            t = win.title.strip()
            if not t:
                continue
            if any(b in t for b in ['Chrome', 'Edge', 'Firefox', 'LookBusyAgent']):
                continue
            
            is_match = False
            if self.app_name == "企业微信":
                # 放宽对企业微信的识别条件，很多被拆出的独立聊天、或者是附属服务都包含这四个字
                if '企业微信' in t or 'wxwork' in t.lower():
                    is_match = True
            else:
                if t == "微信" or t.lower() == "wechat":
                    is_match = True
                    
            if is_match:
                try:
                    # 强过滤：只选有真实可视面积的窗口，过滤掉大量悬浮影子窗
                    if win.width > 50 and win.height > 50:
                        win.activate()
                        time.sleep(random.uniform(0.3, 0.6))
                        return True
                except Exception:
                    continue
        return False

    def _generate_behavior_chain(self) -> list:
        """生成连贯且完全零发送风险的微信沟通大忙人动作链（发信必秒删）"""
        chains = [
            # 剧本1: 搜历史记录与秒回 - 切联系人 -> 快速回两句(删) -> 思考再回一句(删) -> 搜记录
            ['switch_chat', 'fake_type_burst', 'fake_type', 'search_chat'],
            # 剧本2: 爬楼看群 - 上下滚动看半天群消息 -> 切个群继续看 -> 假装回一句(删)
            ['scroll_read', 'scroll_read', 'switch_chat', 'scroll_read', 'fake_type_burst'],
            # 剧本3: 盯着屏幕看长文 - 啥也不干仔细看某段聊天 -> 假装写长文回复(删)
            ['scroll_read', 'just_look', 'fake_type'],
            # 剧本4: 把群翻个底朝天 - 连续翻滚历史消息 -> 最后查一下
            ['switch_chat', 'scroll_read', 'scroll_read', 'search_chat']
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
            elif action == 'search_chat':
                self._action_search_chat()
            elif action == 'scroll_read':
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
        """快速输入1条短回复，随后绝不发送立刻清空"""
        screen_w, screen_h = pyautogui.size()
        input_x = random.randint(int(screen_w * 0.4), int(screen_w * 0.75))
        input_y = random.randint(int(screen_h * 0.85), int(screen_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.4)

        text = self._get_reply() if random.random() < 0.4 else random.choice(_FALLBACK_REPLIES)
        be.human_type_burst(text)
        be.short_pause(0.3, 0.7)
        # 安全清空（绝不敲击 Enter 发出）
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_fake_type(self):
        """在输入框流式打长文，随后端盘清空（绝不发送）"""
        screen_w, screen_h = pyautogui.size()
        input_x = random.randint(int(screen_w * 0.4), int(screen_w * 0.75))
        input_y = random.randint(int(screen_h * 0.85), int(screen_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.5)
        text = self._get_reply()
        be.human_type(text)
        be.short_pause(0.5, 1.5)
        # 撤销所有假装打的内容
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

    def _action_search_chat(self):
        """极其安全逼真的动作：在当前聊天记录里按 Ctrl+F 搜索某个同事或事情"""
        time.sleep(random.uniform(0.2, 0.5))
        pyautogui.hotkey('ctrl', 'f')
        be.short_pause(0.3, 0.6)
        query = random.choice(['会议', '文件', '链接', 'PPT', '确认', '进度', '安排'])
        be.human_type(query)
        be.short_pause(1.5, 3.0)
        # 退出搜索状态，不留痕迹
        pyautogui.press('escape')
        time.sleep(0.3)
        pyautogui.press('escape')

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
