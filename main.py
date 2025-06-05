import os
import sys

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize, QUrl
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QApplication, QTableWidgetItem, QHBoxLayout, \
    QAbstractItemView
from qfluentwidgets import FluentIcon as FIF, StateToolTip, InfoBarPosition, TableWidget, InfoBar, SettingCardGroup, \
    ComboBox, TransparentToolButton
# 导入 PyQt-Fluent-Widgets 相关模块
from qfluentwidgets import (setTheme, Theme, FluentWindow, NavigationItemPosition,
                            SubtitleLabel, SwitchButton,
                            BodyLabel, TitleLabel, PushButton, SearchLineEdit, FluentIcon, GroupHeaderCardWidget,
                            TeachingTip, TeachingTipView)
from qfluentwidgets.multimedia import StandardMediaPlayBar

from config import cfg
from crawlerCore.main import create_video_list_file
from crawlerCore.searchCore import search_song_online
from infoManager.SongList import SongList
from musicDownloader.main import run_download, search_songList
from utils.fileManager import MAIN_PATH, read_all_audio_info, batch_clean_audio_files


# if __name__ == '__main__':
#     print("")
#     create_video_list_file()
#
#     download_main()

# 将爬虫线程分离
class CrawlerWorkerThread(QThread):
    # 定义一个信号，用于通知主线程任务完成
    # noinspection PyArgumentList
    task_finished: pyqtSignal | pyqtSignal = pyqtSignal(str)

    def run(self):
        # 模拟一个耗时任务
        create_video_list_file()
        # 任务完成后发出信号
        self.task_finished.emit("获取歌曲列表完成！")


def changeDownloadType(index):
    """修改下载歌曲格式"""
    file_types = ['mp3', 'ogg', 'wav']
    selected_type = file_types[index]
    cfg.downloadType = selected_type
    InfoBar.success(
        "设置成功",
        f"已将下载格式设为 {selected_type}",
        orient=Qt.Orientation.Horizontal,
        position=InfoBarPosition.BOTTOM_RIGHT,
        duration=1500,
        parent=window
    )


class SettinsCard(GroupHeaderCardWidget):
    """设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scrollWidget = QWidget()
        self.setTitle("设置")

        # self.setBorderRadius(8)
        self.setFixedHeight(240)

        # 修改下载歌曲格式
        self.comboBox = ComboBox(self)
        items = ['mp3', 'ogg', 'wav']
        self.comboBox.addItems(items)

        current_index = items.index(cfg.downloadType.value)
        self.comboBox.setCurrentIndex(current_index)
        self.comboBox.currentIndexChanged.connect(changeDownloadType)


        # 切换主题按钮
        self.themeSwitch = SwitchButton(self)
        self.themeSwitch.setOffText(self.tr("浅色"))
        self.themeSwitch.setOnText(self.tr("深色"))
        current_theme_is_dark = QApplication.instance().property("darkMode")
        self.themeSwitch.setChecked(
            current_theme_is_dark if current_theme_is_dark is not None else (Theme.DARK == Theme.DARK))  # 默认为深色
        self.themeSwitch.checkedChanged.connect(on_theme_switched)

        self.fixMusic = PushButton("修复音频", self)
        self.fixMusic.clicked.connect(on_fix_music)


        # 添加组件到分组中
        self.addGroup(FluentIcon.BRIGHTNESS, "主题", "切换深色/浅色模式", self.themeSwitch)
        self.addGroup(FluentIcon.DOWNLOAD, "下载格式", "选择默认音乐格式", self.comboBox)
        self.addGroup(FluentIcon.MUSIC, "修复音频文件", "修复下载异常的音频文件", self.fixMusic)


def on_fix_music():
    music_dir = os.path.join(MAIN_PATH, "music")
    try:
        batch_clean_audio_files(music_dir, target_format='mp3', overwrite=True)
        InfoBar.success(
            "修复完成",
            "修复完成！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=window
        )
    except Exception as e:
        print(e)
        InfoBar.error(
            "修复失败",
            "修复失败！",
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=window
        )


def on_theme_switched(checked):
    """切换主题"""
    if checked:
        setTheme(Theme.DARK)
    else:
        setTheme(Theme.LIGHT)


def showLoading(self):
    """加载动画实现"""
    view = TeachingTipView(
        title="",
        content="",
        image=os.path.join(MAIN_PATH, "res", "loading.gif"),
        isClosable=False
    )

    view.setFixedSize(250, 250)
    view.imageLabel.setMinimumSize(250, 250)

    # show view
    w = TeachingTip.make(view, self.GetVideoBtn, duration=-1)
    return w


class SettingInterface(QWidget):
    """ 设置GUI """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        self.layout.addWidget(SettinsCard(), Qt.AlignmentFlag.AlignTop)
        self.layout.addStretch(1)


class LocPlayerInterface(QWidget):
    """ 本地播放器GUI """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("locPlayerInterface")
        self.setStyleSheet("LocPlayerInterface{background: transparent}")

        self.layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.bar = StandardMediaPlayBar()
        self.bar.player.setVolume(50)

        # 创建标题和刷新按钮的水平布局
        title_layout = QHBoxLayout()

        self.titleLabel = TitleLabel("本地播放器", self)

        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip("刷新歌曲列表")

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)

        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.tableView)
        self.layout.addWidget(self.bar)

        self.tableView.cellDoubleClicked.connect(self.play_selected_song)
        self.refreshButton.clicked.connect(self.load_local_songs)

        self.load_local_songs()

    def load_local_songs(self):
        music_dir = os.path.join(MAIN_PATH, "music")
        try:
            songs = read_all_audio_info(music_dir)
            self.tableView.setRowCount(len(songs))
            self.tableView.setColumnCount(2)
            self.tableView.setHorizontalHeaderLabels(['文件名', '时长'])

            for i, (filename, duration) in enumerate(songs):
                self.tableView.setItem(i, 0, QTableWidgetItem(filename))
                self.tableView.setItem(i, 1, QTableWidgetItem(f"{duration}s"))

            self.tableView.resizeColumnsToContents()
        except Exception as e:
            print("加载本地歌曲失败:", e)

    def play_selected_song(self, row):
        """双击播放指定行的歌曲"""
        item = self.tableView.item(row, 0)
        if not item:
            return

        filename = item.text()
        music_dir = os.path.join(MAIN_PATH, "music")
        file_path = os.path.join(music_dir, filename)

        if not os.path.exists(file_path):
            InfoBar.error(
                "错误", f"找不到文件: {filename}",
                duration=2000, parent=window, position=InfoBarPosition.BOTTOM_RIGHT
            )
            return

        url = QUrl.fromLocalFile(file_path)
        self.bar.player.setSource(url)
        self.bar.player.play()


def searchOnBili(search_content):
    # 将搜索结果写入json
    result_info = search_song_online(search_content)
    temp_list = SongList()
    temp_list.append_list(result_info)
    temp_list.unique_by_bv()
    temp_list.save_list(r"data\search_data.json")


class SearchInterface(QWidget):
    """ 搜索GUI """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.GetVideoBtn = None
        self.stateTooltip = None
        self.loading = None
        self.thread = None
        self.setObjectName("searchInterface")

        self.layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # enable border
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(60)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.tableView.verticalHeader().hide()

        btnGroup = QWidget()
        btnLayout = QHBoxLayout(btnGroup)

        self.GetVideoBtn = PushButton('获取歌曲列表', self)
        self.GetVideoBtn.clicked.connect(lambda: self.getVideo_btn())

        DownloadBtn = PushButton('下载歌曲', self)
        DownloadBtn.clicked.connect(lambda: self.Download_btn())

        btnLayout.addWidget(self.GetVideoBtn)
        btnLayout.addWidget(DownloadBtn)
        btnLayout.setSpacing(15)

        self.searchLine = SearchLineEdit(self)
        self.searchLine.setClearButtonEnabled(True)
        self.searchLine.searchButton.clicked.connect(lambda: self.search_btn())
        self.searchLine.returnPressed.connect(self.search_btn)

        self.titleLabel = TitleLabel("搜索歌回", self)

        self.tableView.resizeColumnsToContents()
        self.layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.tableView)
        self.layout.addWidget(btnGroup)
        self.layout.addWidget(self.searchLine, Qt.AlignmentFlag.AlignBottom)

    def getVideo_btn(self):
        """获取歌曲列表按钮功能实现"""
        try:
            print("获取歌曲列表中...")
            self.GetVideoBtn.setEnabled(False)

            # 显示加载动画
            self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 设置主窗口不可操作
            self.loading = showLoading(self)
            window.setEnabled(False)

            # 显示进度条
            if self.stateTooltip:
                self.stateTooltip.setContent('获取列表完成!!!')
                self.stateTooltip.setState(True)
                self.stateTooltip = None
            else:
                self.stateTooltip = StateToolTip('正在获取歌曲列表...', '请耐心等待<3', self)
                self.stateTooltip.move(self.stateTooltip.getSuitablePos())
                self.stateTooltip.show()

            # 创建并启动工作线程
            # noinspection PyArgumentList
            self.thread = CrawlerWorkerThread()
            self.thread.task_finished.connect(self.on_c_task_finished)
            self.thread.start()
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)

    def search_btn(self):
        """实现搜索按钮功能"""
        self.tableView.clear()
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(['Title', 'Author', 'Date', 'BV'])
        search_content = self.searchLine.text().lower()
        try:
            main_search_list = search_songList(search_content)
            print("---搜索开始---")
            if main_search_list is None:
                # 本地查找失败时，尝试使用bilibili搜索查找
                print("没有在本地列表找到该歌曲，正在尝试bilibili搜索")
                try:
                    searchOnBili(search_content)

                    main_search_list = search_songList(search_content)
                    self.writeList(main_search_list)
                except TypeError:
                    print("bilibili搜索结果为空")
                    InfoBar.error(
                        title='错误',
                        content="没有找到任何结果",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=2000,
                        parent=self
                    )
                except Exception as e:
                    print(f"错误:{e};" + type(e).__name__)
            else:
                if True:
                    print(f"本地获取 {len(main_search_list)} 个有效视频数据:")
                    print(main_search_list)
                    # 本地查找成功，追加使用bilibili搜索查找
                    # 或许可以做一个设置项进行配置?
                    print("在本地列表找到该歌曲，继续尝试bilibili搜索")
                    try:
                        searchOnBili(search_content)

                        more_search_list = search_songList(search_content)
                        print(f"bilibili获取 "
                              f"{len(more_search_list) - len(main_search_list)} "
                              f"个有效视频数据:")

                        self.writeList(more_search_list)
                    except Exception as e:
                        print(f"错误:{e};" + type(e).__name__)
                        if type(main_search_list) != "NoneType":
                            print("bilibili搜索失败,返回本地列表项")
                            self.writeList(main_search_list)
                else:
                    # 暂时不可到达
                    # 直接写入列表
                    self.writeList(main_search_list)
        except TypeError:
            print("搜索结果为空")
            InfoBar.error(
                title='错误',
                content="没有找到任何结果",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title='未知错误，请在github上提交issue',
                content=type(e).__name__,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            print(f"错误:{e};" + type(e).__name__)
        print("---搜索结束---\n")
        self.tableView.resizeColumnsToContents()

    # 当爬虫任务结束时
    def on_c_task_finished(self):
        self.loading.close()
        window.setEnabled(True)
        self.GetVideoBtn.setEnabled(True)
        self.setWindowModality(Qt.WindowModality.NonModal)  # 恢复正常模式

        print("获取歌曲列表完成！")
        self.stateTooltip.setContent('获取列表完成!!!')
        self.stateTooltip.setState(True)
        self.stateTooltip = None

    def writeList(self, searchResult):
        """
        将搜索结果写入表格

        searchResult: 包含搜索结果的列表，每个元素是一个包含歌曲信息的列表
        """
        print(f"总计获取 {len(searchResult)} 个有效视频数据:")
        print(searchResult)
        self.tableView.setRowCount(len(searchResult))

        for i, songInfo in enumerate(searchResult):
            for j in range(4):
                self.tableView.setItem(i, j, QTableWidgetItem(songInfo[j]))

    def Download_btn(self):
        index = self.tableView.currentRow()
        try:
            fileType = cfg.downloadType
            run_download(index, fileType)
            InfoBar.success(
                title='完成',
                content="歌曲下载完成",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except IndexError:
            messageBox = QMessageBox()
            QMessageBox.about(messageBox, "提示", "你还没有选择歌曲！")
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)


class HomeInterface(QWidget):
    """ 主页GUI """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # 实现主页文字
        self.titleLabel = TitleLabel("NeuroSangSpider 1.1", self)
        self.subTitleLabel = SubtitleLabel("全新的NeuroSangSpider", self)
        self.infoLabel = BodyLabel(
            "- 更加智能的搜索机制 \n"
            "- 更多的参数设定 \n"
            "- 更现代化的GUI \n"
            "- 更丰富的功能 \n",
            self
        )

        self.readmeLabel = SubtitleLabel("介绍", self)
        self.readmeInfoLabel = BodyLabel(
            "这是一个基于 Python 3.13 开发的程序，\n"
            "用于从 Bilibili（哔哩哔哩）爬取 Neuro/Evil 的歌曲的视频内容。\n"
            "如果搜索没结果的话，可以试试多搜几次\n"
            "(当然未来也支持通过自定义UP 主列表和关键词，灵活调整爬取目标) \n"
            "\nLicense:   AGPL-3.0",
            self
        )

        self.layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.subTitleLabel)
        self.layout.addWidget(self.infoLabel)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.readmeLabel)
        self.layout.addWidget(self.readmeInfoLabel)

        self.layout.addStretch(1)


class DemoWindow(FluentWindow):
    """全新GUI"""

    def __init__(self):
        super().__init__()
        self.setObjectName("demoWindow")
        icon = QtGui.QIcon("res\\main.ico")

        self.homeInterface = HomeInterface(self)
        self.setWindowIcon(icon)

        # 添加子界面
        self.addSubInterface(
            interface=self.homeInterface,
            icon=FIF.HOME,
            text="主页",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            interface=SearchInterface(self),
            icon=FIF.SEARCH,
            text="搜索",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            interface=LocPlayerInterface(self),
            icon=FIF.PLAY,
            text="本地播放",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            interface=SettingInterface(self),
            icon=FIF.SETTING,
            text="设置",
            position=NavigationItemPosition.BOTTOM
        )

        self.setWindowTitle("NeuroSangSpider")

        # 设置初始窗口大小
        desktop = QApplication.primaryScreen()
        if desktop:  # 确保 desktop 对象不是 None
            self.resize(QSize(680, 530))
            # self.resize(QSize(desktop.availableGeometry().width() // 2, desktop.availableGeometry().height() // 2))
        else:  # 如果获取不到主屏幕信息，给一个默认大小
            self.resize(QSize(680, 530))

        # 设置默认音频格式
        cfg.downloadType = "mp3"


if __name__ == '__main__':
    # 新版GUI开发中
    # --- 启用高 DPI 支持 ---
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):  # Qt.HighDpiScaleFactorRoundingPolicy 枚举本身
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    # 设置初始主题
    setTheme(Theme.AUTO)

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())

    # # 旧版GUI
    # print(MAIN_PATH)
    # app = QtWidgets.QApplication(sys.argv)
    # main = MainWindow()
    # main.show()
    # sys.exit(app.exec())
