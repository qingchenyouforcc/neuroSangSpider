from loguru import logger
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition, TransparentToolButton

from src.config import cfg


def open_info_tip():
    """打开正在播放提示"""
    if not cfg.enable_player_bar.value:
        logger.info("悬浮播放栏已禁用，不显示正在播放提示")
        return
    if cfg.info_bar is not None:
        logger.info("检测到已经有了一个正在播放提示，正在关闭...")
        cfg.info_bar.close()
    else:
        logger.info(f"正在播放{cfg.playing_now}")

    info = InfoBar.new(
        icon=FluentIcon.MUSIC,
        title="正在播放",
        content=f"{cfg.playing_now}",
        orient=Qt.Orientation.Horizontal,
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=-1,
        parent=InfoBar.desktopView(),
    )
    info.setCustomBackgroundColor("white", "#202020")
    cfg.info_bar = info

    try:
        playBtn = TransparentToolButton(FluentIcon.PAUSE, info)
        info.hBoxLayout.addWidget(playBtn, 0, Qt.AlignmentFlag.AlignLeft)
        playBtn.setToolTip("暂停/播放")
        playBtn.clicked.connect(infoPlayBtnClicked)
        info.closeButton.clicked.connect(infoCloseBtnClicked)
        cfg.info_bar_play_btn = playBtn

    except AttributeError:
        InfoBar.error(
            "错误",
            "没有正在播放的音乐",
            duration=1000,
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )

    except Exception as e:
        logger.error(e)
        InfoBar.error(
            "未知错误",
            "请复制日志反馈到github issue",
            duration=2000,
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )


def infoCloseBtnClicked():
    """悬浮栏关闭按钮事件"""
    if cfg.info_bar is not None:
        cfg.info_bar.close()
        cfg.info_bar = None


def infoPlayBtnClicked():
    """悬浮栏播放按钮事件"""
    assert cfg.player is not None, "播放器未初始化"
    cfg.player.togglePlayState()
    update_info_tip()


def update_info_tip():
    """更新正在播放提示"""
    if not cfg.enable_player_bar.value:
        return
    assert cfg.player and cfg.info_bar_play_btn, "播放器或播放按钮未初始化"

    icon = FluentIcon.PLAY_SOLID if cfg.player.player.isPlaying() else FluentIcon.PLAY_SOLID
    cfg.info_bar_play_btn.setIcon(icon)
