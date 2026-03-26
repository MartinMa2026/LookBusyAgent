"""
main_window.py
Look-Busy Agent 主界面（tkinter）。
"""

import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from core.app_scanner import scan_available_apps
from core.hotkey_manager import HotkeyManager
from core.scheduler import Scheduler


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    with open(os.path.normpath(config_path), 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_boss_key(combo: str):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
    config_path = os.path.normpath(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['boss_key'] = combo
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎭 Look-Busy Agent")
        self.root.resizable(False, False)

        self.config = _load_config()
        self.hotkey_manager = HotkeyManager(self.config.get('boss_key', 'ctrl+shift+q'))
        self.scheduler: Scheduler = None
        self._running = False

        # 扫描到的软件
        self.available_apps = scan_available_apps()
        self._app_vars: dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self._setup_hotkey()

    # ────────────────────────────────────────────
    # UI 构建
    # ────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        root.configure(bg='#1e1e2e')
        pad = {'padx': 16, 'pady': 8}

        # ── 标题 ──
        title_frame = tk.Frame(root, bg='#1e1e2e')
        title_frame.pack(fill='x', **pad)
        tk.Label(
            title_frame, text="🎭 Look-Busy Agent",
            font=('Segoe UI', 16, 'bold'),
            bg='#1e1e2e', fg='#cdd6f4'
        ).pack(side='left')
        tk.Label(
            title_frame, text="摸鱼不焦虑",
            font=('Segoe UI', 9),
            bg='#1e1e2e', fg='#6c7086'
        ).pack(side='left', padx=8, pady=4)

        # ── 分割线 ──
        ttk.Separator(root, orient='horizontal').pack(fill='x', padx=16)

        # ── 任务描述 ──
        task_frame = tk.LabelFrame(
            root, text="  📝 今天在干什么？  ",
            font=('Segoe UI', 9), bg='#1e1e2e', fg='#a6adc8',
            bd=1, relief='groove'
        )
        task_frame.pack(fill='x', padx=16, pady=8)

        self.task_entry = tk.Entry(
            task_frame,
            font=('Segoe UI', 10),
            bg='#313244', fg='#cdd6f4',
            insertbackground='#cdd6f4',
            relief='flat', bd=4,
            width=38
        )
        self.task_entry.insert(0, "例：做Q1销售数据报告")
        self.task_entry.bind('<FocusIn>', self._clear_placeholder)
        self.task_entry.pack(padx=8, pady=8)

        # ── LLM 设置 ──
        llm_cfg = self.config.get('llm', {})
        llm_frame = tk.Frame(task_frame, bg='#1e1e2e')
        llm_frame.pack(fill='x', padx=8, pady=(0, 6))

        tk.Label(
            llm_frame, text="🤖 LLM API Key（可选）：",
            font=('Segoe UI', 8), bg='#1e1e2e', fg='#6c7086'
        ).pack(side='left')

        self.llm_key_var = tk.StringVar(value=llm_cfg.get('api_key', ''))
        llm_entry = tk.Entry(
            llm_frame, textvariable=self.llm_key_var,
            font=('Segoe UI', 8), bg='#313244', fg='#cdd6f4',
            insertbackground='#cdd6f4', relief='flat', bd=2,
            width=20, show='*'
        )
        llm_entry.pack(side='left', padx=4)

        self.llm_model_var = tk.StringVar(value=llm_cfg.get('model', 'gpt-4o-mini'))
        model_entry = tk.Entry(
            llm_frame, textvariable=self.llm_model_var,
            font=('Segoe UI', 8), bg='#313244', fg='#cdd6f4',
            insertbackground='#cdd6f4', relief='flat', bd=2, width=12
        )
        model_entry.pack(side='left', padx=2)

        # ── 软件选择 ──
        app_frame = tk.LabelFrame(
            root, text="  💻 选择要"工作"的软件  ",
            font=('Segoe UI', 9), bg='#1e1e2e', fg='#a6adc8',
            bd=1, relief='groove'
        )
        app_frame.pack(fill='x', padx=16, pady=4)

        # P0 区域
        tk.Label(
            app_frame, text="即时通讯 & 浏览器",
            font=('Segoe UI', 8, 'bold'), bg='#1e1e2e', fg='#89b4fa'
        ).pack(anchor='w', padx=8, pady=(6, 2))

        p0_frame = tk.Frame(app_frame, bg='#1e1e2e')
        p0_frame.pack(fill='x', padx=12, pady=2)
        self._add_app_checkboxes(p0_frame, priority=0)

        # P1 区域
        tk.Label(
            app_frame, text="办公套件",
            font=('Segoe UI', 8, 'bold'), bg='#1e1e2e', fg='#a6e3a1'
        ).pack(anchor='w', padx=8, pady=(8, 2))

        p1_frame = tk.Frame(app_frame, bg='#1e1e2e')
        p1_frame.pack(fill='x', padx=12, pady=(2, 8))
        self._add_app_checkboxes(p1_frame, priority=1)

        # ── 老板键 ──
        boss_frame = tk.LabelFrame(
            root, text="  🚨 老板键（再按一次恢复）  ",
            font=('Segoe UI', 9), bg='#1e1e2e', fg='#a6adc8',
            bd=1, relief='groove'
        )
        boss_frame.pack(fill='x', padx=16, pady=8)

        inner = tk.Frame(boss_frame, bg='#1e1e2e')
        inner.pack(padx=8, pady=6)

        self.boss_key_var = tk.StringVar(value=self.config.get('boss_key', 'ctrl+shift+q'))
        boss_entry = tk.Entry(
            inner, textvariable=self.boss_key_var,
            font=('Segoe UI', 10, 'bold'),
            bg='#45475a', fg='#f38ba8',
            insertbackground='white',
            relief='flat', bd=4, width=18
        )
        boss_entry.pack(side='left', padx=(0, 8))
        tk.Button(
            inner, text="保存",
            font=('Segoe UI', 9),
            bg='#313244', fg='#cdd6f4',
            relief='flat', bd=0, padx=8, pady=3,
            cursor='hand2',
            command=self._save_boss_key
        ).pack(side='left')

        # ── 状态条 ──
        self.status_var = tk.StringVar(value="准备就绪 ✨")
        tk.Label(
            root, textvariable=self.status_var,
            font=('Segoe UI', 9), bg='#1e1e2e', fg='#6c7086'
        ).pack(pady=(0, 4))

        # ── 启动按钮 ──
        self.start_btn = tk.Button(
            root,
            text="🚀  开始摸鱼",
            font=('Segoe UI', 12, 'bold'),
            bg='#89b4fa', fg='#1e1e2e',
            relief='flat', bd=0,
            padx=20, pady=10,
            cursor='hand2',
            activebackground='#74c7ec',
            command=self._toggle_simulation
        )
        self.start_btn.pack(fill='x', padx=16, pady=(4, 16))

    def _add_app_checkboxes(self, parent: tk.Frame, priority: int):
        """生成指定优先级的软件勾选框"""
        col = 0
        for app_name, info in self.available_apps.items():
            if info['priority'] != priority:
                continue
            var = tk.BooleanVar(value=info['available'])
            self._app_vars[app_name] = var

            status_text = " 🟢" if info['running'] else (" ✅" if info['available'] else " ❌")
            cb = tk.Checkbutton(
                parent,
                text=f"{info['icon']} {app_name}{status_text}",
                variable=var,
                state='normal' if info['available'] else 'disabled',
                font=('Segoe UI', 9),
                bg='#1e1e2e', fg='#cdd6f4',
                selectcolor='#313244',
                activebackground='#1e1e2e',
                relief='flat', bd=0
            )
            cb.grid(row=0, column=col, padx=6, pady=2, sticky='w')
            col += 1

    # ────────────────────────────────────────────
    # 控制逻辑
    # ────────────────────────────────────────────

    def _clear_placeholder(self, event):
        if self.task_entry.get() == "例：做Q1销售数据报告":
            self.task_entry.delete(0, 'end')

    def _save_boss_key(self):
        combo = self.boss_key_var.get().strip()
        if not combo:
            return
        _save_boss_key(combo)
        self.hotkey_manager.set_combo(combo)
        self.status_var.set(f"老板键已更新：{combo}")

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
        selected = [app for app, var in self._app_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("提示", "请至少选择一个软件！")
            return

        task_desc = self.task_entry.get()
        if task_desc == "例：做Q1销售数据报告":
            task_desc = ""

        # 更新 LLM 配置到文件
        self._sync_llm_config()

        self._running = True
        self.hotkey_manager.stop_event.clear()

        self.scheduler = Scheduler(
            selected_apps=selected,
            task_description=task_desc,
            stop_event=self.hotkey_manager.get_stop_event()
        )
        self.scheduler.start()

        self.start_btn.config(text="⏹  停止摸鱼", bg='#f38ba8', fg='#1e1e2e')
        apps_str = "、".join(selected)
        self.status_var.set(f"正在模拟：{apps_str} | 老板键: {self.hotkey_manager.combo}")

    def _stop_simulation(self):
        self._running = False
        if self.scheduler:
            self.scheduler.stop()
        self.start_btn.config(text="🚀  开始摸鱼", bg='#89b4fa', fg='#1e1e2e')
        self.status_var.set("已停止 ✋")

    def _on_boss_arrives(self):
        """老板键触发→暂停"""
        self.root.after(0, self._update_ui_paused)

    def _on_resume(self):
        """再次按老板键→恢复"""
        self.root.after(0, self._update_ui_resumed)

    def _update_ui_paused(self):
        self.status_var.set("⚠️ 已暂停（再按老板键恢复）")
        self.start_btn.config(text="▶  继续摸鱼", bg='#f9e2af', fg='#1e1e2e')

    def _update_ui_resumed(self):
        self.status_var.set(f"继续模拟... | 老板键: {self.hotkey_manager.combo}")
        self.start_btn.config(text="⏹  停止摸鱼", bg='#f38ba8', fg='#1e1e2e')

    def _sync_llm_config(self):
        """将 UI 中的 LLM 设置同步到配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_tasks.json')
        config_path = os.path.normpath(config_path)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['llm']['api_key'] = self.llm_key_var.get().strip()
            data['llm']['model'] = self.llm_model_var.get().strip() or 'gpt-4o-mini'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._stop_simulation()
        self.hotkey_manager.stop()
        self.root.destroy()
