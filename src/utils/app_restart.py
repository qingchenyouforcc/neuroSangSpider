import os
import sys
import subprocess
from loguru import logger

from src.app_context import app_context
from i18n import t


def restart_app():
    """
    重启程序
    通过启动一个新的应用实例并退出当前实例来实现重启功能
    """
    logger.info(t("app.restart_starting"))

    # 设置语言重启环境变量
    os.environ['LANGUAGE_RESTART'] = '1'
    logger.info(t("app.language_restart_env_set").format(value=os.environ.get('LANGUAGE_RESTART')))

    if hasattr(app_context, 'main_window') and app_context.main_window:
        try:
            app_context.main_window.is_language_restart = True
            logger.info(t("app.main_window_restart_flag_set"))
        except Exception as e:
            logger.error(f"设置重启标志时出错: {e}")
    
    logger.info(t("app.quit_waiting_confirm"))

    try:
        if getattr(sys, 'frozen', False):
            # 打包后的情况
            executable = sys.executable
            args = []
        else:
            # 开发环境
            executable = sys.executable
            args = [sys.argv[0]] if sys.argv else []
        
        logger.info(f"启动新实例: {executable} {' '.join(args)}")
        
        subprocess.Popen([executable] + args, 
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                        close_fds=True)

        sys.exit(0)
        
    except Exception as e:
        logger.error(f"重启失败: {e}")
        # 如果subprocess失败，尝试直接退出
        sys.exit(1)