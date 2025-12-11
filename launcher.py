# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import urllib.request
import json
from datetime import datetime

# ================= 配置区域 =================
# 如果你有 GitHub 或服务器，把 raw 链接填在这里
# 例如: "https://raw.githubusercontent.com/yourname/mp4-gps/main/"
UPDATE_URL_BASE = "" 
LOCAL_VERSION_FILE = "version.md"
MAIN_SCRIPT = "main.py"
# ===========================================

def log(msg):
    print(f"[启动器] {msg}")

def check_python_version():
    if sys.version_info < (3, 6):
        log("错误: 需要 Python 3.6 或更高版本。")
        input("按回车键退出...")
        sys.exit(1)

def check_tkinter():
    log("检查 GUI 库 (Tkinter)...")
    try:
        import tkinter
        return True
    except ImportError:
        log("❌ 未检测到 Tkinter！")
        if sys.platform.startswith("linux"):
            print("\n请在终端运行以下命令进行安装：")
            print("sudo apt update && sudo apt install python3-tk\n")
        elif sys.platform == "win32":
            print("\n请重新安装 Python，并勾选 'tcl/tk and IDLE'。\n")
        
        input("安装完成后，请重新运行。按回车键退出...")
        sys.exit(1)

def check_ffmpeg():
    log("检查 FFmpeg 环境...")
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log("✅ FFmpeg 已安装")
    except FileNotFoundError:
        log("⚠️ 未检测到 FFmpeg。")
        log("虽然脚本可以运行，但对于某些特殊视频 (GoPro/DJI)，GPS 解析能力会下降。")
        log("建议安装 FFmpeg 以获得最佳体验。")
        print("-" * 30)

def check_for_updates():
    if not UPDATE_URL_BASE:
        return # 未配置更新地址，跳过

    log("正在检查更新...")
    try:
        # 1. 读取本地版本
        current_ver = "0.0"
        if os.path.exists(LOCAL_VERSION_FILE):
            with open(LOCAL_VERSION_FILE, "r") as f:
                current_ver = f.read().strip()

        # 2. 获取远程版本
        remote_ver_url = UPDATE_URL_BASE + LOCAL_VERSION_FILE
        with urllib.request.urlopen(remote_ver_url, timeout=5) as response:
            remote_ver = response.read().decode('utf-8').strip()

        # 3. 比较
        if remote_ver > current_ver:
            log(f"发现新版本: v{remote_ver} (当前: v{current_ver})")
            log("正在自动下载更新...")
            
            # 下载新的 main.py
            main_url = UPDATE_URL_BASE + MAIN_SCRIPT
            with urllib.request.urlopen(main_url) as response, open(MAIN_SCRIPT, 'wb') as out_file:
                out_file.write(response.read())
            
            # 更新本地版本号
            with open(LOCAL_VERSION_FILE, "w") as f:
                f.write(remote_ver)
                
            log("✅ 更新成功！")
        else:
            log("当前已是最新版本。")

    except Exception as e:
        log(f"⚠️ 更新检查失败: {e}")

def start_main():
    log("正在启动主程序...")
    print("-" * 30)
    # 使用当前 Python 解释器启动 main.py
    try:
        subprocess.call([sys.executable, MAIN_SCRIPT])
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    print("="*40)
    print("   MP4 GPS 查看器 - 智能启动环境")
    print("="*40)
    
    check_python_version()
    check_tkinter()
    check_ffmpeg()
    check_for_updates()
    
    start_main()
