from loguru import logger
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition, TransparentToolButton

from i18n import t
from src.config import cfg
from src.app_context import app_context

def open_info_tip():
    """打开正在播放提示"""
    if not cfg.enable_player_bar.value:
        logger.info("悬浮播放栏已禁用，不显示正在播放提示")
        InfoBar.info(
            t("common.info"),
            t("tipbar.player_bar_disabled"),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
        )
        return
    if app_context.info_bar is not None:
        logger.info("检测到已经有了一个正在播放提示，正在关闭...")
        app_context.info_bar.close()
    else:
        logger.info(f"正在播放{app_context.playing_now}")
        
    song_name = app_context.playing_now.rsplit('.', 1)[0] if app_context.playing_now else t("tipbar.unknown_song")

    info = InfoBar.new(
        icon=FluentIcon.MUSIC,
        title=t("tipbar.now_playing"),
        content=f"{song_name}",
        orient=Qt.Orientation.Horizontal,
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=-1,
        parent=InfoBar.desktopView(),
    )
    info.setCustomBackgroundColor("white", "#202020")
    app_context.info_bar = info

    try:
        playBtn = TransparentToolButton(FluentIcon.PAUSE, info)
        info.hBoxLayout.addWidget(playBtn, 0, Qt.AlignmentFlag.AlignLeft)
        playBtn.setToolTip(t("tipbar.play_pause"))
        playBtn.clicked.connect(infoPlayBtnClicked)
        info.closeButton.clicked.connect(infoCloseBtnClicked)
        app_context.info_bar_play_btn = playBtn

    except AttributeError:
        InfoBar.error(
            t("common.error"),
            t("tipbar.no_music_playing"),
            duration=1000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )

    except Exception as e:
        logger.warning("打开播放提示栏时发生未知错误")
        InfoBar.error(
            t("common.unknown_error"),
            t("tipbar.github_issue", e=e),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )


def infoCloseBtnClicked():
    """悬浮栏关闭按钮事件"""
    if app_context.info_bar is not None:
        app_context.info_bar.close()
        app_context.info_bar = None


def infoPlayBtnClicked():
    """悬浮栏播放按钮事件"""
    assert app_context.player is not None, t("tipbar.player_uninitialized")
    app_context.player.togglePlayState()
    update_info_tip()


def update_info_tip():
    """更新正在播放提示"""
    if not cfg.enable_player_bar.value:
        return
    assert app_context.player and app_context.info_bar_play_btn, "播放器或播放按钮未初始化"

    icon = FluentIcon.PAUSE if app_context.player.player.isPlaying() else FluentIcon.PLAY_SOLID
    app_context.info_bar_play_btn.setIcon(icon)