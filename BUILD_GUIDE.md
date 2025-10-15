# 快速打包指南

## 🚀 一键打包（推荐）

直接双击运行 `build.bat` 或 `build.ps1` 文件，它会：
1. 自动从 `src/config.py` 读取版本号
2. 生成版本信息文件
3. 清理旧的构建文件
4. 执行PyInstaller打包
5. 验证必要资源（assets、ffmpeg、语言文件）
6. 创建运行时必要的目录

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
   pyinstaller main.spec --clean
   ```

4. **创建运行时目录**
   ```cmd
   mkdir dist\NeuroSongSpider\data\music
   mkdir dist\NeuroSongSpider\data\video
   mkdir dist\NeuroSongSpider\data\cache
   mkdir dist\NeuroSongSpider\data\custom_songs
   ```

## ✅ 验证打包结果

打包完成后，检查以下内容：

1. **版本信息**：右键点击 `dist\NeuroSongSpider\NeuroSongSpider.exe`，选择"属性" → "详细信息"，查看版本信息
2. **资源文件**：确认 `dist\NeuroSongSpider\_internal\assets` 目录存在且包含所需资源
3. **FFmpeg**：确认 `dist\NeuroSongSpider\_internal\ffmpeg\bin\ffmpeg.exe` 存在
4. **语言文件**：确认 `dist\NeuroSongSpider\_internal\data\i18n` 目录包含 `.properties` 文件
5. **运行目录**：确认 `dist\NeuroSongSpider\data` 及其子目录已创建

## ⚠️ 注意事项

- 每次更改版本号后需要重新运行生成脚本
- 确保Python环境已安装PyInstaller
- 首次使用建议使用自动打包脚本
- 打包后的程序需要在 `NeuroSongSpider.exe` 所在目录运行
- 程序运行时会自动在exe所在目录创建 `data` 文件夹存放配置和数据

## 🐛 常见问题

### Q: 打包后提示找不到 FFmpeg
A: 确保 `ffmpeg/bin/ffmpeg.exe` 存在于项目根目录，打包脚本会自动将其包含进去

### Q: 打包后语言设置丢失
A: 程序会在首次运行时从打包的资源中复制语言文件到 data 目录

### Q: 打包后无法播放音频
A: 检查 FFmpeg 是否正确打包到 `_internal\ffmpeg\bin` 目录中

## 📦 打包后的目录结构

```
dist/
└── NeuroSongSpider/
    ├── NeuroSongSpider.exe          # 主程序
    ├── _internal/                    # PyInstaller内部文件
    │   ├── assets/                   # 程序资源
    │   ├── ffmpeg/                   # FFmpeg可执行文件
    │   ├── data/                     # 初始数据文件
    │   └── ...                       # 其他依赖文件
    └── data/                         # 运行时数据目录（首次运行后创建）
        ├── config.json               # 用户配置
        ├── music/                    # 音乐文件
        ├── video/                    # 视频数据
        ├── cache/                    # 缓存文件
        └── custom_songs/             # 自定义歌单
```
