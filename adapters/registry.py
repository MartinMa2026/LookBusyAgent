"""
registry.py
动态扫描与注册所有的 BaseAdapter 适配器插件。
支持即插即用（Plug-and-play）架构。
"""

import sys
import importlib
import pkgutil
import inspect
from adapters.base_adapter import BaseAdapter

# 强制 Pyinstaller 收集所有的内置适配器（也可以在打包时用 --collect-submodules adapters）
# 防止打包后反射不到这些内建组件
import adapters.wechat
import adapters.browser
import adapters.excel
import adapters.word
import adapters.coder
import adapters.reader

_ADAPTERS = {}
_METAS = {}
_INITIALIZED = False

def init_registry():
    global _INITIALIZED
    if _INITIALIZED: return
    _INITIALIZED = True

    import adapters
    for _, name, _ in pkgutil.iter_modules(adapters.__path__):
        if name in ('base_adapter', 'registry'):
            continue
        try:
            module = importlib.import_module(f'adapters.{name}')
            for obj_name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAdapter) and obj is not BaseAdapter:
                    if hasattr(obj, 'META'):
                        names = obj.META.get('names', [])
                        # 防止有些写了单名字而不是列表
                        if isinstance(names, str):
                            names = [names]
                            
                        for app_name in names:
                            _ADAPTERS[app_name] = obj
                            
                            # 生成适配器元数据以供 UI 使用
                            _METAS[app_name] = {
                                'icon': obj.META.get('icon', '🖥️'),
                                'processes': obj.META.get('processes', []),
                                'priority': obj.META.get('priority', 1)
                            }
        except Exception as e:
            print(f"[Registry] 自动加载插件 adapters/{name} 失败: {e}")

def get_all_app_metas():
    """给应用扫描器调用：获取所有注册被支持的 APP 数据"""
    init_registry()
    return _METAS

def get_adapter_class(app_name):
    """给执行调度器调用：获取指定 APP 对应的类控制器"""
    init_registry()
    return _ADAPTERS.get(app_name)
