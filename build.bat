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
echo 2. 同步语言文件从 data\i18n 到 src\assets\i18n...
if not exist "src\assets\i18n\" mkdir "src\assets\i18n\"
xcopy /Y /Q "data\i18n\*.properties" "src\assets\i18n\"
if %ERRORLEVEL% neq 0 (
    echo 同步语言文件失败！
    pause
    exit /b 1
)
echo ✅ 语言文件同步完成

echo.
echo 3. 清理旧的构建文件...
if exist "dist\NeuroSongSpider\" (
    rmdir /s /q "dist\NeuroSongSpider\"
    echo ✅ 已清理旧的构建文件
)

echo.
echo 4. 开始PyInstaller打包...
pyinstaller main.spec --clean
if %ERRORLEVEL% neq 0 (
    echo PyInstaller打包失败！
    pause
    exit /b 1
)

echo.
echo 5. 验证必要资源...
if exist "dist\NeuroSongSpider\_internal\assets\main_loading\f0.png" (
    echo ✅ 启动动画资源已成功打包
) else (
    echo ⚠️  警告: 启动动画资源未找到
)

if exist "dist\NeuroSongSpider\_internal\ffmpeg\bin\ffmpeg.exe" (
    echo ✅ FFmpeg已成功打包
) else (
    echo ⚠️  警告: FFmpeg未找到
)

if exist "dist\NeuroSongSpider\_internal\data\i18n\zh_CN.properties" (
    echo ✅ 语言文件已成功打包
) else (
    echo ⚠️  警告: 语言文件未找到
)

echo.
echo 6. 创建运行时必要的目录...
if not exist "dist\NeuroSongSpider\data" mkdir "dist\NeuroSongSpider\data"
if not exist "dist\NeuroSongSpider\data\music" mkdir "dist\NeuroSongSpider\data\music"
if not exist "dist\NeuroSongSpider\data\video" mkdir "dist\NeuroSongSpider\data\video"
if not exist "dist\NeuroSongSpider\data\cache" mkdir "dist\NeuroSongSpider\data\cache"
if not exist "dist\NeuroSongSpider\data\custom_songs" mkdir "dist\NeuroSongSpider\data\custom_songs"
echo ✅ 运行时目录已创建

echo.
echo 7. 打包完成！
echo 可执行文件位置: dist\NeuroSongSpider\NeuroSongSpider.exe
echo.
pause
