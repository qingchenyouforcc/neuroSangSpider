import os
import sys
import subprocess
from loguru import logger


def restart_app():
    """
    重启程序
    通过启动一个新的应用实例并退出当前实例来实现重启功能
    """
    try:
        if getattr(sys, "frozen", False):
            # 打包后的情况
            executable = sys.executable
            args = []
        else:
            # 开发环境
            executable = sys.executable
            args = [sys.argv[0]] if sys.argv else []

        logger.info(f"启动新实例: {executable} {' '.join(args)}")

        # 设置语言重启环境变量
        env = os.environ.copy()
        env["LANGUAGE_RESTART"] = "1"

        subprocess.Popen(
            [executable] + args,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            env=env,
            close_fds=True,
        )

        sys.exit(0)

    except Exception as e:
        logger.error(f"重启失败: {e}")
        # 如果subprocess失败，尝试直接退出
        sys.exit(1)
