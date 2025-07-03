from loguru import logger
from PyQt6 import QtGui
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import SplashScreen
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, MessageBox, NavigationItemPosition, SystemThemeListener

from src.config import ASSETS_DIR, cfg, Theme
from src.app_context import app_context

from src.ui.interface.home import HomeInterface
from src.ui.interface.local_player import LocalPlayerInterface
from src.ui.widgets.media_player_bar import CustomMediaPlayBar
from src.ui.interface.play_queue import PlayQueueInterface
from src.ui.interface.search import SearchInterface
from src.ui.interface.settings import SettingInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 系统主题监听器
        self.themeListener = SystemThemeListener(self)
        
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
            
        # TODO 实现按照配置文件主题切换，bug没修好
        # 临时方案：按照系统主题修改
        cfg.set_theme(Theme.AUTO) 
        logger.info("应用默认主题: AUTO")

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
        app_context.player = self.player_bar

        # 设置默认音频格式
        cfg.download_type.value = "mp3"
        cfg.save()
        
        # 尝试恢复上次的播放队列（如果当前队列为空）
        try:
            if not app_context.play_queue:
                from src.core.player import restore_last_play_queue
                restore_last_play_queue()
        except Exception as e:
            logger.exception(f"尝试恢复播放队列时出错: {e}")
            
        # 隐藏启动页面
        self.splashScreen.finish()

    def closeEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            logger.info("正在弹出退出确认对话框...")

            w = MessageBox("即将关闭整个程序", "您确定要这么做吗？", self)
            w.setDraggable(False)

            if w.exec():
                # 保存当前播放队列
                from src.core.player import save_current_play_queue
                save_current_play_queue()
                
                logger.info("用户确认退出，程序即将关闭。")
                event.accept()
                self.themeListener.terminate()
                self.themeListener.deleteLater()
                QApplication.quit()
            else:
                logger.info("用户取消了退出操作。")
                event.ignore()

        except Exception:
            logger.exception("在退出确认过程中发生错误")
