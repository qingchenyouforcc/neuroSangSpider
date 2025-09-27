import os
import sys
import subprocess
from loguru import logger
from PyQt6 import QtGui
from PyQt6.QtCore import QSize, QProcess
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import SplashScreen
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, MessageBox, NavigationItemPosition, SystemThemeListener

from i18n import t
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

        self.is_language_restart = False

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
            text=t("nav.home"),
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=SearchInterface(self, main_window=self),
            icon=FIF.SEARCH,
            text=t("nav.search"),
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=PlayQueueInterface(self, main_window=self),
            icon=FIF.ALIGNMENT,
            text=t("nav.play_queue"),
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            interface=LocalPlayerInterface(self, main_window=self),
            icon=FIF.PLAY,
            text=t("nav.local_player"),
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            interface=SettingInterface(self),
            icon=FIF.SETTING,
            text=t("nav.settings"),
            position=NavigationItemPosition.BOTTOM,
        )

        self.setWindowTitle(t("app.title"))

        self.player_bar = CustomMediaPlayBar()
        self.player_bar.setFixedSize(300, 120)
        self.player_bar.player.setVolume(cfg.volume.value)
        self.player_bar.setWindowIcon(icon)
        self.player_bar.setWindowTitle(t("player.title"))
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

    def closeEvent(self, event):  # type: ignore[override]
        if not self.is_language_restart:
            # 显示退出确认对话框
            try:
                logger.info("正在弹出退出确认对话框...")
                w = MessageBox(t("common.close_confirm"), t("common.close_confirm_desc"), self)
                w.setDraggable(False)
                w.yesButton.setText(t("common.ok"))
                w.cancelButton.setText(t("common.cancel"))

                if w.exec():
                    logger.info("用户确认退出，程序即将关闭。")
                    self.before_shutdown()
                    event.accept()
                    QApplication.quit()
                else:
                    logger.info("用户取消了退出操作。")
                    event.ignore()
            except Exception as e:
                logger.exception(f"在退出确认过程中发生错误: {e}")
                event.accept()
        else:
            # 显示重启确认对话框
            try:
                logger.info("正在弹出重启确认对话框...")
                w = MessageBox(t("common.restart_confirm"), t("common.restart_confirm_desc"), self)
                w.setDraggable(False)
                w.yesButton.setText(t("common.ok"))
                w.cancelButton.setText(t("common.cancel"))

                result = w.exec()
                logger.info(f"重启确认对话框结果: {result}")

                if result:
                    logger.info("用户确认重启，程序即将重启。")
                    self.before_shutdown()
                    self._perform_restart()
                    event.accept()
                else:
                    logger.info("用户取消了重启操作。")
                    self.is_language_restart = False
                    event.ignore()
            except Exception as e:
                logger.exception(f"在确认重启过程中发生错误: {e}")
                # 出错时默认执行重启
                self.before_shutdown()
                self._perform_restart()
                event.accept()

    def _perform_restart(self):
        logger.info("正在开始重启...")

        # 优先使用subprocess启动新实例，然后退出当前进程
        try:
            if getattr(sys, "frozen", False):
                # 打包后的情况
                executable = sys.executable
                args = []
            else:
                # 开发环境
                executable = sys.executable
                args = [sys.argv[0]] if sys.argv else []

            logger.info(f"使用subprocess重启: {executable} {' '.join(args)}")

            env = os.environ.copy()
            env["LANGUAGE_RESTART"] = "1"

            # 启动新实例
            process = subprocess.Popen(
                [executable] + args,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                env=env,
                close_fds=True,
            )

            logger.info(f"新实例已启动，PID: {process.pid}")

            sys.exit(0)

        except Exception as e:
            logger.error(f"subprocess重启失败: {str(e)}")

            # 回退到QProcess
            try:
                logger.info("回退到QProcess重启方式")
                QProcess.startDetached(sys.executable, sys.argv)

                sys.exit(0)
            except Exception as e2:
                logger.error(f"QProcess重启失败: {str(e2)}")
                # 最后尝试直接使用os.execv
                try:
                    if getattr(sys, "frozen", False):
                        executable = sys.executable
                        args = [executable]
                    else:
                        executable = sys.executable
                        args = [sys.executable] + sys.argv

                    logger.info(f"最后尝试使用os.execv重启: {executable} {' '.join(args[1:])}")
                    os.execv(executable, args)
                except Exception as e3:
                    logger.error(f"所有重启方法都失败了: {str(e3)}")
                    # 所有方法都失败时，仍然退出当前进程
                    sys.exit(1)

    def before_shutdown(self):
        # 保存当前播放队列
        from src.core.player import save_current_play_queue

        save_current_play_queue()

        # 终止系统主题监听器
        self.themeListener.terminate()
        self.themeListener.deleteLater()
