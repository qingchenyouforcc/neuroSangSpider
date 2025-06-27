from pathlib import Path
from loguru import logger
from typing import TYPE_CHECKING, Any
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBarPosition, TableWidget, TitleLabel, TransparentToolButton

from src.app_context import app_context
from src.config import MUSIC_DIR, cfg
from src.utils.file import read_all_audio_info
from src.core.player import getMusicLocal, open_player
from src.utils.text import escape_tag
from src.ui.widgets.tipbar import open_info_tip

import shutil
import time

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class LocalPlayerInterface(QWidget):
    """本地播放器GUI"""

    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.main_window = main_window
        
        self.setAcceptDrops(True)
        self.setObjectName("locPlayerInterface")
        self.setStyleSheet("LocPlayerInterface{background: transparent}")

        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        self.tableView.setBorderVisible(True)
        self.tableView.setSortingEnabled(True) 
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
            # 记录当前排序状态
            header = self.tableView.horizontalHeader()
            sort_column = -1
            sort_order = Qt.SortOrder.AscendingOrder
            
            try:
                # 尝试获取当前排序状态
                if header:
                    sort_column = header.sortIndicatorSection()
                    sort_order = header.sortIndicatorOrder()
            except Exception:
                logger.debug("无法获取当前排序状态")
            
            # 临时关闭排序功能，防止添加数据时自动排序
            self.tableView.setSortingEnabled(False)
            
            self.tableView.clear()
            songs = read_all_audio_info(MUSIC_DIR)
            self.tableView.setRowCount(len(songs))
            self.tableView.setColumnCount(3)
            self.tableView.setHorizontalHeaderLabels(["文件名", "时长", "播放次数"])

            for i, (filename, duration) in enumerate(songs):
                file_item = QTableWidgetItem(filename)
                # 存储原始文件名作为隐藏数据，用于后续查找
                file_item.setData(Qt.ItemDataRole.UserRole, filename)
                
                self.tableView.setItem(i, 0, file_item)
                self.tableView.setItem(i, 1, QTableWidgetItem(f"{duration}s"))
            
                # 从配置中获取播放次数
                play_count = cfg.play_count.value.get(str(filename), 0)
                logger.debug(f"歌曲 {filename} 的播放次数: {play_count}")
                
                # 确保播放次数项可以正确排序（数字排序而非字符串排序）
                count_item = QTableWidgetItem()
                count_item.setData(Qt.ItemDataRole.DisplayRole, str(play_count))  
                count_item.setData(Qt.ItemDataRole.UserRole, int(play_count))  
                self.tableView.setItem(i, 2, count_item)
            
            self.tableView.resizeColumnsToContents()
            
            # 重新启用排序并应用之前的排序设置
            self.tableView.setSortingEnabled(True)
            
            try:
                # 尝试恢复排序状态
                if sort_column >= 0 and header:
                    header.setSortIndicator(sort_column, sort_order)
            except Exception:
                logger.debug("无法恢复之前的排序状态")
                
        except Exception:
            logger.exception("加载本地歌曲失败")

    def play_selected_song(self, row):
        """双击播放指定行的歌曲"""
        try:
            item = self.tableView.item(row, 0)
            assert item is not None, "当前行没有歌曲信息"

            file_path = getMusicLocal(item)
            if file_path is None or not file_path.exists():
                InfoBar.error(
                    "播放失败",
                    "未找到本地歌曲文件",
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=500,
                    parent=self.parent(),
                )
                return

            url = QUrl.fromLocalFile(str(file_path))
            self.main_window.player_bar.player.setSource(url)
            self.main_window.player_bar.player.play()

            app_context.playing_now = item.text()

            open_info_tip()

            self.add_to_queue()
            app_context.play_queue_index = app_context.play_queue.index(file_path)
            logger.info(f"当前播放歌曲队列位置：{app_context.play_queue_index}")
        except Exception:
            logger.exception("播放选中歌曲失败")

    def add_to_queue(self):
        """添加到播放列表"""
        item = self.tableView.currentItem()
        assert item is not None, "当前行没有歌曲信息"

        if file_path := getMusicLocal(item):
            if file_path in app_context.play_queue:
                return

            app_context.play_queue.append(file_path)
            InfoBar.success(
                "成功",
                f"已添加{item.text()}到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )
            logger.info(f"当前播放列表:{app_context.play_queue}")
        else:
            InfoBar.error(
                "失败",
                "添加失败！",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=app_context.main_window,
            )

    def del_song(self):
        """删除列表项文件"""
        try:
            item = self.tableView.currentItem()
            if (file_path := getMusicLocal(item)) and (fp := Path(file_path)).exists():
                fp.unlink()

            if file_path in app_context.play_queue:
                app_context.play_queue.remove(file_path)

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

                if file_path in app_context.play_queue:
                    InfoBar.warning(
                        "已存在",
                        f"{item.text()}已存在播放列表",
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=500,
                        parent=self.parent(),
                    )
                    continue

                app_context.play_queue.append(file_path)
                logger.success(f"已添加 {item.text()} 到播放列表")

            InfoBar.success(
                "成功",
                "已添加所有歌曲到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )
            logger.info(f"当前播放列表:{app_context.play_queue}")

        except Exception as exc:
            InfoBar.error(
                "添加失败",
                str(exc),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=app_context.main_window,
            )
            logger.exception("添加所有歌曲到播放列表失败")

    def dragEnterEvent(self, a0: Any):
        """当用户开始拖动文件到窗口时触发"""
        try:
            # 检查是否为文件拖入
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                # 检查是否为音频文件
                for url in mime_data.urls():
                    file_path = url.toLocalFile()
                    if Path(file_path).suffix.lower() in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                        a0.acceptProposedAction()
                        return
            a0.ignore()
        except Exception as e:
            logger.exception(f"拖拽进入事件处理失败: {e}")
        
    def dragMoveEvent(self, a0: Any):
        """当用户在窗口内移动拖放物时触发"""
        try:
            if a0.mimeData() and a0.mimeData().hasUrls():
                a0.acceptProposedAction()
            else:
                a0.ignore()
        except Exception as e:
            logger.exception(f"拖拽移动事件处理失败: {e}")
            
    def dropEvent(self, a0: Any):
        """当用户释放拖放物时触发"""
        try:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasUrls():
                imported_count = 0
                for url in mime_data.urls():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                        try:
                            self._import_audio_file(file_path)
                            imported_count += 1
                        except Exception as e:
                            logger.exception(f"导入文件失败: {e}")
                    elif file_path.is_dir():
                        # 处理文件夹导入
                        folder_import_count = self._import_audio_folder(file_path)
                        imported_count += folder_import_count
                
                if imported_count > 0:
                    self.load_local_songs()  # 刷新歌曲列表
                    self._show_import_success_message(imported_count)
                
                a0.acceptProposedAction()
            else:
                a0.ignore()
        except Exception as e:
            logger.exception(f"拖拽释放事件处理失败: {e}")
            
    def _import_audio_file(self, source_path: Path) -> Path:
        """导入音频文件到音乐目录"""
        target_path = MUSIC_DIR / source_path.name
        
        # 如果文件已存在，添加时间戳
        if target_path.exists():
            timestamp = int(time.time())
            new_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            target_path = MUSIC_DIR / new_name
        
        # 复制文件
        shutil.copy2(source_path, target_path)
        
        logger.info(f"已导入音频文件: {target_path}")
        return target_path
        
    def _import_audio_folder(self, folder_path: Path) -> int:
        """导入文件夹中的所有音频文件，返回导入的文件数量"""
        if not folder_path.is_dir():
            return 0
            
        imported_count = 0
        for file_path in folder_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                try:
                    self._import_audio_file(file_path)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"导入文件 {file_path} 失败: {e}")
        
        return imported_count
        
    def _show_import_success_message(self, count):
        """显示导入成功的消息"""
        InfoBar.success(
            "导入成功",
            f"已成功导入 {count} 首歌曲",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def showEvent(self, a0):
        """当页面显示时触发刷新"""
        super().showEvent(a0)
        self.load_local_songs()