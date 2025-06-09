import sys

from qfluentwidgets import QConfig, OptionsConfigItem, OptionsValidator

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

class Config(QConfig):
    downloadType = OptionsConfigItem(
        "Download", "downloadType", "mp3",
        OptionsValidator(["mp3", "ogg", "wav"]), restart=False)


# 初始化变量
cfg = Config()

search_page = 1

volume = 50
play_queue = []
play_queue_index = 0
# 播放模式 0是列表循环 1是顺序播放 2是单曲循环
play_mode = 0

playing_now = None
# 这个是播放器类，player在这个里面
player = None

info_bar = None
info_bar_play_btn = None

HAS_INFOPLAYERBAR = False