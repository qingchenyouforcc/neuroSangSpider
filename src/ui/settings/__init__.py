from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea

from .card import SettingsCard
from .search_card import SearchSettingsCard


class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")

        self._layout = QVBoxLayout(self)
        # self._layout.setContentsMargins(30, 30, 30, 30)
        # 减小控件间距
        # self._layout.setSpacing(15)

        # 添加滚动区域
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 创建容器控件
        container = QWidget(scroll_area)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)

        # 添加设置卡片
        container_layout.addWidget(SettingsCard())
        container_layout.addWidget(SearchSettingsCard())
        container_layout.addStretch(1)

        # 设置滚动区域的控件
        scroll_area.setWidget(container)

        # 将滚动区域添加到主布局
        self._layout.addWidget(scroll_area)
