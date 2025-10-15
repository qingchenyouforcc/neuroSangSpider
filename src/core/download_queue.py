"""下载队列管理器

支持多个音频同时下载,管理下载任务队列。
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Queue
from threading import Lock, Thread, current_thread

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

from src.bili_api import run_music_download
from src.core.song_list import SongList


class DownloadStatus(Enum):
    """下载状态枚举"""

    PENDING = "pending"  # 等待中
    DOWNLOADING = "downloading"  # 下载中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败


@dataclass
class DownloadTask:
    """下载任务"""

    index: int  # 歌曲索引
    title: str  # 歌曲标题
    bvid: str  # BV号
    search_list: SongList  # 搜索结果列表
    file_type: str  # 文件格式
    output_file: Path  # 输出文件路径
    status: DownloadStatus = DownloadStatus.PENDING  # 状态
    error_msg: str = ""  # 错误信息


class DownloadQueueManager(QObject):
    """下载队列管理器"""

    # 信号定义
    task_added = pyqtSignal(DownloadTask)  # 任务添加
    task_started = pyqtSignal(DownloadTask)  # 任务开始
    task_completed = pyqtSignal(DownloadTask)  # 任务完成
    task_failed = pyqtSignal(DownloadTask)  # 任务失败
    queue_completed = pyqtSignal()  # 队列完成

    def __init__(self, max_workers: int = 3):
        """初始化下载队列管理器

        Args:
            max_workers: 最大并发下载数
        """
        super().__init__()
        self.max_workers = max_workers
        self.task_queue: Queue[DownloadTask] = Queue()
        self.active_tasks: list[DownloadTask] = []
        self.completed_tasks: list[DownloadTask] = []
        self.failed_tasks: list[DownloadTask] = []
        self.lock = Lock()
        self.is_running = False
        self.worker_threads: list[Thread] = []
        self.pending_tasks: list[DownloadTask] = []  # 存储等待中的任务，用于去重和展示

    def add_task(self, task: DownloadTask) -> bool:
        """添加下载任务到队列

        Args:
            task: 下载任务

        Returns:
            bool: True表示添加成功，False表示任务已存在
        """
        with self.lock:
            # 检查是否已存在相同BV号的任务
            if self._is_task_exists(task.bvid):
                logger.warning(f"任务已存在，跳过: {task.title} ({task.bvid})")
                return False

            self.task_queue.put(task)
            self.pending_tasks.append(task)
            logger.info(f"添加下载任务到队列: {task.title} ({task.bvid})")
            self.task_added.emit(task)
            return True

    def _is_task_exists(self, bvid: str) -> bool:
        """检查任务是否已存在（包括等待、下载中、已完成、失败）

        Args:
            bvid: BV号

        Returns:
            bool: 任务是否已存在
        """
        # 检查等待队列
        for task in self.pending_tasks:
            if task.bvid == bvid:
                return True
        # 检查活动任务
        for task in self.active_tasks:
            if task.bvid == bvid:
                return True
        # 检查已完成任务
        for task in self.completed_tasks:
            if task.bvid == bvid:
                return True
        # 检查失败任务
        for task in self.failed_tasks:
            if task.bvid == bvid:
                return True
        return False

    def start(self) -> None:
        """启动下载队列"""
        if self.is_running:
            logger.warning("下载队列已在运行中")
            return

        self.is_running = True
        logger.info(f"启动下载队列，最大并发数: {self.max_workers}")

        # 启动工作线程
        for i in range(self.max_workers):
            thread = Thread(target=self._worker, name=f"DownloadWorker-{i}", daemon=True)
            thread.start()
            self.worker_threads.append(thread)

    def stop(self) -> None:
        """停止下载队列"""
        logger.info("停止下载队列")
        self.is_running = False

        # 等待所有工作线程结束
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=1)

        self.worker_threads.clear()

    def _worker(self) -> None:
        """工作线程函数"""
        while self.is_running:
            try:
                # 从队列获取任务，超时1秒
                task = self.task_queue.get(timeout=1)

                with self.lock:
                    # 从等待列表移除
                    if task in self.pending_tasks:
                        self.pending_tasks.remove(task)
                    task.status = DownloadStatus.DOWNLOADING
                    self.active_tasks.append(task)

                logger.info(f"开始下载: {task.title} ({task.bvid})")
                self.task_started.emit(task)

                # 执行下载
                try:
                    success = run_music_download(task.index, task.search_list, task.file_type)

                    with self.lock:
                        if task in self.active_tasks:
                            self.active_tasks.remove(task)

                        if success:
                            task.status = DownloadStatus.SUCCESS
                            self.completed_tasks.append(task)
                            logger.success(f"下载完成: {task.title}")
                            self.task_completed.emit(task)
                        else:
                            task.status = DownloadStatus.FAILED
                            task.error_msg = "下载失败"
                            self.failed_tasks.append(task)
                            logger.error(f"下载失败: {task.title}")
                            self.task_failed.emit(task)

                except Exception as e:
                    logger.exception(f"下载任务异常: {task.title}")
                    with self.lock:
                        if task in self.active_tasks:
                            self.active_tasks.remove(task)
                        task.status = DownloadStatus.FAILED
                        task.error_msg = str(e)
                        self.failed_tasks.append(task)
                        self.task_failed.emit(task)

                finally:
                    self.task_queue.task_done()

            except Exception:
                # 队列超时，检查是否需要退出
                with self.lock:
                    # 如果队列空且没有活动任务，退出线程
                    if self.task_queue.empty() and not self.active_tasks:
                        break
                continue

        # 工作线程结束，最后一个线程发送完成信号
        with self.lock:
            # 检查是否是最后一个活动线程
            alive_workers = sum(1 for t in self.worker_threads if t.is_alive() and t != current_thread())
            if alive_workers == 0 and self.task_queue.empty() and not self.active_tasks:
                logger.info("所有下载任务已完成")
                self.is_running = False
                self.queue_completed.emit()

    def get_status(self) -> dict:
        """获取队列状态

        Returns:
            包含队列状态信息的字典
        """
        with self.lock:
            return {
                "is_running": self.is_running,
                "pending": self.task_queue.qsize(),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "total": (
                    self.task_queue.qsize()
                    + len(self.active_tasks)
                    + len(self.completed_tasks)
                    + len(self.failed_tasks)
                ),
            }

    def clear_completed(self) -> None:
        """清除已完成和失败的任务记录"""
        with self.lock:
            self.completed_tasks.clear()
            self.failed_tasks.clear()
            logger.info("已清除完成和失败的任务记录")

    def clear_all(self) -> int:
        """清空所有任务（等待中、已完成、失败）

        Returns:
            int: 清除的任务数量
        """
        if self.is_running:
            logger.warning("队列运行中，无法清空")
            return 0

        with self.lock:
            # 清空等待队列
            pending_count = len(self.pending_tasks)
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                    self.task_queue.task_done()
                except Exception:
                    break
            self.pending_tasks.clear()

            # 清空已完成和失败
            completed_count = len(self.completed_tasks)
            failed_count = len(self.failed_tasks)
            self.completed_tasks.clear()
            self.failed_tasks.clear()

            total = pending_count + completed_count + failed_count
            logger.info(f"已清空所有任务: 等待{pending_count}，完成{completed_count}，失败{failed_count}")
            return total

    def get_all_tasks(self) -> dict[str, list[DownloadTask]]:
        """获取所有任务列表

        Returns:
            包含各状态任务列表的字典
        """
        with self.lock:
            return {
                "pending": self.pending_tasks.copy(),
                "active": self.active_tasks.copy(),
                "completed": self.completed_tasks.copy(),
                "failed": self.failed_tasks.copy(),
            }

    def get_active_tasks(self) -> list[DownloadTask]:
        """获取正在下载的任务列表"""
        with self.lock:
            return self.active_tasks.copy()

    def get_pending_tasks(self) -> list[DownloadTask]:
        """获取等待中的任务列表"""
        with self.lock:
            return self.pending_tasks.copy()

    def get_pending_count(self) -> int:
        """获取等待中的任务数量"""
        return self.task_queue.qsize()
