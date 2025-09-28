from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from loguru import logger

from src.app_context import app_context
from src.core.player import playSongByIndex, restore_last_play_queue


class PlayQueueService:
    """播放队列服务

    - 统一管理 app_context.play_queue 与 play_queue_index
    - 提供基础的添加/删除/移动/播放等操作
    - UI 层仅调用本服务，避免直接操作全局状态，降低耦合
    """

    # 作为简单的单例使用
    _instance: "PlayQueueService | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # -------- 查询 --------
    def get_queue(self) -> list[Path]:
        return app_context.play_queue

    def length(self) -> int:
        return len(app_context.play_queue)

    def index(self) -> int:
        return app_context.play_queue_index

    # -------- 修改 --------
    def clear(self) -> None:
        app_context.play_queue.clear()
        app_context.play_queue_index = -1

    def set_current_index(self, idx: int) -> None:
        if 0 <= idx < len(app_context.play_queue):
            app_context.play_queue_index = idx
        else:
            logger.debug(f"set_current_index 忽略越界索引: {idx}")

    def ensure_in_queue(self, file_path: Path) -> int:
        """确保歌曲存在于队列中，返回其索引"""
        if file_path in app_context.play_queue:
            return app_context.play_queue.index(file_path)
        app_context.play_queue.append(file_path)
        return len(app_context.play_queue) - 1

    def add(self, file_path: Path) -> bool:
        """添加到队列（去重）。返回是否真的新增。"""
        if file_path in app_context.play_queue:
            return False
        app_context.play_queue.append(file_path)
        return True

    def add_many(self, paths: Iterable[Path]) -> dict[str, int]:
        added = 0
        exists = 0
        for p in paths:
            if p in app_context.play_queue:
                exists += 1
            else:
                app_context.play_queue.append(p)
                added += 1
        return {"added": added, "exists": exists}

    def remove_at(self, index: int) -> Optional[Path]:
        if 0 <= index < len(app_context.play_queue):
            removed = app_context.play_queue.pop(index)
            # 调整当前播放索引
            if app_context.play_queue_index == index:
                # 若删除的是当前播放项，保持 index 指向同一逻辑位置
                app_context.play_queue_index = min(index, len(app_context.play_queue) - 1)
            elif app_context.play_queue_index > index:
                app_context.play_queue_index -= 1
            return removed
        return None

    def remove_path(self, file_path: Path) -> bool:
        try:
            idx = app_context.play_queue.index(file_path)
        except ValueError:
            return False
        self.remove_at(idx)
        return True

    def move_up(self, index: int) -> int:
        if 0 < index < len(app_context.play_queue):
            q = app_context.play_queue
            q[index - 1], q[index] = q[index], q[index - 1]
            # 调整当前播放索引
            if app_context.play_queue_index == index:
                app_context.play_queue_index -= 1
            elif app_context.play_queue_index == index - 1:
                app_context.play_queue_index += 1
            return index - 1
        return index

    def move_down(self, index: int) -> int:
        if 0 <= index < len(app_context.play_queue) - 1:
            q = app_context.play_queue
            q[index + 1], q[index] = q[index], q[index + 1]
            # 调整当前播放索引
            if app_context.play_queue_index == index:
                app_context.play_queue_index += 1
            elif app_context.play_queue_index == index + 1:
                app_context.play_queue_index -= 1
            return index + 1
        return index

    # -------- 播放 --------
    def play_index(self, index: int) -> None:
        """设置索引并调用播放器播放"""
        self.set_current_index(index)
        try:
            playSongByIndex()
        except Exception:
            logger.exception(f"按索引播放失败: {index}")

    # -------- 其他 --------
    def restore_last_queue(self) -> bool:
        """尝试恢复上次播放队列，返回是否成功"""
        try:
            return bool(restore_last_play_queue())
        except Exception:
            logger.exception("恢复上次播放队列失败")
            return False


# 导出一个默认实例，便于导入使用
queue_service = PlayQueueService()
