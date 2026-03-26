"""
behavior_engine.py
仿真真人行为的基础模块：鼠标贝塞尔曲线移动、随机打字、停顿管理。
"""

import time
import random
import threading
import pyautogui
import pyperclip

# 禁用 pyautogui 的故障安全（移动到角落不中断），由老板键统一处理
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # 禁用默认停顿，我们自己控制


# ─────────────────────────────────────────────
# 全局停止信号
# ─────────────────────────────────────────────

_stop_event = threading.Event()


def set_stop_event(event: threading.Event):
    """注入来自外部的 stop_event（由 HotkeyManager 控制）"""
    global _stop_event
    _stop_event = event


def is_stopped() -> bool:
    return _stop_event.is_set()


def _check_stop():
    """在关键节点检查是否需要停止"""
    if is_stopped():
        raise InterruptedError("Boss key triggered — stopping simulation.")


# ─────────────────────────────────────────────
# 鼠标仿真
# ─────────────────────────────────────────────

def _bezier_point(t, p0, p1, p2):
    """二阶贝塞尔曲线插值"""
    return (
        (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1],
    )


def human_move(target_x: int, target_y: int, duration: float = None):
    """
    通过贝塞尔曲线模拟真人鼠标移动。
    duration: 秒，默认随机 0.3~1.2 秒
    """
    _check_stop()

    if duration is None:
        duration = random.uniform(0.3, 1.2)

    start_x, start_y = pyautogui.position()

    # 随机控制点（曲线的"弯曲程度"）
    ctrl_x = (start_x + target_x) / 2 + random.randint(-120, 120)
    ctrl_y = (start_y + target_y) / 2 + random.randint(-80, 80)
    control = (ctrl_x, ctrl_y)

    steps = max(20, int(duration * 60))
    for i in range(steps + 1):
        _check_stop()
        t = i / steps
        # 缓入缓出（ease in-out）
        t_eased = t * t * (3 - 2 * t)
        x, y = _bezier_point(t_eased, (start_x, start_y), control, (target_x, target_y))
        # 接近目标时加入轻微抖动
        jitter = max(0, (1 - t) * 3)
        x += random.uniform(-jitter, jitter)
        y += random.uniform(-jitter, jitter)
        pyautogui.moveTo(int(x), int(y), _pause=False)
        time.sleep(duration / steps)


def human_click(x: int = None, y: int = None, button='left', double=False):
    """移动到目标位置后点击，可选双击"""
    _check_stop()
    if x is not None and y is not None:
        human_move(x, y)
    time.sleep(random.uniform(0.05, 0.15))
    if double:
        pyautogui.doubleClick(button=button)
    else:
        pyautogui.click(button=button)


def human_scroll(clicks: int = None, direction: str = None):
    """
    随机滚动。
    clicks: 滚动量（默认随机 3~12）
    direction: 'up' / 'down'（默认随机）
    """
    _check_stop()
    if clicks is None:
        clicks = random.randint(3, 12)
    if direction is None:
        direction = random.choice(['up', 'down', 'down', 'down'])  # 偏向向下（阅读习惯）
    delta = clicks if direction == 'up' else -clicks
    pyautogui.scroll(delta)


# ─────────────────────────────────────────────
# 键盘仿真
# ─────────────────────────────────────────────

def human_type(text: str, use_clipboard: bool = True):
    """
    模拟真人打字。
    use_clipboard=True 时通过剪贴板粘贴（解决中文输入问题）。
    use_clipboard=False 时逐字符输入（适合英文/数字，有随机错误）。
    """
    _check_stop()

    if use_clipboard:
        # 中文内容：先写入剪贴板再粘贴
        pyperclip.copy(text)
        time.sleep(random.uniform(0.1, 0.3))
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(random.uniform(0.2, 0.5))
        return

    # 英文/数字：逐字符模拟，带随机错误
    for i, char in enumerate(text):
        _check_stop()

        # 偶发性错字（每15个字有10%概率）
        if i > 0 and i % 15 == 0 and random.random() < 0.10:
            # 多打一个随机字符再退格
            typo = random.choice('qwertyuiop')
            pyautogui.typewrite(typo, interval=0)
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.press('backspace')
            time.sleep(random.uniform(0.05, 0.15))

        pyautogui.typewrite(char, interval=0)
        time.sleep(random.uniform(0.05, 0.18))

        # 每句话后停顿（逗号、句号）
        if char in '，。,. ':
            time.sleep(random.uniform(0.3, 1.5))


def human_type_then_clear(text: str):
    """打字然后清空（用于微信/钉钉输入框，防止误发）"""
    _check_stop()
    human_type(text)
    time.sleep(random.uniform(0.5, 1.5))
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')


# ─────────────────────────────────────────────
# 停顿管理
# ─────────────────────────────────────────────

def short_pause(min_s=1.0, max_s=4.0):
    """短停顿：窗口内操作间隙"""
    _check_stop()
    duration = random.uniform(min_s, max_s)
    _interruptible_sleep(duration)


def medium_pause(min_s=5.0, max_s=20.0):
    """中停顿：阅读/思考"""
    _check_stop()
    duration = random.uniform(min_s, max_s)
    _interruptible_sleep(duration)


def long_pause(min_s=30.0, max_s=120.0):
    """长停顿：接电话/喝水（低概率触发）"""
    _check_stop()
    duration = random.uniform(min_s, max_s)
    _interruptible_sleep(duration)


def _interruptible_sleep(duration: float, chunk: float = 0.3):
    """可中断的 sleep，每个 chunk 秒检查一次 stop_event"""
    elapsed = 0.0
    while elapsed < duration:
        if is_stopped():
            raise InterruptedError("Boss key triggered during sleep.")
        sleep_time = min(chunk, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time


def maybe_long_pause(probability: float = 0.02):
    """以给定概率触发长停顿（模拟接电话）"""
    if random.random() < probability:
        long_pause()
