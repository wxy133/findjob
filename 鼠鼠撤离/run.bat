@echo off
chcp 65001 >nul
title 🐹 鼠鼠撤离

REM -------- 检查 Python --------
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM -------- 检查依赖 --------
python -c "import tkinterdnd2, pdfplumber, docx, selenium, webdriver_manager, PIL" >nul 2>&1
if errorlevel 1 (
    echo 📦 检测到缺少依赖包，正在自动安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ❌ 依赖安装失败，请检查网络或手动执行:
        echo       pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM -------- 首次使用自动生成 ICO / 头像 / 横幅素材 --------
if not exist "assets\app.ico" (
    if exist "assets\app_icon.jpg" (
        echo 🎨 首次启动，正在生成鼠鼠图标和素材...
        python tools\make_assets.py
    )
)

echo.
echo 🐹  鼠鼠撤离 · BOSS直聘自动投递  启动中...
echo      "不干了！提起小水桶去投新简历～"
echo.
python main.py
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出，按任意键关闭...
    pause >nul
)
