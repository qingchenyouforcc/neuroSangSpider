import os
import sys

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel, QWidget, QVBoxLayout, QApplication

from crawlerCore.main import create_video_list_file
from crawlerCore.searchCore import search_song_online

from utils.fileManager import MAIN_PATH
from musicDownloader.main import run_download, search_songList
from ui.main_windows import Ui_NeuroSongSpider

from infoManager.SongList import SongList

# 导入 PyQt-Fluent-Widgets 相关模块
from qfluentwidgets import (setTheme, Theme, FluentWindow, NavigationItemPosition,
                            SubtitleLabel, PrimaryPushButton, LineEdit, SwitchButton,
                            InfoBar, InfoBarPosition, Flyout, FlyoutView, BodyLabel)
from qfluentwidgets import FluentIcon as FIF


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


# 加载动画的窗口
class LoadingWindow(QWidget):
    def __init__(self, parent=None):
        super(LoadingWindow, self).__init__(parent)
        self.loading_label = None
        self.loading_gif = None
        self.m_winX = parent.x()
        self.m_winY = parent.y()
        self.initUI()

    def initUI(self):
        # 设置窗口基础类型
        self.resize(250, 250)
        self.move(self.m_winX + 340 - 125, self.m_winY + 265 - 100)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
        )
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        # 设置背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 加载动画
        self.loading_gif = QMovie(os.path.join(MAIN_PATH, "res", "loading.gif"))
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_gif)
        self.loading_gif.start()


# 主窗口
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
        self.GetVideoBtn.clicked.connect(lambda: self.getVideo_btn())
        self.SearchBtn.clicked.connect(lambda: self.search_btn())
        self.DownloadBtn.clicked.connect(lambda: self.Download_btn())
        self.DownloadBtn_ogg.clicked.connect(lambda: self.Download_ogg_btn())
        # 将 Enter 键绑定到搜索按钮
        self.search_line.returnPressed.connect(self.search_btn)

    def getVideo_btn(self):
        try:
            print("获取歌曲列表中...")
            self.GetVideoBtn.setEnabled(False)

            # 显示加载动画
            self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 设置主窗口不可操作
            self.loading = LoadingWindow(parent=self)
            self.loading.show()

            # 创建并启动工作线程
            # noinspection PyArgumentList
            self.thread = CrawlerWorkerThread()
            self.thread.task_finished.connect(self.on_c_task_finished)
            self.thread.start()
        except Exception as e:
            print(f"错误:{e};" + type(e).__name__)

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


class HomeInterface(QWidget):
    """ 全新GUI开发 """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        self.titleLabel = SubtitleLabel("这是全新的NeuroSangSpider GUI", self)
        self.infoLabel = BodyLabel(
            "这是一个简单的 PyQt6 示例，展示了一些基本的组件。\n"
            "全新的NeuroSangSpiderGUI正在开发中，将会带来全新的体验。 \n"
            "尝试点击按钮或与下面的控件交互。",
            self
        )

        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText("在这里输入一些文本...")

        self.button = PrimaryPushButton("点击我", self)
        self.button.clicked.connect(self.on_button_clicked)

        self.themeSwitch = SwitchButton("切换主题 (深色/浅色)", self)
        # 根据当前主题设置初始状态 (确保 app 实例已存在)
        # 在 __main__ 中设置初始主题，这里可以先读取
        current_theme_is_dark = QApplication.instance().property("darkMode")
        self.themeSwitch.setChecked(
            current_theme_is_dark if current_theme_is_dark is not None else (Theme.DARK == Theme.DARK))  # 默认为深色
        self.themeSwitch.checkedChanged.connect(self.on_theme_switched)

        self.layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.infoLabel)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.button)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.themeSwitch, 0, Qt.AlignmentFlag.AlignBottom)
        self.layout.addStretch(1)

    def on_theme_switched(self, checked):
        if checked:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)


# ----------------------------------------------------------------------
#   主演示窗口
# ----------------------------------------------------------------------
class DemoWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("demoWindow")
        icon = QtGui.QIcon("res\\main.ico")

        self.homeInterface = HomeInterface(self)
        self.setWindowIcon(icon)
        self.addSubInterface(  # <--- 注意这里，直接调用 self.addSubInterface
            interface=self.homeInterface,
            icon=FIF.HOME,
            text="主页",
            position=NavigationItemPosition.TOP
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
    # 在 PyQt6 中，这些通常是默认启用的，或者通过平台插件处理得更好。
    # 但显式设置通常无害，并且可以确保行为一致性。
    # Qt6 使用更明确的枚举路径
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):  # Qt.HighDpiScaleFactorRoundingPolicy 枚举本身
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    # --- 设置初始主题 ---
    # setTheme(Theme.LIGHT) # 或者 Theme.DARK
    setTheme(Theme.DARK) # 默认启动为深色主题

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())

    # # 旧版GUI
    # print(MAIN_PATH)
    # app = QtWidgets.QApplication(sys.argv)
    # main = MainWindow()
    # main.show()
    # sys.exit(app.exec())
