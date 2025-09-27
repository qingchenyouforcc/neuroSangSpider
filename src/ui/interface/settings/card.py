import sys
from pathlib import Path
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

from i18n import t
from src.utils.app_restart import restart_app
from src.app_context import app_context
from src.config import PlayMode, Theme, cfg
from src.utils.file import on_fix_music
from src.bili_api.music import import_custom_songs_and_download


def changeDownloadType(selected_type: str) -> None:
    cfg.download_type.value = selected_type
    cfg.save()
    InfoBar.success(
        t("common.settings_success"),
        t("common.download_format_set", format=selected_type),
        orient=Qt.Orientation.Horizontal,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=1500,
        parent=app_context.main_window,
    )


def changeLanguage(language: str) -> None:
    """
    切换显示语言
    切换语言需要重启应用程序才能生效
    """
    if language == cfg.language.value:
        return

    # 先通过i18n_manager设置语言，确保翻译状态一致
    if hasattr(app_context, 'i18n_manager') and app_context.i18n_manager:
        app_context.i18n_manager.set_language_with_restart(language, app_context.main_window)
    
    cfg.language.value = language
    cfg.save()

    if hasattr(app_context, 'main_window') and app_context.main_window:
        app_context.main_window.close()


def get_theme_display():
    """获取主题显示文本"""
    return {
        Theme.AUTO: t("settings.theme_auto"),
        Theme.LIGHT: t("settings.theme_light"),
        Theme.DARK: t("settings.theme_dark"),
    }


def get_theme_display_reverse():
    """获取主题显示文本的反向映射"""
    theme_display = get_theme_display()
    return {v: k for k, v in theme_display.items()}


def on_theme_switched(current_text: str) -> None:
    """切换主题"""
    theme_display_reverse = get_theme_display_reverse()
    theme = theme_display_reverse[current_text]
    try:
        cfg.set_theme(theme)
    except Exception:
        logger.exception("不是哥们你这怎么报错的？")


class BiliApiDialog(MessageBoxBase):
    """Bilibili API 参数设置对话框"""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(t("bili_api.title"))

        self.descriptionLabel = SubtitleLabel(t("bili_api.desc"), self)
        self.viewLayout.addWidget(self.descriptionLabel)

        self.helpLink = HyperlinkButton(
            "https://nemo2011.github.io/bilibili-api/#/get-credential",
            t("bili_api.help_link"),
            self,
        )
        self.viewLayout.addWidget(self.helpLink)

        # SESSDATA 输入框
        self.sessdataEdit = LineEdit(self)
        self.sessdataEdit.setPlaceholderText(t("bili_api.sessdata_placeholder"))
        self.sessdataEdit.setText(cfg.bili_sessdata.value)
        self.viewLayout.addWidget(self.sessdataEdit)

        # bili_jct 输入框
        self.jctEdit = LineEdit(self)
        self.jctEdit.setPlaceholderText(t("bili_api.jct_placeholder"))
        self.jctEdit.setText(cfg.bili_jct.value)
        self.viewLayout.addWidget(self.jctEdit)

        # buvid3 输入框
        self.buvid3Edit = LineEdit(self)
        self.buvid3Edit.setPlaceholderText(t("bili_api.buvid3_placeholder"))
        self.buvid3Edit.setText(cfg.bili_buvid3.value)
        self.viewLayout.addWidget(self.buvid3Edit)

        # 设置按钮文本
        self.yesButton.setText(t("common.save"))
        self.cancelButton.setText(t("common.cancel"))

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
            t("bili_api.save_success"),
            t("bili_api.saved"),
            duration=1500,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )

        super().accept()


class SettingsCard(GroupHeaderCardWidget):
    """常规设置卡片"""

    def __init__(self, parent=None):  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__(parent)
        self.setTitle(t("settings.basic_title"))
        self.setMinimumHeight(200)

        # 显示语言设置
        language_items = ["zh_CN", "en_US"]
        self.languageComboBox = ComboBox(self)
        self.languageComboBox.addItems(language_items)
        self.languageComboBox.setCurrentIndex(language_items.index(cfg.language.value))
        self.languageComboBox.currentIndexChanged.connect(lambda idx: changeLanguage(language_items[idx]))

        # 下载格式设置（保持原有代码）
        items = ["mp3", "ogg", "wav"]
        self.downloadFormatComboBox = ComboBox(self)
        self.downloadFormatComboBox.addItems(items)
        self.downloadFormatComboBox.setCurrentIndex(items.index(cfg.download_type.value))
        self.downloadFormatComboBox.currentIndexChanged.connect(lambda idx: changeDownloadType(items[idx]))

        # 主题模式设置
        theme_display = get_theme_display()
        theme_items = [theme_display[t] for t in Theme]
        self.themeComboBox = ComboBox(self)
        self.themeComboBox.addItems(theme_items)
        self.themeComboBox.setCurrentText(theme_display[cfg.theme_mode.value])
        self.themeComboBox.currentTextChanged.connect(on_theme_switched)

        # 播放模式设置
        play_mode_items = {
            PlayMode.LIST_LOOP: t("settings.play_mode_list_loop"),
            PlayMode.SEQUENTIAL: t("settings.play_mode_sequential"),
            PlayMode.SINGLE_LOOP: t("settings.play_mode_single_loop"),
            PlayMode.RANDOM: t("settings.play_mode_random"),
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
        self.biliApiBtn = PushButton(t("settings.bili_api_settings"), self)
        self.biliApiBtn.clicked.connect(lambda: BiliApiDialog(self).exec())

        # 修复音频按钮
        self.fixMusicBtn = PushButton(t("settings.fix_audio"), self)
        self.fixMusicBtn.clicked.connect(on_fix_music)

        # 从自定义歌曲文件夹下载
        self.customSongsBtn = PushButton(t("settings.download"), self)
        self.customSongsBtn.clicked.connect(lambda: import_custom_songs_and_download())

        # 添加到布局
        self.addGroup(
            FluentIcon.DOWNLOAD,
            t("settings.download_format"),
            t("settings.download_format_desc"),
            self.downloadFormatComboBox,
        )
        self.addGroup(
            FluentIcon.GLOBE,
            t("settings.display_language"),
            t("settings.display_language_desc"),
            self.languageComboBox,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.theme_mode"),
            t("settings.theme_mode_desc"),
            self.themeComboBox,
        )
        self.addGroup(
            FluentIcon.PLAY,
            t("settings.play_mode"),
            t("settings.play_mode_desc"),
            self.playModeComboBox,
        )
        self.addGroup(
            FluentIcon.LABEL,
            t("settings.player_bar"),
            t("settings.player_bar_desc"),
            self.playerBarSwitch,
        )
        self.addGroup(
            FluentIcon.SEARCH,
            t("settings.search_pages"),
            t("settings.search_pages_desc"),
            self.searchPageSpinBox,
        )
        self.addGroup(
            FluentIcon.SETTING,
            t("settings.bili_api_settings"),
            t("settings.bili_api_settings_desc"),
            self.biliApiBtn,
        )
        self.addGroup(
            FluentIcon.MUSIC,
            t("settings.fix_audio"),
            t("settings.fix_audio_desc"),
            self.fixMusicBtn,
        )
        self.addGroup(
            FluentIcon.DOWNLOAD,
            t("settings.import_custom_bv"),
            t("settings.import_custom_bv_desc"),
            self.customSongsBtn,
        )

    def change_play_mode(self, text: str, mode_map: dict[PlayMode, str]) -> None:
        """更改播放模式"""
        # 反向查找枚举值
        mode = next(k for k, v in mode_map.items() if v == text)
        cfg.play_mode.value = mode
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("common.play_mode_set", play_mode=text),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def change_search_page(self, value: int) -> None:
        """更改搜索页数"""
        cfg.search_page.value = value
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("common.search_pages_set", value=value),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def on_player_bar_switch_changed(self, checked: bool) -> None:
        cfg.enable_player_bar.value = checked
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("common.player_bar_set", display_mode=t("common.enabled") if checked else t("common.disabled")),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )