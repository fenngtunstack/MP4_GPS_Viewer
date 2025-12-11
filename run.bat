@echo off
title MP4 GPS Project Launcher
echo Checking Python environment...

:: 检查 python 是否存在
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    echo Opening download page...
    start https://www.python.org/downloads/
    pause
    exit
)

:: 运行 Python 启动器
python launcher.py
pause
