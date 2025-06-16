import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

from loguru import logger
from qfluentwidgets import ConfigItem, InfoBar, OptionsConfigItem, OptionsValidator, QConfig, ToolButton, setTheme
from qfluentwidgets import Theme as QtTheme

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow
    from src.ui.media_player_bar import CustomMediaPlayBar

IS_WINDOWS = sys.platform == "win32"


class PlayMode(int, Enum):
    """播放模式枚举"""

    LIST_LOOP = 0  # 列表循环
    SEQUENTIAL = 1  # 顺序播放
    SINGLE_LOOP = 2  # 单曲循环
    RANDOM = 3  # 随机播放


class Theme(str, Enum):
    """主题枚举"""

    AUTO = "Auto"
    LIGHT = "Light"
    DARK = "Dark"


_DEFAULT_UP_LIST = [
    351692111,
    1880487363,
    22535350,
    3546612622166788,
    5971855,
    483178955,
    690857494,
]
_DEFAULT_BLACKLIST = ["李19"]
_DEFAULT_FILTER_WORDS = [
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


class Config(QConfig):
    """应用程序配置类"""

    # 持久化配置项
    download_type = OptionsConfigItem(
        "Download",
        "Type",
        "mp3",
        OptionsValidator(["mp3", "ogg", "wav"]),
    )
    volume = ConfigItem("Player", "Volume", 50)
    enable_player_bar = ConfigItem("Player", "EnablePlayerBar", True)
    play_mode = ConfigItem("Player", "Mode", PlayMode.LIST_LOOP)
    search_page = ConfigItem("Search", "PageCount", 3)
    up_list = ConfigItem("Search", "UpList", _DEFAULT_UP_LIST.copy())
    black_author_list = ConfigItem("Search", "BlackList", _DEFAULT_BLACKLIST.copy())
    filter_list = ConfigItem("Search", "FilterWords", _DEFAULT_FILTER_WORDS.copy())
    theme_mode = ConfigItem(
        "Appearance",
        "ThemeMode",
        Theme.AUTO,
        OptionsValidator([Theme.AUTO, Theme.LIGHT, Theme.DARK]),
    )

    # bilibili-api-python
    bili_sessdata = ConfigItem("Bilibili", "SESSDATA", "")
    bili_jct = ConfigItem("Bilibili", "BILI_JCT", "")
    bili_buvid3 = ConfigItem("Bilibili", "BUVID3", "")

    def __init__(self, path: Path):
        # 指定配置文件路径
        super().__init__()
        self.file = path

        # 运行时状态
        self.playing_now: str | None = None
        self.play_queue: list[Path] = []
        self.play_queue_index: int = 0
        self.main_window: "MainWindow | None" = None
        self.player: "CustomMediaPlayBar | None" = None
        self.info_bar: InfoBar | None = None
        self.info_bar_play_btn: ToolButton | None = None

        setTheme(QtTheme(self.theme_mode.value.value))

    def set_theme(self, theme: Theme) -> None:
        """设置主题"""
        setTheme(QtTheme(theme.value))
        self.theme_mode.value = theme
        self.save()


class _SubprocessOptions(TypedDict):
    startupinfo: NotRequired["subprocess.STARTUPINFO"]
    creationflags: NotRequired[int]


def subprocess_options() -> _SubprocessOptions:
    if not IS_WINDOWS:
        return {}

    # 在 Windows 下使用 pyinstaller console=False 打包时
    # 隐藏启动 subprocess 的控制台窗口
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    creationflags = subprocess.CREATE_NO_WINDOW
    return {"startupinfo": startupinfo, "creationflags": creationflags}


def detect_ffmpeg() -> Path:
    if IS_WINDOWS and (fp := MAIN_PATH / "ffmpeg" / "bin" / "ffmpeg.exe").exists():
        return fp

    if IS_WINDOWS:
        cmd = ["cmd.exe", "/c", "where ffmpeg"]
    else:
        cmd = ["which", "ffmpeg"]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, **subprocess_options())
    stdout, _ = p.communicate()
    if p.returncode == 0:
        ffmpeg_path = stdout.decode().strip()
        if (fp := Path(ffmpeg_path)).exists():
            return fp

    logger.error("未找到 FFMPEG，请安装 FFMPEG 并正确设置路径。")
    raise FileNotFoundError


def get_assets_path() -> Path:
    """获取资源文件路径"""
    if getattr(sys, "frozen", False):
        # 打包后的环境
        # noinspection PyProtectedMember
        return Path(sys._MEIPASS) / "assets"  # type: ignore
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

CONFIG_PATH = DATA_DIR / "config.json"
cfg = Config(CONFIG_PATH)
if CONFIG_PATH.exists():
    cfg.load()


VERSION = "1.1.4"
