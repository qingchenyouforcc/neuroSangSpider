from pathlib import Path
from loguru import logger
from typing import TYPE_CHECKING, Any
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QSizePolicy
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBarPosition, TableWidget, TitleLabel, TransparentToolButton

from src.i18n import t
from src.app_context import app_context
from src.config import MUSIC_DIR, cfg
from src.utils.file import read_all_audio_info
from src.core.player import getMusicLocalStr, open_player
from src.utils.text import escape_tag
from src.ui.widgets.tipbar import open_info_tip
from src.ui.widgets.song_cell import build_song_cell, SongTableWidgetItem
from src.utils.cover import get_cover_pixmap
from src.ui.widgets.pixmap_utils import rounded_pixmap
from src.core.queue_service import queue_service

import shutil
import time
import os
import subprocess
import platform

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class NumericTableWidgetItem(QTableWidgetItem):
    """支持数值排序的表格项"""

    def __init__(self, value):
        # 存储值并显示为字符串
        super().__init__(str(value))
        self._value = int(value) if isinstance(value, (int, float)) else 0

    def data(self, role):
        # 对于排序角色，返回数值类型
        if role == Qt.ItemDataRole.EditRole or role == Qt.ItemDataRole.UserRole:
            return self._value

        # 对于显示角色，使用父类的实现（即显示为字符串）
        return super().data(role)

    def __lt__(self, other):
        # 确保排序时比较数值大小
        if isinstance(other, NumericTableWidgetItem):
            return self._value < other._value
        return super().__lt__(other)

    def setText(self, atext):
        """设置显示文本，但不影响内部排序值"""
        super().setText(atext)


class LocalPlayerInterface(QWidget):
    """本地播放器GUI"""

    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.main_window = main_window
        self._first_load = True  # 标记首次加载，用于控制无效文件提示

        self.setAcceptDrops(True)
        self.setObjectName("locPlayerInterface")
        self.setStyleSheet("LocPlayerInterface{background: transparent}")

        # 布局与表格
        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)
        self.tableView.setBorderVisible(True)
        self.tableView.setSortingEnabled(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 封面图标尺寸（与播放队列保持一致）
        self.cover_icon_size = 40
        self.tableView.setIconSize(QSize(self.cover_icon_size, self.cover_icon_size))

        # 标题栏
        title_layout = QHBoxLayout()
        self.titleLabel = TitleLabel(t("local_player.title"), self)
        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip(t("local_player.refresh_tooltip"))
        self.addQueueButton = TransparentToolButton(FIF.ADD, self)
        self.addQueueButton.setToolTip(t("local_player.add_queue_tooltip"))
        self.openPlayer = TransparentToolButton(FIF.MUSIC, self)
        self.openPlayer.setToolTip(t("local_player.open_player_tooltip"))
        self.openInfoTip = TransparentToolButton(FIF.INFO, self)
        self.openInfoTip.setToolTip(t("local_player.open_info_tip_tooltip"))
        self.delSongBtn = TransparentToolButton(FIF.DELETE, self)
        self.delSongBtn.setToolTip(t("local_player.delete_tooltip"))
        self.addQueueAllBtn = TransparentToolButton(FIF.CHEVRON_DOWN_MED, self)
        self.addQueueAllBtn.setToolTip(t("local_player.add_all_tooltip"))
        self.openFolderBtn = TransparentToolButton(FIF.FOLDER, self)
        self.openFolderBtn.setToolTip(t("local_player.open_folder_tooltip"))

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.openInfoTip, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.openPlayer, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.openFolderBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.addQueueAllBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delSongBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.addQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self._layout.addLayout(title_layout)
        self._layout.addWidget(self.tableView)

        # 信号
        self.tableView.cellDoubleClicked.connect(self.play_selected_song)
        self.refreshButton.clicked.connect(self.load_local_songs)
        self.addQueueButton.clicked.connect(self.add_to_queue)
        self.openPlayer.clicked.connect(open_player)
        self.openInfoTip.clicked.connect(open_info_tip)
        self.delSongBtn.clicked.connect(self.del_song)
        self.addQueueAllBtn.clicked.connect(self.add_all_to_queue)
        self.openFolderBtn.clicked.connect(self.open_music_folder)

        # 监听表头点击事件，禁用封面列排序
        header = self.tableView.horizontalHeader()
        header.sectionClicked.connect(self.on_header_clicked)

        self._setup_table_resize_policy()

        self.load_local_songs()

    def on_header_clicked(self, logical_index):
        """处理表头点击事件，仅禁用封面列的排序"""
        show_cover = bool(cfg.enable_cover.value)
    
        # 禁用封面列的排序，允许文件名列排序
        if show_cover and logical_index == 0:
            # 点击的是封面列，不允许排序，恢复之前的排序状态
            header = self.tableView.horizontalHeader()
            current_sort = header.sortIndicatorSection()
            current_order = header.sortIndicatorOrder()
    
            # 找到第一个可排序的列（文件名列）
            sort_col = 1 if show_cover else 0
    
            # 如果当前点击的是封面列，恢复为文件名列排序
            if current_sort == logical_index:
                header.setSortIndicator(sort_col, current_order)
                self.tableView.sortItems(sort_col, current_order)

    def _setup_table_resize_policy(self):
        """设置表格的列宽策略"""
        header = self.tableView.horizontalHeader()
        show_cover = bool(cfg.enable_cover.value)

        if show_cover:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

            self.tableView.setColumnWidth(0, self.cover_icon_size + 50)
            self.tableView.setColumnWidth(2, 100)
            self.tableView.setColumnWidth(3, 120)
        else:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

            self.tableView.setColumnWidth(1, 100)
            self.tableView.setColumnWidth(2, 120)

        self.tableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header.setMinimumSectionSize(60)

        # 使表格随窗口大小变化
        self.tableView.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _name_col(self) -> int:
        """根据是否显示封面返回文件名所在列索引"""
        show_cover = bool(cfg.enable_cover.value)
        return 1 if show_cover else 0

    def _duration_col(self) -> int:
        """根据是否显示封面返回时长所在列索引"""
        show_cover = bool(cfg.enable_cover.value)
        return 2 if show_cover else 1

    def _count_col(self) -> int:
        """根据是否显示封面返回播放次数所在列索引"""
        show_cover = bool(cfg.enable_cover.value)
        return 3 if show_cover else 2

    def load_local_songs(self):
        try:
            # 清理无效文件
            self._clean_invalid_files()
    
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
            show_cover = bool(cfg.enable_cover.value)
            if show_cover:
                self.tableView.setColumnCount(4)
                self.tableView.setHorizontalHeaderLabels(
                    [
                        t("play_queue.header_cover"),
                        t("local_player.header_filename"),
                        t("local_player.header_duration"),
                        t("local_player.header_play_count"),
                    ]
                )
            else:
                self.tableView.setColumnCount(3)
                self.tableView.setHorizontalHeaderLabels(
                    [
                        t("local_player.header_filename"),
                        t("local_player.header_duration"),
                        t("local_player.header_play_count"),
                    ]
                )
    
            # 设置列宽策略
            self._setup_table_resize_policy()
    
            for i, (filename, duration) in enumerate(songs):
                # 用于排序与数据存储的表格项（始终设置在文件名列）
                name_col = self._name_col()
    
                # 为文件名列添加支持排序的表格项
                name_item = SongTableWidgetItem(filename)
                self.tableView.setItem(i, name_col, name_item)
                
                # 视觉展示采用可复用的歌曲单元格控件（解析标签显示副标题）
                song_cell = build_song_cell(filename, parent=self.tableView, parse_brackets=True, compact=False)
                song_cell.layout().setContentsMargins(30, 0, 0, 5)  # 让文件名向右下偏移
                self.tableView.setCellWidget(
                    i,
                    name_col,
                    song_cell,
                )

                # 封面列
                if show_cover:
                    cover_item = QTableWidgetItem()
                    audio_path = MUSIC_DIR / filename
                    pix = get_cover_pixmap(audio_path, size=self.cover_icon_size)
                    radius = max(0, int(cfg.cover_corner_radius.value))
                    pix = rounded_pixmap(pix, radius)
                    cover_item.setIcon(QIcon(pix))
                    cover_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.tableView.setItem(i, 0, cover_item)

                # 行高匹配封面
                self.tableView.setRowHeight(i, self.cover_icon_size + 12)

                # 时长也应该按照数字排序
                duration_item = NumericTableWidgetItem(duration)
                duration_mod_second = duration % 60 * 10 if 0 <= duration % 60 < 10 else duration % 60
                duration_item.setText(f"{int(duration / 60):02}:{duration_mod_second:.0f}")
                # 时长列位置
                self.tableView.setItem(i, self._duration_col(), duration_item)

                # 从配置中获取播放次数
                play_count = cfg.play_count.value.get(str(filename), 0)
                logger.debug(f"歌曲 {filename} 的播放次数: {play_count}")

                # 创建一个特殊的表格项，确保按照数字大小排序
                count_item = NumericTableWidgetItem(play_count)
                self.tableView.setItem(i, self._count_col(), count_item)
    
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

    def select_and_highlight_song(self, filename: str):
        """在本地播放器中选中并高亮显示指定文件名的歌曲"""
        try:
            name_col = self._name_col()
            # 遍历所有行查找匹配的文件名
            for row in range(self.tableView.rowCount()):
                item = self.tableView.item(row, name_col)
                if item and item.data(Qt.ItemDataRole.UserRole) == filename:
                    # 选中该行
                    self.tableView.selectRow(row)
                    # 滚动到该行
                    self.tableView.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                    logger.info(f"已在本地播放器中选中歌曲: {filename}")
                    return True

            logger.warning(f"未在本地播放器中找到歌曲: {filename}")
            return False
        except Exception as e:
            logger.exception(f"选中歌曲时出错: {e}")
            return False

    def play_selected_song(self, row, column=None):
        """双击播放指定行的歌曲

        Args:
            row: 行号
            column: 列号，无论点击哪一列，都会传递给第0列（文件名列）获取歌曲信息
        """
        try:
            # 无论点击哪一列，取文件名列的隐藏数据
            item = self.tableView.item(row, self._name_col())
            assert item is not None, t("local_player.current_line_no_sang_info")
            file_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
            file_path = getMusicLocalStr(str(file_name))
            if file_path is None or not file_path.exists():
                InfoBar.error(
                    t("common.play_song_error"),
                    t("local_player.no_local_songs_found"),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=500,
                    parent=self.parent(),
                )
                return

            url = QUrl.fromLocalFile(str(file_path))
            self.main_window.player_bar.player.setSource(url)
            self.main_window.player_bar.player.play()

            app_context.playing_now = str(file_name)

            open_info_tip()

            # 确保歌曲在播放队列中 & 更新索引（通过服务）
            idx = queue_service.ensure_in_queue(file_path)
            queue_service.set_current_index(idx)
            logger.info(f"当前播放歌曲队列位置：{idx}")
        except Exception:
            logger.exception("播放选中歌曲失败")

    def add_to_queue(self, row=None):
        """添加到播放列表

        Args:
            row: 指定行号，如果为None或False(按钮点击信号)则使用当前选中行
        """
        try:
            logger.debug(f"add_to_queue 被调用, row={row}, type={type(row)}")

            # 确定要处理的项：如果指定了有效的行号，则获取该行的第0列项，否则使用当前选中项
            # 注意: PyQt6的clicked信号会传递False，需要排除
            # bool是int的子类，需要先排除bool类型
            if isinstance(row, int) and not isinstance(row, bool) and row >= 0:
                logger.debug(f"使用指定行号: {row}")
                item = self.tableView.item(row, self._name_col())
            else:
                logger.debug("使用当前选中行")
                current_item = self.tableView.currentItem()
                if current_item is None:
                    logger.warning("没有选中的歌曲")
                    InfoBar.warning(
                        t("common.warning"),
                        "请先选中一首歌曲",
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=1500,
                        parent=self.parent(),
                    )
                    return

                # 获取当前选中项所在行的第0列项（文件名列）
                current_row = current_item.row()
                logger.debug(f"当前选中行: {current_row}")
                item = self.tableView.item(current_row, self._name_col())

            if item is None:
                logger.warning("无法获取歌曲信息")
                return

            # 获取文件路径并添加到播放队列
            file_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
            if file_name and (file_path := getMusicLocalStr(str(file_name))):
                # 使用服务添加避免重复
                if not queue_service.add(file_path):
                    logger.debug(f"歌曲 {file_name} 已在播放列表中")
                    return
                InfoBar.success(
                    t("common.success"),
                    t("local_player.add_sang_success", name=str(file_name)),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self.parent(),
                )
                logger.info("已添加到播放队列")
            else:
                InfoBar.error(
                    t("common.fail"),
                    t("local_player.add_sang_error"),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=app_context.main_window,
                )
        except Exception:
            logger.exception("添加到播放列表失败")

    def del_song(self):
        """删除列表项文件"""
        try:
            # 获取当前选中项
            current_item = self.tableView.currentItem()
            if current_item is None:
                logger.warning("没有选中的歌曲")
                return

            # 获取当前选中项所在行的第0列项（文件名列）
            current_row = current_item.row()
            item = self.tableView.item(current_row, self._name_col())

            if item is None:
                logger.warning("无法获取歌曲信息")
                return

            # 获取文件路径并删除
            file_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
            if file_name and (file_path := getMusicLocalStr(str(file_name))) and (fp := Path(file_path)).exists():
                # 删除文件
                fp.unlink()

                # 如果文件在播放队列中，从队列中移除
                # 同步移除播放队列中的文件
                queue_service.remove_path(file_path)
                logger.info(f"已从播放队列中移除: {file_name}")

                # 显示成功消息
                InfoBar.success(
                    t("common.success"),
                    t("local_player.delete_sang_success", name=str(file_name)),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1000,
                    parent=self.parent(),
                )

                # 重新加载歌曲列表
                self.load_local_songs()
            else:
                InfoBar.error(
                    t("common.fail"),
                    t("local_player.delete_sang_error"),
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self.parent(),
                )

        except Exception as e:
            logger.exception(f"删除歌曲失败: {e}")
            InfoBar.error(
                t("common.delete_failed"),
                t("local_player.delete_sang_failed_with_error", error=str(e)),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )

    def add_all_to_queue(self):
        """添加列表所有歌曲到播放列表"""
        try:
            # 统计信息
            total_files = self.tableView.rowCount()
            added_count = 0
            already_exists_count = 0
            invalid_count = 0

            # 显示进度开始提示
            InfoBar.info(
                "添加中",
                t("local_player.adding_sang_to_queue", number=total_files),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )

            name_col = self._name_col()
            for i in range(total_files):
                # 在每次循环中都获取当前行的第0列（文件名列）项
                item = self.tableView.item(i, name_col)
                if item is None:
                    logger.warning(f"第 {i} 行没有歌曲信息，跳过")
                    continue

                file_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
                file_path = getMusicLocalStr(str(file_name)) if file_name else None
                if file_path is None or not file_path.exists():
                    # 处理文件失效
                    logger.opt(colors=True).warning(f"第 {i} 行的文件无效，跳过: {escape_tag(str(file_name))}")
                    # 记录失效文件，用于后续清理表格
                    self._mark_invalid_file(str(file_name))
                    invalid_count += 1
                    continue

                # 通过服务添加
                if queue_service.add(file_path):
                    added_count += 1
                else:
                    already_exists_count += 1
                filename = str(file_name) if file_name else t("common.unknown_file")
                logger.success(f"已添加 {filename} 到播放列表")

            # 显示添加结果的详细信息
            message = t("local_player.added_count", added_count=added_count)
            if already_exists_count > 0:
                message += t("local_player.already_exists_count", already_exists_count=already_exists_count)
            if invalid_count > 0:
                message += t("local_player.invalid_count", invalid_count=invalid_count)

            InfoBar.success(
                t("common.add_song_success"),
                message,
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent(),
            )

            logger.info(f"添加完成: 新增 {added_count}, 已存在 {already_exists_count}, 无效 {invalid_count}")
            logger.debug(f"当前播放列表大小: {queue_service.length()}")

        except Exception as exc:
            InfoBar.error(
                t("common.add_song_failed"),
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
                    if Path(file_path).suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a"]:
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
                    if file_path.is_file() and file_path.suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a"]:
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
            if file_path.is_file() and file_path.suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a"]:
                try:
                    self._import_audio_file(file_path)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"导入文件 {file_path} 失败: {e}")

        return imported_count

    def _show_import_success_message(self, count):
        """显示导入成功的消息"""
        InfoBar.success(
            t("common.import_success"),
            t("local_player.import_sang_success_count", count=count),
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def _mark_invalid_file(self, filename: str):
        """标记无效文件并从配置中清除其相关信息

        Args:
            filename: 文件名
        """
        try:
            # 从播放计数中移除
            if filename in cfg.play_count.value:
                logger.info(f"从播放计数中移除无效文件: {filename}")
                del cfg.play_count.value[filename]
                cfg.save()

            # 从播放序列中移除
            play_sequences = cfg.play_sequences.value
            for seq_name, files in list(play_sequences.items()):
                if filename in files:
                    logger.info(f"从播放序列 {seq_name} 中移除无效文件: {filename}")
                    play_sequences[seq_name] = [f for f in files if f != filename]
                    # 如果序列变为空，考虑是否需要删除该序列
                    if not play_sequences[seq_name]:
                        logger.warning(f"播放序列 {seq_name} 已变为空")

            # 更新播放序列配置
            cfg.play_sequences.value = play_sequences
            cfg.save()

            # 从恢复的播放队列中移除
            last_play_data = cfg.last_play_queue.value
            if isinstance(last_play_data, dict) and "queue" in last_play_data:
                queue = last_play_data.get("queue", [])
                if isinstance(queue, list) and filename in queue:
                    logger.info(f"从恢复的播放队列中移除无效文件: {filename}")
                    last_play_data["queue"] = [f for f in queue if f != filename]
                    cfg.last_play_queue.value = last_play_data
                    cfg.save()
        except Exception as e:
            logger.error(f"标记无效文件时出错: {e}")

    def _clean_invalid_files(self):
        """清理界面上的无效文件并更新相关配置"""
        try:
            invalid_files = []
            name_col = self._name_col()

            # 扫描表格中的所有文件
            for i in range(self.tableView.rowCount()):
                item = self.tableView.item(i, name_col)
                if item is None:
                    continue
                file_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
                file_path = getMusicLocalStr(str(file_name)) if file_name else None
                if file_path is None or not file_path.exists():
                    invalid_files.append(str(file_name))  # 如果有无效文件，进行清理
            if invalid_files:
                # 打印无效文件列表
                logger.warning(f"发现 {len(invalid_files)} 个无效文件")
                for f in invalid_files:
                    logger.warning(f"  - {f}")
                    self._mark_invalid_file(f)

                # 仅当首次加载时显示清理提示，避免频繁打扰用户
                if hasattr(self, "_first_load") and self._first_load:
                    InfoBar.info(
                        t("local_player.remove_invalid_files_title"),
                        t("local_player.remove_invalid_files_desc", count=len(invalid_files)),
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self,
                    )

            # 标记非首次加载
            if not hasattr(self, "_first_load"):
                self._first_load = False
            else:
                self._first_load = False
        except Exception as e:
            logger.exception(f"清理无效文件时出错: {e}")

    def open_music_folder(self):
        """打开音乐文件夹"""
        try:
            music_dir = str(MUSIC_DIR.absolute())

            # 确保文件夹存在
            if not MUSIC_DIR.exists():
                MUSIC_DIR.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建音乐文件夹: {music_dir}")

            # 根据操作系统打开文件夹
            system = platform.system()
            if system == "Windows":
                os.startfile(music_dir)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", music_dir])
            else:  # Linux
                subprocess.Popen(["xdg-open", music_dir])

            logger.info(f"已打开音乐文件夹: {music_dir}")
        except Exception as e:
            logger.exception(f"打开音乐文件夹失败: {e}")
            InfoBar.error(
                t("common.fail"),
                t("local_player.open_folder_error"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent(),
            )

    def showEvent(self, a0):
        """当页面显示时触发刷新"""
        super().showEvent(a0)
        self.load_local_songs()