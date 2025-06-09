# -*- mode: python ; coding: utf-8 -*-

py_files = [
    'main.py', 
    'crawlerCore\\main.py', 'crawlerCore\\videosList.py', 'crawlerCore\\searchCore.py',
    'musicDownloader\\main.py', 'musicDownloader\\downloader.py', 
    'utils\\bili_tools.py', 'utils\\file_tools.py', 'utils\\text_tools.py', 'utils\\textbroswer_tools.py',
    'utils\\tipbar_tools.py', 'utils\\player_tools.py',
    'common\\config.py',
    'SongListManager\\SongList.py'
]


a = Analysis(
    py_files,
    pathex=['.'],
    binaries=[],
    datas=[
        ('res\\main.ico', 'images'),
    ],
    hiddenimports=[
        'socket', 
        'ssl', 
        'idna', 
        'urllib3', 
        'httpx', 
        'httpx._transports', 
        'aiohttp', 
        'aiohttp',
        'bilibili_api.clients.AioHTTPClient',
        'bilibili_api.clients.httpx_client',
        'bilibili_api.clients.requests_client',
        'bilibili_api.clients.base',
        'PyQt6.QtMultimedia',
        'PyQt6.QtNetwork',
        'qfluentwidgets.common.icon',
        'qfluentwidgets.components.widgets.flyout',
        'qfluentwidgets.multimedia.media_play_bar',
        'qfluentwidgets.window.fluent_window',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NeuroSongSpider',
    icon='.\\res\\main.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NeuroSongSpider',
)
