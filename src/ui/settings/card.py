from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import (
    ComboBox,
    FluentIcon,
    GroupHeaderCardWidget,
    InfoBar,
    InfoBarPosition,
    PushButton,
    SwitchButton,
    Theme,
    isDarkTheme,
    setTheme,
)

from src.config import cfg
from src.utils.file import on_fix_music


def changeDownloadType(selected_type: str):
    cfg.downloadType.value = selected_type
    InfoBar.success(
        "设置成功",
        f"已将下载格式设为 {selected_type}",
        orient=Qt.Orientation.Horizontal,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=1500,
        parent=cfg.MAIN_WINDOW,
    )


def on_theme_switched(checked):
    """切换主题"""
    try:
        setTheme(Theme.DARK if checked else Theme.LIGHT)
    except Exception as e:
        logger.error(f"不是哥们你这怎么报错的？{e}")


class SettingsCard(GroupHeaderCardWidget):
    """常规设置卡片"""

    def __init__(self, parent=None):  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__(parent)
        self.setTitle("基本设置")

        # self.setBorderRadius(8)
        self.setFixedHeight(240)

        # 修改下载歌曲格式
        items = ["mp3", "ogg", "wav"]
        self.comboBox = ComboBox(self)
        self.comboBox.addItems(items)

        current_index = items.index(cfg.downloadType.value)
        self.comboBox.setCurrentIndex(current_index)
        self.comboBox.currentIndexChanged.connect(lambda idx: changeDownloadType(items[idx]))

        # 切换主题按钮
        self.themeSwitch = SwitchButton(self)
        self.themeSwitch.setOffText(self.tr("浅色"))
        self.themeSwitch.setOnText(self.tr("深色"))

        current_theme_is_dark: bool | None = (application := QApplication.instance()) and application.property(
            "darkMode"
        )
        # 默认系统主题
        if current_theme_is_dark is None:
            current_theme_is_dark = isDarkTheme()

        self.themeSwitch.setChecked(current_theme_is_dark)
        self.themeSwitch.checkedChanged.connect(on_theme_switched)

        self.fixMusic = PushButton("修复音频", self)
        self.fixMusic.clicked.connect(on_fix_music)

        # 添加组件到分组中
        self.addGroup(
            FluentIcon.BRIGHTNESS,
            "主题",
            "切换深色/浅色模式",
            self.themeSwitch,
        )
        self.addGroup(
            FluentIcon.DOWNLOAD,
            "下载格式",
            "选择默认音乐格式",
            self.comboBox,
        )
        self.addGroup(
            FluentIcon.MUSIC,
            "修复音频文件",
            "修复下载异常的音频文件",
            self.fixMusic,
        )
