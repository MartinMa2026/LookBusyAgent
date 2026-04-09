"""
registry_v2.py
Dynamic adapter registry used by the app at runtime.
"""

import importlib
import inspect
import pkgutil

from adapters.base_adapter import BaseAdapter

# Keep enabled built-in adapters discoverable for PyInstaller.
import adapters.browser
import adapters.excel
import adapters.wps
import adapters.word


_ADAPTERS = {}
_METAS = {}
_INITIALIZED = False
_DISABLED_MODULES = {"wechat", "wxwork"}


def init_registry():
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    import adapters

    for _, name, _ in pkgutil.iter_modules(adapters.__path__):
        if name in {"base_adapter", "registry", "registry_v2"} or name in _DISABLED_MODULES:
            continue

        try:
            module = importlib.import_module(f"adapters.{name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, BaseAdapter) or obj is BaseAdapter:
                    continue
                if not hasattr(obj, "META"):
                    continue

                names = obj.META.get("names", [])
                if isinstance(names, str):
                    names = [names]

                for app_name in names:
                    _ADAPTERS[app_name] = obj
                    _METAS[app_name] = {
                        "icon": obj.META.get("icon", "🧩"),
                        "processes": obj.META.get("processes", []),
                        "priority": obj.META.get("priority", 1),
                    }
        except Exception as e:
            print(f"[Registry] Failed to load adapters/{name}: {e}")


def get_all_app_metas():
    init_registry()
    return _METAS


def get_adapter_class(app_name):
    init_registry()
    return _ADAPTERS.get(app_name)
