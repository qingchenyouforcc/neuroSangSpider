import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from qfluentwidgets import InfoBar, OptionsConfigItem, OptionsValidator, QConfig, ToolButton

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow
    from src.ui.media_player_bar import CustomMediaPlayBar


class Config(QConfig):
    downloadType = OptionsConfigItem(
        "Download",
        "downloadType",
        "mp3",
        OptionsValidator(["mp3", "ogg", "wav"]),
        restart=False,
    )

    def __init__(self):
        super().__init__()
        self.playing_now: str | None = None
        self.volume = 50
        self.play_queue = []
        self.play_queue_index = 0
        self.play_mode = 0  # 播放模式 0是列表循环 1是顺序播放 2是单曲循环 3是随机播放
        self.search_page = 3
        self.up_list = [
            351692111,
            1880487363,
            22535350,
            3546612622166788,
            5971855,
            483178955,
            690857494,
        ]
        self.black_author_list = ["李19"]
        self.filter_list = [
            "neuro",
            "歌回",
            "手书",
            "切片",
            "熟肉",
            "evil",
            "社区",
            "21",
            "歌曲",
            "歌切",
        ]

        self.MAIN_WINDOW: "MainWindow | None" = None
        self.PLAYER: "CustomMediaPlayBar | None" = None
        self.info_bar: InfoBar | None = None
        self.info_bar_play_btn: ToolButton | None = None

    def set_main_window(self, window: "MainWindow"):
        self.MAIN_WINDOW = window

    # 这个是播放器类，player在这个里面
    def set_player(self, Player: "CustomMediaPlayBar"):
        self.PLAYER = Player


def detect_ffmpeg():
    fp = MAIN_PATH / "ffmpeg" / "bin" / "ffmpeg.exe"
    if fp.exists():
        return fp

    if sys.platform == "win32":
        cmd = ["cmd.exe", "/c", "where ffmpeg"]
    else:
        cmd = ["which", "ffmpeg"]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    if p.returncode == 0:
        ffmpeg_path = stdout.decode().strip()
        if (fp := Path(ffmpeg_path)).exists():
            return fp

    logger.error("FFMPEG not found in PATH or specified directory.")
    raise FileNotFoundError("FFMPEG not found. Please install FFMPEG and set the path correctly.")


def get_assets_path() -> Path:
    """获取资源文件路径"""
    if getattr(sys, "frozen", False):
        # 打包后的环境
        return Path(sys._MEIPASS) / "assets"  # pyright:ignore[reportAttributeAccessIssue]
    else:
        # 开发环境
        return Path(__file__).parent / "assets"


MAIN_PATH = Path.cwd()
DATA_DIR = MAIN_PATH / "data"
CACHE_DIR = DATA_DIR / "cache"
MUSIC_DIR = DATA_DIR / "music"
VIDEO_DIR = DATA_DIR / "video"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)
MUSIC_DIR.mkdir(exist_ok=True, parents=True)
VIDEO_DIR.mkdir(exist_ok=True, parents=True)

ASSETS_DIR = get_assets_path()
FFMPEG_PATH = detect_ffmpeg()

cfg = Config()

VERSION = "1.1.4"
