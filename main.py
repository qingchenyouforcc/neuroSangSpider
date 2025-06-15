import sys
from datetime import datetime

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from common.config import cfg
from src.ui import MainWindow


def setup_logger() -> None:
    logger.remove()
    log_format = "<g>{time:HH:mm:ss}</g> [<lvl>{level}</lvl>] <c><u>{name}</u></c>:<c>{function}:{line}</c> | {message}"

    # pyinstaller 打包并禁用控制台后, sys.stdout 为 None
    if sys.stdout:
        logger.add(
            sys.stdout,
            format=log_format,
            level="DEBUG",
            colorize=True,
        )

    now = datetime.now()
    logger.add(
        f"logs/{now:%Y-%m-%d}/{now:%Y-%m-%d_%H-%M-%S}.log",
        format=log_format,
        level="DEBUG",
        diagnose=True,
    )


if __name__ == "__main__":
    # --- 启用高 DPI 支持 ---
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        # noinspection PyArgumentList
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):  # Qt.HighDpiScaleFactorRoundingPolicy 枚举本身
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
            # noinspection PyArgumentList
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    setup_logger()

    app = QApplication(sys.argv)
    window = cfg.main_window = MainWindow()
    window.show()
    sys.exit(app.exec())
