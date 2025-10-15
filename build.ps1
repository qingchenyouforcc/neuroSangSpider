# NeuroSongSpider 自动打包脚本
# PowerShell版本

Write-Host "NeuroSongSpider 自动打包脚本" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

Write-Host "1. 生成版本信息文件..." -ForegroundColor Yellow
$result = python generate_version_info.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "生成版本信息文件失败！" -ForegroundColor Red
    Read-Host "按任意键继续..."
    exit 1
}

Write-Host ""
Write-Host "2. 清理旧的构建文件..." -ForegroundColor Yellow
if (Test-Path "dist\NeuroSongSpider") {
    Remove-Item -Path "dist\NeuroSongSpider" -Recurse -Force
    Write-Host "✅ 已清理旧的构建文件" -ForegroundColor Green
}

Write-Host ""
Write-Host "3. 开始PyInstaller打包..." -ForegroundColor Yellow
$result = pyinstaller main.spec --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller打包失败！" -ForegroundColor Red
    Read-Host "按任意键继续..."
    exit 1
}

Write-Host ""
Write-Host "4. 验证必要资源..." -ForegroundColor Yellow

$animationPath = "dist\NeuroSongSpider\_internal\assets\main_loading"
if (Test-Path "$animationPath\f0.png") {
    $frameCount = (Get-ChildItem "$animationPath\f*.png").Count
    Write-Host "✅ 启动动画资源已成功打包 ($frameCount 帧)" -ForegroundColor Green
} else {
    Write-Host "⚠️  警告: 启动动画资源未找到" -ForegroundColor Yellow
}

if (Test-Path "dist\NeuroSongSpider\_internal\ffmpeg\bin\ffmpeg.exe") {
    Write-Host "✅ FFmpeg已成功打包" -ForegroundColor Green
} else {
    Write-Host "⚠️  警告: FFmpeg未找到" -ForegroundColor Yellow
}

if (Test-Path "dist\NeuroSongSpider\_internal\data\i18n\zh_CN.properties") {
    Write-Host "✅ 语言文件已成功打包" -ForegroundColor Green
} else {
    Write-Host "⚠️  警告: 语言文件未找到" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "5. 创建运行时必要的目录..." -ForegroundColor Yellow
$dirs = @(
    "dist\NeuroSongSpider\data",
    "dist\NeuroSongSpider\data\music",
    "dist\NeuroSongSpider\data\video",
    "dist\NeuroSongSpider\data\cache",
    "dist\NeuroSongSpider\data\custom_songs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}
Write-Host "✅ 运行时目录已创建" -ForegroundColor Green

Write-Host ""
Write-Host "6. 打包完成！" -ForegroundColor Green
Write-Host "可执行文件位置: dist\NeuroSongSpider\NeuroSongSpider.exe" -ForegroundColor Cyan
Write-Host ""
Read-Host "按任意键继续..."
