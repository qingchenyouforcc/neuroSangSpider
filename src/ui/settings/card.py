from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import (
    ComboBox,
    FluentIcon,
    GroupHeaderCardWidget,
    HyperlinkButton,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBoxBase,
    PushButton,
    SpinBox,
    SubtitleLabel,
    SwitchButton,
)

from src.config import PlayMode, Theme, cfg
from src.utils.file import on_fix_music


def changeDownloadType(selected_type: str) -> None:
    cfg.download_type.value = selected_type
    cfg.save()
    InfoBar.success(
        "设置成功",
        f"已将下载格式设为 {selected_type}",
        orient=Qt.Orientation.Horizontal,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=1500,
        parent=cfg.main_window,
    )


THEME_DISPLAY = {
    Theme.AUTO: "自动",
    Theme.LIGHT: "浅色",
    Theme.DARK: "深色",
}
THEME_DISPLAY_REVERSE = {v: k for k, v in THEME_DISPLAY.items()}


def on_theme_switched(current_text: str) -> None:
    """切换主题"""
    theme = THEME_DISPLAY_REVERSE[current_text]
    try:
        cfg.set_theme(theme)
    except Exception:
        logger.exception("不是哥们你这怎么报错的？")


class BiliApiDialog(MessageBoxBase):
    """Bilibili API 参数设置对话框"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Bilibili API 参数设置")

        self.descriptionLabel = SubtitleLabel("Bilibili API 参数设置\n用于请求 Bilibili API 时避免触发反爬", self)
        self.viewLayout.addWidget(self.descriptionLabel)

        self.helpLink = HyperlinkButton(
            "https://nemo2011.github.io/bilibili-api/#/get-credential",
            "查看获取方式",
            self,
        )
        self.viewLayout.addWidget(self.helpLink)

        # SESSDATA 输入框
        self.sessdataEdit = LineEdit(self)
        self.sessdataEdit.setPlaceholderText("SESSDATA")
        self.sessdataEdit.setText(cfg.bili_sessdata.value)
        self.viewLayout.addWidget(self.sessdataEdit)

        # bili_jct 输入框
        self.jctEdit = LineEdit(self)
        self.jctEdit.setPlaceholderText("bili_jct")
        self.jctEdit.setText(cfg.bili_jct.value)
        self.viewLayout.addWidget(self.jctEdit)

        # buvid3 输入框
        self.buvid3Edit = LineEdit(self)
        self.buvid3Edit.setPlaceholderText("buvid3")
        self.buvid3Edit.setText(cfg.bili_buvid3.value)
        self.viewLayout.addWidget(self.buvid3Edit)

        # 设置按钮文本
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

    def accept(self) -> None:
        """保存设置"""
        # 获取输入值
        sessdata = self.sessdataEdit.text().strip()
        jct = self.jctEdit.text().strip()
        buvid3 = self.buvid3Edit.text().strip()

        # 更新配置
        cfg.bili_sessdata.value = sessdata
        cfg.bili_jct.value = jct
        cfg.bili_buvid3.value = buvid3
        cfg.save()

        # 显示成功提示
        InfoBar.success(
            "保存成功",
            "Bilibili API 参数已更新",
            duration=1500,
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )

        super().accept()


class SettingsCard(GroupHeaderCardWidget):
    """常规设置卡片"""

    def __init__(self, parent=None):  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__(parent)
        self.setTitle("基本设置")
        self.setMinimumHeight(200)

        # 下载格式设置（保持原有代码）
        items = ["mp3", "ogg", "wav"]
        self.downloadFormatComboBox = ComboBox(self)
        self.downloadFormatComboBox.addItems(items)
        self.downloadFormatComboBox.setCurrentIndex(items.index(cfg.download_type.value))
        self.downloadFormatComboBox.currentIndexChanged.connect(lambda idx: changeDownloadType(items[idx]))

        # 主题模式设置
        theme_items = [THEME_DISPLAY[t] for t in Theme]
        self.themeComboBox = ComboBox(self)
        self.themeComboBox.addItems(theme_items)
        self.themeComboBox.setCurrentText(THEME_DISPLAY[cfg.theme_mode.value])
        self.themeComboBox.currentTextChanged.connect(on_theme_switched)

        # 播放模式设置
        play_mode_items = {
            PlayMode.LIST_LOOP: "列表循环",
            PlayMode.SEQUENTIAL: "顺序播放",
            PlayMode.SINGLE_LOOP: "单曲循环",
            PlayMode.RANDOM: "随机播放",
        }
        self.playModeComboBox = ComboBox(self)
        self.playModeComboBox.addItems(play_mode_items.values())
        current_mode = play_mode_items[cfg.play_mode.value]
        self.playModeComboBox.setCurrentText(current_mode)
        self.playModeComboBox.currentTextChanged.connect(lambda t: self.change_play_mode(t, play_mode_items))
        
        # 播放悬浮栏设置
        self.playerBarSwitch = SwitchButton(parent=self)
        self.playerBarSwitch.setChecked(cfg.enable_player_bar.value)
        self.playerBarSwitch.checkedChanged.connect(self.on_player_bar_switch_changed)
    
        # 搜索页数设置
        self.searchPageSpinBox = SpinBox(self)
        self.searchPageSpinBox.setRange(1, 10)
        self.searchPageSpinBox.setValue(cfg.search_page.value)
        self.searchPageSpinBox.valueChanged.connect(self.change_search_page)

        # Bilibili API 参数设置
        self.biliApiBtn = PushButton("Bilibili API 设置", self)
        self.biliApiBtn.clicked.connect(lambda: BiliApiDialog(self).exec())

        # 修复音频按钮
        self.fixMusicBtn = PushButton("修复音频", self)
        self.fixMusicBtn.clicked.connect(on_fix_music)

        # 添加到布局
        self.addGroup(
            FluentIcon.DOWNLOAD,
            "下载格式",
            "选择默认音乐格式",
            self.downloadFormatComboBox,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            "主题模式",
            "设置应用主题（自动/浅色/深色）",
            self.themeComboBox,
        )
        self.addGroup(
            FluentIcon.PLAY,
            "播放模式",
            "设置默认播放模式",
            self.playModeComboBox,
        )
        self.addGroup(
            FluentIcon.LABEL,
            "播放悬浮栏",
            "开启或关闭播放悬浮栏",
            self.playerBarSwitch,
        )
        self.addGroup(
            FluentIcon.SEARCH,
            "搜索页数",
            "设置每次搜索的页数 (1-10)",
            self.searchPageSpinBox,
        )
        self.addGroup(
            FluentIcon.SETTING,
            "Bilibili API 设置",
            "设置 Bilibili API 的访问参数",
            self.biliApiBtn,
        )
        self.addGroup(
            FluentIcon.MUSIC,
            "修复音频文件",
            "修复下载异常的音频文件",
            self.fixMusicBtn,
        )

    def change_play_mode(self, text: str, mode_map: dict[PlayMode, str]) -> None:
        """更改播放模式"""
        # 反向查找枚举值
        mode = next(k for k, v in mode_map.items() if v == text)
        cfg.play_mode.value = mode
        cfg.save()
        InfoBar.success(
            "设置成功",
            f"已将播放模式设为 {text}",
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def change_search_page(self, value: int) -> None:
        """更改搜索页数"""
        cfg.search_page.value = value
        cfg.save()
        InfoBar.success(
            "设置成功",
            f"已将搜索页数设为 {value}",
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def on_player_bar_switch_changed(self, checked: bool) -> None:
        cfg.enable_player_bar.value = checked
        cfg.save()
        InfoBar.success(
            "设置成功",
            f"已将播放悬浮栏设为 {'开启' if checked else '关闭'}",
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )