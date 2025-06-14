from PyQt6.QtCore import Qt
from loguru import logger
from qfluentwidgets import InfoBar, FluentIcon, InfoBarPosition, TransparentToolButton
from common.config import cfg

import common.config


def open_info_tip():

    """打开正在播放提示"""
    if cfg.has_infoplayerbar:
        logger.info("检测到已经有了一个正在播放提示，正在关闭...")
        config.info_bar.close()
        config.info_bar = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{cfg.playing_now}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
    else:
        logger.info(f"正在播放{cfg.playing_now}")
        info = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{cfg.playing_now}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
        info.setCustomBackgroundColor('white', '#202020')

        config.info_bar = info
        cfg.has_infoplayerbar = True
    try:
        info = config.info_bar

        playBtn = TransparentToolButton(FluentIcon.PAUSE, info)
        info.hBoxLayout.addWidget(playBtn, 0, Qt.AlignmentFlag.AlignLeft)
        playBtn.setToolTip("暂停/播放")

        config.info_bar_play_btn = playBtn

        playBtn.clicked.connect(infoPlayBtnClicked)
        info.closeButton.clicked.connect(infoCloseBtnClicked)

    except AttributeError:
        InfoBar.error(
            "错误", "没有正在播放的音乐",
            duration=1000, parent=config.cfg.MAIN_WINDOW, position=InfoBarPosition.BOTTOM_RIGHT
        )

    except Exception as e:
        logger.error(e)
        InfoBar.error(
            "未知错误", "请复制日志反馈到github issue",
            duration=2000, parent=config.cfg.MAIN_WINDOW, position=InfoBarPosition.BOTTOM_RIGHT
        )

def infoCloseBtnClicked():
    """悬浮栏关闭按钮事件"""
    config.info_bar.close()
    cfg.has_infoplayerbar = False

def infoPlayBtnClicked():
    """悬浮栏播放按钮事件"""
    cfg.PLAYER.togglePlayState()
    update_info_tip()

def update_info_tip():
    """更新正在播放提示"""
    if cfg.PLAYER.player.isPlaying():
        config.info_bar_play_btn.setIcon(FluentIcon.PAUSE_BOLD)
    else:
        config.info_bar_play_btn.setIcon(FluentIcon.PLAY_SOLID)