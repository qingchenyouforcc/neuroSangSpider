from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, InfoBar, InfoBarPosition, TableWidget, TitleLabel, TransparentToolButton

from src.config import cfg
from src.core.player import playSongByIndex, sequencePlay


class PlayQueueInterface(QWidget):
    """播放队列GUI"""

    def __init__(self, parent, main_window: FluentWindow):
        super().__init__(parent=parent)
        self.main_window = main_window
        self.setObjectName("playQueueInterface")

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

        self.titleLabel = TitleLabel("播放列表", self)

        self.seqPlayBtn = TransparentToolButton(FIF.MENU, self)
        self.seqPlayBtn.setToolTip("按顺序播放(不改变播放模式)")

        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip("刷新歌曲列表")

        self.delQueueButton = TransparentToolButton(FIF.DELETE, self)
        self.delQueueButton.setToolTip("从播放列表中删除")

        self.upSongButton = TransparentToolButton(FIF.UP, self)
        self.upSongButton.setToolTip("将当前歌曲上移")

        self.downSongButton = TransparentToolButton(FIF.DOWN, self)
        self.downSongButton.setToolTip("将当前歌曲下移")

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.seqPlayBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.upSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.downSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self._layout.addLayout(title_layout)
        self._layout.addWidget(self.tableView)

        self.seqPlayBtn.clicked.connect(sequencePlay)
        self.upSongButton.clicked.connect(self.move_up)
        self.downSongButton.clicked.connect(self.move_down)
        self.delQueueButton.clicked.connect(self.del_queue)
        self.refreshButton.clicked.connect(self.load_play_queue)
        self.tableView.cellDoubleClicked.connect(self.play_selected_song)

        self.load_play_queue()

    def load_play_queue(self):
        if not cfg.play_queue:
            InfoBar.warning(
                "提示",
                "播放列表为空",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self.main_window,
            )
            self.tableView.clear()
            return

        try:
            self.tableView.setRowCount(len(cfg.play_queue))
            self.tableView.setColumnCount(1)
            self.tableView.setHorizontalHeaderLabels(["歌曲"])

            for i, song in enumerate(cfg.play_queue):
                self.tableView.setItem(i, 0, QTableWidgetItem(song.name))

            self.tableView.resizeColumnsToContents()
        except Exception:
            logger.exception("加载歌曲列表失败")

    def move_up(self):
        index = self.tableView.currentIndex().row()
        if index > 0:
            cfg.play_queue[index - 1], cfg.play_queue[index] = (
                cfg.play_queue[index],
                cfg.play_queue[index - 1],
            )
            if model := self.tableView.model():
                self.tableView.setCurrentIndex(model.index(index - 1, 0))

            if cfg.play_queue_index == index:
                cfg.play_queue_index -= 1

        self.load_play_queue()

    def move_down(self):
        index = self.tableView.currentIndex().row()
        if index < len(cfg.play_queue) - 1:
            cfg.play_queue[index + 1], cfg.play_queue[index] = (
                cfg.play_queue[index],
                cfg.play_queue[index + 1],
            )
            if model := self.tableView.model():
                self.tableView.setCurrentIndex(model.index(index + 1, 0))

            if cfg.play_queue_index == index:
                cfg.play_queue_index += 1

        self.load_play_queue()

    def del_queue(self):
        index = self.tableView.currentIndex().row()
        if index >= 0:
            try:
                logger.info(f"删除歌曲: {cfg.play_queue[index]}, 位置: {index}")
                cfg.play_queue.pop(index)
                self.load_play_queue()
            except Exception:
                logger.exception("删除歌曲失败")

    @staticmethod
    def play_selected_song(row):
        """双击播放指定行的歌曲"""
        try:
            cfg.play_queue_index = row
            playSongByIndex()
        except Exception:
            logger.exception(f"播放 {row=} 的歌曲时出错")
