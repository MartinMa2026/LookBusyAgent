import os
import sys
import subprocess

# Force utf-8 encoding for prints
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("🚀 准备打包 LookBusyAgent...")
    
    # 针对 Anaconda 环境的特殊处理：自动将 DLL 库注入至运行时 PATH，防止缺失 _ctypes / _tkinter
    library_bin = os.path.join(sys.prefix, "Library", "bin")
    if os.path.exists(library_bin):
        print("🐍 检测到特殊环境 (如 Conda)，正在自动修正 DLL 依赖安全路径...")
        bin_paths = [
            os.path.join(sys.prefix, "Library", "mingw-w64", "bin"),
            os.path.join(sys.prefix, "Library", "usr", "bin"),
            library_bin,
            os.path.join(sys.prefix, "Scripts"),
        ]
        
        # 预先将依赖路径挂在最前面
        current_path = os.environ.get("PATH", "")
        new_path = os.pathsep.join(p for p in bin_paths if os.path.exists(p)) + os.pathsep + current_path
        os.environ["PATH"] = new_path
        print("✅ 已配置 DLL 依赖动态注入安全策略")

    # 规范化 PyInstaller 的路径格式，适配跨系统分隔符
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon", "assets/icon.ico",
        "--add-data", f"config{os.pathsep}config",
        "--add-data", f"assets{os.pathsep}assets",
        "--collect-submodules", "adapters",
        "--exclude-module", "numpy",
        "--exclude-module", "IPython",
        "--exclude-module", "cv2",
        "--exclude-module", "PyQt5",
        "--exclude-module", "pandas",
        "main.py",
        "-n", "LookBusyAgent"
    ]
    
    print("📦 执行一键打包子进程...")
    try:
        subprocess.check_call(cmd, env=os.environ)
        print("\n==================================")
        print("🎉 打包大功告成！")
        print("✨ 可执行文件位于: dist/LookBusyAgent.exe")
        print("==================================")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包因错误退出，错误代码：{e.returncode}，请检查上方日志详情。")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
