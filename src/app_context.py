from pathlib import Path
from qfluentwidgets import QConfig, InfoBar, ToolButton
from typing import TYPE_CHECKING, Optional

from src.config import DATA_DIR

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow
    from src.ui.widgets.media_player_bar import CustomMediaPlayBar
    from src.i18n.manager import I18nManager


class AppContext(QConfig):
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
        self.i18n_manager: Optional["I18nManager"] = None


CONFIG_PATH = DATA_DIR / "config.json"
app_context = AppContext(CONFIG_PATH)
