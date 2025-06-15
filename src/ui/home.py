from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, SubtitleLabel, TitleLabel

from src.config import VERSION


class HomeInterface(QWidget):
    """主页GUI"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        # 实现主页文字
        self.titleLabel = TitleLabel(f"NeuroSangSpider {VERSION}", self)
        self.subTitleLabel = SubtitleLabel("全新的NeuroSangSpider", self)
        self.infoLabel = BodyLabel(
            "- 更加智能的搜索机制 \n- 更多的参数设定 \n- 更现代化的GUI \n- 更丰富的功能 \n",
            self,
        )

        # todo
        # 实现主页显示player情况
        # neuro主题  个性化元素
        # 显示当前版本号
        # 显示neuro直播时间表

        self.readmeLabel = SubtitleLabel("介绍", self)
        self.readmeInfoLabel = BodyLabel(
            "这是一个基于 Python 3.13 开发的程序，\n"
            "用于从 Bilibili（哔哩哔哩）爬取 Neuro/Evil 的歌曲的视频内容。\n"
            "如果搜索没结果的话，可以试试多搜几次\n"
            "(当然未来也支持通过自定义UP 主列表和关键词，灵活调整爬取目标) \n"
            f"\nLicense:   AGPL-3.0\nVersion: {VERSION}",
            self,
        )

        self._layout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self.subTitleLabel)
        self._layout.addWidget(self.infoLabel)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.readmeLabel)
        self._layout.addWidget(self.readmeInfoLabel)

        self._layout.addStretch(1)
