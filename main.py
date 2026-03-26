"""
main.py
Look-Busy Agent 程序入口。
"""

import sys
import os

# 将项目根目录加入 Python 路径（兼容 PyInstaller --onefile 打包）
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    from ui.main_window import MainWindow
    app = MainWindow()
    app.run()


if __name__ == '__main__':
    main()
