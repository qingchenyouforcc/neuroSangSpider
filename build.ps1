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
Write-Host "2. 开始PyInstaller打包..." -ForegroundColor Yellow
$result = pyinstaller main.spec
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller打包失败！" -ForegroundColor Red
    Read-Host "按任意键继续..."
    exit 1
}

Write-Host ""
Write-Host "3. 打包完成！" -ForegroundColor Green
Write-Host "可执行文件位置: dist\NeuroSongSpider\NeuroSongSpider.exe" -ForegroundColor Cyan
Write-Host ""
Read-Host "按任意键继续..."
