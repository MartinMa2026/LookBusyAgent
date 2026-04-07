from core.utils import get_config_path, get_resource_path
"""
app_scanner.py
扫描 Windows 系统中已安装和正在运行的已知办公软件。
"""

import json
import os
import sys
import psutil

# 尝试导入 winreg（仅 Windows 可用）
try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False


def _load_known_apps():
    """从适配器注册中心获取动态加载的软体元数据聚合"""
    from adapters.registry import get_all_app_metas
    return get_all_app_metas()


def _get_running_processes():
    """获取当前所有运行中的进程名（小写）"""
    running = set()
    try:
        for proc in psutil.process_iter(['name']):
            name = proc.info.get('name')
            if name:
                running.add(name.lower())
    except Exception:
        pass
    return running


def _get_installed_via_registry():
    """
    通过 Windows 注册表查询已安装软件。
    返回 DisplayName 集合（小写）。
    """
    installed = set()
    if not WINREG_AVAILABLE:
        return installed

    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]
    hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]

    for hive in hives:
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(hive, reg_path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                        installed.add(display_name.lower())
                        winreg.CloseKey(subkey)
                    except (OSError, FileNotFoundError):
                        continue
                winreg.CloseKey(key)
            except (OSError, FileNotFoundError):
                continue

    return installed


def scan_available_apps():
    """
    扫描系统中可用的已知软件。
    返回：
        dict[str, dict] — 软件名 → {icon, processes, priority, available, running}
    """
    known_apps = _load_known_apps()
    running_procs = _get_running_processes()

    result = {}
    for app_name, info in known_apps.items():
        processes = info.get('processes', [])
        is_running = any(p.lower() in running_procs for p in processes)

        result[app_name] = {
            'icon': info.get('icon', '🖥️'),
            'processes': processes,
            'priority': info.get('priority', 1),
            'available': True,   # 所有已知软件均显示，由用户自行勾选决定是否启用
            'running': is_running,
        }

    return result


if __name__ == '__main__':
    apps = scan_available_apps()
    print("=== 已检测到的软件 ===")
    for name, info in apps.items():
        status = "🟢 运行中" if info['running'] else ("✅ 已安装" if info['available'] else "❌ 未安装")
        print(f"  {info['icon']} {name}: {status}")
