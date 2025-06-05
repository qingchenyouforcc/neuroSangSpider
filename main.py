import os
import sys

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QApplication
from qfluentwidgets import FluentIcon as FIF, StateToolTip, InfoBarPosition, TableWidget
# 导入 PyQt-Fluent-Widgets 相关模块
from qfluentwidgets import (setTheme, Theme, FluentWindow, NavigationItemPosition,
                            SubtitleLabel, SwitchButton,
                            BodyLabel, TitleLabel, PushButton, SearchLineEdit, FluentIcon, GroupHeaderCardWidget,
                            MessageBoxBase,
                            ImageLabel, TeachingTip, TeachingTipView)

from crawlerCore.main import create_video_list_file
from crawlerCore.searchCore import search_song_online
from infoManager.SongList import SongList
from musicDownloader.main import run_download, search_songList
from ui.main_windows import Ui_NeuroSongSpider
from utils.fileManager import MAIN_PATH


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


# 旧版GUI
class MainWindow(QMainWindow, Ui_NeuroSongSpider):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)
        self.worker = None
        self.thread = None
        self.loading = None
        icon = QtGui.QIcon("res\\main.ico")

        self.setupUi(self)
        self.setWindowIcon(icon)
        self.setFixedSize(680, 530)
        self.SearchBtn.clicked.connect(lambda: self.search_btn())
        self.DownloadBtn.clicked.connect(lambda: self.Download_btn())
        self.DownloadBtn_ogg.clicked.connect(lambda: self.Download_ogg_btn())
        # 将 Enter 键绑定到搜索按钮
        self.search_line.returnPressed.connect(self.search_btn)


    def search_btn(self):
        self.listWidget.clear()
        search_content = self.search_line.text().lower()
        try:

            main_search_list = search_songList(search_content)
            if main_search_list is None:
                # 本地查找失败时，尝试使用bilibili搜索查找
                print("没有在本地列表找到该歌曲，正在尝试bilibili搜索")
                try:
                    # 将搜索结果写入json
                    result_info = search_song_online(search_content)
                    temp_list = SongList()
                    temp_list.append_list(result_info)
                    temp_list.unique_by_bv()
                    temp_list.save_list(r"data\search_data.json")

                    main_search_list = search_songList(search_content)
                    '''插入的item是字符串类型'''
                    for item in main_search_list:
                        self.listWidget.addItem(item)
                except Exception as e:
                    print(f"错误:{e};" + type(e).__name__)
            else:
                if True:
                    # 本地查找成功，追加使用bilibili搜索查找
                    # 或许可以做一个设置项进行配置?
                    print("在本地列表找到该歌曲，继续尝试bilibili搜索")
                    try:
                        # 将搜索结果写入json
                        result_info = search_song_online(search_content)
                        temp_list = SongList()
                        temp_list.append_list(result_info)
                        temp_list.unique_by_bv()
                        temp_list.save_list(r"data\search_data.json")

                        more_search_list = search_songList(search_content)
                        for item in more_search_list:
                            self.listWidget.addItem(item)
                    except Exception as e:
                        print(f"错误:{e};" + type(e).__name__)
                        if type(main_search_list) != "NoneType":
                            print("bilibili搜索失败,返回本地列表项")
                            main_search_list = search_songList(search_content)
                            for item in main_search_list:
                                self.listWidget.addItem(item)
                else:
                    # 暂时不可到达
                    # 直接写入列表
                    for item in main_search_list:
                        self.listWidget.addItem(item)
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)

    def Download_btn(self):
        index = self.listWidget.currentRow()
        try:
            run_download(index)
        except IndexError:
            messageBox = QMessageBox()
            QMessageBox.about(messageBox, "提示", "你还没有选择歌曲！")
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)

    def Download_ogg_btn(self):
        index = self.listWidget.currentRow()
        try:
            run_download(index, "ogg")
        except IndexError:
            messageBox = QMessageBox()
            QMessageBox.about(messageBox, "提示", "你还没有选择歌曲！")
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)

    # 当爬虫任务结束时
    def on_c_task_finished(self):
        self.loading.close()
        self.GetVideoBtn.setEnabled(True)
        self.setWindowModality(Qt.WindowModality.NonModal)  # 恢复正常模式
        print("获取歌曲列表完成！")


class SettinsCard(GroupHeaderCardWidget):
    """设置卡片"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("基本设置")
        # self.setBorderRadius(8)

        self.bottomLayout = QVBoxLayout()
        self.setFixedHeight(120)

        # 切换主题按钮
        self.themeSwitch = SwitchButton(self)
        self.themeSwitch.setOffText(self.tr("浅色"))
        self.themeSwitch.setOnText(self.tr("深色"))
        # 根据当前主题设置初始状态 (确保 app 实例已存在)
        # 在 __main__ 中设置初始主题，这里可以先读取
        current_theme_is_dark = QApplication.instance().property("darkMode")
        self.themeSwitch.setChecked(
            current_theme_is_dark if current_theme_is_dark is not None else (Theme.DARK == Theme.DARK))  # 默认为深色
        self.themeSwitch.checkedChanged.connect(on_theme_switched)

        self.bottomLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 添加组件到分组中
        self.addGroup(FluentIcon.BRIGHTNESS,"主题", "切换深色/浅色模式", self.themeSwitch)

        # 添加底部工具栏
        self.vBoxLayout.addLayout(self.bottomLayout)


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


# noinspection PyTypeChecker
class loadingCard(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(250, 250)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.loading_gif = ImageLabel(os.path.join(MAIN_PATH, "res", "loading.gif"))

        self.viewLayout.addWidget(self.loading_gif)


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


class SearchInterface(QWidget):
    """ 搜索GUI """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
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
        self.tableView.setColumnCount(5)

        self.tableView.verticalHeader().hide()
        self.tableView.setHorizontalHeaderLabels(['Title', 'Author', 'Date', 'URL', 'BV'])

        self.GetVideoBtn = PushButton('获取歌曲列表', self)
        self.GetVideoBtn.clicked.connect(lambda: self.getVideo_btn())

        self.lineEdit = SearchLineEdit(self)
        self.lineEdit.setClearButtonEnabled(True)

        self.titleLabel = TitleLabel("搜索歌回", self)

        self.tableView.resizeColumnsToContents()
        self.layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.tableView)
        self.layout.addWidget(self.GetVideoBtn)
        self.layout.addWidget(self.lineEdit, Qt.AlignmentFlag.AlignBottom)


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
