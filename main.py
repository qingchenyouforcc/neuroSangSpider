import os
import sys
from typing import cast

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize, QUrl
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QApplication, QTableWidgetItem, QHBoxLayout, \
    QAbstractItemView
from qfluentwidgets import FluentIcon as FIF, StateToolTip, InfoBarPosition, TableWidget, InfoBar, ComboBox, \
    TransparentToolButton, CaptionLabel
# 导入 PyQt-Fluent-Widgets 相关模块
from qfluentwidgets import (setTheme, Theme, FluentWindow, NavigationItemPosition,
                            SubtitleLabel, SwitchButton,
                            BodyLabel, TitleLabel, PushButton, SearchLineEdit, FluentIcon, GroupHeaderCardWidget,
                            TeachingTip, TeachingTipView)
from qfluentwidgets.multimedia import MediaPlayer, MediaPlayBarButton, MediaPlayerBase
from qfluentwidgets.multimedia.media_play_bar import MediaPlayBarBase

import config
from config import cfg
from crawlerCore.main import create_video_list_file
from crawlerCore.searchCore import search_song_online
from infoManager.SongList import SongList
from musicDownloader.main import run_download, search_songList
from string_tools import remove_before_last_backslash
from utils.fileManager import MAIN_PATH, read_all_audio_info, batch_clean_audio_files

global window


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


class CustomMediaPlayBar(MediaPlayBarBase):
    """自定义播放栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.timeLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.leftButtonContainer = QWidget()
        self.centerButtonContainer = QWidget()
        self.rightButtonContainer = QWidget()
        self.leftButtonLayout = QHBoxLayout(self.leftButtonContainer)
        self.centerButtonLayout = QHBoxLayout(self.centerButtonContainer)
        self.rightButtonLayout = QHBoxLayout(self.rightButtonContainer)

        self.skipBackButton = MediaPlayBarButton(FluentIcon.SKIP_BACK, self)
        self.skipForwardButton = MediaPlayBarButton(FluentIcon.SKIP_FORWARD, self)

        self.currentTimeLabel = CaptionLabel('0:00:00', self)
        self.remainTimeLabel = CaptionLabel('0:00:00', self)

        self.__initWidgets()

    def __initWidgets(self):
        self.setFixedHeight(102)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setContentsMargins(5, 9, 5, 9)
        self.vBoxLayout.addWidget(self.progressSlider, 1, Qt.AlignmentFlag.AlignTop)

        self.vBoxLayout.addLayout(self.timeLayout)
        self.timeLayout.setContentsMargins(10, 0, 10, 0)
        self.timeLayout.addWidget(self.currentTimeLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.timeLayout.addWidget(self.remainTimeLabel, 0, Qt.AlignmentFlag.AlignRight)

        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.leftButtonLayout.setContentsMargins(4, 0, 0, 0)
        self.centerButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.rightButtonLayout.setContentsMargins(0, 0, 4, 0)

        self.leftButtonLayout.addWidget(self.volumeButton, 0, Qt.AlignmentFlag.AlignLeft)
        self.centerButtonLayout.addWidget(self.skipBackButton)
        self.centerButtonLayout.addWidget(self.playButton)
        self.centerButtonLayout.addWidget(self.skipForwardButton)

        self.buttonLayout.addWidget(self.leftButtonContainer, 0, Qt.AlignmentFlag.AlignLeft)
        self.buttonLayout.addWidget(self.centerButtonContainer, 0, Qt.AlignmentFlag.AlignHCenter)
        self.buttonLayout.addWidget(self.rightButtonContainer, 0, Qt.AlignmentFlag.AlignRight)

        self.setMediaPlayer(cast(MediaPlayerBase, MediaPlayer(self)))

        self.volumeButton.clicked.connect(self.volumeSet)
        self.volumeButton.volumeView.volumeSlider.valueChanged.connect(self.volumeChanged)
        self.skipBackButton.clicked.connect(lambda: self.skipBack(10000))
        self.skipForwardButton.clicked.connect(lambda: self.skipForward(30000))

    @staticmethod
    def volumeChanged(value):
        config.volume = value

    def volumeSet(self):
        """ 音量设置 """
        self.setVolume(config.volume)

    def skipBack(self, ms: int):
        """ Back up for specified milliseconds """
        self.player.setPosition(self.player.position() - ms)

    def skipForward(self, ms: int):
        """ Fast forward specified milliseconds """
        self.player.setPosition(self.player.position() + ms)

    def _onPositionChanged(self, position: int):
        super()._onPositionChanged(position)
        self.currentTimeLabel.setText(self._formatTime(position))
        self.remainTimeLabel.setText(self._formatTime(self.player.duration() - position))

    @staticmethod
    def _formatTime(time: int):
        time = int(time / 1000)
        s = time % 60
        m = int(time / 60)
        h = int(time / 3600)
        return f'{h}:{m:02}:{s:02}'


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
        items = ['mp3', 'ogg', 'wav']
        self.comboBox = ComboBox(self)
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


class PlayQueueInterface(QWidget):
    """ 播放队列GUI """

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent=parent)
        self.main_window = main_window
        self.setObjectName("playQueueInterface")

        self.layout = QVBoxLayout(self)
        self.tableView = TableWidget(self)

        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 创建标题和刷新按钮的水平布局
        title_layout = QHBoxLayout()

        self.titleLabel = TitleLabel("播放列表", self)

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
        title_layout.addWidget(self.upSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.downSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.tableView)
        # todo
        # 实现歌曲移动操作

        self.refreshButton.clicked.connect(self.load_play_queue)

        self.load_play_queue()

    def load_play_queue(self):
        if not config.play_queue:
            return

        try:
            self.tableView.setRowCount(len(config.play_queue))
            self.tableView.setColumnCount(1)
            self.tableView.setHorizontalHeaderLabels(['歌曲'])

            for i, (song) in enumerate(config.play_queue):
                song = remove_before_last_backslash(song)
                self.tableView.setItem(i, 0, QTableWidgetItem(song))

            self.tableView.resizeColumnsToContents()
        except Exception as e:
            print("加载歌曲列表失败:", e)


def getMusicLocal(fileName):
    """获取音乐文件位置"""
    if not fileName:
        return None

    filename = fileName.text()
    music_dir = os.path.join(MAIN_PATH, "music")
    file_path = os.path.join(music_dir, filename)

    if not os.path.exists(file_path):
        InfoBar.error(
            "错误", f"找不到文件: {filename}",
            duration=2000, parent=window, position=InfoBarPosition.BOTTOM_RIGHT
        )
        return None

    return file_path


def open_player():
    """打开播放器"""
    window.bar.show()


def open_info_tip():
    """打开正在播放提示"""
    if config.HAS_INFOPLAYERBAR:
        print("检测到已经有了一个正在播放提示，正在关闭...")
        config.infoBar.close()
        config.infoBar = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{config.playingNow.text()}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
    else:
        info = InfoBar.new(
            icon=FluentIcon.MUSIC,
            title='正在播放',
            content=f"{config.playingNow.text()}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=InfoBar.desktopView()
        )
        info.setCustomBackgroundColor('white', '#202020')

        config.infoBar = info
        config.HAS_INFOPLAYERBAR = True
    try:
        info = config.infoBar

        playBtn = TransparentToolButton(FluentIcon.PAUSE, info)
        info.hBoxLayout.addWidget(playBtn, 0, Qt.AlignmentFlag.AlignLeft)
        playBtn.setToolTip("暂停/播放")

        config.infoBarPlayBtn = playBtn

        playBtn.clicked.connect(infoPlayBtnClicked)

    except AttributeError:
        InfoBar.error(
            "错误", "没有正在播放的音乐",
            duration=1000, parent=window, position=InfoBarPosition.BOTTOM_RIGHT
        )

    except Exception as e:
        print(e)
        InfoBar.error(
            "未知错误", "请复制日志反馈到github issue",
            duration=2000, parent=window, position=InfoBarPosition.BOTTOM_RIGHT
        )


def infoPlayBtnClicked():
    """悬浮栏播放按钮事件"""
    config.player.togglePlayState()

    if config.player.player.isPlaying():
        config.infoBarPlayBtn.setIcon(FluentIcon.PAUSE_BOLD)
    else:
        config.infoBarPlayBtn.setIcon(FluentIcon.PLAY_SOLID)


class LocPlayerInterface(QWidget):
    """ 本地播放器GUI """

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.main_window = main_window
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

        title_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addStretch(1)
        title_layout.addWidget(self.openInfoTip, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.openPlayer, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.addQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.tableView)

        self.tableView.cellDoubleClicked.connect(self.play_selected_song)
        self.refreshButton.clicked.connect(self.load_local_songs)
        self.addQueueButton.clicked.connect(self.add_to_queue)
        self.openPlayer.clicked.connect(open_player)
        self.openInfoTip.clicked.connect(open_info_tip)

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
        file_path = getMusicLocal(item)

        url = QUrl.fromLocalFile(file_path)
        self.main_window.bar.player.setSource(url)
        self.main_window.bar.player.play()

        config.playingNow = item

        open_info_tip()

    def add_to_queue(self):
        """添加到播放列表"""
        item = self.tableView.currentItem()
        file_path = getMusicLocal(item)

        if file_path:
            if file_path in config.play_queue:
                InfoBar.warning(
                    "已存在",
                    f"{item.text()}已存在播放列表",
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self.parent()
                )
                return

            config.play_queue.append(file_path)
            InfoBar.success(
                "成功",
                f"已添加{item.text()}到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent()
            )
            print(config.play_queue)
        else:
            InfoBar.error(
                "失败",
                "添加失败！",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=window
            )


def searchOnBili(search_content):
    # 将搜索结果写入json
    result_info = search_song_online(search_content, config.search_page)
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
        self.tableView.setHorizontalHeaderLabels(['标题', 'UP主', '日期', 'BV号'])
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

        self.bar = CustomMediaPlayBar()
        self.bar.setFixedSize(300, 120)
        self.bar.player.setVolume(config.volume)
        self.bar.setWindowIcon(icon)
        self.bar.setWindowTitle("Player")
        self.bar.show()
        config.player = self.bar

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
            interface=PlayQueueInterface(self, main_window=self),
            icon=FIF.ALIGNMENT,
            text="播放队列",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            interface=LocPlayerInterface(self, main_window=self),
            icon=FIF.PLAY,
            text="本地播放",
            position=NavigationItemPosition.BOTTOM
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
