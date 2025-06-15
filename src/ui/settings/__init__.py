from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea, isDarkTheme

from src.config import cfg

from .card import SettingsCard
from .search_card import SearchSettingsCard


class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        self.settingLabel = QLabel("设置", self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # 添加滚动区域
        self.scroll_area = scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 创建容器控件
        container = QWidget(scroll_area)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(15)

        # 添加设置卡片
        container_layout.addWidget(SettingsCard())
        container_layout.addStretch(1)
        container_layout.addWidget(SearchSettingsCard())

        # 设置滚动区域的控件
        scroll_area.setWidget(container)

        # 将滚动区域添加到主布局
        self._layout.addWidget(scroll_area)

        cfg.theme_mode.valueChanged.connect(self._update_style)

    def _update_style(self):
        """更新控件样式"""
        # 根据主题设置背景色

        bg_color = "#202020" if isDarkTheme() else "#ffffff"
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {bg_color};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {bg_color};
            }}
        """)
