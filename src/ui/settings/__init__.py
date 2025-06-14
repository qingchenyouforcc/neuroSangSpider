from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from .card import SettingsCard
from .search_card import SearchSettingsCard


class SettingInterface(QWidget):
    """设置GUI"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(15)

        self._layout.addWidget(SettingsCard(), Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(30)
        self._layout.addWidget(SearchSettingsCard())
        self._layout.addStretch(1)
