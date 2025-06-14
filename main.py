import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import cast

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QTableWidgetItem, QHBoxLayout, \
    QAbstractItemView
from loguru import logger
from qfluentwidgets import FluentIcon as FIF, StateToolTip, InfoBarPosition, TableWidget, InfoBar, ComboBox, \
    TransparentToolButton, CaptionLabel, isDarkTheme, MessageBox, FlowLayout, CardGroupWidget, \
    ToolButton, MessageBoxBase, LineEdit
# 导入 PyQt-Fluent-Widgets 相关模块
from qfluentwidgets import (setTheme, Theme, FluentWindow, NavigationItemPosition,
                            SubtitleLabel, SwitchButton,
                            BodyLabel, TitleLabel, PushButton, SearchLineEdit, FluentIcon, GroupHeaderCardWidget,
                            TeachingTip, TeachingTipView)
from qfluentwidgets.multimedia import MediaPlayer, MediaPlayBarButton, MediaPlayerBase
from qfluentwidgets.multimedia.media_play_bar import MediaPlayBarBase

import common.config
from SongListManager.SongList import SongList
from common.config import cfg, MAIN_PATH
from crawlerCore.main import create_video_list_file
from musicDownloader.main import run_download, search_song_list
from utils.player_tools import open_player, nextSong, previousSong, playSongByIndex, getMusicLocal, sequencePlay
from crawlerCore.searchCore import searchOnBili
from utils.text_tools import remove_before_last_backslash, format_date_str
from utils.tipbar_tools import open_info_tip, update_info_tip
from utils.file_tools import read_all_audio_info, create_dir, on_fix_music

global window


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


# noinspection PyArgumentList,PyTypeHints
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

        self.nextSongButton = MediaPlayBarButton(FluentIcon.CARE_RIGHT_SOLID, self)
        self.previousSongButton = MediaPlayBarButton(FluentIcon.CARE_LEFT_SOLID, self)

        self.skipBackButton = MediaPlayBarButton(FluentIcon.SKIP_BACK, self)

        self.modeChangeButton = MediaPlayBarButton(FluentIcon.SYNC, self)
        self.modeChangeButton.setToolTip('列表循环')

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

        self.centerButtonLayout.addWidget(self.skipBackButton)
        self.centerButtonLayout.addWidget(self.previousSongButton)
        self.centerButtonLayout.addWidget(self.playButton)
        self.centerButtonLayout.addWidget(self.nextSongButton)
        self.centerButtonLayout.addWidget(self.modeChangeButton)

        self.rightButtonLayout.addWidget(self.volumeButton, 0, Qt.AlignmentFlag.AlignRight)

        self.buttonLayout.addWidget(self.leftButtonContainer, 0, Qt.AlignmentFlag.AlignLeft)
        self.buttonLayout.addWidget(self.centerButtonContainer, 0, Qt.AlignmentFlag.AlignHCenter)
        self.buttonLayout.addWidget(self.rightButtonContainer, 0, Qt.AlignmentFlag.AlignRight)

        self.setMediaPlayer(cast(MediaPlayerBase, MediaPlayer(self)))

        self.volumeButton.clicked.connect(self.volumeSet)
        self.volumeButton.volumeView.volumeSlider.valueChanged.connect(self.volumeChanged)
        self.skipBackButton.clicked.connect(lambda: self.skipBack(10000))
        self.previousSongButton.clicked.connect(previousSong)
        self.nextSongButton.clicked.connect(nextSong)
        self.modeChangeButton.clicked.connect(self.modeChange)

    @staticmethod
    def volumeChanged(value):
        cfg.volume = value

    def volumeSet(self):
        """ 音量设置 """
        self.setVolume(cfg.volume)

    def skipBack(self, ms: int):
        """ Back up for specified milliseconds """
        self.player.setPosition(self.player.position() - ms)

    # noinspection PyProtectedMember
    def _onPositionChanged(self, position: int):
        super()._onPositionChanged(position)
        self.currentTimeLabel.setText(self._formatTime(position))
        self.remainTimeLabel.setText(self._formatTime(self.player.duration() - position))

        remainTime = self.player.duration() - position

        if remainTime == 0:
            match cfg.play_mode:
                case 0:
                    logger.info("歌曲播放完毕，自动播放下一首。")
                    nextSong()
                case 1:
                    if cfg.play_queue_index < len(cfg.play_queue):
                        logger.info("歌曲播放完毕，自动播放下一首。")
                        nextSong()
                case 2:
                    playSongByIndex()
                case 3:
                    logger.info("歌曲播放完毕，自动播放下一首。")
                    nextSong()

    @staticmethod
    def _formatTime(time: int):
        time = int(time / 1000)
        s = time % 60
        m = int(time / 60)
        h = int(time / 3600)
        return f'{h}:{m:02}:{s:02}'

    def modeChange(self):
        if cfg.play_mode >= 3:
            cfg.play_mode = 0
        else:
            cfg.play_mode += 1

        if cfg.play_mode == 0:
            self.modeChangeButton.setIcon(FluentIcon.SYNC)
            self.modeChangeButton.setToolTip('列表循环')
        elif cfg.play_mode == 1:
            self.modeChangeButton.setIcon(FluentIcon.MENU)
            self.modeChangeButton.setToolTip('顺序播放')
        elif cfg.play_mode == 2:
            self.modeChangeButton.setIcon(FluentIcon.ROTATE)
            self.modeChangeButton.setToolTip('单曲循环')
        elif cfg.play_mode == 3:
            self.modeChangeButton.setIcon(FluentIcon.QUESTION)
            self.modeChangeButton.setToolTip('随机播放')

    def togglePlayState(self):
        """ toggle the play state of media player """
        super().togglePlayState()

        if config.info_bar is not None:
            try:
                update_info_tip()
            except Exception as e:
                logger.warning(e)


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


# noinspection PyArgumentList
class SearchSettingsCard(GroupHeaderCardWidget):
    """搜索设置卡片"""

    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__()
        self.filterLayout = None
        self.addWordBtn = None
        self.filterInfo = None

        self.setTitle("搜索设置")
        self.flow_container = QWidget()

        self.init_filter_card()
        self.__init_widget()

    def init_filter_card(self):
        """初始化过滤器卡片"""
        self.filterLayout = FlowLayout(self.flow_container, needAni=True)

        self.filterLayout.setContentsMargins(30, 30, 30, 30)

        for word in cfg.filter_list:
            word_btn = PushButton(word)
            word_btn.clicked.connect(self.remove_filter_word)

            self.filterLayout.addWidget(word_btn)

        self.addWordBtn = ToolButton()
        self.addWordBtn.setIcon(FluentIcon.ADD)
        self.addWordBtn.clicked.connect(self.add_filter_word)
        self.filterLayout.addWidget(self.addWordBtn)

        self.filterInfo = CardGroupWidget(FluentIcon.SEARCH, '调整过滤器', '搜索结果只会显示符合过滤条件的歌曲(单击删除)', self)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')

    def __init_widget(self):
        self.vBoxLayout.addWidget(self.filterInfo, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.flow_container)

    def remove_filter_word(self):
        try:
            word_btn = self.sender()
            cfg.filter_list.remove(word_btn.text())
            logger.info(f"当前过滤器列表为{cfg.filter_list}")
            self.filterLayout.removeWidget(word_btn)
            word_btn.deleteLater()

            # 强制刷新布局，确保及时更新
            self.filterLayout.update()
            self.update()
        except Exception as e:
            logger.error(e)

    # noinspection PyTypeChecker
    def add_filter_word(self):
        try:
            mbox = MessageBoxBase(cfg.MAIN_WINDOW)

            mbox.titleLabel = SubtitleLabel('添加过滤词', self)
            mbox.wordLineEdit = LineEdit(self)

            mbox.wordLineEdit.setPlaceholderText('输入你要添加的过滤词')
            mbox.wordLineEdit.setClearButtonEnabled(True)

            # add widget to view layout
            mbox.viewLayout.addWidget(mbox.titleLabel)
            mbox.viewLayout.addWidget(mbox.wordLineEdit)

            # change the text of button
            mbox.yesButton.setText('添加')
            mbox.cancelButton.setText('取消')

            mbox.setMinimumWidth(350)

            if mbox.exec():
                word: str = mbox.wordLineEdit.text().strip()
                if not word:
                    InfoBar.error(
                        "错误",
                        "请输入要添加的过滤词",
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        parent=cfg.MAIN_WINDOW
                    )
                    return
                if word in cfg.filter_list:
                    InfoBar.error(
                        "错误",
                        "该过滤词已存在",
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        parent=cfg.MAIN_WINDOW
                    )
                    return
                else:
                    cfg.filter_list.append(word)
                    logger.info(f"当前过滤器列表为{cfg.filter_list}")
                    word_btn = PushButton(word)
                    word_btn.clicked.connect(self.remove_filter_word)
                    self.filterLayout.addWidget(word_btn)
                    self.filterLayout.removeWidget(self.addWordBtn)
                    self.filterLayout.addWidget(self.addWordBtn)
                    self.filterLayout.update()
                    self.update()
                    return

        except Exception as e:
            logger.error(f"添加过滤词错误：错误内容:{e}，错误类型:{type(e)}\n错误位置:{traceback.format_exc()}")
            return


# noinspection PyArgumentList
class SettingsCard(GroupHeaderCardWidget):
    """常规设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("基本设置")

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
        # 默认系统主题
        if current_theme_is_dark is None:
            current_theme_is_dark = isDarkTheme()
        self.themeSwitch.setChecked(current_theme_is_dark)
        self.themeSwitch.checkedChanged.connect(on_theme_switched)

        self.fixMusic = PushButton("修复音频", self)
        self.fixMusic.clicked.connect(on_fix_music)

        # 添加组件到分组中
        self.addGroup(FluentIcon.BRIGHTNESS, "主题", "切换深色/浅色模式", self.themeSwitch)
        self.addGroup(FluentIcon.DOWNLOAD, "下载格式", "选择默认音乐格式", self.comboBox)
        self.addGroup(FluentIcon.MUSIC, "修复音频文件", "修复下载异常的音频文件", self.fixMusic)


def on_theme_switched(checked):
    """切换主题"""
    try:
        if checked:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
    except Exception as e:
        logger.error(f"不是哥们你这怎么报错的？{e}")


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

        self.layout.addWidget(SettingsCard(), Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(30)
        self.layout.addWidget(SearchSettingsCard())
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

        self.seqPlayBtn = TransparentToolButton(FIF.MENU, self)
        self.seqPlayBtn.setToolTip("按顺序播放(不改变播放模式)")

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
        title_layout.addWidget(self.seqPlayBtn, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.upSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.downSongButton, alignment=Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.delQueueButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.tableView)

        self.seqPlayBtn.clicked.connect(sequencePlay)
        self.upSongButton.clicked.connect(self.move_up)
        self.downSongButton.clicked.connect(self.move_down)
        self.delQueueButton.clicked.connect(self.del_queue)
        self.refreshButton.clicked.connect(self.load_play_queue)
        self.tableView.cellDoubleClicked.connect(self.play_selected_song)

        self.load_play_queue()

    def load_play_queue(self):
        if not cfg.play_queue:
            InfoBar.warning(
                "提示",
                "播放列表为空",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=cfg.MAIN_WINDOW
            )
            self.tableView.clear()
            return

        try:
            self.tableView.setRowCount(len(cfg.play_queue))
            self.tableView.setColumnCount(1)
            self.tableView.setHorizontalHeaderLabels(['歌曲'])

            for i, (song) in enumerate(cfg.play_queue):
                song = remove_before_last_backslash(song)
                self.tableView.setItem(i, 0, QTableWidgetItem(song))

            self.tableView.resizeColumnsToContents()
        except Exception as e:
            logger.error("加载歌曲列表失败:", e)

    def move_up(self):
        index = self.tableView.currentIndex().row()
        if index > 0:
            cfg.play_queue[index - 1], cfg.play_queue[index] = cfg.play_queue[index], cfg.play_queue[
                index - 1]
            self.tableView.setCurrentIndex(self.tableView.model().index(index - 1, 0))

            if cfg.play_queue_index == index:
                cfg.play_queue_index -= 1

        self.load_play_queue()

    def move_down(self):
        index = self.tableView.currentIndex().row()
        if index < len(cfg.play_queue) - 1:
            cfg.play_queue[index + 1], cfg.play_queue[index] = cfg.play_queue[index], cfg.play_queue[
                index + 1]
            self.tableView.setCurrentIndex(self.tableView.model().index(index + 1, 0))

            if cfg.play_queue_index == index:
                cfg.play_queue_index += 1

        self.load_play_queue()

    def del_queue(self):
        index = self.tableView.currentIndex().row()
        if index >= 0:
            try:
                logger.info(f"删除了歌曲: {cfg.play_queue[index]}, 位置: {index}")
                cfg.play_queue.pop(index)
                self.load_play_queue()
            except Exception as e:
                logger.error(e)

    @staticmethod
    def play_selected_song(row):
        """双击播放指定行的歌曲"""
        try:
            cfg.play_queue_index = row
            playSongByIndex()
        except Exception as e:
            logger.error(e)


# noinspection PyArgumentList
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

        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.tableView)

        self.tableView.cellDoubleClicked.connect(self.play_selected_song)
        self.refreshButton.clicked.connect(self.load_local_songs)
        self.addQueueButton.clicked.connect(self.add_to_queue)
        self.openPlayer.clicked.connect(open_player)
        self.openInfoTip.clicked.connect(open_info_tip)
        self.delSongBtn.clicked.connect(self.del_song)
        self.addQueueAllBtn.clicked.connect(self.add_all_to_queue)

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
            logger.error("加载本地歌曲失败:", e)

    def play_selected_song(self, row):
        """双击播放指定行的歌曲"""
        try:
            item = self.tableView.item(row, 0)
            file_path = getMusicLocal(item)

            url = QUrl.fromLocalFile(file_path)
            self.main_window.player_bar.player.setSource(url)
            self.main_window.player_bar.player.play()

            cfg.playing_now = item.text()

            open_info_tip()

            self.add_to_queue()
            cfg.play_queue_index = cfg.play_queue.index(file_path)
            logger.info(f"当前播放歌曲队列位置：{cfg.play_queue_index}")
        except Exception as e:
            logger.error(e)

    def add_to_queue(self):
        """添加到播放列表"""
        item = self.tableView.currentItem()
        file_path = getMusicLocal(item)

        if file_path:
            if file_path in cfg.play_queue:
                InfoBar.warning(
                    "已存在",
                    f"{item.text()}已存在播放列表",
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self.parent()
                )
                return

            cfg.play_queue.append(file_path)
            InfoBar.success(
                "成功",
                f"已添加{item.text()}到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent()
            )
            logger.info(f"当前播放列表:{cfg.play_queue}")
        else:
            InfoBar.error(
                "失败",
                "添加失败！",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=window
            )

    def del_song(self):
        """删除列表项文件"""
        try:
            item = self.tableView.currentItem()
            file_path = getMusicLocal(item)
            os.remove(file_path)

            if file_path in cfg.play_queue:
                cfg.play_queue.remove(file_path)

            InfoBar.success(
                "完成",
                f"已删除该歌曲",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self.parent()
            )
            self.load_local_songs()

        except Exception as e:
            logger.error(e)

    def add_all_to_queue(self):
        """添加列表所有歌曲到播放列表"""
        try:
            for i in range(self.tableView.rowCount()):
                item = self.tableView.item(i, 0)
                file_path = getMusicLocal(item)
                if file_path in cfg.play_queue:
                    InfoBar.warning(
                        "已存在",
                        f"{item.text()}已存在播放列表",
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=500,
                        parent=self.parent()
                    )
                else:
                    cfg.play_queue.append(file_path)
            InfoBar.success(
                "成功",
                f"已添加所有歌曲到播放列表",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.parent()
            )
            logger.info(f"当前播放列表:{cfg.play_queue}")
        except Exception as e:
            InfoBar.error(
                "添加失败",
                f"{e}",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=window
            )
            logger.error(e)


# noinspection PyArgumentList
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

        self.search_result = SongList()

    def getVideo_btn(self):
        """获取歌曲列表按钮功能实现"""
        try:
            logger.info("获取歌曲列表中...")
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
            logger.error(f"错误:{e};" + type(e).__name__)

    def search_btn(self):
        """实现搜索按钮功能"""
        self.tableView.clear()
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(['标题', 'UP主', '日期', 'BV号'])

        self.search_result.clear()
        search_content = self.searchLine.text().lower()

        try:
            logger.info("---搜索开始---")
            # 获取本地数据
            main_search_list = search_song_list(search_content)
            if main_search_list is None:
                # 本地查找失败时，尝试使用bilibili搜索查找
                logger.info("没有在本地列表找到该歌曲，正在尝试bilibili搜索")
                try:
                    searchOnBili(search_content)
                    main_search_list = search_song_list(search_content)
                    if main_search_list is None:
                        raise TypeError
                except TypeError:
                    logger.error("bilibili搜索结果为空")
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
                    logger.error(f"错误:{e};" + type(e).__name__)
            else:
                if True:
                    logger.info(f"本地获取 {len(main_search_list.get_data())} 个有效视频数据:")
                    logger.info(main_search_list.get_data())
                    # 本地查找成功，追加使用bilibili搜索查找
                    # todo:可以加入一个设置项配置是否联网搜索
                    logger.info("在本地列表找到该歌曲，继续尝试bilibili搜索")
                    try:
                        searchOnBili(search_content)

                        more_search_list = search_song_list(search_content)
                        logger.info(f"bilibili获取 "
                                    f"{len(more_search_list.get_data()) - len(main_search_list.get_data())} "
                                    f"个有效视频数据:")

                    except Exception as e:
                        logger.error(f"错误:{e};" + type(e).__name__)
                        if type(main_search_list) != "NoneType":
                            logger.warning("bilibili搜索失败,返回本地列表项")

            # 写入表格和数据
            if main_search_list is not None:
                self.search_result = main_search_list
                self.writeList()
            else:
                raise TypeError

            self.tableView.setCurrentIndex(self.tableView.model().index(0, 0))
        except TypeError:
            logger.error("搜索结果为空")
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
            logger.error(f"错误:{e};" + type(e).__name__)
        logger.info("---搜索结束---\n")
        self.tableView.resizeColumnsToContents()

    # 当爬虫任务结束时
    def on_c_task_finished(self):
        self.loading.close()
        window.setEnabled(True)
        self.GetVideoBtn.setEnabled(True)
        self.setWindowModality(Qt.WindowModality.NonModal)  # 恢复正常模式

        logger.info("获取歌曲列表完成！")
        self.stateTooltip.setContent('获取列表完成!!!')
        self.stateTooltip.setState(True)
        self.stateTooltip = None

    def writeList(self):
        """将搜索结果写入表格"""
        search_result = self.search_result
        print(f"总计获取 {len(search_result.get_data())} 个有效视频数据:")
        print(search_result.get_data())
        self.tableView.setRowCount(len(search_result.get_data()))

        for i, songInfo in enumerate(search_result.get_data()):
            self.tableView.setItem(i, 0, QTableWidgetItem(songInfo["title"]))
            self.tableView.setItem(i, 1, QTableWidgetItem(songInfo["author"]))
            self.tableView.setItem(i, 2, QTableWidgetItem(format_date_str(songInfo["date"])))
            self.tableView.setItem(i, 3, QTableWidgetItem(songInfo["bv"]))

    def Download_btn(self):
        index = self.tableView.currentRow()
        InfoBar.info(
            title='提示',
            content="开始下载歌曲，请耐心等待",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )
        try:
            fileType = cfg.downloadType
            run_download(index, self.search_result, fileType)
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
            InfoBar.error(
                title='错误',
                content="你还没有选择歌曲",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
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
            logger.error(f"[Error]{e}")


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

        # todo
        # 实现主页显示player情况
        # neuro主题  个性化元素
        # 显示当前版本号
        # 显示neuro直播时间表

        self.readmeLabel = SubtitleLabel("介绍", self)
        self.readmeInfoLabel = BodyLabel(
            "这是一个基于 Python 3.13 开发的程序，\n"
            "用于从 Bilibili（哔哩哔哩）爬取 Neuro/Evil 的歌曲的视频内容。\n"
            "如果搜索没结果的话，可以试试多搜几次\n"
            "(当然未来也支持通过自定义UP 主列表和关键词，灵活调整爬取目标) \n"
            f"\nLicense:   AGPL-3.0\nVersion: {config.VERSION}",
            self
        )

        self.layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.subTitleLabel)
        self.layout.addWidget(self.infoLabel)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.readmeLabel)
        self.layout.addWidget(self.readmeInfoLabel)

        self.layout.addStretch(1)


# noinspection PyArgumentList
class DemoWindow(FluentWindow):
    """全新GUI"""

    def __init__(self):
        super().__init__()
        self.setObjectName("demoWindow")
        icon = QtGui.QIcon("res\\main.ico")

        self.homeInterface = HomeInterface(self)
        self.setWindowIcon(icon)

        self.player_bar = CustomMediaPlayBar()
        self.player_bar.setFixedSize(300, 120)
        self.player_bar.player.setVolume(cfg.volume)
        self.player_bar.setWindowIcon(icon)
        self.player_bar.setWindowTitle("Player")
        self.player_bar.show()
        cfg.set_player(self.player_bar)

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

    def closeEvent(self, event):
        try:
            logger.info("正在弹出退出确认对话框...")

            w = MessageBox(
                '即将关闭整个程序',
                "您确定要这么做吗？",
                self
            )
            w.setDraggable(False)

            if w.exec():
                logger.info("用户确认退出，程序即将关闭。")
                event.accept()
                QApplication.quit()
            else:
                logger.info("用户取消了退出操作。")
                event.ignore()

        except Exception as e:
            logger.error(f"在退出确认过程中发生错误: {e}")


if __name__ == '__main__':
    # 新版GUI开发中
    # --- 启用高 DPI 支持 ---
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):  # Qt.HighDpiScaleFactorRoundingPolicy 枚举本身
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
            # noinspection PyArgumentList
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 初始化
    create_dir("data")
    create_dir("log")

    # 初始化日志
    log_file_name_format = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_folder_name = datetime.now().strftime("%Y-%m-%d")
    base_log_dir = Path("log")
    daily_log_dir = base_log_dir / log_folder_name
    log_file_name = f"{log_file_name_format}.log"
    log_file_path = daily_log_dir / log_file_name

    # 添加 sink，Loguru 会自动创建 "daily_logs/2025-06-09/" 这样的目录结构
    logger.add(log_file_path, format="[{time:HH:mm:ss}]-[{level}]{message}")

    app = QApplication(sys.argv)

    # 设置初始主题
    setTheme(Theme.AUTO)

    window = DemoWindow()
    cfg.set_main_window(window)

    window.show()
    sys.exit(app.exec())
