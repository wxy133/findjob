@echo off
chcp 65001 >nul
title 米菲跑路 - 一键打包 EXE
echo ================================================================
echo    🐰  米菲跑路 - 一键打包成独立 EXE
echo ================================================================
echo.

echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    %%v

echo.
echo [2/6] 安装/更新依赖包...
pip install -r requirements.txt
pip install --upgrade pyinstaller Pillow
if errorlevel 1 (
    echo ⚠️  部分依赖安装可能失败，继续尝试打包...
)

echo.
echo [3/6] 生成米菲素材 (ICO / 圆形头像 / 横幅)...
if exist "assets\mifei_original.jpg" (
    python tools\make_mifei_assets.py
) else (
    echo ❌ 找不到 assets\mifei_original.jpg，请先放入米菲原图
    pause
    exit /b 1
)
if errorlevel 1 (
    echo ❌ 素材生成失败
    pause
    exit /b 1
)

echo.
echo [4/6] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "米菲跑路.spec" del /q "米菲跑路.spec"

echo.
echo [5/6] 开始打包单文件 EXE（含米菲图标），请耐心等待...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "米菲跑路" ^
    --icon "assets\app.ico" ^
    --add-data "assets\app.ico;assets" ^
    --add-data "assets\logo_circle.png;assets" ^
    --add-data "assets\header_banner_final.png;assets" ^
    --hidden-import tkinterdnd2 ^
    --hidden-import tkinterdnd2.tkdnd ^
    --hidden-import pdfplumber ^
    --hidden-import docx ^
    --hidden-import docx.oxml.ns ^
    --hidden-import docx.opc.constants ^
    --hidden-import selenium ^
    --hidden-import webdriver_manager ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --collect-all tkinterdnd2 ^
    --collect-submodules pdfplumber ^
    --collect-submodules docx ^
    main.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！请查看上方错误信息
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    ✅ 打包完成！
echo    可执行文件: dist\米菲跑路.exe
echo    桌面图标: 已使用米菲 ICO（16/24/32/48/64/128/256 多尺寸）
echo ================================================================
echo.
echo 💡 使用提示:
echo    1. 首次运行会自动下载匹配版本的 ChromeDriver
echo    2. 请确保本机已安装 Chrome 浏览器
echo    3. 启动后先上传简历 → 启动浏览器 → 在浏览器扫码登录BOSS直聘 → 开始投递
echo.
pause
