from PyQt6.QtCore import Qt
from qfluentwidgets import InfoBar, FluentIcon, InfoBarPosition, TransparentToolButton
from config import cfg

import config


def open_info_tip():
    """打开正在播放提示"""
    if config.HAS_INFOPLAYERBAR:
        print("检测到已经有了一个正在播放提示，正在关闭...")
        config.info_bar.close()
        config.info_bar = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{config.playing_now}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
    else:
        print(f"正在播放{config.playing_now}")
        info = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{config.playing_now}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
        info.setCustomBackgroundColor('white', '#202020')

        config.info_bar = info
        config.HAS_INFOPLAYERBAR = True
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
        print(e)
        InfoBar.error(
            "未知错误", "请复制日志反馈到github issue",
            duration=2000, parent=config.cfg.MAIN_WINDOW, position=InfoBarPosition.BOTTOM_RIGHT
        )

def infoCloseBtnClicked():
    """悬浮栏关闭按钮事件"""
    config.info_bar.close()
    config.HAS_INFOPLAYERBAR = False

def infoPlayBtnClicked():
    """悬浮栏播放按钮事件"""
    cfg.PLAYER.togglePlayState()

    if cfg.PLAYER.player.isPlaying():
        config.info_bar_play_btn.setIcon(FluentIcon.PAUSE_BOLD)
    else:
        config.info_bar_play_btn.setIcon(FluentIcon.PLAY_SOLID)