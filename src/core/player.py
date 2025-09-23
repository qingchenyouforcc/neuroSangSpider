import random
from pathlib import Path
from typing import Protocol

from loguru import logger
from PyQt6.QtCore import Qt, QUrl
from qfluentwidgets import InfoBar, InfoBarPosition

from src.app_context import app_context
from src.config import MUSIC_DIR, PlayMode, cfg
from i18n import t

from src.ui.widgets.tipbar import open_info_tip


def open_player() -> None:
    """打开播放器"""
    if app_context.player is not None:
        app_context.player.show()


def previousSong():
    """播放上一首"""
    if app_context.play_queue_index <= 0:
        InfoBar.info(
            t("common.info"),
            t("player.no_previous_song"),
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
        return
    try:
        app_context.play_queue_index = app_context.play_queue_index - 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            t("common.info"),
            t("player.no_previous_song"),
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
    except Exception:
        logger.exception(t("player.previous_song_error"))


def nextSong():
    """播放下一首"""
    if cfg.play_mode.value == PlayMode.SEQUENTIAL:
        if app_context.play_queue_index >= len(app_context.play_queue) - 1:
            InfoBar.info(
                t("common.info"),
                t("player.no_next_song"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=InfoBar.desktopView(),
            )
            return
    elif cfg.play_mode.value == PlayMode.LIST_LOOP:
        if app_context.play_queue_index >= len(app_context.play_queue) - 1:
            app_context.play_queue_index = -1
    elif cfg.play_mode.value == PlayMode.RANDOM:
        getRandomIndex()
        playSongByIndex()
        return

    try:
        app_context.play_queue_index += 1
        playSongByIndex()

    except IndexError:
        InfoBar.info(
            t("common.info"),
            t("player.no_next_song"),
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1000,
            parent=InfoBar.desktopView(),
        )
    except Exception:
        logger.exception(t("player.next_song_error"))


# noinspection PyTypeChecker
def playSongByIndex():
    if not app_context.play_queue:
        InfoBar.error(
            t("common.error"),
            t("player.play_queue_empty"),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return

    file_path = getMusicLocalStr(app_context.play_queue[app_context.play_queue_index].name)

    url = QUrl.fromLocalFile(file_path and str(file_path))
    assert app_context.player is not None, t("player.player_not_initialized")
    app_context.player.player.setSource(url)
    app_context.player.player.play()

    app_context.playing_now = app_context.play_queue[app_context.play_queue_index].name

    logger.info(f"当前播放歌曲队列位置：{app_context.play_queue_index}")
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
            t("common.error"),
            t("player.file_not_found", file_name=file_name),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return None

    return file_path


def getRandomIndex() -> None:
    """当处于随机模式时，获取随机的歌曲"""
    index = random.randint(0, len(app_context.play_queue) - 1)
    while index == app_context.play_queue_index:
        index = random.randint(0, len(app_context.play_queue) - 1)
    app_context.play_queue_index = index


def sequencePlay() -> None:
    """顺序播放"""
    try:
        cfg.play_mode.value = PlayMode.LIST_LOOP
        playSongByIndex()
    except Exception:
        logger.exception(t("player.sequence_play_error"))


def save_play_sequence(sequence_name: str) -> None:
    """保存当前播放序列
    
    Args:
        sequence_name: 序列名称
    """
    if not app_context.play_queue:
        InfoBar.warning(
            t("common.warning"),
            t("player.play_queue_empty_cannot_save"),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return

    # 转换为相对于音乐目录的相对路径
    file_names = [path.name for path in app_context.play_queue]
    
    # 存储播放序列
    play_sequences = cfg.play_sequences.value
    play_sequences[sequence_name] = file_names
    cfg.play_sequences.value = play_sequences
    cfg.save()
    
    logger.info(t("player.play_sequence_saved", sequence_name=sequence_name, count=len(file_names)))
    
    InfoBar.success(
        t("common.success"),
        t("player.play_sequence_saved_success", sequence_name=sequence_name),
        duration=2000,
        parent=app_context.main_window,
        position=InfoBarPosition.BOTTOM_RIGHT,
    )


def load_play_sequence(sequence_name: str) -> bool:
    """加载播放序列
    
    Args:
        sequence_name: 序列名称
        
    Returns:
        bool: 是否成功加载
    """
    play_sequences = cfg.play_sequences.value
    if sequence_name not in play_sequences:
        InfoBar.warning(
            t("common.warning"),
            t("player.play_sequence_not_exist", sequence_name=sequence_name),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return False
    
    # 获取文件名列表
    file_names = play_sequences[sequence_name]
    
    # 转换为完整路径并验证文件存在
    play_queue = []
    for name in file_names:
        file_path = MUSIC_DIR / name
        if file_path.exists():
            play_queue.append(file_path)
        else:
            logger.warning(t("player.file_not_found_removed", name=name))
    
    if not play_queue:
        InfoBar.warning(
            t("common.warning"),
            t("player.play_sequence_no_valid_files", sequence_name=sequence_name),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return False
    
    # 更新播放队列
    app_context.play_queue = play_queue
    app_context.play_queue_index = 0
    cfg.save()
    
    logger.info(t("player.play_sequence_loaded", sequence_name=sequence_name, count=len(play_queue)))
    
    InfoBar.success(
        t("common.success"),
        t("player.play_sequence_loaded_success", sequence_name=sequence_name),
        duration=2000,
        parent=app_context.main_window,
        position=InfoBarPosition.BOTTOM_RIGHT,
    )
    
    return True


def delete_play_sequence(sequence_name: str) -> bool:
    """删除播放序列
    
    Args:
        sequence_name: 序列名称
        
    Returns:
        bool: 是否成功删除
    """
    play_sequences = cfg.play_sequences.value
    if sequence_name not in play_sequences:
        InfoBar.warning(
            t("common.warning"),
            t("player.play_sequence_not_exist", sequence_name=sequence_name),
            duration=2000,
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
        )
        return False
    
    # 删除序列
    del play_sequences[sequence_name]
    cfg.play_sequences.value = play_sequences
    # 不需要特殊处理最近播放序列
    cfg.save()
    
    logger.info(t("player.play_sequence_deleted", sequence_name=sequence_name))
    
    InfoBar.success(
        t("common.success"),
        t("player.play_sequence_deleted_success", sequence_name=sequence_name),
        duration=2000,
        parent=app_context.main_window,
        position=InfoBarPosition.BOTTOM_RIGHT,
    )
    
    return True


def get_play_sequences() -> dict:
    """获取所有播放序列
    
    Returns:
        dict: {"序列名": [文件名1, 文件名2, ...]}
    """
    return cfg.play_sequences.value


def get_play_sequence_names() -> list[str]:
    """获取所有播放序列名称
    
    Returns:
        list[str]: 序列名称列表
    """
    return list(cfg.play_sequences.value.keys())


def save_current_play_queue():
    """保存当前播放队列到配置，在程序关闭时自动调用
    
    保存内容包括：
    1. 歌曲文件名列表
    2. 当前播放索引
    """
    try:
        if not app_context.play_queue:
            logger.debug(t("player.no_play_queue_to_save"))
            return
        
        # 转换为相对于音乐目录的相对路径
        file_names = []
        for path in app_context.play_queue:
            if hasattr(path, 'name') and isinstance(path.name, str):
                file_names.append(path.name)
            else:
                logger.warning(t("player.cannot_get_filename", path=path))
        
        # 确保播放索引是有效的整数
        play_index = app_context.play_queue_index
        if not isinstance(play_index, int) or play_index < 0:
            logger.warning(t("player.invalid_play_index", play_index=play_index))
            play_index = 0
        
        # 保存播放队列和当前播放索引
        last_play_data = {
            "queue": file_names,
            "index": play_index
        }
        
        cfg.last_play_queue.value = last_play_data
        cfg.save()
        
        logger.info(t("player.play_queue_saved", count=len(file_names), index=play_index))
    except Exception as e:
        logger.exception(t("player.save_play_queue_error", error=str(e)))


def restore_last_play_queue() -> bool:
    """恢复上次保存的播放队列
    
    Returns:
        bool: 是否成功恢复
    """
    try:
        last_play_data = cfg.last_play_queue.value
        
        # 确保数据结构正确
        if not isinstance(last_play_data, dict) or "queue" not in last_play_data:
            logger.debug(t("player.no_valid_last_play_queue_data"))
            return False
        
        # 获取文件名列表和索引
        file_names = last_play_data.get("queue", [])
        play_index = last_play_data.get("index", 0)
        
        # 确保文件名列表是一个列表
        if not isinstance(file_names, list):
            logger.debug(t("player.play_queue_data_format_error", type_name=str(type(file_names))))
            return False
            
        if not file_names:
            logger.debug(t("player.last_play_queue_empty"))
            return False
        
        # 转换为完整路径并验证文件存在
        play_queue = []
        for name in file_names:
            try:
                # 确保文件名是有效的字符串
                if not isinstance(name, str) or not name.strip():
                    logger.warning(t("player.invalid_filename", name=name))
                    continue
                    
                file_path = MUSIC_DIR / name
                if file_path.exists():
                    play_queue.append(file_path)
                else:
                    logger.warning(t("player.file_not_found_removed_from_queue", name=name))
            except Exception as e:
                logger.error(t("player.process_file_error", name=name, error=str(e)))
        
        if not play_queue:
            logger.warning(t("player.no_valid_music_files_in_restored_queue"))
            return False
        
        # 更新播放队列
        app_context.play_queue = play_queue
        
        # 确保索引是整数且在有效范围内
        if not isinstance(play_index, int):
            try:
                if isinstance(play_index, (str, float)) and play_index:
                    play_index = int(play_index)
                else:
                    logger.warning(t("player.invalid_play_index_type", type_name=str(type(play_index))))
                    play_index = 0
            except (TypeError, ValueError):
                logger.warning(t("player.invalid_play_index_value", play_index=play_index))
                play_index = 0
            
        app_context.play_queue_index = max(0, min(play_index, len(play_queue) - 1))  # 确保索引有效且不小于0
        
        logger.info(t("player.play_queue_restored", count=len(play_queue), index=app_context.play_queue_index))
        
        return True
    except Exception as e:
        logger.exception(t("player.restore_play_queue_error", error=str(e)))
        return False