from loguru import logger
from PyQt6.QtCore import QTimer, Qt
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

from src.i18n import t
from src.app_context import app_context
from src.config import PlayMode, Theme, cfg
from src.utils.file import on_fix_music
from src.utils.thread import SimpleThread
from src.bili_api.music import import_custom_songs_and_download
from src.ui.interface.play_queue import PlayQueueInterface
from bilibili_api import request_settings


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
    if hasattr(app_context, "i18n_manager") and app_context.i18n_manager:
        app_context.i18n_manager.set_language_with_restart(language, app_context.main_window)

    cfg.language.value = language
    cfg.save()

    if hasattr(app_context, "main_window") and app_context.main_window:
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

    # 主题切换会触发 qfluentwidgets 的全局样式表更新。
    # 在 ComboBox 的点击回调里同步切换，某些打包/运行时序下会导致 weakref 字典
    # 在迭代过程中被修改（RuntimeError: dictionary changed size during iteration）。
    # 延迟到当前事件处理结束后执行，可规避该类时序问题。
    def _apply_theme() -> None:
        try:
            cfg.set_theme(theme)
        except Exception:
            logger.exception("不是哥们你这怎么报错的？")

    QTimer.singleShot(0, _apply_theme)


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

        # 最小化到托盘设置
        self.minimizeToTraySwitch = SwitchButton(parent=self)
        self.minimizeToTraySwitch.setChecked(cfg.minimize_to_tray.value)
        self.minimizeToTraySwitch.checkedChanged.connect(self.on_minimize_to_tray_changed)

        # 下载后自动聚焦到歌曲列表
        self.autoSwitchPlaylistSwitch = SwitchButton(parent=self)
        self.autoSwitchPlaylistSwitch.setChecked(cfg.auto_switch_playlist.value)
        self.autoSwitchPlaylistSwitch.checkedChanged.connect(self.on_auto_switch_playlist_changed)

        # 封面显示开关
        self.coverSwitch = SwitchButton(parent=self)
        self.coverSwitch.setChecked(cfg.enable_cover.value)
        self.coverSwitch.checkedChanged.connect(self.on_cover_switch_changed)

        # 封面圆角半径
        self.coverRadiusSpin = SpinBox(self)
        self.coverRadiusSpin.setRange(0, 64)
        self.coverRadiusSpin.setValue(cfg.cover_corner_radius.value)
        self.coverRadiusSpin.valueChanged.connect(self.on_cover_radius_changed)

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
        self.customSongsBtn.clicked.connect(self.on_custom_songs_download)

        # 监听配置变化，更新开关状态
        cfg.minimize_to_tray.valueChanged.connect(
            lambda v: self.minimizeToTraySwitch.setChecked(v) if self.minimizeToTraySwitch.isChecked() != v else None
        )

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
            FluentIcon.MINIMIZE,
            t("settings.minimize_to_tray"),
            t("settings.minimize_to_tray_desc"),
            self.minimizeToTraySwitch,
        )
        self.addGroup(
            FluentIcon.LINK,
            t("settings.auto_switch_playlist_title"),
            t("settings.auto_switch_playlist_desc"),
            self.autoSwitchPlaylistSwitch,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.cover_switch_title"),
            t("settings.cover_switch_desc"),
            self.coverSwitch,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.cover_radius_title"),
            t("settings.cover_radius_desc"),
            self.coverRadiusSpin,
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

        # 代理设置
        self.proxySwitch = SwitchButton(parent=self)
        self.proxySwitch.setChecked(cfg.enable_proxy.value)
        self.proxySwitch.checkedChanged.connect(self.on_proxy_switch_changed)

        self.addGroup(
            FluentIcon.GLOBE,
            t("settings.proxy_enable"),
            t("settings.proxy_enable_desc"),
            self.proxySwitch,
        )

        self.proxyEdit = LineEdit(self)
        self.proxyEdit.setPlaceholderText("http://127.0.0.1:7890")
        self.proxyEdit.setText(cfg.proxy_url.value)
        self.proxyEdit.textChanged.connect(self.on_proxy_url_changed)

        self.proxyUrlItem = self.addGroup(
            FluentIcon.EDIT,
            t("settings.proxy_url"),
            t("settings.proxy_url_desc"),
            self.proxyEdit,
        )
        self.proxyUrlItem.setVisible(cfg.enable_proxy.value)

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

    def on_minimize_to_tray_changed(self, checked: bool) -> None:
        if cfg.minimize_to_tray.value == checked:
            return
        cfg.minimize_to_tray.value = checked
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("common.success"),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def on_auto_switch_playlist_changed(self, checked: bool) -> None:
        cfg.auto_switch_playlist.value = checked
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("settings.auto_switch_playlist_to", status=t("common.enabled") if checked else t("common.disabled")),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def on_cover_switch_changed(self, checked: bool) -> None:
        cfg.enable_cover.value = checked
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("settings.cover_switch_to", status=t("common.enabled") if checked else t("common.disabled")),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )
        # 尝试刷新播放列表界面
        try:
            if hasattr(app_context, "main_window") and app_context.main_window:
                # 找到播放列表子界面并刷新
                for w in app_context.main_window.findChildren(PlayQueueInterface):
                    if getattr(w, "objectName", lambda: "")() == "playQueueInterface":
                        if hasattr(w, "load_play_queue"):
                            w.load_play_queue()
        except Exception:
            logger.exception("刷新播放列表封面显示失败")

    def on_cover_radius_changed(self, value: int) -> None:
        cfg.cover_corner_radius.value = value
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("settings.cover_radius_set", value=value),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )
        # 尝试刷新播放列表界面
        try:
            if hasattr(app_context, "main_window") and app_context.main_window:
                for w in app_context.main_window.findChildren(PlayQueueInterface):
                    if getattr(w, "objectName", lambda: "")() == "playQueueInterface":
                        if hasattr(w, "load_play_queue"):
                            w.load_play_queue()
        except Exception:
            logger.exception("刷新播放列表封面圆角失败")

    def on_custom_songs_download(self):
        """处理自定义歌曲下载"""
        self.customSongsBtn.setEnabled(False)

        # 显示提示
        InfoBar.info(
            t("common.info"),
            t("search.start_download_wait"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=app_context.main_window,
        )

        # 启动线程
        self._custom_download_thread = SimpleThread(import_custom_songs_and_download)
        self._custom_download_thread.task_finished.connect(self.on_custom_songs_download_finished)
        self._custom_download_thread.start()

    def on_custom_songs_download_finished(self, result: dict):
        """自定义歌曲下载完成回调"""
        self.customSongsBtn.setEnabled(True)
        self._custom_download_thread = None

        status = result.get("status")
        message = result.get("message", "")

        if status == "success":
            data = result.get("data", {})
            success_count = data.get("success", 0)
            failed_count = data.get("failed", 0)

            InfoBar.success(
                t("common.success"),
                f"{message} (成功: {success_count}, 失败: {failed_count})",
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=3000,
            )
        elif status == "created_dir":
            InfoBar.info(
                t("common.info"),
                message,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=3000,
            )
        elif status == "no_bv":
            InfoBar.warning(
                t("common.warning"),
                message,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=3000,
            )
        else:
            InfoBar.error(
                t("common.error"),
                message,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=3000,
            )

    def on_proxy_switch_changed(self, checked: bool) -> None:
        cfg.enable_proxy.value = checked
        cfg.save()
        self.proxyUrlItem.setVisible(checked)

        if checked:
            request_settings.set_proxy(cfg.proxy_url.value)
        else:
            request_settings.set_proxy("")

        InfoBar.success(
            t("common.settings_success"),
            t("settings.proxy_status_changed", status=t("common.enabled") if checked else t("common.disabled")),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )

    def on_proxy_url_changed(self, text: str) -> None:
        cfg.proxy_url.value = text
        cfg.save()
        if cfg.enable_proxy.value:
            request_settings.set_proxy(text)
