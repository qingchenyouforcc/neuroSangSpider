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