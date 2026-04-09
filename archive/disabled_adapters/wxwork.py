"""
wxwork.py - 企业微信 适配器（硬核工作版）
定位：硬核工作、汇报、流程审批、找人对齐。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be

_CORPORATE_REPLIES = [
    "好的老板", "收到，我马上跟进", "这就拉群对齐", 
    "我正在核对一下数据", "这个需求我们排期一下",
    "会议纪要发群里了", "流程已经提交审批了", 
    "这块逻辑我们需要再拉通一下", "明白，辛苦了"
]

class WXWorkAdapter(BaseAdapter):
    META = {
        "names": ["企业微信"],
        "processes": ["WXWork.exe"],
        "icon": "🏢",
        "priority": 1
    }

    def _activate_window(self) -> bool:
        for win in gw.getAllWindows():
            t = win.title.strip()
            if not t:
                continue
            if any(b in t for b in ['Chrome', 'Edge', 'Firefox', 'LookBusyAgent']):
                continue
            
            if '企业微信' in t or 'wxwork' in t.lower():
                if win.width > 50 and win.height > 50:
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
                    else:
                        continue
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
        """企业微信需要体现强工作流，搜报表，看组织架构，查工作台"""
        chains = [
            ['switch_chat', 'fake_type_burst', 'check_workbench', 'search_chat'],
            ['scroll_read', 'check_org_chart', 'switch_chat', 'fake_type'],
            ['check_workbench', 'scroll_read', 'scroll_read', 'search_chat'],
            ['switch_chat', 'check_org_chart', 'fake_type_burst']
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
            elif action == 'check_workbench':
                self._action_check_workbench()
            elif action == 'check_org_chart':
                self._action_check_org_chart()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[WXWork] {action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_fake_type_burst(self):
        win_x, win_y, win_w, win_h = self._get_window_rect()
        input_x = random.randint(int(win_x + win_w * 0.4), int(win_x + win_w * 0.75))
        input_y = random.randint(int(win_y + win_h * 0.85), int(win_y + win_h * 0.93))
        be.human_click(input_x, input_y)
        be.short_pause(0.2, 0.4)

        text = self._get_reply() if random.random() < 0.3 else random.choice(_CORPORATE_REPLIES)
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
        query = random.choice(['需求文档', '发票', '报销', '会议纪要', '排期', '周报', 'OKR'])
        be.human_type(query)
        be.short_pause(1.5, 3.0)
        # 终极安全措施：全选并删除，既能清空搜索栏恢复原状，又防防范了Ctrl+F失效而可能误发信息
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.press('delete')

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
        for _ in range(random.randint(3, 8)):
            chat_y = random.randint(int(win_y + win_h * 0.15), int(win_y + win_h * 0.85))
            be.human_click(chat_x, chat_y)
            be.short_pause(0.1, 0.4)
            if random.random() < 0.3:
                be.human_scroll(clicks=random.randint(2, 5))

    def _action_check_workbench(self):
        """假装点开左侧下方的“工作台”图标，寻找OA应用"""
        win_x, win_y, win_w, win_h = self._get_window_rect()
        # 点击左下角区域
        be.human_click(int(win_x) + random.randint(20, 60), random.randint(int(win_y + win_h * 0.7), int(win_y + win_h * 0.9)))
        be.short_pause(1.0, 2.0)
        # 浏览工作台
        be.human_move(
            random.randint(int(win_x + win_w * 0.4), int(win_x + win_w * 0.7)), 
            random.randint(int(win_y + win_h * 0.4), int(win_y + win_h * 0.6))
        )
        for _ in range(random.randint(1, 3)):
            be.human_scroll(clicks=random.randint(3, 8), direction='down')
            be.short_pause(0.5, 1.5)

    def _action_check_org_chart(self):
        """假装在左侧边栏寻找组织架构/通讯录的人"""
        win_x, win_y, win_w, win_h = self._get_window_rect()
        # 点击左侧中间的通讯录图标
        be.human_click(int(win_x) + random.randint(20, 60), random.randint(int(win_y + win_h * 0.4), int(win_y + win_h * 0.6)))
        be.short_pause(1.0, 2.0)
        # 在多级列表中寻找
        org_x = random.randint(int(win_x + win_w * 0.1), int(win_x + win_w * 0.25))
        for _ in range(random.randint(3, 5)):
            org_y = random.randint(int(win_y + win_h * 0.3), int(win_y + win_h * 0.8))
            be.human_click(org_x, org_y)
            be.short_pause(0.5, 1.0)
