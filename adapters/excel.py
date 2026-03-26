"""
excel.py
Excel 适配器。
模拟：在单元格间移动、输入数字/文本、使用筛选菜单、滚动表格。
"""

import random
import time
import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


_FAKE_NUMBERS = [
    lambda: str(random.randint(100, 99999)),
    lambda: f"{random.uniform(0.01, 99.99):.2f}",
    lambda: str(random.randint(1, 100)) + "%",
]

_FAKE_HEADERS = ["Q1", "Q2", "Q3", "季度", "合计", "占比", "环比", "同比", "目标", "完成率"]


class ExcelAdapter(BaseAdapter):
    """Excel 行为适配器"""

    def _find_window(self):
        for win in gw.getAllWindows():
            title = win.title.lower()
            if 'excel' in title or '.xlsx' in title or '.xls' in title or 'wps' in title:
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            self._create_temp_workbook()
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

    def _create_temp_workbook(self):
        """如果没有 Excel 打开，创建临时工作簿"""
        import subprocess
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False,
                                          prefix='look_busy_temp_', dir=tempfile.gettempdir())
        tmp.close()
        # 用系统默认程序打开
        os.startfile(tmp.name)

    def run_action(self):
        if not self._activate_window():
            be.medium_pause(10, 30)
            return

        action = random.choices(
            ['navigate_cells', 'type_data', 'scroll', 'menu_action', 'select_range'],
            weights=[30, 25, 20, 15, 10]
        )[0]

        try:
            if action == 'navigate_cells':
                self._action_navigate_cells()
            elif action == 'type_data':
                self._action_type_data()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'menu_action':
                self._action_open_close_menu()
            else:
                self._action_select_range()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Excel] 动作 {action} 失败: {e}")

        be.short_pause(1, 5)

    def _action_navigate_cells(self):
        """用方向键或鼠标点击在单元格间移动"""
        # 键盘导航
        keys = ['right', 'right', 'down', 'left', 'down', 'right', 'up']
        for key in random.choices(keys, k=random.randint(3, 10)):
            pyautogui.press(key)
            time.sleep(random.uniform(0.1, 0.4))
        be.short_pause(0.5, 2.0)

    def _action_type_data(self):
        """在当前单元格输入数据"""
        # 随机：数字 or 文字
        if random.random() < 0.6:
            content = random.choice(_FAKE_NUMBERS)()
        else:
            content = random.choice(_FAKE_HEADERS + self._get_task_keywords())
        pyautogui.typewrite(content, interval=random.uniform(0.05, 0.15))
        time.sleep(0.2)
        # Tab 跳到下一格（不用 Enter，避免意外触发公式）
        pyautogui.press('tab')
        be.short_pause(0.5, 2.0)

    def _action_scroll(self):
        """滚动表格"""
        screen_w, screen_h = pyautogui.size()
        x = random.randint(int(screen_w * 0.3), int(screen_w * 0.8))
        y = random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        be.human_move(x, y)
        be.human_scroll(clicks=random.randint(3, 15),
                        direction=random.choice(['down', 'down', 'up', 'right']))
        be.short_pause(1, 4)

    def _action_open_close_menu(self):
        """打开菜单后关闭（视觉上看起来在操作）"""
        # Alt 打开菜单栏
        pyautogui.press('alt')
        time.sleep(random.uniform(0.5, 1.0))
        pyautogui.press('escape')
        be.short_pause(0.5, 2.0)

    def _action_select_range(self):
        """Shift+方向键选中一个范围，然后取消选择"""
        pyautogui.keyDown('shift')
        for _ in range(random.randint(3, 8)):
            pyautogui.press(random.choice(['right', 'down']))
            time.sleep(random.uniform(0.08, 0.2))
        pyautogui.keyUp('shift')
        be.short_pause(1.0, 3.0)
        pyautogui.press('escape')
