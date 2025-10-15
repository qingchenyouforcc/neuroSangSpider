import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

from loguru import logger
from qfluentwidgets import ConfigItem, OptionsConfigItem, OptionsValidator, QConfig, setTheme
from qfluentwidgets import Theme as QtTheme

if TYPE_CHECKING:
    pass

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

_SUPPORTED_LANGUAGES = [
    "en_US",
    "zh_CN",
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
    language = ConfigItem("Language", "Language", "zh_CN")
    volume = ConfigItem("Player", "Volume", 50)
    enable_player_bar = ConfigItem("Player", "EnablePlayerBar", True)
    play_mode = ConfigItem("Player", "Mode", PlayMode.LIST_LOOP)
    search_page = ConfigItem("Search", "PageCount", 3)
    up_list = ConfigItem("Search", "UpList", _DEFAULT_UP_LIST.copy())
    black_author_list = ConfigItem("Search", "BlackList", _DEFAULT_BLACKLIST.copy())
    filter_list = ConfigItem("Search", "FilterWords", _DEFAULT_FILTER_WORDS.copy())
    # 是否启用搜索结果过滤（默认启用）
    enable_filter = ConfigItem("Search", "EnableFilter", True)
    theme_mode = ConfigItem(
        "Appearance",
        "ThemeMode",
        Theme.AUTO,
        OptionsValidator([Theme.AUTO, Theme.LIGHT, Theme.DARK]),
    )

    # 播放列表封面设置
    enable_cover = ConfigItem("Appearance", "EnableCover", True)
    cover_corner_radius = ConfigItem("Appearance", "CoverCornerRadius", 10)

    # 是否在下载完成后自动跳转到播放列表并聚焦
    auto_switch_playlist = ConfigItem("AutoSwitchPlaylist", "EnableAutoSwitchPlaylist", False)

    # 亚克力背景设置（主页正在播放卡片使用）
    acrylic_enabled = ConfigItem("Appearance", "AcrylicEnabled", True)
    acrylic_blur_radius = ConfigItem("Appearance", "AcrylicBlurRadius", 3)
    # 颜色以 RGBA 数组保存，便于 JSON 序列化
    acrylic_tint_rgba = ConfigItem("Appearance", "AcrylicTintRGBA", [242, 242, 242, 140])
    acrylic_luminosity_rgba = ConfigItem("Appearance", "AcrylicLuminosityRGBA", [255, 255, 255, 12])

    play_count = ConfigItem("Player", "PlayCount", {})
    play_sequences = ConfigItem("Player", "PlaySequences", {})
    last_play_queue = ConfigItem("Player", "LastPlayQueue", {"queue": [], "index": 0})

    # bilibili-api-python
    bili_sessdata = ConfigItem("Bilibili", "SESSDATA", "")
    bili_jct = ConfigItem("Bilibili", "BILI_JCT", "")
    bili_buvid3 = ConfigItem("Bilibili", "BUVID3", "")

    def __init__(self, path: Path):
        # 指定配置文件路径
        super().__init__()
        self.file = path

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
    # 首先检查打包后的ffmpeg位置
    if getattr(sys, "frozen", False):
        # 打包后的环境，ffmpeg在_internal目录中
        # noinspection PyProtectedMember
        bundled_ffmpeg = Path(sys._MEIPASS) / "ffmpeg" / "bin" / "ffmpeg.exe"  # type: ignore
        if bundled_ffmpeg.exists():
            return bundled_ffmpeg

    # 然后检查开发环境的ffmpeg位置
    if IS_WINDOWS and (fp := MAIN_PATH / "ffmpeg" / "bin" / "ffmpeg.exe").exists():
        return fp

    # 最后尝试从系统路径查找
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


def get_main_path() -> Path:
    """获取主程序路径（exe所在目录或项目根目录）"""
    if getattr(sys, "frozen", False):
        # 打包后的环境，返回exe所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境，返回当前工作目录
        return Path.cwd()


MAIN_PATH = get_main_path()
DATA_DIR = MAIN_PATH / "data"
CACHE_DIR = DATA_DIR / "cache"
MUSIC_DIR = DATA_DIR / "music"
VIDEO_DIR = DATA_DIR / "video"
CUSTOM_SANG_DIR = DATA_DIR / "custom_songs"
I18N_DIR = DATA_DIR / "i18n"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)
MUSIC_DIR.mkdir(exist_ok=True, parents=True)
VIDEO_DIR.mkdir(exist_ok=True, parents=True)
CUSTOM_SANG_DIR.mkdir(exist_ok=True, parents=True)
I18N_DIR.mkdir(exist_ok=True, parents=True)

ASSETS_DIR = get_assets_path()
FFMPEG_PATH = detect_ffmpeg()

CONFIG_PATH = DATA_DIR / "config.json"
cfg = Config(CONFIG_PATH)


if CONFIG_PATH.exists():
    cfg.load()
    # logger.info(f"已找到配置文件，正在加载配置文件主题{cfg.theme_mode.value}")
    # match cfg.theme_mode.value:
    #     case Theme.AUTO:
    #         cfg.set_theme(Theme.AUTO)
    #         logger.info("应用主题: AUTO")
    #     case Theme.LIGHT:
    #         cfg.set_theme(Theme.LIGHT)
    #         logger.info("应用主题: LIGHT")
    #     case Theme.DARK:
    #         cfg.set_theme(Theme.DARK)
    #         logger.info("应用主题: DARK")

else:
    logger.info("未找到配置文件，正在应用默认主题: AUTO")
    cfg.set_theme(Theme.AUTO)
    setTheme(QtTheme.AUTO)


VERSION = "1.2.0"
