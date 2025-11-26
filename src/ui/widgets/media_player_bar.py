from typing import cast

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import CaptionLabel, FluentIcon
from qfluentwidgets.multimedia import MediaPlayBarButton, MediaPlayer, MediaPlayerBase
from qfluentwidgets.multimedia.media_play_bar import MediaPlayBarBase

from src.i18n import t
from src.app_context import app_context
from src.config import PlayMode, cfg
from src.core.player import nextSong, playSongByIndex, previousSong
from src.ui.widgets.tipbar import update_info_tip


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
        self.modeChangeButton.setToolTip(t("play_mode.list_loop"))

        self.currentTimeLabel = CaptionLabel("0:00:00", self)
        self.remainTimeLabel = CaptionLabel("0:00:00", self)

        self.__initWidgets()

    def __initWidgets(self) -> None:
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

        cast(QMediaPlayer, self.player).playbackStateChanged.connect(self._onPlayStateChanged)

        self.volumeButton.clicked.connect(lambda: self.setVolume(cfg.volume.value))
        self.volumeButton.volumeView.volumeSlider.valueChanged.connect(self.volumeChanged)
        self.skipBackButton.clicked.connect(lambda: self.skipBack(10000))
        self.previousSongButton.clicked.connect(previousSong)
        self.nextSongButton.clicked.connect(nextSong)
        self.modeChangeButton.clicked.connect(self.modeChange)

    def _onPlayStateChanged(self, state: QMediaPlayer.PlaybackState):
        """Handle play state changed signal"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playButton.setIcon(FluentIcon.PAUSE_BOLD)
        else:
            self.playButton.setIcon(FluentIcon.PLAY_SOLID)

    @staticmethod
    def volumeChanged(value) -> None:
        cfg.volume.value = value
        cfg.save()

    def skipBack(self, ms: int) -> None:
        """Back up for specified milliseconds"""
        self.player.setPosition(self.player.position() - ms)

    def _onPositionChanged(self, position: int) -> None:
        super()._onPositionChanged(position)
        self.currentTimeLabel.setText(self._formatTime(position))
        self.remainTimeLabel.setText(self._formatTime(self.player.duration() - position))

        remainTime = self.player.duration() - position

        if remainTime == 0:
            # 实现音乐播放次数统计
            song_name = app_context.play_queue[app_context.play_queue_index].name
            if song_name in cfg.play_count.value:
                cfg.play_count.value[song_name] += 1
            else:
                cfg.play_count.value[song_name] = 1

            cfg.save()

            match cfg.play_mode.value:
                case PlayMode.LIST_LOOP:
                    logger.info("歌曲播放完毕，自动播放下一首。")
                    nextSong()
                case PlayMode.SEQUENTIAL:
                    if app_context.play_queue_index < len(app_context.play_queue):
                        logger.info("歌曲播放完毕，自动播放下一首。")
                        nextSong()
                case PlayMode.SINGLE_LOOP:
                    playSongByIndex()
                case PlayMode.RANDOM:
                    logger.info("歌曲播放完毕，自动播放下一首。")
                    nextSong()

    @staticmethod
    def _formatTime(time: int):
        time = int(time / 1000)
        s = time % 60
        m = int(time / 60)
        h = int(time / 3600)
        return f"{h}:{m:02}:{s:02}"

    def modeChange(self):
        if cfg.play_mode.value >= PlayMode.RANDOM:
            cfg.play_mode.value = PlayMode.LIST_LOOP
        else:
            cfg.play_mode.value = PlayMode(cfg.play_mode.value + 1)

        match cfg.play_mode.value:
            case PlayMode.LIST_LOOP:
                self.modeChangeButton.setIcon(FluentIcon.SYNC)
                self.modeChangeButton.setToolTip(t("play_mode.list_loop"))
            case PlayMode.SEQUENTIAL:
                self.modeChangeButton.setIcon(FluentIcon.MENU)
                self.modeChangeButton.setToolTip(t("play_mode.sequential"))
            case PlayMode.SINGLE_LOOP:
                self.modeChangeButton.setIcon(FluentIcon.ROTATE)
                self.modeChangeButton.setToolTip(t("play_mode.single_loop"))
            case PlayMode.RANDOM:
                self.modeChangeButton.setIcon(FluentIcon.QUESTION)
                self.modeChangeButton.setToolTip(t("play_mode.random"))

    def togglePlayState(self):
        """toggle the play state of media player"""
        super().togglePlayState()

        if app_context.info_bar is not None:
            try:
                update_info_tip()
            except Exception as e:
                logger.warning(e)
