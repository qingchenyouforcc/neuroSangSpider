from loguru import logger
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    TableWidget,
    TitleLabel,
    TransparentToolButton,
)

from src.i18n import t
from src.core.player import sequencePlay
from src.core.queue_service import queue_service

# from src.app_context import app_context  # 不再直接使用全局上下文，改由 service 管理
from src.ui.widgets.play_sequence_dialog import PlaySequenceDialog
from src.utils.cover import get_cover_pixmap
from src.config import cfg
from src.ui.widgets.song_cell import build_song_cell
from src.ui.widgets.pixmap_utils import rounded_pixmap


def _rounded_pixmap(pix, radius: int):
    # 兼容旧私有方法名，内部转到通用工具
    return rounded_pixmap(pix, radius)


class PlayQueueInterface(QWidget):
    """播放队列GUI"""

    def __init__(self, parent, main_window: FluentWindow):
        super().__init__(parent=parent)
        self.main_window = main_window
        self.setObjectName("playQueueInterface")
        self.is_first_show = True  # 标记是否是第一次显示

        # 主布局与表格
        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 封面图标尺寸（可按需调整）
        self.cover_icon_size = 40
        self.tableView.setIconSize(QSize(self.cover_icon_size, self.cover_icon_size))

        # 标题栏与按钮
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
        self.sequenceButton = TransparentToolButton(FIF.SAVE, self)
        self.sequenceButton.setToolTip(t("play_queue.sequence_tooltip"))
        self.clearAllButton = TransparentToolButton(FIF.CANCEL, self)
        self.clearAllButton.setToolTip(t("play_queue.clear_all_tooltip"))

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.sequenceButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.seqPlayBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.upSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.downSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delQueueButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.clearAllButton, alignment=Qt.AlignmentFlag.AlignRight)

        self._layout.addLayout(title_layout)
        self._layout.addWidget(self.tableView)

        # 信号连接
        self.seqPlayBtn.clicked.connect(sequencePlay)
        self.upSongButton.clicked.connect(self.move_up)
        self.downSongButton.clicked.connect(self.move_down)
        self.delQueueButton.clicked.connect(self.del_queue)
        self.refreshButton.clicked.connect(self.load_play_queue)
        self.sequenceButton.clicked.connect(self.open_sequence_dialog)
        self.clearAllButton.clicked.connect(self.clear_all_queue)
        self.tableView.cellDoubleClicked.connect(self.play_selected_song)

        # 初次加载
        self.load_play_queue()

    def _build_song_cell(self, display_name: str) -> QWidget:
        # 向后兼容旧方法名，直接复用通用构建器
        return build_song_cell(display_name, parent=self.tableView)

    def load_play_queue(self):
        if not queue_service.get_queue():
            InfoBar.warning(
                t("common.info"),
                t("play_queue.empty"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self.main_window,
            )
            self.tableView.clearContents()
            self.tableView.setRowCount(0)
            return

        try:
            self.tableView.setRowCount(queue_service.length())
            show_cover = bool(cfg.enable_cover.value)
            self.tableView.setColumnCount(2 if show_cover else 1)
            if show_cover:
                self.tableView.setHorizontalHeaderLabels([t("play_queue.header_cover"), t("play_queue.header_song")])
            else:
                self.tableView.setHorizontalHeaderLabels([t("play_queue.header_song")])

            icon_size = self.cover_icon_size

            for i, song_path in enumerate(queue_service.get_queue()):
                if show_cover:
                    # 封面
                    cover_item = QTableWidgetItem()
                    pix = get_cover_pixmap(song_path, size=icon_size)
                    # 圆角半径来自设置
                    radius = max(0, int(cfg.cover_corner_radius.value))
                    pix = _rounded_pixmap(pix, radius=radius)
                    cover_item.setIcon(QIcon(pix))
                    cover_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.tableView.setItem(i, 0, cover_item)
                    # 歌曲名
                    self.tableView.setCellWidget(i, 1, self._build_song_cell(song_path.stem))
                else:
                    # 仅歌曲名
                    self.tableView.setCellWidget(i, 0, self._build_song_cell(song_path.stem))

                # 行高匹配图标
                self.tableView.setRowHeight(i, icon_size + 12)

            if show_cover:
                self.tableView.setColumnWidth(0, icon_size + 24)
                self.tableView.resizeColumnToContents(1)
            else:
                self.tableView.resizeColumnToContents(0)
        except Exception:
            logger.exception("加载歌曲列表失败")

    def move_up(self):
        index = self.tableView.currentIndex().row()
        new_index = queue_service.move_up(index)
        if model := self.tableView.model():
            self.tableView.setCurrentIndex(model.index(new_index, 0))
        self.load_play_queue()

    def move_down(self):
        index = self.tableView.currentIndex().row()
        new_index = queue_service.move_down(index)
        if model := self.tableView.model():
            self.tableView.setCurrentIndex(model.index(new_index, 0))
        self.load_play_queue()

    def del_queue(self):
        index = self.tableView.currentIndex().row()
        if index >= 0:
            try:
                removed = queue_service.remove_at(index)
                logger.info(f"删除歌曲: {removed}, 位置: {index}")
                self.load_play_queue()
            except Exception:
                logger.exception("删除歌曲失败")

    def clear_all_queue(self):
        """清空播放队列"""
        if not queue_service.get_queue():
            InfoBar.warning(
                t("common.info"),
                t("play_queue.empty"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self.main_window,
            )
            return

        # 获取当前队列长度
        queue_count = queue_service.length()

        # 创建确认对话框
        w = MessageBox(
            t("play_queue.clear_confirm"),
            t("play_queue.clear_confirm_message", count=queue_count),
            self.main_window,
        )
        if w.exec():
            try:
                queue_service.clear()
                logger.info(f"已清空播放队列，共 {queue_count} 首歌曲")
                self.load_play_queue()
                InfoBar.success(
                    t("common.info"),
                    t("play_queue.cleared_success", count=queue_count),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.main_window,
                )
            except Exception:
                logger.exception("清空播放队列失败")

    @staticmethod
    def play_selected_song(row):
        """双击播放指定行的歌曲"""
        try:
            queue_service.play_index(row)
        except Exception:
            logger.exception(f"播放 {row=} 的歌曲时出错")

    def showEvent(self, a0):
        """当页面显示时触发刷新"""
        super().showEvent(a0)

        # 第一次显示界面且播放队列为空时，尝试恢复上次的播放队列
        try:
            if self.is_first_show and not queue_service.get_queue():
                logger.info("尝试恢复上次播放队列")
                if queue_service.restore_last_queue():
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
