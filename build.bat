@echo off
chcp 65001
echo NeuroSongSpider 自动打包脚本
echo ==============================

echo 1. 生成版本信息文件...
python generate_version_info.py
if %ERRORLEVEL% neq 0 (
    echo 生成版本信息文件失败！
    pause
    exit /b 1
)

echo.
echo 2. 开始PyInstaller打包...
pyinstaller main.spec
if %ERRORLEVEL% neq 0 (
    echo PyInstaller打包失败！
    pause
    exit /b 1
)

echo.
echo 3. 验证启动动画资源...
if exist "dist\NeuroSongSpider\assets\main_loading\f0.png" (
    echo ✅ 启动动画资源已成功打包
) else (
    echo ⚠️  警告: 启动动画资源未找到
)

echo.
echo 4. 打包完成！
echo 可执行文件位置: dist\NeuroSongSpider\NeuroSongSpider.exe
echo.
pause
