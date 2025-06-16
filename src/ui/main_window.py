from loguru import logger
from PyQt6 import QtGui
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import SplashScreen
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, MessageBox, NavigationItemPosition

from src.config import ASSETS_DIR, cfg

from .home import HomeInterface
from .local_player import LocalPlayerInterface
from .media_player_bar import CustomMediaPlayBar
from .play_queue import PlayQueueInterface
from .search import SearchInterface
from .settings import SettingInterface   


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("demoWindow")
        icon = QtGui.QIcon(str(ASSETS_DIR / "main.ico"))

        self.homeInterface = HomeInterface(self)
        self.setWindowIcon(icon)
        
        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(64, 64))
        
        # 设置初始窗口大小
        desktop = QApplication.primaryScreen()
        if desktop:  # 确保 desktop 对象不是 None
            self.resize(QSize(680, 530)) 
        # self.resize(QSize(desktop.availableGeometry().width() // 2, desktop.availableGeometry().height() // 2))
        else:  # 如果获取不到主屏幕信息，给一个默认大小
            self.resize(QSize(680, 530))

        # 在创建其他子页面前先显示主界面
        self.show()

        # 添加子界面
        self.addSubInterface(
            interface=self.homeInterface,
            icon=FIF.HOME,
            text="主页",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=SearchInterface(self, main_window=self),
            icon=FIF.SEARCH,
            text="搜索",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=PlayQueueInterface(self, main_window=self),
            icon=FIF.ALIGNMENT,
            text="播放队列",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=LocalPlayerInterface(self, main_window=self),
            icon=FIF.PLAY,
            text="本地播放",
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            interface=SettingInterface(self),
            icon=FIF.SETTING,
            text="设置",
            position=NavigationItemPosition.BOTTOM,
        )

        self.setWindowTitle("NeuroSangSpider")
        
        self.player_bar = CustomMediaPlayBar()
        self.player_bar.setFixedSize(300, 120)
        self.player_bar.player.setVolume(cfg.volume.value)
        self.player_bar.setWindowIcon(icon)
        self.player_bar.setWindowTitle("Player")
        self.player_bar.show()
        cfg.player = self.player_bar

        # 设置默认音频格式
        cfg.download_type.value = "mp3"
        cfg.save()

        # 隐藏启动页面
        self.splashScreen.finish()

    def closeEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            logger.info("正在弹出退出确认对话框...")

            w = MessageBox("即将关闭整个程序", "您确定要这么做吗？", self)
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
