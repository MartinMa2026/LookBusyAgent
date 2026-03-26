"""
behavior_engine.py  (v3 - 热火朝天版)
- 鼠标更快（0.06~0.25s）
- 停顿大幅缩短
- 流式打字速度提升（中文每字更快）
- 真正的"忙碌感"：短暂休息后立刻继续
"""

import time
import random
import threading
import pyautogui
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ── 全局停止信号 ────────────────────────────────────────────

_stop_event = threading.Event()


def set_stop_event(event: threading.Event):
    global _stop_event
    _stop_event = event


def is_stopped() -> bool:
    return _stop_event.is_set()


def _check_stop():
    if is_stopped():
        raise InterruptedError("Boss key triggered.")


# ── 鼠标仿真 ────────────────────────────────────────────────

def _bezier_point(t, p0, p1, p2):
    return (
        (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1],
    )


def human_move(target_x: int, target_y: int, duration: float = None):
    """贝塞尔曲线移动，热火朝天模式默认 0.06~0.25s。"""
    _check_stop()
    if duration is None:
        duration = random.uniform(0.06, 0.25)

    start_x, start_y = pyautogui.position()
    ctrl_x = (start_x + target_x) / 2 + random.randint(-40, 40)
    ctrl_y = (start_y + target_y) / 2 + random.randint(-25, 25)
    control = (ctrl_x, ctrl_y)

    steps = max(8, int(duration * 60))
    for i in range(steps + 1):
        _check_stop()
        t = i / steps
        t_eased = t * t * (3 - 2 * t)
        x, y = _bezier_point(t_eased, (start_x, start_y), control, (target_x, target_y))
        x += random.uniform(-1, 1)
        y += random.uniform(-1, 1)
        pyautogui.moveTo(int(x), int(y), _pause=False)
        time.sleep(duration / steps)


def human_click(x: int = None, y: int = None, button='left', double=False):
    _check_stop()
    if x is not None and y is not None:
        human_move(x, y)
    time.sleep(random.uniform(0.02, 0.06))
    if double:
        pyautogui.doubleClick(button=button)
    else:
        pyautogui.click(button=button)


def human_scroll(clicks: int = None, direction: str = None):
    _check_stop()
    if clicks is None:
        clicks = random.randint(2, 8)
    if direction is None:
        direction = random.choice(['up', 'down', 'down', 'down'])
    delta = clicks if direction == 'up' else -clicks
    # 注意：Windows 下传统系统滚动步幅基准通常是 120
    pyautogui.scroll(delta * 120)


def anti_sleep_jitter():
    """防休眠的微小鼠标抖动，几乎不可察觉"""
    _check_stop()
    x, y = pyautogui.position()
    pyautogui.moveTo(int(x) + random.randint(-3, 3), int(y) + random.randint(-3, 3), 0.1)
    time.sleep(0.1)
    pyautogui.moveTo(x, y, 0.1)


def dismiss_notification_popup():
    """模拟关闭系统右下角的弹窗通知（如微信、邮件提醒）"""
    _check_stop()
    screen_width, screen_height = pyautogui.size()
    # 移动到右下角通知区域的关闭按钮大致位置 (向左大约 10-40 像素，向上大约 30-80 像素)
    target_x = screen_width - random.randint(10, 40)
    target_y = screen_height - random.randint(30, 80)
    
    human_move(target_x, target_y, duration=0.3)
    time.sleep(random.uniform(0.1, 0.4))
    human_click()
    time.sleep(random.uniform(0.1, 0.3))
    # 随机移回屏幕中央附近
    human_move(screen_width // 2 + random.randint(-200, 200), screen_height // 2 + random.randint(-200, 200), duration=0.4)


# ── 流式打字（核心优化）──────────────────────────────────────

def human_type(text: str, use_clipboard: bool = False):
    """
    流式打字增强版：不再逐字敲击引发系统输入法弹窗截断，
    而是将文本切分为 2~6 个字的“短语块”，逐块复制粘贴，
    既有“一段一段往外蹦”的连贯真人感，又能彻底规避输入法冲突。
    """
    _check_stop()
    if not text:
        return

    # 随机切割片断
    chunks = []
    idx = 0
    while idx < len(text):
        chunk_size = random.randint(2, 6)
        chunks.append(text[idx:idx + chunk_size])
        idx += chunk_size

    for chunk in chunks:
        _check_stop()
        pyperclip.copy(chunk)
        pyautogui.hotkey('ctrl', 'v')
        
        # 块之间正常停顿
        time.sleep(random.uniform(0.1, 0.3))

        # 3% 概率"停顿思考" 0.3~0.8s
        if random.random() < 0.03:
            time.sleep(random.uniform(0.3, 0.8))

        # 标点后轻微停顿
        if chunk[-1] in '，。,.!！?？；;':
            time.sleep(random.uniform(0.15, 0.4))


def human_type_burst(text: str):
    """快速打字（大块输出，几乎不停顿），模拟熟练打字员黏贴或连打。"""
    _check_stop()
    if not text:
        return
    
    chunks = []
    idx = 0
    while idx < len(text):
        chunk_size = random.randint(5, 12)
        chunks.append(text[idx:idx + chunk_size])
        idx += chunk_size

    for chunk in chunks:
        _check_stop()
        pyperclip.copy(chunk)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(random.uniform(0.05, 0.15))


def human_type_then_clear(text: str):
    _check_stop()
    human_type(text)
    time.sleep(random.uniform(0.2, 0.5))
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.05)
    pyautogui.press('delete')


# ── 停顿管理（热火朝天版）────────────────────────────────────

def short_pause(min_s=0.15, max_s=0.8):
    """短停顿：操作间隙（0.15~0.8s）"""
    _check_stop()
    _interruptible_sleep(random.uniform(min_s, max_s))


def medium_pause(min_s=0.8, max_s=3.0):
    """中停顿：切换/阅读（0.8~3s）"""
    _check_stop()
    _interruptible_sleep(random.uniform(min_s, max_s))


def long_pause(min_s=5.0, max_s=15.0):
    """长停顿：极低概率（接电话）"""
    _check_stop()
    _interruptible_sleep(random.uniform(min_s, max_s))


def _interruptible_sleep(duration: float, chunk: float = 0.15):
    elapsed = 0.0
    while elapsed < duration:
        if is_stopped():
            raise InterruptedError("Boss key triggered during sleep.")
        sleep_time = min(chunk, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time


def maybe_long_pause(probability: float = 0.002):
    if random.random() < probability:
        long_pause()
