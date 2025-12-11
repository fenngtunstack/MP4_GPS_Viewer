#!/bin/bash

echo "=== MP4 GPS Project Launcher ==="

# 检查 Python3
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 could not be found."
    echo "Please install python3 using your package manager."
    echo "Example: sudo apt install python3"
    read -p "Press Enter to exit..."
    exit
fi

# 检查 Tkinter (Linux特有的痛点)
python3 -c "import tkinter" &> /dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] 'tkinter' module is missing."
    echo "Attempting to install automatically (requires sudo)..."
    
    # 尝试检测包管理器并自动安装
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3-tk ffmpeg
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-tkinter ffmpeg
    else
        echo "[ERROR] Cannot identify package manager."
        echo "Please manually install 'python3-tk' and 'ffmpeg'."
    fi
fi

# 运行启动器
python3 launcher.py
