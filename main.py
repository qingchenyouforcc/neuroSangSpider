import os
import sys
from datetime import datetime

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog

from src.config import ASSETS_DIR, I18N_DIR
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

    # 语言资源目录迁移到 data/i18n，若为空则从 assets 引导复制
    language_file_dir = I18N_DIR
    try:
        if not any(language_file_dir.glob("*.properties")):
            language_file_dir.mkdir(parents=True, exist_ok=True)
            src_dir = ASSETS_DIR / "i18n"
            if src_dir.exists():
                for fp in src_dir.glob("*.properties"):
                    # 避免覆盖已存在文件
                    target = language_file_dir / fp.name
                    if not target.exists():
                        target.write_bytes(fp.read_bytes())
    except Exception as e:
        logger.error(f"初始化语言文件失败: {e}")

    app_context.i18n_manager = I18nManager(language_file_dir)
    app = QApplication(sys.argv)

    # 检查是否为首次运行
    from src.ui import WelcomeDialog

    if WelcomeDialog.is_first_run():
        welcome_dialog = WelcomeDialog()
        if welcome_dialog.exec() != QDialog.DialogCode.Accepted:
            # 如果用户关闭了对话框，使用默认语言继续
            pass

    window = app_context.main_window = MainWindow()
    logger.info("主窗口创建完成")

    # 检查是否是语言切换重启
    is_language_restart = os.environ.get("LANGUAGE_RESTART", "0") == "1"
    window.is_language_restart = is_language_restart
    if is_language_restart:
        # 清除环境变量
        os.environ["LANGUAGE_RESTART"] = "0"
        window.is_language_restart = False

    # 不在这里显示主窗口，等待启动画面动画完成后自动显示
    # window.show()
    # logger.info("主窗口显示")

    logger.info("开始应用程序主循环")
    sys.exit(app.exec())
