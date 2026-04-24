"""
excel.py - Excel 适配器（热火朝天版）
优化：
- 窗口不存在直接跳过（不等待）
- type_data 改用 human_type_burst（修复中文乱码）
- 新增"连续填表"动作：快速填入多个单元格
- 整体节奏加快
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


_FAKE_NUMBERS = [
    lambda: str(random.randint(100, 99999)),
    lambda: f"{random.uniform(0.01, 99.99):.2f}",
    lambda: str(random.randint(1, 100)) + "%",
    lambda: str(random.randint(10, 500)) + "万",
]

_FAKE_HEADERS = ["Q1", "Q2", "Q3", "Q4", "季度", "合计", "占比",
                 "环比", "同比", "目标", "完成率", "差异", "备注"]

_FAKE_TEXT_VALUES = {
    "ZH": ["报表", "数据", "汇总", "分析", "进度", "核对"],
    "EN": ["report", "data", "summary", "analysis", "progress", "review"],
    "JA": ["報告", "データ", "集計", "分析", "進捗", "確認"],
}


class ExcelAdapter(BaseAdapter):
    META = {
        "names": ["Excel"],
        "processes": ["EXCEL.EXE"],
        "icon": "📊",
        "priority": 1
    }


    def _find_window(self):
        for win in gw.getAllWindows():
            t = win.title.lower()
            if 'excel' in t or '.xlsx' in t or '.xls' in t or ('wps' in t and 'et' in t):
                return win
        return None

    def _activate_window(self) -> bool:
        # 针对所有的潜在影子窗口进行逐个硬激活尝试
        def attempt_activation():
            for win in gw.getAllWindows():
                t = win.title.lower()
                if 'excel' in t or '.xlsx' in t or '.xls' in t or ('wps' in t and 'et' in t):
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
            
        # ✅ 尝试创建临时文件，挂起寻找
        self._launch_blank_workbook()
        time.sleep(2.5)
        
        return attempt_activation()

    def _get_excel_executable(self):
        candidates = [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\root\Office15\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office15\EXCEL.EXE",
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
            matches = list(root.rglob("EXCEL.EXE"))
            if matches:
                return str(matches[0])
        return None

    def _launch_blank_workbook(self):
        exe = self._get_excel_executable()
        try:
            if exe:
                subprocess.Popen([exe, "/x"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.startfile("excel")
            return True
        except Exception as e:
            print(f"[Excel] launch failed: {e}")
            return False

    def _generate_behavior_chain(self) -> list:
        """生成支持当面录入的 Excel 动作链（不保存）"""
        chains = [
            ['mouse_review', 'fill_table', 'scroll', 'type_data'],
            ['navigate_cells', 'scroll', 'type_data', 'mouse_review'],
            ['fill_table', 'navigate_cells', 'scroll'],
            ['type_data', 'fill_table', 'mouse_review'],
        ]
        return random.choice(chains)

    def run_action(self):
        if not self._activate_window():
            return

        if not getattr(self, 'action_queue', None):
            self.action_queue = self._generate_behavior_chain()

        action = self.action_queue.pop(0)

        try:
            if action == 'fill_table':
                self._action_fill_table()
            elif action == 'type_data':
                self._action_type_data()
            elif action == 'navigate_cells':
                self._action_navigate_cells()
            elif action == 'scroll':
                self._action_scroll()
            elif action == 'mouse_review':
                self._action_mouse_review()
            else:
                self._action_navigate_cells()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[Excel] 动作 {action} 失败: {e}")

        be.short_pause(0.2, 0.8)

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
                kw = random.choice(_FAKE_TEXT_VALUES.get(self.language, _FAKE_TEXT_VALUES["ZH"]))
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
            kw = random.choice(_FAKE_TEXT_VALUES.get(self.language, _FAKE_TEXT_VALUES["ZH"]))
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

    def _action_mouse_review(self):
        screen_w, screen_h = pyautogui.size()
        for _ in range(random.randint(2, 4)):
            be.human_move(
                random.randint(int(screen_w * 0.35), int(screen_w * 0.85)),
                random.randint(int(screen_h * 0.25), int(screen_h * 0.75)),
                duration=random.uniform(0.2, 0.5),
            )
            be.short_pause(0.2, 0.5)
        if random.random() < 0.5:
            be.human_click()
