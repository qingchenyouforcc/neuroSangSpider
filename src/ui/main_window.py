import os
import sys
import subprocess
from loguru import logger
from PyQt6 import QtGui
from PyQt6.QtCore import QSize, QProcess
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    SystemThemeListener,
    MessageBox,
    MessageBoxBase,
    SubtitleLabel,
    BodyLabel,
    CheckBox,
    PushButton,
)

from src.i18n import t
from src.config import ASSETS_DIR, cfg, Theme
from src.app_context import app_context

from src.ui.interface.home import HomeInterface
from src.ui.interface.local_player import LocalPlayerInterface
from src.ui.widgets.media_player_bar import CustomMediaPlayBar
from src.ui.widgets.animated_splash_screen import AnimatedSplashScreen
from src.ui.interface.play_queue import PlayQueueInterface
from src.ui.interface.search import SearchInterface
from src.ui.interface.settings import SettingInterface


class CloseActionDialog(MessageBoxBase):
    """关闭动作选择对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 标题
        self.titleLabel = SubtitleLabel(t("dialog.close_choice.title"), self)
        self.viewLayout.addWidget(self.titleLabel)

        # 内容详情
        self.contentLabel = BodyLabel(t("dialog.close_choice.content"), self)
        self.viewLayout.addWidget(self.contentLabel)

        # 总是最小化复选框
        self.checkBox = CheckBox(t("dialog.close_choice.always_minimize"))
        self.viewLayout.addWidget(self.checkBox)

        # 最小化按钮
        self.minimizeBtn = PushButton(t("dialog.close_choice.minimize"))
        self.minimizeBtn.setObjectName("minimizeBtn")
        self.minimizeBtn.clicked.connect(self._onMinimize)

        # 将最小化按钮插入到 Yes(Exit) 和 Cancel 之间
        # MessageBoxBase 的 buttonLayout 包含 yesButton, cancelButton (可能还有 spacer)
        # 通常 yesButton 是 Exit, cancelButton 是 Cancel
        self.buttonLayout.insertWidget(1, self.minimizeBtn)

        self.yesButton.setText(t("dialog.close_choice.exit"))
        self.cancelButton.setText(t("common.cancel"))

        self.action = None

        # 设置默认按钮样式等
        self.yesButton.setObjectName("exitBtn")

    def _onMinimize(self):
        self.action = "minimize"
        self.accept()

    def accept(self):
        # 如果不是点击最小化进来的，且 self.action 还没设置，说明是点击了 Yes(Exit)
        if self.action is None:
            self.action = "exit"
        super().accept()


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()

        self.is_language_restart = False

        # 系统主题监听器
        self.themeListener = SystemThemeListener(self)

        self.setObjectName("demoWindow")
        icon = QtGui.QIcon(str(ASSETS_DIR / "main.ico"))

        self.homeInterface = HomeInterface(self)
        self.setWindowIcon(icon)

        # 系统托盘
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_menu = QMenu()

        self.show_action = QtGui.QAction(t("common.show"), self)
        self.show_action.triggered.connect(self.showNormal)

        self.quit_action = QtGui.QAction(t("common.exit"), self)
        self.quit_action.triggered.connect(self.quit_app)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

        # 设置初始窗口大小
        desktop = QApplication.primaryScreen()
        if desktop:  # 确保 desktop 对象不是 None
            available_geometry = desktop.availableGeometry()
            width = int(available_geometry.width() * 0.615)
            height = int(available_geometry.height() * 0.735)
            initial_size = QSize(width, height)
            self.resize(initial_size)

            # 移动到屏幕中心
            x = available_geometry.x() + (available_geometry.width() - width) // 2
            y = available_geometry.y() + (available_geometry.height() - height) // 2
            self.move(x, y)

            self._initial_size = initial_size  # 保存初始大小，供启动画面结束后恢复使用
            logger.info(f"已设置初始窗口大小为 {self.size().width()}x{self.size().height()} 并已居中显示")
        else:  # 如果获取不到主屏幕信息，给一个默认大小
            initial_size = QSize(780, 530)
            self.resize(initial_size)
            self._initial_size = initial_size  # 保存初始大小
            logger.warning("未找到可用的屏幕，已使用默认大小 780x530")

        # 创建并显示启动页面（使用 GIF 动画，播放 1 轮后自动关闭并显示主窗口）
        frames_dir = ASSETS_DIR / "main_loading"
        self.splashScreen = AnimatedSplashScreen(frames_dir, self, frame_delay=100, loop_count=1)
        self.splashScreen.show()  # 立即显示启动画面

        # TODO 实现按照配置文件主题切换，bug没修好
        # 临时方案：按照系统主题修改
        cfg.set_theme(Theme.AUTO)
        logger.info("应用默认主题: AUTO")

        # 不在这里显示主窗口，等启动画面动画完成后再显示
        # self.show()  # 注释掉这行

        # 添加子界面
        self.addSubInterface(
            interface=self.homeInterface,
            icon=FIF.HOME,
            text=t("nav.home"),
            position=NavigationItemPosition.TOP,
        )
        QApplication.processEvents()  # 让启动画面动画有机会播放

        self.searchInterface = SearchInterface(self, main_window=self)
        self.addSubInterface(
            interface=self.searchInterface,
            icon=FIF.SEARCH,
            text=t("nav.search"),
            position=NavigationItemPosition.TOP,
        )
        QApplication.processEvents()  # 让启动画面动画有机会播放

        self.playQueueInterface = PlayQueueInterface(self, main_window=self)
        self.addSubInterface(
            interface=self.playQueueInterface,
            icon=FIF.ALIGNMENT,
            text=t("nav.play_queue"),
            position=NavigationItemPosition.TOP,
        )
        QApplication.processEvents()  # 让启动画面动画有机会播放

        self.localPlayerInterface = LocalPlayerInterface(self, main_window=self)
        self.addSubInterface(
            interface=self.localPlayerInterface,
            icon=FIF.PLAY,
            text=t("nav.local_player"),
            position=NavigationItemPosition.BOTTOM,
        )
        QApplication.processEvents()  # 让启动画面动画有机会播放

        self.settingsInterface = SettingInterface(self)
        self.addSubInterface(
            interface=self.settingsInterface,
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
        # 不在这里显示播放器窗口，等启动画面动画完成后再显示
        # self.player_bar.show()
        app_context.player = self.player_bar

        # 初始化默认界面
        # 使用 QTimer 延迟设置，确保在布局完成后执行
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(50, lambda: self.switchTo(self.homeInterface))

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

        # 启动画面会在动画播放完成后自动关闭并显示主窗口
        # 不需要手动调用 finish()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                if self.isMinimized():
                    self.showNormal()
                    self.activateWindow()
                else:
                    self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def quit_app(self):
        self._is_force_quit = True
        self.close()

    def closeEvent(self, event):  # type: ignore[override]
        # 如果启用了最小化到托盘，且不是语言切换重启
        if cfg.minimize_to_tray.value and not self.is_language_restart:
            event.ignore()
            self.hide()
            return

        # 如果是强制退出（如托盘菜单退出），直接关闭
        if getattr(self, "_is_force_quit", False):
            self.before_shutdown()
            event.accept()
            QApplication.quit()
        elif not self.is_language_restart:
            # 显示关闭动作选择对话框
            try:
                logger.info("正在弹出关闭动作选择对话框...")
                w = CloseActionDialog(self)

                if w.exec():
                    if w.action == "minimize":
                        logger.info("用户选择最小化到托盘")
                        if w.checkBox.isChecked():
                            cfg.minimize_to_tray.value = True
                            cfg.save()
                        event.ignore()
                        self.hide()
                        return
                    elif w.action == "exit":
                        logger.info("用户选择直接退出")
                        self.before_shutdown()
                        event.accept()
                        QApplication.quit()
                    else:
                        # 理论上不应该到这里，除非 exec 返回 True 但 action 是 None
                        logger.warning("未知的关闭动作，默认为取消")
                        event.ignore()
                else:
                    logger.info("用户取消了关闭操作。")
                    event.ignore()
            except Exception as e:
                logger.exception(f"在关闭选择过程中发生错误: {e}")
                # 发生错误时安全退出
                self.before_shutdown()
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

        # 停止下载队列
        try:
            # 遍历所有子界面，找到SearchInterface并停止其下载队列
            for i in range(self.stackedWidget.count()):
                widget = self.stackedWidget.widget(i)
                download_queue = getattr(widget, "download_queue", None)
                if download_queue and hasattr(download_queue, "stop"):
                    logger.info("正在停止下载队列...")
                    download_queue.stop()
        except Exception:
            logger.exception("停止下载队列时出错")

        # 终止系统主题监听器
        self.themeListener.terminate()
        self.themeListener.deleteLater()
