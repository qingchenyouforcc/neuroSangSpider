from collections.abc import Callable

from loguru import logger
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView
from PyQt6.QtGui import QFontMetrics
import random
from qfluentwidgets import (
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    PushButton,
    SearchLineEdit,
    StateToolTip,
    TableWidget,
    TeachingTip,
    TeachingTipView,
    TitleLabel,
)

from src.i18n import t
from src.app_context import app_context
from src.bili_api import create_video_list_file, run_music_download, search_song_list
from src.config import ASSETS_DIR, MUSIC_DIR, cfg
from src.core.song_list import SongList
from src.core.search_core import (
    perform_search,
    sort_song_list_by_date_desc,
    sort_song_list_by_relevance,
)
from src.core.download_queue import DownloadQueueManager, DownloadTask
from src.ui.components.download_queue_dialog import DownloadQueueDialog
from src.utils.text import fix_filename, format_date_str


class SimpleThread(QThread):
    task_finished: pyqtSignal = pyqtSignal(object)

    def __init__(self, call: Callable[[], object]) -> None:
        super().__init__(None)
        self.call = call

    def run(self):
        self.task_finished.emit(self.call())


def showLoading(target):
    """加载动画实现"""
    view = TeachingTipView(
        title="",
        content="",
        image=str(ASSETS_DIR / "loading.gif"),
        isClosable=False,
    )

    view.setFixedSize(250, 250)
    view.imageLabel.setMinimumSize(250, 250)

    return TeachingTip.make(view, target, duration=-1)


class SearchInterface(QWidget):
    """搜索GUI"""

    def __init__(self, parent, main_window: FluentWindow):
        super().__init__(parent=parent)
        self._search_ = None
        self.main_window = main_window

        self.stateTooltip = None
        self.loading = None
        self.searching = False
        self.search_tip = None
        self.setObjectName("searchInterface")
        self._download_thread: SimpleThread | None = None

        # 初始化下载队列管理器
        self.download_queue = DownloadQueueManager(max_workers=3)
        self.queue_dialog: DownloadQueueDialog | None = None

        # 布局与表格
        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setWordWrap(False)
        self.tableView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  # 支持多选
        try:
            self.tableView.setTextElideMode(Qt.TextElideMode.ElideRight)  # type: ignore[attr-defined]
        except Exception:
            pass
        self.tableView.setRowCount(60)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        if header := self.tableView.verticalHeader():
            header.hide()
        if hheader := self.tableView.horizontalHeader():
            hheader.setMinimumSectionSize(60)
            hheader.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            for col in (1, 2, 3):
                hheader.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # 双击下载：双击任意单元格即触发下载当前行
        try:
            self.tableView.cellDoubleClicked.connect(self._on_table_double_click)  # type: ignore[attr-defined]
        except Exception:
            # 兼容性兜底（某些版本可用 itemDoubleClicked 信号）
            try:  # noqa: SIM105
                self.tableView.itemDoubleClicked.connect(
                    lambda _item: self._on_table_double_click(self.tableView.currentRow(), 0)
                )  # type: ignore[attr-defined]
            except Exception:
                logger.warning("未能绑定双击信号，双击下载功能不可用")

        # 标题列宽度控制参数
        self._title_max_abs_px = 800
        self._title_max_ratio = 0.6

        # 控件
        btnGroup = QWidget()
        btnLayout = QHBoxLayout(btnGroup)
        self.GetVideoBtn = PushButton(t("search.get_video_list"), self)
        self.GetVideoBtn.clicked.connect(lambda: self.getVideo_btn())
        self.DownloadBtn = PushButton(t("search.download_song"), self)
        self.DownloadBtn.clicked.connect(self.Download_btn)
        self.AddToQueueBtn = PushButton(t("search.add_to_queue"), self)
        self.AddToQueueBtn.clicked.connect(self.add_to_queue_btn)
        self.AddToQueueBtn.setToolTip(t("search.batch_add_tooltip"))
        self.QueueManagerBtn = PushButton(t("search.download_queue"), self)
        self.QueueManagerBtn.clicked.connect(self.show_queue_dialog)
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText(t("search.input_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.searchButton.clicked.connect(self.search_btn)
        self.search_input.returnPressed.connect(self.search_btn)
        btnLayout.addWidget(self.GetVideoBtn)
        btnLayout.addWidget(self.DownloadBtn)
        btnLayout.addWidget(self.AddToQueueBtn)
        btnLayout.addWidget(self.QueueManagerBtn)
        btnGroup.setLayout(btnLayout)

        # 组装
        self._layout.addWidget(TitleLabel(t("search.title"), self))
        self._layout.addWidget(self.tableView)
        self._layout.addWidget(btnGroup)
        self._layout.addWidget(self.search_input, Qt.AlignmentFlag.AlignBottom)

        # 状态
        self.search_result = SongList()
        self._last_query = ""

        # 启动后自动获取列表（无加载动画）
        QTimer.singleShot(0, lambda: self.getVideo_btn(auto=True))

    # 算法已下沉至 core，UI 层仅调用

    def on_download_finished(self, success: bool):
        """下载任务结束时的回调"""
        if self.loading:
            self.loading.close()
            self.loading = None
        self.main_window.setEnabled(True)
        self.DownloadBtn.setEnabled(True)

        if success:
            InfoBar.success(
                title=t("common.success"),
                content=t("search.download_complete"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        else:
            InfoBar.error(
                title=t("common.error"),
                content=t("search.download_failed"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        self._download_thread = None

    def getVideo_btn(self, auto: bool = False):
        """获取歌曲列表按钮功能实现"""
        try:
            logger.info("获取歌曲列表中...")
            self.GetVideoBtn.setEnabled(False)

            # 显示加载动画
            if not auto:
                self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 设置主窗口不可操作
                self.loading = showLoading(self.GetVideoBtn)
                self.main_window.setEnabled(False)

            # 显示进度条
            if not auto:
                if self.stateTooltip:
                    self.stateTooltip.setContent(t("search.list_complete"))
                    self.stateTooltip.setState(True)
                    self.stateTooltip = None
                else:
                    self.stateTooltip = StateToolTip(t("search.getting_list"), t("search.getting_list_wait"), self)
                    self.stateTooltip.move(self.stateTooltip.getSuitablePos())
                    self.stateTooltip.show()

            # 创建并启动工作线程
            self._thread = SimpleThread(create_video_list_file)
            self._thread.task_finished.connect(self.on_c_task_finished)
            self._thread.start()
        except Exception:
            logger.exception("获取歌曲列表失败")

    @staticmethod
    def do_search(search_content: str):
        result = perform_search(search_content)
        if result is None:
            logger.warning(t("search.search_result_empty"))
            InfoBar.warning(
                title=t("common.warning"),
                content=t("search.no_results"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=app_context.main_window,
                duration=2000,
            )
        return result

    def on_search_finished(self, main_search_list: SongList | None) -> None:
        # 写入表格和数据
        if main_search_list is not None:
            # 排序：按搜索相关度
            sort_song_list_by_relevance(main_search_list, self._last_query)
            self.search_result = main_search_list
            self.writeList()
        if model := self.tableView.model():
            self.tableView.setCurrentIndex(model.index(0, 0))
        # 调整除标题外的列宽
        for col in (1, 2, 3):
            self.tableView.resizeColumnToContents(col)
        # 根据窗口大小给标题列设置一个自适应上限
        self._update_title_column_width()
        self.searching = False
        self.search_input.searchButton.setEnabled(True)

        if self.loading:
            self.loading.close()
            self.loading = None

        self.main_window.setEnabled(True)

        logger.success("搜索完成！")
        if self.search_tip is not None:
            self.search_tip.setContent(t("search.search_complete"))
            self.search_tip.setState(True)
            self.search_tip = None

    def search_btn(self):
        """实现搜索按钮功能"""
        if self.searching:
            return

        self.tableView.clear()
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(
            [t("common.header_title"), t("common.video_blogger"), t("common.date"), t("common.bvid")]
        )
        self.search_result.clear()

        # 显示加载动画
        self.loading = showLoading(self.search_input)

        tip = StateToolTip(t("search.searching_song"), t("search.please_wait"), self)
        tip.move(tip.getSuitablePos())
        tip.show()
        self.search_tip = tip
        self.searching = True
        self.search_input.searchButton.setEnabled(False)

        logger.info("---搜索开始---")
        search_content = self.search_input.text().lower()
        self._last_query = search_content
        self._search_ = self.do_search(search_content)
        self.on_search_finished(self._search_)

    # 当爬虫任务结束时
    def on_c_task_finished(self):
        if self.loading:
            self.loading.close()
            self.loading = None

        self.main_window.setEnabled(True)
        self.GetVideoBtn.setEnabled(True)
        self.setWindowModality(Qt.WindowModality.NonModal)  # 恢复正常模式

        logger.success("获取歌曲列表完成！")
        if self.stateTooltip is not None:
            self.stateTooltip.setContent(t("search.list_complete"))
            self.stateTooltip.setState(True)
            self.stateTooltip = None

        # 自动填充：读取全部列表（空关键字返回全部），按时间倒序显示
        try:
            self.tableView.clear()
            self.tableView.setColumnCount(4)
            self.tableView.setHorizontalHeaderLabels(
                [t("common.header_title"), t("common.video_blogger"), t("common.date"), t("common.bvid")]
            )

            slist = search_song_list("")
            if slist is not None:
                sort_song_list_by_date_desc(slist)
                self.search_result = slist
                self.writeList()
                if model := self.tableView.model():
                    self.tableView.setCurrentIndex(model.index(0, 0))
                for col in (1, 2, 3):
                    self.tableView.resizeColumnToContents(col)
                self._update_title_column_width()
            else:
                logger.warning("自动获取后未找到任何视频数据")
        except Exception:
            logger.exception("自动填充初始列表失败")

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        # 窗口尺寸变化时更新标题列宽度上限
        self._update_title_column_width()

    def _update_title_column_width(self) -> None:
        """根据表格可视宽度与其它列宽动态设置标题列宽度的上限。"""
        try:
            vp = self.tableView.viewport()
            vpw = vp.width() if vp is not None else self.tableView.width()
            other_w = sum(self.tableView.columnWidth(c) for c in (1, 2, 3)) + 8  # padding 估计
            remaining = max(120, vpw - other_w)

            # 基于样本的自适应宽度（像素）
            suggested = self._compute_adaptive_title_width()

            max_cap = min(int(vpw * self._title_max_ratio), self._title_max_abs_px)

            if suggested and suggested > 0:
                title_w = suggested
            else:
                title_w = remaining

            # 夹紧：不能超过剩余空间与上限，也不要太小
            title_w = max(200, min(title_w, remaining, max_cap))
            self.tableView.setColumnWidth(0, title_w)
        except Exception:
            logger.exception("更新标题列宽度时出错")

    def _compute_adaptive_title_width(self) -> int:
        """按作者分组随机抽样（每个作者最多2条），基于当前字体计算标题平均像素宽度。"""
        try:
            data = self.search_result.get_data()
            if not data:
                return 0

            # 按作者分组
            groups: dict[str, list[str]] = {}
            for item in data:
                author = str(item.get("author", ""))
                title = str(item.get("title", ""))
                if not title:
                    continue
                groups.setdefault(author, []).append(title)

            fm = QFontMetrics(self.tableView.font())
            widths: list[int] = []

            for titles in groups.values():
                if not titles:
                    continue
                k = min(2, len(titles))
                # 随机抽样 k 条
                sample = random.sample(titles, k) if len(titles) > k else titles[:k]
                for s in sample:
                    w = fm.horizontalAdvance(s)
                    widths.append(w)

            if not widths:
                return 0

            avg = sum(widths) / len(widths)
            # 留出表格内边距和排序指示空间
            padding = 40
            return int(avg + padding)
        except Exception:
            logger.exception("计算自适应标题宽度失败")
            return 0

    def writeList(self):
        """将搜索结果写入表格"""
        search_result = self.search_result
        logger.info(f"总计获取 {len(search_result.get_data())} 个有效视频数据:")
        logger.info(search_result.get_data())
        self.tableView.setRowCount(len(search_result.get_data()))

        for i, songInfo in enumerate(search_result.get_data()):
            self.tableView.setItem(i, 0, QTableWidgetItem(songInfo["title"]))
            self.tableView.setItem(i, 1, QTableWidgetItem(songInfo["author"]))
            self.tableView.setItem(i, 2, QTableWidgetItem(format_date_str(songInfo["date"])))
            self.tableView.setItem(i, 3, QTableWidgetItem(songInfo["bv"]))

    def _on_table_double_click(self, row: int, _column: int) -> None:
        """表格双击时触发下载当前行。"""
        try:
            if row is None or row < 0:
                return
            # 聚焦到当前行第0列，保持与按钮下载一致的行为
            self.tableView.setCurrentCell(row, 0)
            self.Download_btn()
        except Exception:
            logger.exception("处理双击下载时出错")

    def Download_btn(self):
        index = self.tableView.currentRow()
        if index < 0:
            InfoBar.warning(
                title=t("common.info"),
                content=t("search.select_song_first"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self,
            )
            return

        # 已有下载任务在运行时阻止并发启动
        if self._download_thread is not None and self._download_thread.isRunning():
            InfoBar.info(
                title=t("common.info"),
                content=t("search.download_in_progress"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self,
            )
            return

        info = self.search_result.select_info(index)
        if not info:
            return

        fileType = cfg.download_type.value
        title = fix_filename(info["title"]).replace(" ", "").replace("_", "", 1)
        output_file = MUSIC_DIR / f"{title}.{fileType}"

        # 如果文件存在，先在主线程弹出提示窗口
        if output_file.exists():
            m = MessageBox(t("common.info"), t("search.file_exists_overwrite"), self.main_window)
            if not m.exec():
                logger.info("用户取消下载")
                return

        InfoBar.info(
            title=t("common.info"),
            content=t("search.start_download_wait"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
            parent=self,
        )

        # 显示加载动画并禁用主窗口
        self.loading = showLoading(self.DownloadBtn)
        self.DownloadBtn.setEnabled(False)
        self.main_window.setEnabled(False)

        # 创建并启动下载线程
        thread = SimpleThread(lambda idx=index, sr=self.search_result, ft=fileType: run_music_download(idx, sr, ft))
        thread.task_finished.connect(self.on_download_finished)
        thread.finished.connect(thread.deleteLater)
        self._download_thread = thread
        thread.start()

    def add_to_queue_btn(self):
        """添加选中项到下载队列"""
        selected_rows = set(item.row() for item in self.tableView.selectedIndexes())

        if not selected_rows:
            InfoBar.warning(
                title=t("common.info"),
                content=t("search.select_song_first"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self,
            )
            return

        fileType = cfg.download_type.value
        added_count = 0
        skipped_count = 0

        for row in sorted(selected_rows):
            info = self.search_result.select_info(row)
            if not info:
                continue

            title = fix_filename(info["title"]).replace(" ", "").replace("_", "", 1)
            output_file = MUSIC_DIR / f"{title}.{fileType}"

            # 创建下载任务
            task = DownloadTask(
                index=row,
                title=info["title"],
                bvid=info["bv"],
                search_list=self.search_result,
                file_type=fileType,
                output_file=output_file,
            )

            # 添加任务，检查是否重复
            if self.download_queue.add_task(task):
                added_count += 1
            else:
                skipped_count += 1

        # 显示添加结果
        if added_count > 0:
            message = t("search.added_to_queue") + f" ({added_count})"
            if skipped_count > 0:
                message += f"，{t('search.skipped_duplicates', count=skipped_count)}"

            InfoBar.success(
                title=t("common.success"),
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self,
            )
            logger.info(f"已添加 {added_count} 个任务到下载队列，跳过 {skipped_count} 个重复任务")
        else:
            InfoBar.warning(
                title=t("common.warning"),
                content=t("search.all_tasks_exist"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self,
            )
            logger.warning("所有任务都已存在于队列中")

    def show_queue_dialog(self):
        """显示下载队列对话框"""
        if self.queue_dialog is None:
            self.queue_dialog = DownloadQueueDialog(self.download_queue, self.main_window)

        self.queue_dialog.show()
        self.queue_dialog.raise_()
        self.queue_dialog.activateWindow()
