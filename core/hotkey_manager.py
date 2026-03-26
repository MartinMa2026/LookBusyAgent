"""
hotkey_manager.py
全局热键管理：「老板来了」一键暂停所有模拟动作。
"""

import threading
import time
import keyboard
import pyautogui


class HotkeyManager:
    """
    监听全局热键，触发后：
    1. 设置 stop_event，中断行为引擎
    2. 释放所有修饰键（防止 Ctrl/Shift 卡住）
    3. 回调 on_boss_arrives（由主程序实现：恢复 UI、更新状态）
    """

    def __init__(self, combo: str = "ctrl+shift+q"):
        self.combo = combo
        self.stop_event = threading.Event()
        self._on_boss_callback = None
        self._on_resume_callback = None
        self._paused = False
        self._listener_thread = None

    def set_combo(self, combo: str):
        self.combo = combo

    def on_boss_arrives(self, callback):
        """注册「老板来了」触发后的回调函数"""
        self._on_boss_callback = callback

    def on_resume(self, callback):
        """注册「继续摸鱼」恢复后的回调函数"""
        self._on_resume_callback = callback

    def start(self):
        """开始监听热键（在后台线程中）"""
        self._listener_thread = threading.Thread(
            target=self._listen_loop, daemon=True
        )
        self._listener_thread.start()

    def _listen_loop(self):
        keyboard.add_hotkey(self.combo, self._trigger)
        keyboard.wait()  # 阻塞线程直到程序退出

    def _trigger(self):
        """热键触发时执行"""
        if not self._paused:
            self._pause()
        else:
            self._resume()

    def _pause(self):
        """暂停模拟"""
        self._paused = True
        self.stop_event.set()

        # 释放所有修饰键，防止键盘状态卡住
        time.sleep(0.05)
        for key in ['ctrl', 'shift', 'alt', 'win']:
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass

        if self._on_boss_callback:
            self._on_boss_callback()

    def _resume(self):
        """恢复模拟（再次按热键）"""
        self._paused = False
        self.stop_event.clear()
        if self._on_resume_callback:
            self._on_resume_callback()

    def stop(self):
        """停止监听（程序退出时调用）"""
        try:
            keyboard.remove_hotkey(self.combo)
        except Exception:
            pass
        self.stop_event.set()

    def get_stop_event(self) -> threading.Event:
        return self.stop_event
