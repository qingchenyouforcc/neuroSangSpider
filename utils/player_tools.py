import os

from PyQt6.QtCore import Qt, QUrl
from qfluentwidgets import InfoBar, InfoBarPosition

import config
from config import MAIN_PATH, cfg
from text_tools import remove_before_last_backslash
from tipbar_tools import open_info_tip


def open_player():
    """打开播放器"""
    cfg.PLAYER.show()
    
def previousSong():
    """ 播放上一首 """
    if config.play_queue_index <= 0:
        InfoBar.info(
            "提示",
            "已经没有上一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView()
        )
        return
    try:
        config.play_queue_index = config.play_queue_index - 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            "提示",
            "已经没有上一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView()
        )
    except Exception as e:
        print(e)

def nextSong():
    """ 播放下一首 """
    if config.play_mode == 1:
        if config.play_queue_index >= len(config.play_queue) - 1:
            InfoBar.info(
                "提示",
                "已经没有下一首了",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=InfoBar.desktopView()
            )
            return
    elif config.play_mode == 0:
        if config.play_queue_index >= len(config.play_queue) - 1:
            config.play_queue_index = -1

    try:
        config.play_queue_index += 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            "提示",
            "已经没有下一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView()
        )
    except Exception as e:
        print(e)

def playSongByIndex():
    file_path = getMusicLocalStr(
        config.play_queue[config.play_queue_index])

    url = QUrl.fromLocalFile(file_path)
    cfg.PLAYER.player.setSource(url)
    cfg.PLAYER.player.play()

    config.playing_now = remove_before_last_backslash(config.play_queue[config.play_queue_index])

    print(f"当前播放歌曲队列位置：{config.play_queue_index}")
    open_info_tip()

def getMusicLocal(fileName):
    """获取音乐文件位置"""
    if not fileName:
        return None

    return summonMusicLocal(fileName.text())

def getMusicLocalStr(fileName):
    """获取音乐文件位置(字符串)"""
    if not fileName:
        return None

    return summonMusicLocal(fileName)

def summonMusicLocal(fileName):
    """生成音乐文件路径"""
    if not fileName:
        return None

    music_dir = os.path.join(MAIN_PATH, "music")
    file_path = os.path.join(music_dir, fileName)

    if not os.path.exists(file_path):
        InfoBar.error(
            "错误", f"找不到文件: {fileName}",
            duration=2000, parent=config.cfg.MAIN_WINDOW, position=InfoBarPosition.BOTTOM_RIGHT
        )
        return None

    return file_path


