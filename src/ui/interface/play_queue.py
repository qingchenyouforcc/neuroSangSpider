from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, InfoBar, InfoBarPosition, TableWidget, TitleLabel, TransparentToolButton

from i18n import t
from src.core.player import playSongByIndex, sequencePlay
from src.app_context import app_context
from src.ui.widgets.play_sequence_dialog import PlaySequenceDialog


class PlayQueueInterface(QWidget):
    """播放队列GUI"""

    def __init__(self, parent, main_window: FluentWindow):
        super().__init__(parent=parent)
        self.main_window = main_window
        self.setObjectName("playQueueInterface")
        self.is_first_show = True  # 标记是否是第一次显示

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

        self.titleLabel = TitleLabel(t("play_queue.title"), self)

        self.seqPlayBtn = TransparentToolButton(FIF.MENU, self)
        self.seqPlayBtn.setToolTip(t("play_queue.seq_play_tooltip"))

        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip(t("play_queue.refresh_tooltip"))

        self.delQueueButton = TransparentToolButton(FIF.DELETE, self)
        self.delQueueButton.setToolTip(t("play_queue.delete_tooltip"))

        self.upSongButton = TransparentToolButton(FIF.UP, self)
        self.upSongButton.setToolTip(t("play_queue.up_tooltip"))

        self.downSongButton = TransparentToolButton(FIF.DOWN, self)
        self.downSongButton.setToolTip(t("play_queue.down_tooltip"))
        
        # 添加播放序列管理按钮
        self.sequenceButton = TransparentToolButton(FIF.SAVE, self)
        self.sequenceButton.setToolTip(t("play_queue.sequence_tooltip"))

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.sequenceButton, alignment=Qt.AlignmentFlag.AlignRight)
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
        self.sequenceButton.clicked.connect(self.open_sequence_dialog)
        self.tableView.cellDoubleClicked.connect(self.play_selected_song)

        self.load_play_queue()

    def load_play_queue(self):
        if not app_context.play_queue:
            InfoBar.warning(
                t("common.info"),
                t("play_queue.empty"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self.main_window,
            )
            self.tableView.clear()
            return

        try:
            self.tableView.setRowCount(len(app_context.play_queue))
            self.tableView.setColumnCount(1)
            self.tableView.setHorizontalHeaderLabels([t("play_queue.header_song")])

            for i, song in enumerate(app_context.play_queue):
                self.tableView.setItem(i, 0, QTableWidgetItem(song.name))

            self.tableView.resizeColumnsToContents()
        except Exception:
            logger.exception("加载歌曲列表失败")

    def move_up(self):
        index = self.tableView.currentIndex().row()
        if index > 0:
            app_context.play_queue[index - 1], app_context.play_queue[index] = (
                app_context.play_queue[index],
                app_context.play_queue[index - 1],
            )
            if model := self.tableView.model():
                self.tableView.setCurrentIndex(model.index(index - 1, 0))

            if app_context.play_queue_index == index:
                app_context.play_queue_index -= 1

        self.load_play_queue()

    def move_down(self):
        index = self.tableView.currentIndex().row()
        if index < len(app_context.play_queue) - 1:
            app_context.play_queue[index + 1], app_context.play_queue[index] = (
                app_context.play_queue[index],
                app_context.play_queue[index + 1],
            )
            if model := self.tableView.model():
                self.tableView.setCurrentIndex(model.index(index + 1, 0))

            if app_context.play_queue_index == index:
                app_context.play_queue_index += 1

        self.load_play_queue()

    def del_queue(self):
        index = self.tableView.currentIndex().row()
        if index >= 0:
            try:
                logger.info(f"删除歌曲: {app_context.play_queue[index]}, 位置: {index}")
                app_context.play_queue.pop(index)
                self.load_play_queue()
            except Exception:
                logger.exception("删除歌曲失败")

    @staticmethod
    def play_selected_song(row):
        """双击播放指定行的歌曲"""
        try:
            app_context.play_queue_index = row
            playSongByIndex()
        except Exception:
            logger.exception(f"播放 {row=} 的歌曲时出错")
            
    def showEvent(self, a0):
        """当页面显示时触发刷新"""
        super().showEvent(a0)
        
        # 第一次显示界面且播放队列为空时，尝试恢复上次的播放队列
        try:
            if self.is_first_show and not app_context.play_queue:
                from src.core.player import restore_last_play_queue
                
                logger.info("尝试恢复上次播放队列")
                if restore_last_play_queue():
                    InfoBar.success(
                        t("common.info"),
                        t("play_queue.restored"),
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        duration=2000,
                        parent=self.main_window,
                    )
                self.is_first_show = False
        except Exception as e:
            logger.exception(f"恢复播放队列时出错: {e}")
            
        self.load_play_queue()
        
        # 打开播放序列对话框时，检查并应用当前主题
        
    def open_sequence_dialog(self):
        """打开播放序列管理对话框"""
        logger.info("正在打开播放序列管理对话框")
        try:
            # 创建对话框并设置父窗口
            dialog = PlaySequenceDialog(self.main_window)
            
            # 确保对话框显示前应用当前主题样式
            dialog._update_card_style()
            
            # 显示对话框
            logger.info("即将显示播放序列对话框")
            # 使用show()和exec()的组合以确保对话框显示在前端
            dialog.show()
            result = dialog.exec()
            logger.info(f"对话框返回结果: {result}")
            
            if result:
                # 对话框被接受（如加载了序列），刷新界面
                self.load_play_queue()
        except Exception:
            logger.exception("打开播放序列对话框时出错")