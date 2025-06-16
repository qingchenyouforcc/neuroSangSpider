from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBarPosition, TableWidget, TitleLabel, TransparentToolButton

from src.config import MUSIC_DIR, cfg
from src.utils.file import read_all_audio_info
from src.utils.player import getMusicLocal, open_player
from src.utils.tipbar import open_info_tip
from src.utils.text import escape_tag

if TYPE_CHECKING:
    from .main_window import MainWindow


class LocalPlayerInterface(QWidget):
    """本地播放器GUI"""

    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.main_window = main_window
        self.setObjectName("locPlayerInterface")
        self.setStyleSheet("LocPlayerInterface{background: transparent}")

        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 创建标题和刷新按钮的水平布局
        title_layout = QHBoxLayout()

        self.titleLabel = TitleLabel("本地播放器", self)

        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip("刷新歌曲列表")

        self.addQueueButton = TransparentToolButton(FIF.ADD, self)
        self.addQueueButton.setToolTip("添加到播放列表")

        self.openPlayer = TransparentToolButton(FIF.MUSIC, self)
        self.openPlayer.setToolTip("打开播放器")

        self.openInfoTip = TransparentToolButton(FIF.INFO, self)
        self.openInfoTip.setToolTip("打开正在播放提示")

        self.delSongBtn = TransparentToolButton(FIF.DELETE, self)
        self.delSongBtn.setToolTip("删除文件")

        self.addQueueAllBtn = TransparentToolButton(FIF.CHEVRON_DOWN_MED, self)
        self.addQueueAllBtn.setToolTip("添加所有文件到播放列表")

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.openInfoTip, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.openPlayer, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.addQueueAllBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delSongBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.addQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self._layout.addLayout(title_layout)
        self._layout.addWidget(self.tableView)

        self.tableView.cellDoubleClicked.connect(self.play_selected_song)
        self.refreshButton.clicked.connect(self.load_local_songs)
        self.addQueueButton.clicked.connect(self.add_to_queue)
        self.openPlayer.clicked.connect(open_player)
        self.openInfoTip.clicked.connect(open_info_tip)
        self.delSongBtn.clicked.connect(self.del_song)
        self.addQueueAllBtn.clicked.connect(self.add_all_to_queue)

        self.load_local_songs()

    def load_local_songs(self):
        try:
            songs = read_all_audio_info(MUSIC_DIR)
            self.tableView.setRowCount(len(songs))
            self.tableView.setColumnCount(2)
            self.tableView.setHorizontalHeaderLabels(["文件名", "时长"])

            for i, (filename, duration) in enumerate(songs):
                self.tableView.setItem(i, 0, QTableWidgetItem(filename))
                self.tableView.setItem(i, 1, QTableWidgetItem(f"{duration}s"))

            self.tableView.resizeColumnsToContents()
        except Exception:
            logger.exception("加载本地歌曲失败")

    def play_selected_song(self, row):
        """双击播放指定行的歌曲"""
        try:
            item = self.tableView.item(row, 0)
            assert item is not None, "当前行没有歌曲信息"

            file_path = getMusicLocal(item)
            assert file_path is not None, "无法获取音乐文件路径"

            url = QUrl.fromLocalFile(file_path and str(file_path))
            self.main_window.player_bar.player.setSource(url)
            self.main_window.player_bar.player.play()

            cfg.playing_now = item.text()

            open_info_tip()

            self.add_to_queue()
            cfg.play_queue_index = cfg.play_queue.index(file_path)
            logger.info(f"当前播放歌曲队列位置：{cfg.play_queue_index}")
        except Exception:
            logger.exception("播放选中歌曲失败")

    def add_to_queue(self):
        """添加到播放列表"""
        item = self.tableView.currentItem()
        assert item is not None, "当前行没有歌曲信息"

        if file_path := getMusicLocal(item):
            if file_path in cfg.play_queue:
                InfoBar.warning(
                    "已存在",
                    f"{item.text()}已存在播放列表",
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self.parent(),
                )
                return

            cfg.play_queue.append(file_path)
            InfoBar.success(
                "成功",
                f"已添加{item.text()}到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )
            logger.info(f"当前播放列表:{cfg.play_queue}")
        else:
            InfoBar.error(
                "失败",
                "添加失败！",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=cfg.main_window,
            )

    def del_song(self):
        """删除列表项文件"""
        try:
            item = self.tableView.currentItem()
            if (file_path := getMusicLocal(item)) and (fp := Path(file_path)).exists():
                fp.unlink()

            if file_path in cfg.play_queue:
                cfg.play_queue.remove(file_path)

            InfoBar.success(
                "完成",
                "已删除该歌曲",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self.parent(),
            )
            self.load_local_songs()

        except Exception:
            logger.exception("删除歌曲失败")

    def add_all_to_queue(self):
        """添加列表所有歌曲到播放列表"""
        try:
            for i in range(self.tableView.rowCount()):
                item = self.tableView.item(i, 0)
                if item is None:
                    logger.warning(f"第 {i} 行没有歌曲信息，跳过")
                    continue

                file_path = getMusicLocal(item)
                if file_path is None or not file_path.exists():
                    # TODO: 可能需要处理文件失效
                    logger.opt(colors=True).warning(
                        f"第 {i} 行的文件路径 <y><u>{escape_tag(str(file_path))}</u></y> 无效，跳过"
                    )
                    continue

                if file_path in cfg.play_queue:
                    InfoBar.warning(
                        "已存在",
                        f"{item.text()}已存在播放列表",
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=500,
                        parent=self.parent(),
                    )
                    continue

                cfg.play_queue.append(file_path)
                logger.success(f"已添加 {item.text()} 到播放列表")

            InfoBar.success(
                "成功",
                "已添加所有歌曲到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )
            logger.info(f"当前播放列表:{cfg.play_queue}")

        except Exception as exc:
            InfoBar.error(
                "添加失败",
                str(exc),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=cfg.main_window,
            )
            logger.exception("添加所有歌曲到播放列表失败")
