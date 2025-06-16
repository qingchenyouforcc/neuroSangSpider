import random
from pathlib import Path
from typing import Protocol

from loguru import logger
from PyQt6.QtCore import Qt, QUrl
from qfluentwidgets import InfoBar, InfoBarPosition

from src.config import MUSIC_DIR, PlayMode, cfg

from .tipbar import open_info_tip


def open_player() -> None:
    """打开播放器"""
    if cfg.player is not None:
        cfg.player.show()


def previousSong():
    """播放上一首"""
    if cfg.play_queue_index <= 0:
        InfoBar.info(
            "提示",
            "已经没有上一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
        return
    try:
        cfg.play_queue_index = cfg.play_queue_index - 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            "提示",
            "已经没有上一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
    except Exception:
        logger.exception("播放上一首时发生错误")


def nextSong():
    """播放下一首"""
    if cfg.play_mode.value == PlayMode.SEQUENTIAL:
        if cfg.play_queue_index >= len(cfg.play_queue) - 1:
            InfoBar.info(
                "提示",
                "已经没有下一首了",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=InfoBar.desktopView(),
            )
            return
    elif cfg.play_mode.value == PlayMode.LIST_LOOP:
        if cfg.play_queue_index >= len(cfg.play_queue) - 1:
            cfg.play_queue_index = -1
    elif cfg.play_mode.value == PlayMode.RANDOM:
        getRandomIndex()
        playSongByIndex()
        return

    try:
        cfg.play_queue_index += 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            "提示",
            "已经没有下一首了",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
    except Exception:
        logger.exception("播放下一首时发生错误")


# noinspection PyTypeChecker
def playSongByIndex():
    if not cfg.play_queue:
        InfoBar.error(
            "错误",
            "播放队列为空",
            duration=2000,
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return

    file_path = getMusicLocalStr(cfg.play_queue[cfg.play_queue_index].name)

    url = QUrl.fromLocalFile(file_path and str(file_path))
    assert cfg.player is not None, "播放器未初始化"
    cfg.player.player.setSource(url)
    cfg.player.player.play()

    cfg.playing_now = cfg.play_queue[cfg.play_queue_index].name

    logger.info(f"当前播放歌曲队列位置：{cfg.play_queue_index}")
    open_info_tip()


class _ItemWithText(Protocol):
    def text(self) -> str: ...


def getMusicLocal(item: _ItemWithText | None) -> Path | None:
    """获取音乐文件位置"""
    if not item:
        return None

    return summonMusicLocal(item.text())


def getMusicLocalStr(file_name: str) -> Path | None:
    """获取音乐文件位置(字符串)"""
    if not file_name:
        return None

    return summonMusicLocal(file_name)


def summonMusicLocal(file_name: str) -> Path | None:
    """生成音乐文件路径"""
    if not file_name:
        return None

    file_path = MUSIC_DIR / file_name

    if not file_path.exists():
        InfoBar.error(
            "错误",
            f"找不到文件: {file_name}",
            duration=2000,
            parent=cfg.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return None

    return file_path


def getRandomIndex() -> None:
    """当处于随机模式时，获取随机的歌曲"""
    index = random.randint(0, len(cfg.play_queue) - 1)
    while index == cfg.play_queue_index:
        index = random.randint(0, len(cfg.play_queue) - 1)
    cfg.play_queue_index = index


def sequencePlay() -> None:
    """顺序播放"""
    try:
        cfg.play_mode.value = PlayMode.LIST_LOOP
        playSongByIndex()
    except Exception:
        logger.exception("顺序播放时发生错误")
