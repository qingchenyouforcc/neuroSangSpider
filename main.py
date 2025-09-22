import os
import sys
from datetime import datetime

from loguru import logger
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtWidgets import QApplication, QDialog

from src.config import ASSETS_DIR, cfg
from src.i18n.manager import I18nManager
from src.app_context import app_context
from src.ui import MainWindow

LOG_FORMAT = "<g>{time:HH:mm:ss}</g> [<lvl>{level:<7}</lvl>] <c><u>{name}</u></c>:<c>{function}:{line}</c> | {message}"


def setup_logger() -> None:
    logger.remove()

    # pyinstaller 打包并禁用控制台后, sys.stdout 为 None
    if sys.stdout:
        logger.add(
            sys.stdout,
            format=LOG_FORMAT,
            level="DEBUG",
            colorize=True,
        )

    now = datetime.now()
    logger.add(
        f"logs/{now:%Y-%m-%d}/{now:%Y-%m-%d_%H-%M-%S}.log",
        format=LOG_FORMAT,
        level="DEBUG",
        diagnose=True,
    )


def restart_app():
    """重启程序
    
    通过启动一个新的应用实例并退出当前实例来实现重启功能，
    这样可以避免在语言切换时出现退出确认对话框的问题。
    """
    logger.info("开始重启应用程序...")

    # 设置语言重启环境变量
    os.environ['LANGUAGE_RESTART'] = '1'
    logger.info(f"设置LANGUAGE_RESTART环境变量为: {os.environ.get('LANGUAGE_RESTART')}")

    # 如果主窗口存在，设置重启标志
    if hasattr(app_context, 'main_window') and app_context.main_window:
        app_context.main_window.is_language_restart = True
        logger.info("设置主窗口is_language_restart标志为True")
    
    # 优先使用subprocess启动新实例，然后退出当前进程
    import subprocess
    try:
        if getattr(sys, 'frozen', False):
            # 打包后的情况
            executable = sys.executable
            args = []
        else:
            # 开发环境
            executable = sys.executable
            args = [sys.argv[0]] if sys.argv else []
        
        logger.info(f"使用subprocess启动新实例: {executable} {' '.join(args)}")
        
        env = os.environ.copy()
        env['LANGUAGE_RESTART'] = '1'
        
        # 启动新实例
        process = subprocess.Popen([executable] + args, 
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                                 env=env,
                                 close_fds=True)
        
        logger.info(f"新实例已启动，PID: {process.pid}")
        
        # 等待一小段时间确保新实例启动
        import time
        time.sleep(0.5)
        
        # 退出当前应用程序
        logger.info("退出当前应用程序")
        QApplication.quit()
        
    except Exception as e:
        logger.error(f"subprocess重启失败: {e}")
        
        # 回退到QProcess
        try:
            logger.info("回退到QProcess重启")
            QProcess.startDetached(sys.executable, sys.argv)
            QApplication.quit()
        except Exception as e2:
            logger.error(f"QProcess也失败: {e2}")
            # 最后尝试直接使用os.execv
            try:
                if getattr(sys, 'frozen', False):
                    executable = sys.executable
                    args = [executable]
                else:
                    executable = sys.executable
                    args = [sys.executable] + sys.argv
                
                logger.info(f"最后尝试os.execv: {executable} {' '.join(args[1:])}")
                os.execv(executable, args)
            except Exception as e3:
                logger.error(f"所有重启方法都失败: {e3}")


if __name__ == "__main__":
    # --- 启用高 DPI 支持 ---
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)  # type: ignore
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)  # type: ignore
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):  # Qt.HighDpiScaleFactorRoundingPolicy 枚举本身
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
            # noinspection PyArgumentList
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    setup_logger()

    language_file_dir = ASSETS_DIR / "i18n"
    app_context.i18n_manager = I18nManager(language_file_dir)
    app = QApplication(sys.argv)

    # 检查是否为首次运行
    from src.ui import WelcomeDialog
    
    if WelcomeDialog.is_first_run():
        welcome_dialog = WelcomeDialog()
        if welcome_dialog.exec() != QDialog.DialogCode.Accepted:
            # 如果用户关闭了对话框，使用默认语言继续
            pass

    app_context.i18n_manager.set_language(cfg.language.value)

    window = app_context.main_window = MainWindow()
    logger.info("主窗口创建完成")

    window.show()
    logger.info("主窗口显示")
    
    logger.info("开始应用程序主循环")
    sys.exit(app.exec())