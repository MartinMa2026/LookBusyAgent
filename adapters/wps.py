"""
wps.py
Dedicated WPS adapter with workspace-aware behavior.
"""

import random
import time

import pyautogui
import pygetwindow as gw

from adapters.base_adapter import BaseAdapter
from core import behavior_engine as be


_WPS_TEXT_TEMPLATES = [
    "根据当前材料，先把关键数据和结论补齐。",
    "这一版先整理结构，细节稍后再补充。",
    "先把重点问题拆开，后续逐项跟进。",
    "这里需要补充背景说明和处理建议。",
]

_WPS_SHEET_LABELS = ["汇总", "分析", "预算", "进度", "复盘", "数据"]
_BLOCKING_DIALOG_KEYWORDS = (
    "打开",
    "open",
    "另存为",
    "save as",
    "选择文件",
    "选择要打开的文件",
    "文件夹",
    "浏览",
    "此电脑",
    "desktop",
    "downloads",
    "documents",
)


class WPSAdapter(BaseAdapter):
    META = {
        "names": ["WPS"],
        "processes": ["wps.exe", "et.exe", "wpp.exe", "wpspdf.exe"],
        "icon": "📘",
        "priority": 1,
    }

    def __init__(self, app_name: str, task_description: str, stop_event, llm=None):
        super().__init__(app_name, task_description, stop_event, llm)
        self.action_queue = []
        self.current_window = None
        self._mode = "home"

    def _activate_window(self) -> bool:
        for win in gw.getAllWindows():
            title = (win.title or "").strip()
            lower = title.lower()
            if not title:
                continue
            if not any(token in lower for token in ("wps", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf")):
                continue

            try:
                if getattr(win, "isMinimized", False):
                    win.restore()
                    time.sleep(0.2)
                pyautogui.press("alt")
                win.activate()
            except Exception:
                pass

            time.sleep(random.uniform(0.3, 0.6))
            if getattr(win, "isActive", False):
                self.current_window = win
                return True
        return False

    def _get_window_rect(self):
        try:
            if self.current_window:
                win = self.current_window
                return win.left, win.top, win.width, win.height
        except Exception:
            pass
        w, h = pyautogui.size()
        return 0, 0, w, h

    def _window_point(self, xr: float, yr: float):
        x, y, w, h = self._get_window_rect()
        return int(x + w * xr), int(y + h * yr)

    def _detect_mode(self) -> str:
        title = (getattr(self.current_window, "title", "") or "").lower()
        if any(ext in title for ext in (".xls", ".xlsx", ".csv")) or "et" in title:
            return "sheet"
        if any(ext in title for ext in (".ppt", ".pptx")) or "演示" in title:
            return "slides"
        if ".pdf" in title or "pdf" in title:
            return "pdf"
        if any(ext in title for ext in (".doc", ".docx", ".wps")) or "文字" in title or "writer" in title:
            return "writer"
        return "home"

    def _generate_behavior_chain(self, mode: str) -> list[str]:
        chains = {
            "home": [
                ["hover_nav", "browse_recent", "create_blank_document"],
                ["hover_cards", "pause_reading", "create_blank_document"],
                ["hover_nav", "pause_reading", "create_blank_document"],
            ],
            "writer": [
                ["read_document", "search_document", "type_short_note", "switch_tab"],
                ["read_document", "review_selection", "read_document"],
                ["type_short_note", "read_document", "navigate_document"],
            ],
            "sheet": [
                ["sheet_navigate", "sheet_scroll", "sheet_fill", "switch_tab"],
                ["sheet_select", "sheet_navigate", "sheet_scroll"],
                ["sheet_fill", "sheet_navigate", "sheet_scroll"],
            ],
            "slides": [
                ["switch_tab", "thumbnail_browse", "navigate_document", "pause_reading"],
                ["thumbnail_browse", "navigate_document", "switch_tab"],
            ],
            "pdf": [
                ["thumbnail_browse", "read_document", "navigate_document"],
                ["read_document", "navigate_document", "pause_reading"],
            ],
        }
        return list(random.choice(chains.get(mode, chains["home"])))

    def _dismiss_blocking_dialogs(self) -> bool:
        candidates = []
        try:
            active = gw.getActiveWindow()
            if active:
                candidates.append(active)
        except Exception:
            pass

        candidates.extend(gw.getAllWindows())

        seen = set()
        for win in candidates:
            if id(win) in seen:
                continue
            seen.add(id(win))
            title = (win.title or "").strip()
            lower = title.lower()
            if not title:
                continue
            if not any(keyword in lower for keyword in _BLOCKING_DIALOG_KEYWORDS):
                continue

            try:
                if getattr(win, "isMinimized", False):
                    win.restore()
                    time.sleep(0.2)
                pyautogui.press("alt")
                win.activate()
            except Exception:
                pass

            time.sleep(0.2)
            pyautogui.press("escape")
            time.sleep(0.2)
            pyautogui.press("escape")
            time.sleep(0.2)
            pyautogui.hotkey("alt", "f4")
            time.sleep(0.2)
            close_x = int(getattr(win, "left", 0) + max(getattr(win, "width", 200) - 18, 24))
            close_y = int(getattr(win, "top", 0) + 14)
            be.human_click(close_x, close_y)
            be.short_pause(0.3, 0.8)
            return True
        return False

    def run_action(self):
        if self._dismiss_blocking_dialogs():
            self.action_queue = []
            return

        if not self._activate_window():
            return

        mode = self._detect_mode()
        if mode != self._mode or not self.action_queue:
            self._mode = mode
            self.action_queue = self._generate_behavior_chain(mode)

        action = self.action_queue.pop(0)

        try:
            getattr(self, f"_action_{action}")()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"[WPS] {mode}/{action} failed: {e}")

        be.short_pause(0.3, 1.0)

    def _action_hover_nav(self):
        for _ in range(random.randint(2, 4)):
            x, y = self._window_point(random.uniform(0.06, 0.16), random.uniform(0.18, 0.78))
            be.human_move(x, y, duration=random.uniform(0.25, 0.6))
            be.short_pause(0.2, 0.6)

    def _action_browse_recent(self):
        x, y = self._window_point(random.uniform(0.32, 0.72), random.uniform(0.28, 0.62))
        be.human_move(x, y)
        for _ in range(random.randint(2, 4)):
            be.human_scroll(clicks=random.randint(3, 8), direction=random.choice(["down", "down", "up"]))
            be.short_pause(0.4, 0.9)

    def _action_hover_cards(self):
        for _ in range(random.randint(2, 4)):
            x, y = self._window_point(random.uniform(0.28, 0.78), random.uniform(0.22, 0.52))
            be.human_move(x, y, duration=random.uniform(0.3, 0.7))
            be.short_pause(0.3, 0.7)

    def _open_new_panel(self):
        x, y = self._window_point(random.uniform(0.06, 0.16), random.uniform(0.10, 0.18))
        be.human_click(x, y)
        be.short_pause(0.6, 1.1)

    def _action_create_blank_document(self):
        # Prefer keyboard creation first to avoid misclicking "Open" on the home page.
        pyautogui.hotkey("ctrl", "n")
        be.medium_pause(0.8, 1.6)
        if self._dismiss_blocking_dialogs():
            self.action_queue = []
            return

        if self._detect_mode() == "home":
            self._open_new_panel()
            x, y = self._window_point(random.uniform(0.24, 0.38), random.uniform(0.24, 0.40))
            be.human_click(x, y)
            be.medium_pause(0.8, 1.8)
        self._mode = "writer"
        self.action_queue = self._generate_behavior_chain("writer")

    def _action_create_blank_sheet(self):
        self._open_new_panel()
        x, y = self._window_point(random.uniform(0.42, 0.60), random.uniform(0.28, 0.46))
        be.human_click(x, y)
        be.medium_pause(0.8, 1.8)
        self._mode = "sheet"
        self.action_queue = self._generate_behavior_chain("sheet")

    def _action_switch_tab(self):
        if random.random() < 0.55:
            pyautogui.hotkey("ctrl", "tab")
        else:
            x, y = self._window_point(random.uniform(0.20, 0.72), random.uniform(0.08, 0.14))
            be.human_click(x, y)
        be.short_pause(0.5, 1.0)

    def _action_pause_reading(self):
        be.medium_pause(1.2, 3.0)

    def _action_read_document(self):
        start_x, start_y = self._window_point(random.uniform(0.30, 0.78), 0.26)
        be.human_move(start_x, start_y, duration=random.uniform(0.35, 0.8))
        for _ in range(random.randint(2, 5)):
            next_x, next_y = self._window_point(random.uniform(0.28, 0.82), random.uniform(0.28, 0.76))
            be.human_move(next_x, next_y, duration=random.uniform(0.4, 0.9))
            be.short_pause(0.3, 0.9)
        if random.random() < 0.7:
            be.human_scroll(clicks=random.randint(3, 8), direction=random.choice(["down", "down", "up"]))

    def _action_search_document(self):
        pyautogui.hotkey("ctrl", "f")
        be.short_pause(0.3, 0.6)
        keywords = self._get_task_keywords() or ["报告", "分析", "数据", "方案"]
        be.human_type(random.choice(keywords))
        be.short_pause(1.0, 2.0)
        pyautogui.press("escape")

    def _action_type_short_note(self):
        text = self._get_paragraph() if random.random() < 0.35 else random.choice(_WPS_TEXT_TEMPLATES)
        x, y = self._window_point(random.uniform(0.42, 0.74), random.uniform(0.74, 0.86))
        be.human_click(x, y)
        be.short_pause(0.2, 0.5)
        be.human_type(text[: random.randint(12, min(len(text), 28))])
        if random.random() < 0.6:
            pyautogui.press("enter")

    def _action_review_selection(self):
        pyautogui.keyDown("shift")
        for _ in range(random.randint(3, 8)):
            pyautogui.press(random.choice(["down", "right", "right"]))
            time.sleep(random.uniform(0.05, 0.12))
        pyautogui.keyUp("shift")
        be.short_pause(0.6, 1.4)
        pyautogui.press("left")

    def _action_navigate_document(self):
        key = random.choice(["pagedown", "pageup", "ctrl+home", "ctrl+end"])
        if "+" in key:
            pyautogui.hotkey(*key.split("+"))
        else:
            pyautogui.press(key)
        be.short_pause(0.5, 1.3)

    def _action_sheet_navigate(self):
        for _ in range(random.randint(4, 10)):
            pyautogui.press(random.choice(["up", "down", "left", "right", "tab", "down", "right"]))
            time.sleep(random.uniform(0.05, 0.16))

    def _action_sheet_scroll(self):
        x, y = self._window_point(random.uniform(0.36, 0.84), random.uniform(0.28, 0.72))
        be.human_move(x, y)
        for _ in range(random.randint(2, 4)):
            be.human_scroll(clicks=random.randint(2, 6), direction=random.choice(["down", "down", "up"]))
            be.short_pause(0.2, 0.5)

    def _action_sheet_fill(self):
        for _ in range(random.randint(1, 3)):
            if random.random() < 0.7:
                pyautogui.typewrite(str(random.randint(10, 9999)), interval=random.uniform(0.04, 0.09))
            else:
                be.human_type_burst(random.choice(_WPS_SHEET_LABELS))
            pyautogui.press(random.choice(["tab", "enter"]))
            be.short_pause(0.1, 0.3)

    def _action_sheet_select(self):
        pyautogui.keyDown("shift")
        for _ in range(random.randint(2, 6)):
            pyautogui.press(random.choice(["right", "down", "right"]))
            time.sleep(random.uniform(0.05, 0.12))
        pyautogui.keyUp("shift")
        be.short_pause(0.4, 1.0)
        pyautogui.press("escape")

    def _action_thumbnail_browse(self):
        x, y = self._window_point(random.uniform(0.08, 0.18), random.uniform(0.22, 0.78))
        be.human_move(x, y)
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.65:
                be.human_click(x, y + random.randint(-60, 60))
            be.human_scroll(clicks=random.randint(2, 5), direction=random.choice(["down", "up", "down"]))
            be.short_pause(0.4, 0.9)
