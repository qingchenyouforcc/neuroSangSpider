# 快速打包指南

## 🚀 一键打包（推荐）

直接双击运行 `build.bat` 文件，它会：
1. 自动从 `src/config.py` 读取版本号
2. 生成版本信息文件
3. 执行PyInstaller打包

## 📋 手动打包步骤

1. **更新版本号**（可选）
   - 编辑 `src/config.py`
   - 修改 `VERSION = "x.y.z"` 行

2. **生成版本信息**
   ```cmd
   python generate_version_info.py
   ```

3. **执行打包**
   ```cmd
   pyinstaller main.spec
   ```

## ✅ 验证版本信息

打包完成后，右键点击 `dist\NeuroSongSpider\NeuroSongSpider.exe`，选择"属性" → "详细信息"，查看版本信息。

## ⚠️ 注意事项

- 每次更改版本号后需要重新运行生成脚本
- 确保Python环境已安装PyInstaller
- 首次使用建议使用自动打包脚本
