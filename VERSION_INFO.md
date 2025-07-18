# EXE版本信息配置说明

本项目已配置自动版本信息生成系统，让生成的exe文件包含正确的版本信息。

## 文件说明

1. **`version_info.txt`** - PyInstaller使用的版本信息文件
2. **`generate_version_info.py`** - 自动生成版本信息的Python脚本
3. **`build.bat`** - Windows批处理自动打包脚本
4. **`build.ps1`** - PowerShell自动打包脚本
5. **`main.spec`** - 已更新的PyInstaller配置文件

## 使用方法

### 方法一：使用自动打包脚本（推荐）

#### Windows命令提示符：
```cmd
build.bat
```

#### PowerShell：
```powershell
.\build.ps1
```

### 方法二：手动打包

1. 更新版本号（在 `src/config.py` 中修改 `VERSION` 变量）
2. 生成版本信息文件：
   ```cmd
   python generate_version_info.py
   ```
3. 运行PyInstaller：
   ```cmd
   pyinstaller main.spec
   ```

## 版本信息包含的内容

生成的exe文件将包含以下版本信息：
- **文件版本**: 自动从config.py读取
- **产品版本**: 与文件版本相同
- **公司名称**: qingchenyouforcc
- **文件描述**: NeuroSongSpider - 歌回播放软件
- **产品名称**: NeuroSongSpider
- **版权信息**: Copyright © 2025 qingchenyouforcc. Licensed under AGPL-3.0

## 如何验证版本信息

打包完成后，可以通过以下方式验证版本信息：

1. **Windows资源管理器**：
   - 右键点击exe文件
   - 选择"属性"
   - 查看"详细信息"标签页

2. **PowerShell命令**：
   ```powershell
   (Get-Item .\dist\NeuroSongSpider\NeuroSongSpider.exe).VersionInfo
   ```

## 注意事项

1. 每次更新版本号后，都需要重新生成版本信息文件
2. 版本号格式应为 `x.y.z` 或 `x.y.z.w` 格式
3. 自动打包脚本会自动处理版本信息生成，推荐使用
4. 如果手动修改 `version_info.txt`，下次运行生成脚本时会被覆盖

## 自定义版本信息

如果需要修改版本信息中的其他字段（如公司名称、描述等），请编辑 `generate_version_info.py` 文件中的相应部分。
