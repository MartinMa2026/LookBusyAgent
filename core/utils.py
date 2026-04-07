import os
import sys
import shutil

def get_base_path():
    """如果是打包后的环境，返回原始运行目录，否则返回当前所在的源码的根目录"""
    if getattr(sys, 'frozen', False):
        # pyinstaller 打包后的可执行文件所在的路径
        return os.path.dirname(sys.executable)
    # 未打包时，项目根目录为 core 的上一级
    return os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

def get_resource_path(relative_path):
    """获取静态资源（如图标、UI素材等，只读）的绝对路径"""
    if getattr(sys, 'frozen', False):
        # _MEIPASS 是 PyInstaller 解压静态资源的临时路径
        base_path = sys._MEIPASS
    else:
        base_path = get_base_path()
    return os.path.normpath(os.path.join(base_path, relative_path))

def _do_init_config(target_path):
    """如果外层没有配置，则从内置的 config/ 提取出默认模板复制过去"""
    template_path = get_resource_path(os.path.join('config', 'default_tasks.json'))
    if os.path.exists(template_path):
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(template_path, target_path)

def get_config_path():
    """获取持久化配置文件路径。打包版会在exe旁边加载/创建配置。"""
    if getattr(sys, 'frozen', False):
        # 绿色软件模式：同级目录下创建配置存放
        target_path = os.path.join(get_base_path(), 'lookbusy_config.json')
        if not os.path.exists(target_path):
            _do_init_config(target_path)
        return target_path
    
    # 源码模式：使用直接源码里的 config 目录
    return os.path.normpath(os.path.join(get_base_path(), 'config', 'default_tasks.json'))
