from loguru import logger
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition, TransparentToolButton

from src.config import cfg
from src.app_context import app_context

def open_info_tip():
    """打开正在播放提示"""
    if not cfg.enable_player_bar.value:
        logger.info("悬浮播放栏已禁用，不显示正在播放提示")
        InfoBar.info(
            "提示",
            "你已关闭悬浮播放栏，将不显示播放提示",
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
        
    song_name = app_context.playing_now.rsplit('.', 1)[0] if app_context.playing_now else "未知歌曲"

    info = InfoBar.new(
        icon=FluentIcon.MUSIC,
        title="正在播放",
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
        playBtn.setToolTip("暂停/播放")
        playBtn.clicked.connect(infoPlayBtnClicked)
        info.closeButton.clicked.connect(infoCloseBtnClicked)
        app_context.info_bar_play_btn = playBtn

    except AttributeError:
        InfoBar.error(
            "错误",
            "没有正在播放的音乐",
            duration=1000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )

    except Exception as e:
        logger.warning("打开播放提示栏时发生未知错误")
        InfoBar.error(
            "未知错误",
            f"请在github上提交issue并上传日志文件:\n{e!r}",
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
    assert app_context.player is not None, "播放器未初始化"
    app_context.player.togglePlayState()
    update_info_tip()


def update_info_tip():
    """更新正在播放提示"""
    if not cfg.enable_player_bar.value:
        return
    assert app_context.player and app_context.info_bar_play_btn, "播放器或播放按钮未初始化"

    icon = FluentIcon.PAUSE if app_context.player.player.isPlaying() else FluentIcon.PLAY_SOLID
    app_context.info_bar_play_btn.setIcon(icon)
