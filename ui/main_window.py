from core.utils import get_config_path, get_resource_path
"""
main_window.py  —  Look-Busy Agent  主界面（重构版）
aesthetic: 「黑市操盘手」terminal-hacker
新增：多语言支持与摸鱼图标
"""

import json
import math
import os
import tkinter as tk
from tkinter import messagebox

from core.app_scanner import scan_available_apps
from core.hotkey_manager import HotkeyManager
from core.scheduler import Scheduler
from ui.i18n import TR, SLACKER_ICON_B64

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
    config_path = get_config_path()
    with open(os.path.normpath(config_path), 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_config_obj(data):
    config_path = os.path.normpath(
        get_config_path())
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _save_boss_key(combo: str):
    data = _load_config()
    data['boss_key'] = combo
    _save_config_obj(data)


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


def make_glitch_header(parent, t_main, t_sub, w, h):
    cv = tk.Canvas(parent, width=w, height=h, bg=C['bg'], highlightthickness=0)
    scan_state = [0]

    def draw_base():
        title_id = cv.create_text(w // 2, h // 2 - 8, text=t_main(),
                       font=('Courier New', 14, 'bold'),
                       fill=C['green'], anchor='center', tags='title')
        sub_id = cv.create_text(w // 2, h // 2 + 10,
                       text=t_sub(),
                       font=('Courier New', 7), fill=C['subtext'],
                       anchor='center', tags='sub')
        cv._ids = (title_id, sub_id)

    def animate():
        cv.delete('scan')
        y = scan_state[0] % h
        cv.create_line(0, y, w, y, fill=C['scan'],
                       stipple='gray25', width=1, tags='scan')
        scan_state[0] = (scan_state[0] + 1) % h
        cv.after(30, animate)

    def update_texts():
        if hasattr(cv, '_ids'):
            title_id, sub_id = cv._ids
            cv.itemconfig(title_id, text=t_main())
            cv.itemconfig(sub_id, text=t_sub())

    cv.after(1, draw_base)
    cv.after(20, animate)
    cv.update_texts = update_texts
    return cv


def make_neon_button(parent, t_func, command=None, color=None, w=200, h=38):
    color = color or C['green']
    state = {'text': t_func(), 'color': color, 'hover': False, 't_func': t_func}
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

    def configure_text(new_text=None, color=None):
        if new_text is not None:
            state['text'] = new_text
        if color: state['color'] = color
        _draw(glow=state['hover'])

    def update_lang():
        # Update text via t_func if not overridden manually by explicit set
        state['text'] = state['t_func']()
        _draw(glow=state['hover'])

    cv.configure_text = configure_text
    cv.update_lang = update_lang
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

        # 滑块
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

        self.weight_var.trace_add('write', self._on_var_write)

    def _on_var_write(self, *_):
        if self._clamping:
            return
        self._clamping = True
        try:
            cap = self._on_change(self)
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
        self._clamping = True
        self.weight_var.set(v)
        self._clamping = False

    def is_enabled(self):
        return self.enabled_var.get() and self.available



# ── 主窗口 ──────────────────────────────────────────────────

class MainWindow:

    def __init__(self):
        self.config        = _load_config()
        self.lang          = self.config.get('language', 'ZH')
        self._updaters     = []
        
        self.root = tk.Tk()
        self.root.title(self._t('title'))
        self.root.resizable(False, False)
        self.root.configure(bg=C['bg'])
        
        # 设置 Windows 任务栏应用独立 ID
        import ctypes
        try:
            myappid = 'lookbusy.agent.version.2'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # 应用像素化摸鱼图标
        try:
            icon_path = os.path.normpath(get_resource_path(os.path.join('assets', 'icon.ico')))
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
            else:
                icon_img = tk.PhotoImage(data=SLACKER_ICON_B64)
                self.root.iconphoto(True, icon_img)
        except Exception as e:
            print("Failed to set icon:", e)

        self.hotkey_manager = HotkeyManager(self.config.get('boss_key', 'ctrl+shift+q'))
        self.scheduler     = None
        self._running      = False

        self.available_apps = scan_available_apps()
        self._weight_rows = []

        self._build_ui()
        self._setup_hotkey()
        self._init_weights()
        self._animate_status_dot()

    def _t(self, key):
        return TR.get(self.lang, TR['ZH']).get(key, key)

    def _app_hint_text(self):
        hints = {
            'ZH': '请打开你摸鱼要用的软件、并全屏最大化。',
            'EN': 'Please open the software you want to use and maximize it fullscreen.',
            'JA': '摸魚に使うソフトを開き、全画面で最大化してください。',
        }
        return hints.get(self.lang, hints['ZH'])

    def _add_lbl(self, parent, key, **kwargs):
        lbl = tk.Label(parent, text=self._t(key), **kwargs)
        self._updaters.append(lambda: lbl.config(text=self._t(key)))
        return lbl

    def _set_lang(self, new_lang):
        old_lang = self.lang
        self.lang = new_lang
        self.config['language'] = new_lang
        _save_config_obj(self.config)
        self.root.title(self._t('title'))
        # 刷新所有绑定
        for fn in self._updaters:
            fn()
        # 处理未被 updater 包装的部件
        self._header.update_texts()
        if not self._running:
            self.start_btn.update_lang()
            self.status_var.set(self._t('status_ready'))
            
        # 更新 entry 的占位符
        from ui.i18n import TR
        for entry, pkey in getattr(self, '_placeholders', []):
            old_ph = TR.get(old_lang, {}).get(pkey, '')
            current_val = entry.get()
            if current_val == '' or current_val == old_ph:
                entry.delete(0, 'end')
                entry.insert(0, self._t(pkey))
                entry.config(fg=C['subtext'])
                
        # 更新颜色
        for btn, cur_lang in self._lang_btns:
            btn.config(fg=C['green'] if cur_lang == self.lang else C['dim'])

    # ── UI 构建 ─────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        W = 500

        # Top Bar & Lang switch
        top_bar = tk.Frame(root, bg=C['green'], height=1)
        top_bar.pack(fill='x')
        
        # 语言切换行
        lang_frame = tk.Frame(root, bg=C['bg'])
        lang_frame.pack(fill='x', anchor='e', padx=12, pady=2)
        
        self._lang_btns = []
        for lcode, label in [('ZH', '[ZH]'), ('EN', '[EN]'), ('JA', '[JA]')]:
            fg = C['green'] if lcode == self.lang else C['dim']
            btn = tk.Label(lang_frame, text=label, font=FONT_TINY, bg=C['bg'], fg=fg, cursor='hand2')
            btn.pack(side='right', padx=2)
            btn.bind('<Button-1>', lambda e, lc=lcode: self._set_lang(lc))
            self._lang_btns.append((btn, lcode))

        # Title
        header = tk.Frame(root, bg=C['bg'])
        header.pack(fill='x')
        self._header = make_glitch_header(header, lambda: self._t('header_main'), lambda: self._t('header_sub'), w=W, h=40)
        self._header.pack()
        tk.Frame(root, bg=C['dim'], height=1).pack(fill='x', padx=12)

        # ── 身份 & 任务 ──────────────────────────────────────
        self._section_label(root, 'sec_identity', C['green'])

        id_rf = make_rounded_frame(root, w=W - 24, h=160, border_color=C['border'], accent=C['green'])
        id_rf.pack(padx=12, pady=(2, 8))
        id_inner = get_inner(id_rf)

        self._placeholders = []
        
        # 身份行
        row1 = tk.Frame(id_inner, bg=C['panel'])
        row1.pack(fill='x', pady=(2, 1))
        self._add_lbl(row1, 'lbl_iam', font=FONT_SMALL, bg=C['panel'], fg=C['subtext']).pack(side='left')
        
        self.identity_entry = tk.Entry(
            row1, font=FONT_SMALL, bg=C['entry_bg'], fg=C['entry_fg'],
            insertbackground=C['green'], relief='flat', bd=0, width=36
        )
        self.identity_entry.pack(side='left', padx=4)
        self._setup_placeholder(self.identity_entry, 'ph_identity')

        # 任务行
        row2 = tk.Frame(id_inner, bg=C['panel'])
        row2.pack(fill='x', pady=(4, 1))
        self._add_lbl(row2, 'lbl_doing', font=FONT_SMALL, bg=C['panel'], fg=C['subtext']).pack(side='left')
        
        self.task_entry = tk.Entry(
            row2, font=FONT_SMALL, bg=C['entry_bg'], fg=C['entry_fg'],
            insertbackground=C['green'], relief='flat', bd=0, width=36
        )
        self.task_entry.pack(side='left', padx=4)
        self._setup_placeholder(self.task_entry, 'ph_task')

        # ── LLM 配置行 ─────────────────────────────────────
        llm_cfg = self.config.get('llm', {})

        # 第 1 行：AI Key
        row3 = tk.Frame(id_inner, bg=C['panel'])
        row3.pack(fill='x', pady=(4, 0))
        self._add_lbl(row3, 'lbl_api_key', font=FONT_TINY, bg=C['panel'], fg=C['subtext'], width=8).pack(side='left')
        
        self.llm_key_var = tk.StringVar(value=llm_cfg.get('api_key', ''))
        tk.Entry(row3, textvariable=self.llm_key_var,
                 font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                 insertbackground=C['amber'], relief='flat', bd=0,
                 width=35, show='*').pack(side='left', padx=4)
        self._add_lbl(row3, 'lbl_no_key', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left', padx=4)

        # 第 2 行：Base URL & Model
        row4 = tk.Frame(id_inner, bg=C['panel'])
        row4.pack(fill='x', pady=4)
        self._add_lbl(row4, 'lbl_api_url', font=FONT_TINY, bg=C['panel'], fg=C['subtext'], width=8).pack(side='left')
        
        self.llm_url_var = tk.StringVar(value=llm_cfg.get('base_url', ''))
        url_entry = tk.Entry(row4, textvariable=self.llm_url_var,
                             font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                             insertbackground=C['amber'], relief='flat', bd=0, width=28)
        url_entry.pack(side='left', padx=4)
        self._setup_placeholder(url_entry, 'ph_url', is_var=True, var=self.llm_url_var)

        self._add_lbl(row4, 'lbl_model', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left', padx=(4,0))
        
        self.llm_model_var = tk.StringVar(value=llm_cfg.get('model', 'gpt-4o-mini'))
        model_entry = tk.Entry(row4, textvariable=self.llm_model_var,
                               font=FONT_TINY, bg=C['entry_bg'], fg=C['amber'],
                               insertbackground=C['amber'], relief='flat', bd=0, width=15)
        model_entry.pack(side='left', padx=4)

        # 第 3 行：Test 按钮 & 状态
        row5 = tk.Frame(id_inner, bg=C['panel'])
        row5.pack(fill='x', pady=(0, 4))
        tk.Label(row5, text='', width=8, bg=C['panel']).pack(side='left')
        test_btn = self._add_lbl(row5, 'btn_test', font=FONT_TINY, bg=C['panel'], fg=C['blue'], cursor='hand2')
        test_btn.pack(side='left', padx=4)
        test_btn.bind('<Button-1>', lambda _: self._test_llm_connection())
        test_btn.bind('<Enter>', lambda _: test_btn.config(fg=C['white']))
        test_btn.bind('<Leave>', lambda _: test_btn.config(fg=C['blue']))
        
        self._llm_status_var = tk.StringVar(value='')
        self._llm_status_label = tk.Label(row5, textvariable=self._llm_status_var,
                                          font=FONT_TINY, bg=C['panel'], fg=C['green'], width=12, anchor='w')
        self._llm_status_label.pack(side='left')

        # ── 软件权重分配 ─────────────────────────────────────
        self._section_label(root, 'sec_workload', C['amber'])

        app_hint = tk.Label(
            root, text=self._app_hint_text(),
            font=FONT_TINY, bg=C['bg'], fg=C['amber'],
            justify='left', anchor='w'
        )
        app_hint.pack(fill='x', padx=14, pady=(0, 4))
        self._updaters.append(lambda: app_hint.config(text=self._app_hint_text()))

        n_apps = len(self.available_apps)
        apps_h = max(80, n_apps * 28 + 44)
        apps_rf = make_rounded_frame(root, w=W - 24, h=apps_h, border_color=C['border2'], accent=C['amber'])
        apps_rf.pack(padx=12, pady=(2, 8))
        apps_inner = get_inner(apps_rf)

        total_row = tk.Frame(apps_inner, bg=C['panel'])
        total_row.pack(fill='x', pady=(0, 4))
        self._add_lbl(total_row, 'lbl_allocated', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left')
        
        self._total_var = tk.StringVar(value='0 / 100')
        self._total_label = tk.Label(total_row, textvariable=self._total_var, font=('Courier New', 9, 'bold'), bg=C['panel'], fg=C['amber'])
        self._total_label.pack(side='left')

        self._add_lbl(total_row, 'lbl_click_eq', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left', padx=(8, 0))
        eq_btn = self._add_lbl(total_row, 'btn_eq', font=FONT_TINY, bg=C['panel'], fg=C['green'], cursor='hand2')
        eq_btn.pack(side='left', padx=4)
        eq_btn.bind('<Button-1>', lambda _: self._auto_distribute())
        eq_btn.bind('<Enter>', lambda _: eq_btn.config(fg=C['white']))
        eq_btn.bind('<Leave>', lambda _: eq_btn.config(fg=C['green']))

        for app_name, info in self.available_apps.items():
            wr = WeightRow(apps_inner, app_name, info['icon'], info['available'], self._on_weight_change)
            self._weight_rows.append(wr)


        # ── 老板键 ────────────────────────────────────────────
        self._section_label(root, 'sec_panic', C['red'])
        boss_rf = make_rounded_frame(root, w=W - 24, h=56, border_color=C['red'], accent=C['red'])
        boss_rf.pack(padx=12, pady=(2, 8))
        boss_inner = get_inner(boss_rf)
        boss_row = tk.Frame(boss_inner, bg=C['panel'])
        boss_row.pack(anchor='w', pady=4)

        self._add_lbl(boss_row, 'lbl_combo', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left')
        self.boss_key_var = tk.StringVar(value=self.config.get('boss_key', 'ctrl+shift+q'))
        tk.Entry(boss_row, textvariable=self.boss_key_var,
                 font=('Courier New', 9, 'bold'),
                 bg=C['entry_bg'], fg=C['red'],
                 insertbackground=C['red'], relief='flat', bd=0, width=18).pack(side='left', padx=(4, 8))

        save_btn = self._add_lbl(boss_row, 'btn_save', font=FONT_TINY, bg=C['panel'], fg=C['red'], cursor='hand2')
        save_btn.pack(side='left')
        save_btn.bind('<Button-1>', lambda _: self._save_boss_key())
        save_btn.bind('<Enter>', lambda _: save_btn.config(fg=C['white']))
        save_btn.bind('<Leave>', lambda _: save_btn.config(fg=C['red']))
        self._add_lbl(boss_row, 'lbl_resume_tip', font=FONT_TINY, bg=C['panel'], fg=C['subtext']).pack(side='left')

        # ── 状态 + 主按钮 ─────────────────────────────────────
        tk.Frame(root, bg=C['dim'], height=1).pack(fill='x', padx=12, pady=(0, 6))

        status_frame = tk.Frame(root, bg=C['bg'])
        status_frame.pack(fill='x', padx=14, pady=(0, 4))
        self._dot_canvas = tk.Canvas(status_frame, width=10, height=10, bg=C['bg'], highlightthickness=0)
        self._dot_canvas.pack(side='left', pady=2)
        self._dot_id = self._dot_canvas.create_oval(2, 2, 8, 8, fill=C['dim'], outline='')

        self.status_var = tk.StringVar(value=self._t('status_ready'))
        tk.Label(status_frame, textvariable=self.status_var, font=FONT_TINY, bg=C['bg'], fg=C['subtext']).pack(side='left', padx=6)

        self.start_btn = make_neon_button(
            root, t_func=lambda: self._t('btn_start'),
            command=self._toggle_simulation,
            color=C['green'], w=W - 24, h=42
        )
        self.start_btn.pack(padx=12, pady=(2, 14))

        tk.Frame(root, bg=C['green'], height=1).pack(fill='x')
        tk.Label(root, text='LOOK-BUSY-AGENT  //  open source  //  MIT', font=FONT_TINY, bg=C['bg'], fg=C['dim']).pack(pady=3)

        # 初始填充 placeholder
        for fn in self._updaters:
            fn()

    # ── 辅助 ────────────────────────────────────────────────

    def _section_label(self, parent, t_key, color):
        row = tk.Frame(parent, bg=C['bg'])
        row.pack(fill='x', padx=14, pady=(6, 2))
        self._add_lbl(row, t_key, font=FONT_LABEL, bg=C['bg'], fg=color).pack(side='left')

    def _setup_placeholder(self, entry, pkey, is_var=False, var=None):
        self._placeholders.append((entry, pkey))

        def on_focus_in(_):
            if is_var:
                if var.get() == self._t(pkey):
                    var.set('')
                    entry.config(fg=C['amber' if pkey=='ph_url' else 'entry_fg'])
            else:
                if entry.get() == self._t(pkey):
                    entry.delete(0, 'end')
                    entry.config(fg=C['entry_fg'])

        def on_focus_out(_):
            if is_var:
                if not var.get():
                    var.set(self._t(pkey))
                    entry.config(fg=C['subtext'])
            else:
                if not entry.get():
                    entry.insert(0, self._t(pkey))
                    entry.config(fg=C['subtext'])

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        # init call
        on_focus_out(None)

    # ── 权重逻辑 ─────────────────────────────────────────────

    def _init_weights(self):
        self._auto_distribute()

    def _auto_distribute(self):
        active = [wr for wr in self._weight_rows if wr.is_enabled()]
        if not active:
            self._update_total()
            return
        base = 100 // len(active)
        remainder = 100 - base * len(active)
        for i, wr in enumerate(active):
            wr.set_weight(base + (1 if i < remainder else 0))
        for wr in self._weight_rows:
            if not wr.is_enabled():
                wr.set_weight(0)
        self._update_total()

    def _on_weight_change(self, changed_row = None) -> int:
        if changed_row is not None:
            others_sum = sum(wr.get_weight() for wr in self._weight_rows if wr is not changed_row)
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

    def _get_weights(self) -> dict:
        return {wr.app_name: wr.get_weight() for wr in self._weight_rows if wr.get_weight() > 0}

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

    def _setup_hotkey(self):
        self.hotkey_manager.on_boss_arrives(self._on_boss_arrives)
        self.hotkey_manager.on_resume(self._on_resume)
        self.hotkey_manager.start()

    def _toggle_simulation(self):
        if getattr(self.hotkey_manager, '_paused', False):
            self.hotkey_manager._resume()
        elif not self._running:
            self._start_simulation()
        else:
            self._stop_simulation()

    def _start_simulation(self):
        weights = self._get_weights()
        if not weights:
            messagebox.showwarning('Warning', self._t('msg_no_app'))
            return
        if sum(weights.values()) == 0:
            messagebox.showwarning('Warning', self._t('msg_zero_weight'))
            return

        identity = self.identity_entry.get()
        if identity == self._t('ph_identity'):
            identity = ''
        task_desc = self.task_entry.get()
        if task_desc == self._t('ph_task'):
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

        self.start_btn.configure_text(self._t('btn_stop'), color=C['red'])
        apps_str = ' / '.join(f'{k}({v})' for k, v in weights.items())
        self.status_var.set(f'ACTIVE  ▶  {apps_str}')

    def _stop_simulation(self):
        self._running = False
        if self.scheduler:
            self.scheduler.stop()
        self.start_btn.configure_text(self._t('btn_start'), color=C['green'])
        self.status_var.set(self._t('status_stopped'))

    def _on_boss_arrives(self):
        self.root.after(0, self._update_ui_paused)

    def _on_resume(self):
        self.root.after(0, self._update_ui_resumed)

    def _update_ui_paused(self):
        self.status_var.set(self._t('status_paused'))
        self.start_btn.configure_text(self._t('btn_resume'), color=C['amber'])

    def _update_ui_resumed(self):
        self.status_var.set(f"RESUMED ▶ COMBO: {self.hotkey_manager.combo}")
        self.start_btn.configure_text(self._t('btn_stop'), color=C['red'])
        
        if getattr(self, 'scheduler', None):
            if not getattr(self.scheduler, '_thread', None) or not self.scheduler._thread.is_alive():
                self._start_simulation()

    def _sync_llm_config(self):
        data = _load_config()
        url = self.llm_url_var.get().strip()
        if url == self._t('ph_url'):
            url = ''
            
        data.setdefault('llm', {})
        data['llm']['api_key']  = self.llm_key_var.get().strip()
        data['llm']['base_url'] = url
        data['llm']['model']    = self.llm_model_var.get().strip() or 'gpt-4o-mini'
        _save_config_obj(data)

    def _test_llm_connection(self):
        import threading, urllib.request, urllib.error

        key   = self.llm_key_var.get().strip()
        url   = self.llm_url_var.get().strip()
        model = self.llm_model_var.get().strip() or 'gpt-4o-mini'
        
        if url == self._t('ph_url'):
            url = ''
        if not key:
            self._llm_status_var.set(self._t('t_no_key'))
            self._llm_status_label.config(fg=C['red'])
            return

        self._sync_llm_config()

        self._llm_status_var.set(self._t('t_testing'))
        self._llm_status_label.config(fg=C['subtext'])

        def _do_test():
            try:
                cfg = _load_config().get('llm', {})
                base_url = cfg.get('base_url', 'https://api.openai.com').rstrip('/')
                url = f"{base_url}/v1/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "hello"}],
                    "max_tokens": 5,
                }).encode('utf-8')
                req = urllib.request.Request(
                    url, data=payload,
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    resp.read()
                self.root.after(0, lambda: (
                    self._llm_status_var.set(self._t('t_ok')),
                    self._llm_status_label.config(fg=C['green']),
                    self._trigger_llm_warmup()
                ))
            except urllib.error.HTTPError as e:
                msg = {401: self._t('t_err_key'), 429: self._t('t_err_limit')}.get(e.code, f"✗ HTTP {e.code}")
                self.root.after(0, lambda m=msg: (
                    self._llm_status_var.set(m),
                    self._llm_status_label.config(fg=C['red'])
                ))
            except Exception as e:
                self.root.after(0, lambda: (
                    self._llm_status_var.set(self._t('t_err_net')),
                    self._llm_status_label.config(fg=C['red'])
                ))

        threading.Thread(target=_do_test, daemon=True).start()

    def _trigger_llm_warmup(self):
        try:
            from core.llm_generator import LLMGenerator
            task_desc = self.task_entry.get().strip() or "处理工作文档"
            identity = self.identity_entry.get().strip() or "普通员工"
            LLMGenerator(identity=identity, task_description=task_desc)
        except Exception:
            pass

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
