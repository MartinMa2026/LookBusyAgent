"""
main_window.py  —  Look-Busy Agent  主界面（重构版）
aesthetic: 「黑市操盘手」terminal-hacker
新增：身份输入 / 权重分配滑块 / 实时权重显示
"""

import json
import math
import os
import tkinter as tk
from tkinter import messagebox

from core.app_scanner import scan_available_apps
from core.hotkey_manager import HotkeyManager
from core.scheduler import Scheduler

# ── 调色板 ──────────────────────────────────────────────────
C = {
    'bg':        '#0a0a0f',
    'panel':     '#0f0f1a',
    'border':    '#1a2a1a',
    'border2':   '#2a1a0a',
    'green':     '#00ff7f',
    'amber':     '#ffaa00',
    'red':       '#ff3860',
    'dim':       '#334433',
    'text':      '#c8ffc8',
    'subtext':   '#557755',
    'entry_bg':  '#050510',
    'entry_fg':  '#00ff7f',
    'scan':      '#00ff44',
    'white':     '#e8ffe8',
    'blue':      '#4fc3f7',
}

FONT_MONO  = ('Courier New', 10, 'bold')
FONT_TITLE = ('Courier New', 15, 'bold')
FONT_LABEL = ('Courier New', 9)
FONT_BTN   = ('Courier New', 11, 'bold')
FONT_SMALL = ('Courier New', 9)
FONT_TINY  = ('Courier New', 8)


# ── 工具函数 ─────────────────────────────────────────────────

def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    with open(os.path.normpath(config_path), 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_boss_key(combo: str):
    config_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['boss_key'] = combo
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Canvas 工厂函数 ─────────────────────────────────────────

def make_rounded_frame(parent, w, h, radius=8, bg=None, border_color=None, accent=None):
    bg = bg or C['panel']
    bc = border_color or C['border']
    cv = tk.Canvas(parent, width=w, height=h, bg=C['bg'], highlightthickness=0)

    def _draw():
        r = radius
        cv.create_polygon(
            r, 0, w - r, 0, w, r,
            w, h - r, w - r, h, r, h, 0, h - r, 0, r,
            smooth=True, fill=bg, outline=bc, width=1
        )
        if accent:
            cv.create_rectangle(0, r, 3, h - r, fill=accent, outline='')
        offset = 14 if accent else 8
        inner = tk.Frame(cv, bg=bg)
        cv.create_window(offset, 8, anchor='nw', window=inner,
                         width=w - offset - 8, height=h - 16)
        cv._inner = inner
    cv.after(1, _draw)
    return cv


def get_inner(cv):
    cv.update()
    return cv._inner


def make_glitch_header(parent, text, w, h):
    cv = tk.Canvas(parent, width=w, height=h, bg=C['bg'], highlightthickness=0)
    scan_state = [0]

    def draw_base():
        cv.create_text(w // 2, h // 2 - 8, text=text,
                       font=('Courier New', 14, 'bold'),
                       fill=C['green'], anchor='center', tags='title')
        cv.create_text(w // 2, h // 2 + 10,
                       text='— 摸鱼不焦虑  |  LOOK BUSY AGENT —',
                       font=('Courier New', 7), fill=C['subtext'],
                       anchor='center', tags='sub')

    def animate():
        cv.delete('scan')
        y = scan_state[0] % h
        cv.create_line(0, y, w, y, fill=C['scan'],
                       stipple='gray25', width=1, tags='scan')
        scan_state[0] = (scan_state[0] + 1) % h
        cv.after(30, animate)

    cv.after(1, draw_base)
    cv.after(20, animate)
    return cv


def make_neon_button(parent, text, command=None, color=None, w=200, h=38):
    color = color or C['green']
    state = {'text': text, 'color': color, 'hover': False}
    cv = tk.Canvas(parent, width=w, height=h, bg=C['bg'], highlightthickness=0)

    def _draw(glow=False):
        cv.delete('all')
        r = 6
        fill   = state['color'] if glow else C['panel']
        text_c = C['bg'] if glow else state['color']
        cv.create_polygon(
            r, 0, w - r, 0, w, r,
            w, h - r, w - r, h, r, h, 0, h - r, 0, r,
            smooth=True, fill=fill, outline=state['color'],
            width=2 if glow else 1
        )
        cv.create_text(w // 2, h // 2, text=state['text'],
                       font=FONT_BTN, fill=text_c, anchor='center')

    def on_enter(_):
        state['hover'] = True; _draw(glow=True); cv.config(cursor='hand2')

    def on_leave(_):
        state['hover'] = False; _draw(glow=False); cv.config(cursor='')

    def on_click(_):
        if command: command()

    cv.bind('<Enter>',    on_enter)
    cv.bind('<Leave>',    on_leave)
    cv.bind('<Button-1>', on_click)
    cv.after(1, lambda: _draw(glow=False))

    def configure_text(new_text, color=None):
        state['text'] = new_text
        if color: state['color'] = color
        _draw(glow=state['hover'])

    cv.configure_text = configure_text
    return cv


# ── 权重滑块组件 ─────────────────────────────────────────────

class WeightRow:
    """单个 App 的权重行：图标+名称 + 滑块 + 数值显示"""

    def __init__(self, parent, app_name, icon, available, on_change):
        self.app_name   = app_name
        self.available  = available
        self._on_change = on_change
        self._clamping  = False   # 防止 trace 递归

        self.enabled_var = tk.BooleanVar(value=available)
        self.weight_var  = tk.IntVar(value=0)

        bg = C['panel']
        row = tk.Frame(parent, bg=bg)
        row.pack(fill='x', padx=4, pady=2)

        # 勾选框
        self.cb = tk.Checkbutton(
            row, variable=self.enabled_var,
            bg=bg, fg=C['green'], selectcolor=C['entry_bg'],
            activebackground=bg, relief='flat', bd=0,
            state='normal' if available else 'disabled',
            command=self._toggle
        )
        self.cb.pack(side='left')

        # 名称标签
        state_sym = '●' if available else '✕'
        fg = C['green'] if available else C['dim']
        tk.Label(row, text=f'{icon} {app_name} {state_sym}',
                 font=FONT_SMALL, bg=bg, fg=fg, width=12, anchor='w'
                 ).pack(side='left', padx=(0, 6))

        # 滑块（不通过 command 做 clamp，交给 trace 处理）
        self.slider = tk.Scale(
            row, variable=self.weight_var,
            from_=0, to=100, orient='horizontal',
            bg=bg, fg=C['amber'], troughcolor=C['entry_bg'],
            highlightthickness=0, bd=0, sliderlength=12,
            showvalue=False, length=160,
            state='normal' if available else 'disabled'
        )
        self.slider.pack(side='left')

        # 数值标签
        self.val_label = tk.Label(row, textvariable=self.weight_var,
                                  font=FONT_SMALL, bg=bg, fg=C['amber'], width=3)
        self.val_label.pack(side='left', padx=(4, 0))

        # 注册 trace：每次 weight_var 写入都强制 clamp
        self.weight_var.trace_add('write', self._on_var_write)

    def _on_var_write(self, *_):
        """变量被写入时立即 clamp，确保总和不超 100。"""
        if self._clamping:
            return
        self._clamping = True
        try:
            cap = self._on_change(self)   # 返回允许的上限
            cur = self.weight_var.get()
            if cur > cap:
                self.weight_var.set(cap)
        except Exception:
            pass
        finally:
            self._clamping = False

    def _toggle(self):
        if not self.enabled_var.get():
            self._clamping = True
            self.weight_var.set(0)
            self._clamping = False
        self._on_change(self)

    def get_weight(self):
        if not self.enabled_var.get():
            return 0
        return self.weight_var.get()

    def set_weight(self, v):
        self._clamping = True   # 均分时不触发 trace clamp
        self.weight_var.set(v)
        self._clamping = False

    def is_enabled(self):
        return self.enabled_var.get() and self.available



# ── 主窗口 ──────────────────────────────────────────────────

class MainWindow:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('LOOK-BUSY AGENT  //  v2.0')
        self.root.resizable(False, False)
        self.root.configure(bg=C['bg'])

        self.config        = _load_config()
        self.hotkey_manager = HotkeyManager(self.config.get('boss_key', 'ctrl+shift+q'))
        self.scheduler     = None
        self._running      = False

        self.available_apps = scan_available_apps()
        self._weight_rows: list[WeightRow] = []

        self._build_ui()
        self._setup_hotkey()
        self._init_weights()
        self._animate_status_dot()

    # ── UI 构建 ─────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        W = 500

        # ── 顶线 + 标题 ──
        tk.Frame(root, bg=C['green'], height=1).pack(fill='x')
        header = tk.Frame(root, bg=C['bg'])
        header.pack(fill='x')
        make_glitch_header(header, '[ L O O K - B U S Y  A G E N T ]', w=W, h=52).pack()
        tk.Frame(root, bg=C['dim'], height=1).pack(fill='x', padx=12)

        # ── 身份 & 任务 ──────────────────────────────────────
        self._section_label(root, '◆ IDENTITY  /  你是谁？今天干什么？', C['green'])

        id_rf = make_rounded_frame(root, w=W - 24, h=160,
                                   border_color=C['border'], accent=C['green'])
        id_rf.pack(padx=12, pady=(2, 8))
        id_inner = get_inner(id_rf)

        # 身份行
        row1 = tk.Frame(id_inner, bg=C['panel'])
        row1.pack(fill='x', pady=(2, 1))
        tk.Label(row1, text='我是：', font=FONT_SMALL,
                 bg=C['panel'], fg=C['subtext']).pack(side='left')
        self.identity_entry = tk.Entry(
            row1, font=FONT_SMALL,
            bg=C['entry_bg'], fg=C['entry_fg'],
            insertbackground=C['green'], relief='flat', bd=0, width=36
        )
        self.identity_entry.insert(0, '例：产品经理 / 数据分析师')
        self.identity_entry.bind('<FocusIn>', lambda _: self._clear_ph(self.identity_entry, '例：产品经理 / 数据分析师'))
        self.identity_entry.pack(side='left', padx=4)

        # 任务行
        row2 = tk.Frame(id_inner, bg=C['panel'])
        row2.pack(fill='x', pady=(4, 1))
        tk.Label(row2, text='在做：', font=FONT_SMALL,
                 bg=C['panel'], fg=C['subtext']).pack(side='left')
        self.task_entry = tk.Entry(
            row2, font=FONT_SMALL,
            bg=C['entry_bg'], fg=C['entry_fg'],
            insertbackground=C['green'], relief='flat', bd=0, width=36
        )
        self.task_entry.insert(0, '例：Q1 销售数据报告')
        self.task_entry.bind('<FocusIn>', lambda _: self._clear_ph(self.task_entry, '例：Q1 销售数据报告'))
        self.task_entry.pack(side='left', padx=4)

        # ── LLM 配置行（拆为两行） ─────────────────────────────────────
        llm_cfg = self.config.get('llm', {})

        # 第 1 行：AI Key
        row3 = tk.Frame(id_inner, bg=C['panel'])
        row3.pack(fill='x', pady=(4, 0))
        tk.Label(row3, text='AI Key:', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext'], width=8).pack(side='left')
        self.llm_key_var = tk.StringVar(value=llm_cfg.get('api_key', ''))
        tk.Entry(row3, textvariable=self.llm_key_var,
                 font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                 insertbackground=C['amber'], relief='flat', bd=0,
                 width=35, show='*').pack(side='left', padx=4)
        tk.Label(row3, text='(留空则使用内置降级模板)', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left', padx=4)

        # 第 2 行：Base URL & Model
        row4 = tk.Frame(id_inner, bg=C['panel'])
        row4.pack(fill='x', pady=4)
        tk.Label(row4, text='API URL:', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext'], width=8).pack(side='left')
        
        self.llm_url_var = tk.StringVar(value=llm_cfg.get('base_url', ''))
        url_entry = tk.Entry(row4, textvariable=self.llm_url_var,
                             font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                             insertbackground=C['amber'], relief='flat', bd=0, width=28)
        
        if not self.llm_url_var.get():
            self.llm_url_var.set('默认: https://api.openai.com')
            url_entry.config(fg=C['subtext'])
            
        def _on_url_focus(e):
            if self.llm_url_var.get() == '默认: https://api.openai.com':
                self.llm_url_var.set('')
                url_entry.config(fg=C['amber'])
                
        url_entry.bind('<FocusIn>', _on_url_focus)
        url_entry.pack(side='left', padx=4)

        tk.Label(row4, text='Model:', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left', padx=(4,0))
        
        self.llm_model_var = tk.StringVar(value=llm_cfg.get('model', 'gpt-4o-mini'))
        model_entry = tk.Entry(row4, textvariable=self.llm_model_var,
                               font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                               insertbackground=C['amber'], relief='flat', bd=0, width=15)
        model_entry.pack(side='left', padx=4)

        # 第 3 行：Test 按钮 & 状态
        row5 = tk.Frame(id_inner, bg=C['panel'])
        row5.pack(fill='x', pady=(0, 4))
        tk.Label(row5, text='', width=8, bg=C['panel']).pack(side='left') # 占位对齐
        test_btn = tk.Label(row5, text='[ TEST ]', font=FONT_TINY,
                            bg=C['panel'], fg=C['blue'], cursor='hand2')
        test_btn.pack(side='left', padx=4)
        test_btn.bind('<Button-1>', lambda _: self._test_llm_connection())
        test_btn.bind('<Enter>', lambda _: test_btn.config(fg=C['white']))
        test_btn.bind('<Leave>', lambda _: test_btn.config(fg=C['blue']))
        
        # 测试状态标签
        self._llm_status_var = tk.StringVar(value='')
        self._llm_status_label = tk.Label(row5, textvariable=self._llm_status_var,
                                          font=FONT_TINY, bg=C['panel'], fg=C['green'], width=12, anchor='w')
        self._llm_status_label.pack(side='left')

        # ── 软件权重分配 ─────────────────────────────────────
        self._section_label(root, '◆ WORKLOAD  /  操作比重分配（总100份）', C['amber'])

        # 计算框高度：每个 app 约 28px + header 20px + 总分显示 22px
        n_apps = len(self.available_apps)
        apps_h = max(80, n_apps * 28 + 44)
        apps_rf = make_rounded_frame(root, w=W - 24, h=apps_h,
                                     border_color=C['border2'], accent=C['amber'])
        apps_rf.pack(padx=12, pady=(2, 8))
        apps_inner = get_inner(apps_rf)

        # 总份额进度条文字
        total_row = tk.Frame(apps_inner, bg=C['panel'])
        total_row.pack(fill='x', pady=(0, 4))
        tk.Label(total_row, text='已分配：', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left')
        self._total_var = tk.StringVar(value='0 / 100')
        self._total_label = tk.Label(total_row, textvariable=self._total_var,
                                     font=('Courier New', 9, 'bold'),
                                     bg=C['panel'], fg=C['amber'])
        self._total_label.pack(side='left')

        tk.Label(total_row, text='  [ 点击「均分」→ ]', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left', padx=(8, 0))
        eq_btn = tk.Label(total_row, text='均分', font=FONT_TINY,
                          bg=C['panel'], fg=C['green'], cursor='hand2')
        eq_btn.pack(side='left', padx=4)
        eq_btn.bind('<Button-1>', lambda _: self._auto_distribute())
        eq_btn.bind('<Enter>', lambda _: eq_btn.config(fg=C['white']))
        eq_btn.bind('<Leave>', lambda _: eq_btn.config(fg=C['green']))

        # 各 App 权重行
        for app_name, info in self.available_apps.items():
            wr = WeightRow(apps_inner, app_name, info['icon'],
                           info['available'], self._on_weight_change)
            self._weight_rows.append(wr)

        # ── 老板键 ────────────────────────────────────────────
        self._section_label(root, '◆ PANIC KEY  /  老板键', C['red'])
        boss_rf = make_rounded_frame(root, w=W - 24, h=56,
                                     border_color=C['red'], accent=C['red'])
        boss_rf.pack(padx=12, pady=(2, 8))
        boss_inner = get_inner(boss_rf)
        boss_row = tk.Frame(boss_inner, bg=C['panel'])
        boss_row.pack(anchor='w', pady=4)

        tk.Label(boss_row, text='COMBO:', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left')
        self.boss_key_var = tk.StringVar(value=self.config.get('boss_key', 'ctrl+shift+q'))
        tk.Entry(boss_row, textvariable=self.boss_key_var,
                 font=('Courier New', 9, 'bold'),
                 bg=C['entry_bg'], fg=C['red'],
                 insertbackground=C['red'],
                 relief='flat', bd=0, width=18).pack(side='left', padx=(4, 8))

        save_btn = tk.Label(boss_row, text='[ SAVE ]', font=FONT_TINY,
                            bg=C['panel'], fg=C['red'], cursor='hand2')
        save_btn.pack(side='left')
        save_btn.bind('<Button-1>', lambda _: self._save_boss_key())
        save_btn.bind('<Enter>', lambda _: save_btn.config(fg=C['white']))
        save_btn.bind('<Leave>', lambda _: save_btn.config(fg=C['red']))
        tk.Label(boss_row, text='  再按恢复', font=FONT_TINY,
                 bg=C['panel'], fg=C['subtext']).pack(side='left')

        # ── 状态 + 主按钮 ─────────────────────────────────────
        tk.Frame(root, bg=C['dim'], height=1).pack(fill='x', padx=12, pady=(0, 6))

        status_frame = tk.Frame(root, bg=C['bg'])
        status_frame.pack(fill='x', padx=14, pady=(0, 4))
        self._dot_canvas = tk.Canvas(status_frame, width=10, height=10,
                                     bg=C['bg'], highlightthickness=0)
        self._dot_canvas.pack(side='left', pady=2)
        self._dot_id = self._dot_canvas.create_oval(2, 2, 8, 8, fill=C['dim'], outline='')

        self.status_var = tk.StringVar(value='READY  //  准备就绪')
        tk.Label(status_frame, textvariable=self.status_var,
                 font=FONT_TINY, bg=C['bg'], fg=C['subtext']).pack(side='left', padx=6)

        self.start_btn = make_neon_button(
            root, text='▶  START FISHING  //  开始摸鱼',
            command=self._toggle_simulation,
            color=C['green'], w=W - 24, h=42
        )
        self.start_btn.pack(padx=12, pady=(2, 14))

        tk.Frame(root, bg=C['green'], height=1).pack(fill='x')
        tk.Label(root, text='LOOK-BUSY-AGENT  //  open source  //  MIT',
                 font=FONT_TINY, bg=C['bg'], fg=C['dim']).pack(pady=3)

    # ── 辅助 ────────────────────────────────────────────────

    def _section_label(self, parent, text, color):
        row = tk.Frame(parent, bg=C['bg'])
        row.pack(fill='x', padx=14, pady=(6, 2))
        tk.Label(row, text=text, font=FONT_LABEL, bg=C['bg'], fg=color).pack(side='left')

    def _clear_ph(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, 'end')

    # ── 权重逻辑 ─────────────────────────────────────────────

    def _init_weights(self):
        """启动时给可用 App 均分 100 份"""
        self._auto_distribute()

    def _auto_distribute(self):
        """将 100 份均分给所有已勾选的可用 App"""
        active = [wr for wr in self._weight_rows if wr.is_enabled()]
        if not active:
            self._update_total()
            return
        base = 100 // len(active)
        remainder = 100 - base * len(active)
        for i, wr in enumerate(active):
            wr.set_weight(base + (1 if i < remainder else 0))
        # 禁用的设为 0
        for wr in self._weight_rows:
            if not wr.is_enabled():
                wr.set_weight(0)
        self._update_total()

    def _on_weight_change(self, changed_row: 'WeightRow' = None) -> int:
        """返回 changed_row 允许的最大值（= 100 - 其他行之和），并刷新总量显示。"""
        if changed_row is not None:
            others_sum = sum(
                wr.get_weight() for wr in self._weight_rows if wr is not changed_row
            )
            cap = max(0, 100 - others_sum)
        else:
            cap = 100
        self._update_total()
        return cap

    def _update_total(self):
        total = sum(wr.get_weight() for wr in self._weight_rows)
        color = C['green'] if total == 100 else (C['amber'] if total < 100 else C['red'])
        self._total_var.set(f'{total} / 100')
        self._total_label.config(fg=color)

    def _get_weights(self) -> dict[str, int]:
        """返回 {app_name: weight} 仅含正权重"""
        return {wr.app_name: wr.get_weight()
                for wr in self._weight_rows
                if wr.get_weight() > 0}

    # ── 状态点脉冲 ───────────────────────────────────────────

    def _animate_status_dot(self):
        color = C['green'] if not self._running else C['amber']
        t = getattr(self, '_pulse_t', 0)
        bright = color if (t // 8) % 2 == 0 else C['dim']
        self._dot_canvas.itemconfig(self._dot_id, fill=bright)
        self._pulse_t = t + 1
        self.root.after(80, self._animate_status_dot)

    # ── 控制逻辑 ─────────────────────────────────────────────

    def _save_boss_key(self):
        combo = self.boss_key_var.get().strip()
        if not combo:
            return
        _save_boss_key(combo)
        self.hotkey_manager.set_combo(combo)
        self.status_var.set(f'PANIC KEY UPDATED  //  {combo}')

    def _setup_hotkey(self):
        self.hotkey_manager.on_boss_arrives(self._on_boss_arrives)
        self.hotkey_manager.on_resume(self._on_resume)
        self.hotkey_manager.start()

    def _toggle_simulation(self):
        if not self._running:
            self._start_simulation()
        else:
            self._stop_simulation()

    def _start_simulation(self):
        weights = self._get_weights()
        if not weights:
            messagebox.showwarning('提示', '请至少给一个软件分配权重！')
            return
        if sum(weights.values()) == 0:
            messagebox.showwarning('提示', '权重总和为 0，请先分配比重！')
            return

        identity = self.identity_entry.get()
        if identity == '例：产品经理 / 数据分析师':
            identity = ''
        task_desc = self.task_entry.get()
        if task_desc == '例：Q1 销售数据报告':
            task_desc = ''
        full_desc = f'[{identity}] {task_desc}'.strip('[] ') if identity else task_desc

        self._sync_llm_config()
        self._running = True
        self.hotkey_manager.stop_event.clear()

        self.scheduler = Scheduler(
            app_weights=weights,
            task_description=full_desc,
            identity=identity,
            stop_event=self.hotkey_manager.get_stop_event()
        )
        self.scheduler.start()

        self.start_btn.configure_text('■  STOP FISHING  //  停止摸鱼', color=C['red'])
        apps_str = ' / '.join(f'{k}({v})' for k, v in weights.items())
        self.status_var.set(f'ACTIVE  ▶  {apps_str}')

    def _stop_simulation(self):
        self._running = False
        if self.scheduler:
            self.scheduler.stop()
        self.start_btn.configure_text('▶  START FISHING  //  开始摸鱼', color=C['green'])
        self.status_var.set('STOPPED  //  已停止')

    def _on_boss_arrives(self):
        self.root.after(0, self._update_ui_paused)

    def _on_resume(self):
        self.root.after(0, self._update_ui_resumed)

    def _update_ui_paused(self):
        self.status_var.set('⚠  PAUSED  //  老板来了！再按恢复')
        self.start_btn.configure_text('▶  RESUME  //  继续摸鱼', color=C['amber'])

    def _update_ui_resumed(self):
        self.status_var.set(f'RESUMED  ▶  老板键: {self.hotkey_manager.combo}')
        self.start_btn.configure_text('■  STOP FISHING  //  停止摸鱼', color=C['red'])

    def _sync_llm_config(self):
        config_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            url = self.llm_url_var.get().strip()
            if url == '默认: https://api.openai.com':
                url = ''
                
            data['llm']['api_key']  = self.llm_key_var.get().strip()
            data['llm']['base_url'] = url
            data['llm']['model']    = self.llm_model_var.get().strip() or 'gpt-4o-mini'
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _test_llm_connection(self):
        """后台测试 LLM API 连通性，结果显示在状态标签上。"""
        import threading, urllib.request, urllib.error

        key   = self.llm_key_var.get().strip()
        url   = self.llm_url_var.get().strip()
        model = self.llm_model_var.get().strip() or 'gpt-4o-mini'
        
        if url == '默认: https://api.openai.com':
            url = ''
        if not key:
            self._llm_status_var.set('✗ 无 Key')
            self._llm_status_label.config(fg=C['red'])
            return

        # 先保存
        self._sync_llm_config()

        # 显示"测试中"
        self._llm_status_var.set('… 测试中')
        self._llm_status_label.config(fg=C['subtext'])

        def _do_test():
            try:
                config_path = os.path.normpath(
                    os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json'))
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f).get('llm', {})
                base_url = cfg.get('base_url', 'https://api.openai.com').rstrip('/')
                url = f"{base_url}/v1/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "hello"}],
                    "max_tokens": 5,
                }).encode('utf-8')
                req = urllib.request.Request(
                    url, data=payload,
                    headers={'Content-Type': 'application/json',
                             'Authorization': f'Bearer {key}'}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    resp.read()
                # 成功
                self.root.after(0, lambda: (
                    self._llm_status_var.set('✓ 已连接'),
                    self._llm_status_label.config(fg=C['green']),
                    self._trigger_llm_warmup()
                ))
            except urllib.error.HTTPError as e:
                msg = {401: '✗ Key错误', 429: '✗ 超限额'}.get(e.code, f'✗ HTTP {e.code}')
                self.root.after(0, lambda m=msg: (
                    self._llm_status_var.set(m),
                    self._llm_status_label.config(fg=C['red'])
                ))
            except Exception as e:
                self.root.after(0, lambda: (
                    self._llm_status_var.set('✗ 网络错误'),
                    self._llm_status_label.config(fg=C['red'])
                ))

        threading.Thread(target=_do_test, daemon=True).start()

    def _trigger_llm_warmup(self):
        """测试连通性成功后，直接在后台开始预热 LLM 生成文案池，实现开始摸鱼即用"""
        try:
            from core.llm_generator import LLMGenerator
            task_desc = self.task_entry.get().strip() or "处理工作文档"
            identity = self.identity_entry.get().strip() or "普通员工"
            # 初始化即会触发内置的 `_warm_up()` 后台线程
            # 我们只需要抛出这个对象让它在后台默默工作即可，不保存实例也行
            LLMGenerator(identity=identity, task_description=task_desc)
            print("[UI] LLM 背景预热已触发...")
        except Exception as e:
            print(f"[UI] 触发预热失败: {e}")

    def run(self):
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.mainloop()

    def _on_close(self):
        try:
            self._stop_simulation()
            self.hotkey_manager.stop()
        except Exception:
            pass
        self.root.destroy()
