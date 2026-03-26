"""
excel.py - Excel 适配器（热火朝天版）
优化：
- 窗口不存在直接跳过（不等待）
- type_data 改用 human_type_burst（修复中文乱码）
- 新增"连续填表"动作：快速填入多个单元格
- 整体节奏加快
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
    lambda: str(random.randint(10, 500)) + "万",
]

_FAKE_HEADERS = ["Q1", "Q2", "Q3", "Q4", "季度", "合计", "占比",
                 "环比", "同比", "目标", "完成率", "差异", "备注"]


class ExcelAdapter(BaseAdapter):

    def _find_window(self):
        for win in gw.getAllWindows():
            t = win.title.lower()
            if 'excel' in t or '.xlsx' in t or '.xls' in t or ('wps' in t and 'et' in t):
                return win
        return None

    def _activate_window(self) -> bool:
        win = self._find_window()
        if not win:
            # ✅ 尝试创建临时文件，但不等待太久
            self._create_temp_workbook()
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

    def _create_temp_workbook(self):
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False,
                                          prefix='look_busy_', dir=tempfile.gettempdir())
        tmp.close()
        os.startfile(tmp.name)

    def _generate_behavior_chain(self) -> list:
        """生成连贯的 Excel 录入/查阅动作链"""
        chains = [
            # 剧本1: 大量录入数据 - 选区 -> 咔咔填表 -> 下拉滚动核对
            ['select_range', 'fill_table', 'scroll'],
            # 剧本2: 走神看表 - 上下左右按键游动 -> 鼠标滚一滚 -> 偶尔打开菜单看一眼
            ['navigate_cells', 'scroll', 'open_close_menu'],
            # 剧本3: 局部修改 - 游走到某处 -> 填几个字 -> 继续游走
            ['navigate_cells', 'type_data', 'navigate_cells'],
            # 剧本4: 纯粹的连续填表狂魔
            ['fill_table', 'fill_table', 'fill_table']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return   # ✅ 跳过

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'fill_table':
                self._action_fill_table()
            elif action == 'navigate_cells':
                self._action_navigate_cells()
            elif action == 'type_data':
                self._action_type_data()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'select_range':
                self._action_select_range()
            else:
                self._action_open_close_menu()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Excel] 动作 {action} 失败: {e}")

        be.short_pause(0.2, 0.8)

    def _action_fill_table(self):
        """✅ 新增：连续快速填入多个单元格，像在录数据"""
        count = random.randint(5, 15)
        for _ in range(count):
            if random.random() < 0.65:
                content = random.choice(_FAKE_NUMBERS)()
                # 数字用 typewrite 更快更准
                pyautogui.typewrite(content, interval=random.uniform(0.04, 0.1))
            else:
                kw = random.choice(_FAKE_HEADERS + self._get_task_keywords())
                # ✅ 中文用 human_type_burst 避免乱码
                be.human_type_burst(kw)
            time.sleep(0.05)
            pyautogui.press('tab')   # Tab 跳到下一格
            be.short_pause(0.05, 0.2)

        # 偶尔 Enter 换行
        if random.random() < 0.5:
            pyautogui.press('enter')

    def _action_navigate_cells(self):
        """方向键在单元格间快速移动"""
        keys = ['right', 'right', 'down', 'left', 'down', 'right', 'up', 'tab']
        for key in random.choices(keys, k=random.randint(5, 15)):
            pyautogui.press(key)
            time.sleep(random.uniform(0.06, 0.2))
        be.short_pause(0.2, 0.8)

    def _action_type_data(self):
        """✅ 修复：用 human_type_burst 输入（支持中文）"""
        if random.random() < 0.6:
            content = random.choice(_FAKE_NUMBERS)()
            pyautogui.typewrite(content, interval=random.uniform(0.05, 0.12))
        else:
            kw = random.choice(_FAKE_HEADERS + self._get_task_keywords())
            be.human_type_burst(kw)   # ✅ 修复中文乱码
        time.sleep(0.1)
        pyautogui.press('tab')
        be.short_pause(0.2, 0.8)

    def _action_scroll(self):
        screen_w, screen_h = pyautogui.size()
        be.human_move(
            random.randint(int(screen_w * 0.3), int(screen_w * 0.8)),
            random.randint(int(screen_h * 0.3), int(screen_h * 0.7))
        )
        be.human_scroll(clicks=random.randint(3, 12),
                        direction=random.choice(['down', 'down', 'up', 'right']))
        be.short_pause(0.3, 1.0)

    def _action_open_close_menu(self):
        pyautogui.press('alt')
        time.sleep(random.uniform(0.3, 0.6))
        pyautogui.press('escape')

    def _action_select_range(self):
        pyautogui.keyDown('shift')
        for _ in range(random.randint(3, 10)):
            pyautogui.press(random.choice(['right', 'down', 'right']))
            time.sleep(random.uniform(0.05, 0.15))
        pyautogui.keyUp('shift')
        be.short_pause(0.5, 1.5)
        pyautogui.press('escape')
