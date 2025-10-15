"""分P选择对话框

用于视频包含多个分P时，让用户选择下载哪些分P。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QGraphicsDropShadowEffect,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    TitleLabel,
    BodyLabel,
    StrongBodyLabel,
    CardWidget,
    IconWidget,
    TransparentToolButton,
    isDarkTheme,
    InfoBar,
    InfoBarPosition,
)

from src.i18n import t


class PartSelectionDialog(QDialog):
    """分P选择对话框 - Fluent Design 风格"""

    def __init__(self, parts: list[dict], parent=None):
        """初始化对话框

        Args:
            parts: 分P信息列表，每个元素包含 'page' (页码) 和 'part' (标题) 字段
            parent: 父窗口
        """
        super().__init__(parent)
        self.parts = parts
        self.selected_parts: list[int] = []

        self.setWindowTitle(t("search.part_selection_title"))
        self.setFixedSize(600, 500)

        # 设置无边框窗口，保留任务栏按钮
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 设置模态
        self.setModal(True)

        self.setObjectName("partSelectionDialog")

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # 卡片容器
        self.card = CardWidget(self)
        self.card.setObjectName("partSelectionCard")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.card.setGraphicsEffect(shadow)

        # 设置卡片样式
        self._update_card_style()

        # 卡片内容布局
        content_layout = QVBoxLayout(self.card)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        # 图标
        self.icon = IconWidget(FIF.VIDEO, self.card)
        self.icon.setFixedSize(32, 32)

        # 标题和描述
        title_content = QVBoxLayout()
        title_content.setSpacing(4)
        self.title_label = TitleLabel(t("search.part_selection_title"), self.card)
        self.desc_label = BodyLabel(t("search.part_selection_desc"), self.card)
        self.desc_label.setWordWrap(True)
        title_content.addWidget(self.title_label)
        title_content.addWidget(self.desc_label)

        title_layout.addWidget(self.icon)
        title_layout.addLayout(title_content, 1)

        # 关闭按钮
        self.close_btn = TransparentToolButton(FIF.CLOSE, self.card)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.reject)
        title_layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(title_layout)

        # 分隔线
        self.separator = QWidget(self.card)
        self.separator.setFixedHeight(1)
        self._update_separator_style()
        content_layout.addWidget(self.separator)

        # 分P信息提示
        info_label = StrongBodyLabel(f"共 {len(self.parts)} 个分P，支持多选", self.card)
        content_layout.addWidget(info_label)

        # 分P列表
        self.part_list = QListWidget(self.card)
        self.part_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.part_list.setObjectName("partListWidget")
        self._update_part_list_style()

        for part_info in self.parts:
            page = part_info.get("page", 1)
            title = part_info.get("part", f"分P {page}")
            item_text = f"{t('search.part_number', num=page)}: {title}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, page)
            self.part_list.addItem(item)

        content_layout.addWidget(self.part_list, 1)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.select_all_btn = PushButton("全选", self.card)
        self.select_all_btn.setIcon(FIF.CHECKBOX)
        self.select_all_btn.clicked.connect(self._on_select_all)
        button_layout.addWidget(self.select_all_btn)

        button_layout.addStretch()

        self.confirm_btn = PrimaryPushButton(t("common.ok"), self.card)
        self.confirm_btn.setIcon(FIF.ACCEPT)
        self.confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_btn)

        self.cancel_btn = PushButton(t("common.cancel"), self.card)
        self.cancel_btn.setIcon(FIF.CANCEL)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        content_layout.addLayout(button_layout)

        # 将卡片添加到主布局
        main_layout.addWidget(self.card)

    def _update_card_style(self):
        """更新卡片样式"""
        if isDarkTheme():
            bg_color = "rgb(39, 39, 39)"
            border_color = "rgb(58, 58, 58)"
        else:
            bg_color = "rgb(252, 252, 252)"
            border_color = "rgb(229, 229, 229)"

        self.card.setStyleSheet(f"""
            CardWidget#partSelectionCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

    def _update_separator_style(self):
        """更新分隔线样式"""
        if isDarkTheme():
            self.separator.setStyleSheet("background-color: rgba(255, 255, 255, 30);")
        else:
            self.separator.setStyleSheet("background-color: rgba(0, 0, 0, 30);")

    def _update_part_list_style(self):
        """更新分P列表样式"""
        if isDarkTheme():
            self.part_list.setStyleSheet("""
                QListWidget {
                    background-color: rgb(32, 32, 32);
                    border: 1px solid rgb(58, 58, 58);
                    border-radius: 6px;
                    padding: 4px;
                    color: #FFFFFF;
                }
                QListWidget::item {
                    padding: 8px;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: rgb(45, 45, 45);
                }
                QListWidget::item:selected {
                    background-color: rgb(0, 120, 212);
                    color: #FFFFFF;
                }
            """)
        else:
            self.part_list.setStyleSheet("""
                QListWidget {
                    background-color: rgb(245, 245, 245);
                    border: 1px solid rgb(229, 229, 229);
                    border-radius: 6px;
                    padding: 4px;
                    color: #1F1F1F;
                }
                QListWidget::item {
                    padding: 8px;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: rgb(235, 235, 235);
                }
                QListWidget::item:selected {
                    background-color: rgb(0, 120, 212);
                    color: #FFFFFF;
                }
            """)

    def _on_select_all(self):
        """全选所有分P"""
        self.part_list.selectAll()

    def _on_confirm(self):
        """确认选择"""
        selected_items = self.part_list.selectedItems()

        if not selected_items:
            InfoBar.warning(
                title=t("common.warning"),
                content=t("search.no_part_selected"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            return

        self.selected_parts = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        self.accept()

    def get_selected_parts(self) -> list[int]:
        """获取选中的分P页码列表"""
        return self.selected_parts


class MultiPartChoiceDialog(QDialog):
    """多分P选择方式对话框 - Fluent Design 风格"""

    def __init__(self, part_count: int, parent=None):
        """初始化对话框

        Args:
            part_count: 分P数量
            parent: 父窗口
        """
        super().__init__(parent)
        self.part_count = part_count
        self.choice: str | None = None  # 'all' 或 'select'

        self.setWindowTitle(t("search.multi_part_video"))
        self.setFixedSize(500, 320)

        # 设置无边框窗口，保留任务栏按钮
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 设置模态
        self.setModal(True)

        self.setObjectName("multiPartChoiceDialog")

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # 卡片容器
        self.card = CardWidget(self)
        self.card.setObjectName("multiPartChoiceCard")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.card.setGraphicsEffect(shadow)

        # 设置卡片样式
        self._update_card_style()

        # 卡片内容布局
        content_layout = QVBoxLayout(self.card)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        # 图标
        self.icon = IconWidget(FIF.VIDEO, self.card)
        self.icon.setFixedSize(32, 32)

        # 标题和描述
        title_content = QVBoxLayout()
        title_content.setSpacing(4)
        self.title_label = TitleLabel(t("search.multi_part_video"), self.card)
        self.desc_label = BodyLabel(t("search.multi_part_video_desc", count=self.part_count), self.card)
        self.desc_label.setWordWrap(True)
        title_content.addWidget(self.title_label)
        title_content.addWidget(self.desc_label)

        title_layout.addWidget(self.icon)
        title_layout.addLayout(title_content, 1)

        # 关闭按钮
        self.close_btn = TransparentToolButton(FIF.CLOSE, self.card)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.reject)
        title_layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(title_layout)

        # 分隔线
        self.separator = QWidget(self.card)
        self.separator.setFixedHeight(1)
        self._update_separator_style()
        content_layout.addWidget(self.separator)

        # 选项说明
        option_label = BodyLabel("请选择下载方式：", self.card)
        content_layout.addWidget(option_label)

        # 添加间距
        content_layout.addSpacing(8)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        button_layout.addStretch()

        self.download_all_btn = PrimaryPushButton(t("search.download_all_parts"), self.card)
        self.download_all_btn.setIcon(FIF.DOWNLOAD)
        self.download_all_btn.setFixedHeight(40)
        self.download_all_btn.clicked.connect(self._on_download_all)
        button_layout.addWidget(self.download_all_btn)

        self.select_parts_btn = PushButton(t("search.select_parts"), self.card)
        self.select_parts_btn.setIcon(FIF.CHECKBOX)
        self.select_parts_btn.setFixedHeight(40)
        self.select_parts_btn.clicked.connect(self._on_select_parts)
        button_layout.addWidget(self.select_parts_btn)

        self.cancel_btn = PushButton(t("common.cancel"), self.card)
        self.cancel_btn.setIcon(FIF.CANCEL)
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        content_layout.addLayout(button_layout)

        # 将卡片添加到主布局
        main_layout.addWidget(self.card)

    def _update_card_style(self):
        """更新卡片样式"""
        if isDarkTheme():
            bg_color = "rgb(39, 39, 39)"
            border_color = "rgb(58, 58, 58)"
        else:
            bg_color = "rgb(252, 252, 252)"
            border_color = "rgb(229, 229, 229)"

        self.card.setStyleSheet(f"""
            CardWidget#multiPartChoiceCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

    def _update_separator_style(self):
        """更新分隔线样式"""
        if isDarkTheme():
            self.separator.setStyleSheet("background-color: rgba(255, 255, 255, 30);")
        else:
            self.separator.setStyleSheet("background-color: rgba(0, 0, 0, 30);")

    def _on_download_all(self):
        """选择下载全部"""
        self.choice = "all"
        self.accept()

    def _on_select_parts(self):
        """选择指定分P"""
        self.choice = "select"
        self.accept()

    def get_choice(self) -> str | None:
        """获取用户选择

        Returns:
            'all' 表示下载全部，'select' 表示选择指定分P，None 表示取消
        """
        return self.choice
