from collections.abc import Callable

from bilibili_api import sync
from loguru import logger
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget
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

from i18n import t
from src.app_context import app_context
from src.bili_api import create_video_list_file, run_music_download, search_on_bilibili, search_song_list
from src.config import ASSETS_DIR, MUSIC_DIR, cfg
from src.core.song_list import SongList
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

        self._layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        # enable border
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(60)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        if header := self.tableView.verticalHeader():
            header.hide()

        btnGroup = QWidget()
        btnLayout = QHBoxLayout(btnGroup)

        self.GetVideoBtn = PushButton(t("search.get_video_list"), self)
        self.GetVideoBtn.clicked.connect(lambda: self.getVideo_btn())

        self.DownloadBtn = PushButton(t("search.download_song"), self)
        self.DownloadBtn.clicked.connect(self.Download_btn)

        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText(t("search.input_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.searchButton.clicked.connect(self.search_btn)
        self.search_input.returnPressed.connect(self.search_btn)

        btnLayout.addWidget(self.GetVideoBtn)
        btnLayout.addWidget(self.DownloadBtn)
        btnGroup.setLayout(btnLayout)

        self._layout.addWidget(TitleLabel(t("search.title"), self))
        self._layout.addWidget(self.tableView)
        self._layout.addWidget(btnGroup)
        self._layout.addWidget(self.search_input, Qt.AlignmentFlag.AlignBottom)

        self.search_result = SongList()

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

    def getVideo_btn(self):
        """获取歌曲列表按钮功能实现"""
        try:
            logger.info("获取歌曲列表中...")
            self.GetVideoBtn.setEnabled(False)

            # 显示加载动画
            self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 设置主窗口不可操作
            self.loading = showLoading(self.GetVideoBtn)
            self.main_window.setEnabled(False)

            # 显示进度条
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
        try:
            # 获取本地数据
            main_search_list = search_song_list(search_content)
            if main_search_list is None:
                # 本地查找失败时，尝试使用bilibili搜索查找
                logger.info("没有在本地列表找到该歌曲，正在尝试bilibili搜索")
                try:
                    sync(search_on_bilibili(search_content))
                    main_search_list = search_song_list(search_content)
                except Exception:
                    logger.exception("bilibili搜索失败")
                else:
                    if main_search_list is None:
                        logger.warning("bilibili搜索结果为空")

            else:
                logger.info(f"本地获取 {len(main_search_list.get_data())} 个有效视频数据:")
                logger.info(main_search_list.get_data())

                # 本地查找成功，追加使用bilibili搜索查找
                # TODO: 可以加入一个设置项配置是否联网搜索
                logger.info(f"本地获取 {len(main_search_list.get_data())} 个有效视频数据:")
                try:
                    sync(search_on_bilibili(search_content))
                    if more_search_list := search_song_list(search_content):
                        delta = len(more_search_list.get_data()) - len(main_search_list.get_data())
                        logger.info(f"bilibili获取 {delta} 个有效视频数据:")
                        main_search_list.append_list(more_search_list)

                except Exception:
                    logger.exception("bilibili搜索失败")

        except Exception as e:
            InfoBar.error(
                t("common.unknown_error"),
                t("search.github_issue", e=str(e)),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                parent=app_context.main_window,
                duration=2000,
            )
            logger.exception("执行搜索时发生未知错误")

        else:
            if main_search_list is None:
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
            return main_search_list

    def on_search_finished(self, main_search_list: SongList | None) -> None:
        # 写入表格和数据
        if main_search_list is not None:
            self.search_result = main_search_list
            self.writeList()
        if model := self.tableView.model():
            self.tableView.setCurrentIndex(model.index(0, 0))

        self.tableView.resizeColumnsToContents()
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
        self.tableView.setHorizontalHeaderLabels([t("common.header_title"),
                                                  t("common.video_blogger"),
                                                  t("common.date"),
                                                  t("common.bvid")])
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