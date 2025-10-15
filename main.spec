# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("src/assets", "assets"),
        ("src/assets/main_loading", "assets/main_loading"),  # 显式包含启动动画资源
        ("ffmpeg/bin", "ffmpeg/bin"),  # 包含 ffmpeg 可执行文件
        ("data/i18n", "data/i18n"),  # 包含语言文件
    ],
    hiddenimports=[
        "socket",
        "ssl",
        "idna",
        "urllib3",
        "bilibili_api.clients.AioHTTPClient",
        "bilibili_api.clients.base",
        "PyQt6.QtMultimedia",
        "PyQt6.QtNetwork",
        "qfluentwidgets.common.icon",
        "qfluentwidgets.components.widgets.flyout",
        "qfluentwidgets.multimedia.media_play_bar",
        "qfluentwidgets.window.fluent_window",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NeuroSongSpider",
    icon="src/assets/main.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",  # 添加版本信息文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NeuroSongSpider",
)
