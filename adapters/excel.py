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
        """生成支持当面录入的 Excel 动作链（不保存）"""
        chains = [
            # 剧本1: 大盘录入查阅 - 选区高亮 -> 疯狂录数据 -> 下推滚动核对 -> 全局搜索数据
            ['select_range', 'fill_table', 'scroll', 'search_data'],
            # 剧本2: 走神加小改 - 游动 -> 鼠标划 -> 填几个字
            ['navigate_cells', 'scroll', 'type_data', 'navigate_cells'],
            # 剧本3: 核对填表 - 搜索 -> 游走 -> 填一次表
            ['search_data', 'navigate_cells', 'fill_table'],
            # 剧本4: 勤奋表哥 - 疯狂敲键盘
            ['fill_table', 'type_data', 'fill_table']
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'search_data':
                self._action_search_data()
            elif action == 'fill_table':
                self._action_fill_table()
            elif action == 'type_data':
                self._action_type_data()
            elif action == 'navigate_cells':
                self._action_navigate_cells()
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

    def _action_search_data(self):
        """假装按 Ctrl+F 搜索某个数据，安全查阅"""
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(random.uniform(0.3, 0.8))
        query = random.choice([self._get_number_str(), "总计", "合计", "报表", "2024", "汇总"])
        be.human_type(query)
        be.short_pause(1.0, 2.5)
        pyautogui.press('escape')  # 退出搜索框
        time.sleep(0.5)

    def _get_number_str(self):
        import numbers
        return str(random.randint(1000, 99999))

    def _action_fill_table(self):
        count = random.randint(5, 15)
        for _ in range(count):
            if random.random() < 0.65:
                content = self._get_number_str()
                pyautogui.typewrite(content, interval=random.uniform(0.04, 0.1))
            else:
                kw = random.choice(["报表", "数据", "汇总", "分析", "用户", "完成"])
                be.human_type_burst(kw)
            time.sleep(0.05)
            
            # 使用更逼真的矩阵式换行游走，而非无限向右延伸
            if random.random() < 0.7:
                pyautogui.press('tab')
            else:
                pyautogui.press('enter')
                time.sleep(0.1)
                for _ in range(random.randint(1, 4)):
                    pyautogui.press('left')
                    time.sleep(random.uniform(0.05, 0.15))
            
            be.short_pause(0.05, 0.2)

    def _action_type_data(self):
        if random.random() < 0.6:
            content = self._get_number_str()
            pyautogui.typewrite(content, interval=random.uniform(0.05, 0.12))
        else:
            kw = random.choice(["财务", "核对", "报表"])
            be.human_type_burst(kw)
        time.sleep(0.1)
        if random.random() < 0.5:
            pyautogui.press('tab')
        else:
            pyautogui.press('enter')
        be.short_pause(0.2, 0.8)

    def _action_navigate_cells(self):
        """假装在浏览单元格数据（不停按方向键在多处游走审阅）"""
        for _ in range(random.randint(5, 15)):
            pyautogui.press(random.choice(['up', 'down', 'left', 'right', 'down', 'right']))
            time.sleep(random.uniform(0.05, 0.2))
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
