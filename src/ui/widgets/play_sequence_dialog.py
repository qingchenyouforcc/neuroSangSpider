from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidgetItem, QWidget, QGraphicsDropShadowEffect
from qfluentwidgets import (
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    ListWidget,
    PrimaryPushButton,
    PushButton,
    LineEdit,
    MessageBox,
    MessageBoxBase,
    CardWidget,
    IconWidget,
    TitleLabel,
    StrongBodyLabel,
    TransparentToolButton,
    isDarkTheme,
)

from i18n import t
from src.config import cfg
from src.app_context import app_context
from src.core.player import save_play_sequence, load_play_sequence, delete_play_sequence, get_play_sequence_names


class PlaySequenceDialog(QDialog):
    """播放序列管理对话框 - 现代化窗口实现"""

    # 添加主题变化信号
    themeChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 连接自定义主题变化信号
        self.themeChanged.connect(self._update_card_style)
        self.setWindowTitle(t("play_sequence.title"))
        self.setFixedSize(500, 400)

        # 设置无边框窗口，但保留任务栏按钮，并确保对话框模态
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog
        )
        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 确保对话框模态显示
        self.setModal(True)

        # 设置全局样式
        self.setObjectName("playSequenceDialog")

        # 主布局 - 减小外边距，使卡片占据更多空间
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        # 卡片容器
        self.card = CardWidget(self)
        self.card.setObjectName("playSequenceCard")

        # 为卡片添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        # 根据主题设置样式表
        self._update_card_style()

        # 监听窗口显示事件以更新主题
        self.installEventFilter(self)

        # 监听应用主题变化
        # 注意：PyQt6的QApplication没有paletteChanged信号

        # 卡片内容布局
        self.content_layout = QVBoxLayout(self.card)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        # 标题栏布局
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 图标
        self.icon = IconWidget(FIF.SAVE, self.card)

        # 标题和描述
        title_content = QVBoxLayout()
        self.titleLabel = TitleLabel(t("play_sequence.title"), self.card)
        self.descLabel = StrongBodyLabel(t("play_sequence.description"), self.card)
        title_content.addWidget(self.titleLabel)
        title_content.addWidget(self.descLabel)

        title_layout.addWidget(self.icon)
        title_layout.addLayout(title_content, 1)

        # 添加关闭按钮 - 使用自定义样式
        self.closeButton = TransparentToolButton(FIF.CLOSE, self.card)
        self.closeButton.setToolTip(t("common.close"))
        self.closeButton.clicked.connect(self.reject)
        self.closeButton.setFixedSize(32, 32)  # 设置固定大小以确保良好的点击区域
        title_layout.addWidget(self.closeButton)

        self.content_layout.addLayout(title_layout)

        # 分割线
        self.separator = QWidget(self.card)
        self.separator.setFixedHeight(1)
        self.separator.setObjectName("separator")
        # 样式将在_update_card_style中设置
        self.content_layout.addWidget(self.separator)

        # 列表显示所有序列
        self.sequenceList = ListWidget(self.card)
        self.sequenceList.setAlternatingRowColors(True)
        self.sequenceList.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.sequenceList.setMinimumHeight(200)
        self.content_layout.addWidget(self.sequenceList)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 添加按钮
        self.saveButton = PushButton(t("play_sequence.save"), self.card, FIF.SAVE)
        self.saveButton.setToolTip(t("play_sequence.save_tooltip"))
        self.saveButton.clicked.connect(self.on_save_clicked)

        self.loadButton = PrimaryPushButton(t("play_sequence.load"), self.card, FIF.DOWNLOAD)
        self.loadButton.setToolTip(t("play_sequence.load_tooltip"))
        self.loadButton.clicked.connect(self.on_load_clicked)

        self.deleteButton = PushButton(t("play_sequence.delete"), self.card, FIF.DELETE)
        self.deleteButton.setToolTip(t("play_sequence.delete_tooltip"))
        self.deleteButton.clicked.connect(self.on_delete_clicked)

        button_layout.addWidget(self.saveButton)
        button_layout.addWidget(self.loadButton)
        button_layout.addWidget(self.deleteButton)
        button_layout.addStretch(1)  # 添加弹性空间，使按钮左对齐

        self.content_layout.addLayout(button_layout)

        # 添加卡片到主布局
        self.main_layout.addWidget(self.card)

        # 加载序列列表并自动选中上次
        self.load_sequences(auto_select_last=True)
        # 自动加载上次使用的序列
        self.auto_load_last_sequence()

        # 应用初始样式
        self._update_card_style()

        # 窗口拖动相关变量
        self.drag_position = None

    def _update_card_style(self):
        """根据当前主题更新卡片和界面样式，避免鼠标悬停变暗效果"""
        # 保存对分割线的引用
        if not hasattr(self, "separator"):
            # 如果还没初始化完成，先退出
            return

        dark_mode = isDarkTheme()

        # 更新分割线样式
        if dark_mode:
            self.separator.setStyleSheet("background-color: rgba(255, 255, 255, 30);")
        else:
            self.separator.setStyleSheet("background-color: rgba(0, 0, 0, 30);")

        # 卡片样式 - 全边框，大圆角，更符合无边框窗口
        card_style = """
            QWidget#playSequenceCard {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 12px;
            }
            QWidget#playSequenceCard:hover {
                background-color: %s;
            }
        """ % (
            "#2b2b2b" if dark_mode else "white",
            "rgba(255, 255, 255, 40)" if dark_mode else "rgba(0, 0, 0, 30)",
            "#2b2b2b" if dark_mode else "white",
        )

        # 列表样式
        list_style = """
            QListWidget {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                border-radius: 3px;
                padding: 5px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: %s;
            }
            QListWidget::item:hover:!selected {
                background-color: %s;
            }
            QListWidget::item:alternate {
                background-color: %s;
            }
        """ % (
            "#363636" if dark_mode else "#f5f5f5",
            "rgba(255, 255, 255, 20)" if dark_mode else "rgba(0, 0, 0, 15)",
            "#505050" if dark_mode else "#e0e0e0",
            "#404040" if dark_mode else "#ebebeb",
            "#323232" if dark_mode else "#f0f0f0",
        )

        # 关闭按钮样式 - 鲜明红色悬停效果
        if hasattr(self, "closeButton"):
            # 设置图标主题色
            hover_bg_color = "#d13438" if dark_mode else "#e81123"
            pressed_bg_color = "#a5262a" if dark_mode else "#c41019"

            self.closeButton.setStyleSheet(f"""
                TransparentToolButton {{
                    background-color: transparent;
                    border-radius: 5px;
                    margin: 0;
                    padding: 5px;
                }}
                TransparentToolButton:hover {{
                    background-color: {hover_bg_color};
                }}
                TransparentToolButton:pressed {{
                    background-color: {pressed_bg_color};
                }}
            """)

        # 应用样式
        self.card.setStyleSheet(card_style)
        self.sequenceList.setStyleSheet(list_style)

        # 刷新界面
        self.update()

    def load_sequences(self, auto_select_last: bool = False):
        """加载所有序列到列表中"""
        self.sequenceList.clear()
        sequence_names = get_play_sequence_names()
        sequences = cfg.play_sequences.value
        for name in sequence_names:
            item = QListWidgetItem(t("play_sequence.sequence_item_prefix", name=name, sequences=len(sequences[name])))

            item.setData(Qt.ItemDataRole.UserRole, name)  # 存储真实的序列名
            self.sequenceList.addItem(item)

    def auto_load_last_sequence(self):
        """此方法已废弃，保留空方法以保持兼容性"""
        pass

    def on_save_clicked(self):
        """保存当前播放队列为序列"""
        if not app_context.play_queue:
            InfoBar.warning(
                t("common.warning"),
                t("play_sequence.empty_queue"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
            return

        # 创建输入对话框
        dialog = MessageBoxBase(self)
        dialog.setWindowTitle(t("play_sequence.save_dialog_title"))

        # 添加说明文字
        label = StrongBodyLabel(t("play_sequence.input_name"), dialog)
        dialog.viewLayout.addWidget(label)

        # 添加输入框
        lineEdit = LineEdit(dialog)
        dialog.viewLayout.addWidget(lineEdit)

        # 设置按钮文本
        dialog.yesButton.setText(t("common.save"))
        dialog.cancelButton.setText(t("common.cancel"))

        # 显示对话框
        if dialog.exec():
            name = lineEdit.text().strip()
            if not name:
                return

            # 检查是否存在同名序列
            if name in get_play_sequence_names():
                # 使用 MessageBox 确认是否覆盖
                w = MessageBox(
                    t("play_sequence.confirm_overwrite"), t("play_sequence.overwrite_message", name=name), self
                )
                if not w.exec():
                    return

            save_play_sequence(name)
            self.load_sequences()

    def on_load_clicked(self):
        """加载选中的序列"""
        selected_items = self.sequenceList.selectedItems()
        if not selected_items:
            InfoBar.warning(
                t("common.warning"),
                t("play_sequence.select_sequence"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
            return

        sequence_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if load_play_sequence(sequence_name):
            self.accept()  # 关闭对话框

    def on_delete_clicked(self):
        """删除选中的序列"""
        selected_items = self.sequenceList.selectedItems()
        if not selected_items:
            InfoBar.warning(
                t("common.warning"),
                t("play_sequence.select_sequence"),
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
            return

        sequence_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # 使用 MessageBox 确认是否删除
        w = MessageBox(
            t("play_sequence.confirm_delete"), t("play_sequence.delete_message", sequence_name=sequence_name), self
        )
        if w.exec():
            if delete_play_sequence(sequence_name):
                self.load_sequences()

    def on_item_double_clicked(self, item):
        """双击列表项加载序列"""
        sequence_name = item.data(Qt.ItemDataRole.UserRole)
        if load_play_sequence(sequence_name):
            self.accept()  # 关闭对话框

    def eventFilter(self, a0, a1):
        """事件过滤器处理显示事件和其他窗口事件"""
        if a0 is self and a1 is not None and a1.type() == QEvent.Type.Show:
            # 窗口显示时更新主题
            self._update_card_style()
        return super().eventFilter(a0, a1)

    def changeEvent(self, a0):
        """处理窗口状态变化事件"""
        if a0 is not None and a0.type() == QEvent.Type.PaletteChange:
            # 调色板变化（主题变化）时更新样式
            self._update_card_style()
        super().changeEvent(a0)

    def mousePressEvent(self, a0):
        """处理鼠标按下事件，支持窗口拖动，只允许在标题区域拖动"""
        # 只有当点击在标题区域时才允许拖动窗口
        try:
            if a0 and a0.button() == Qt.MouseButton.LeftButton:
                # 获取鼠标位置
                pos = a0.position()

                # 标题区域高度约为 60 像素
                # 这里增加了判断：只有当鼠标在标题区域 (Y < 60) 且不在关闭按钮区域时才可拖动
                title_height = 60

                if pos.y() < title_height:
                    # 判断是否点击在关闭按钮区域
                    close_btn_x = self.closeButton.x()
                    close_btn_y = self.closeButton.y()
                    close_btn_width = self.closeButton.width()
                    close_btn_height = self.closeButton.height()

                    # 判断点击位置是否在关闭按钮区域
                    in_close_btn = (
                        close_btn_x <= pos.x() <= close_btn_x + close_btn_width
                        and close_btn_y <= pos.y() <= close_btn_y + close_btn_height
                    )

                    if not in_close_btn:
                        self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    else:
                        self.drag_position = None
                else:
                    self.drag_position = None
            else:
                self.drag_position = None
        except Exception:
            self.drag_position = None

        super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0):
        """处理鼠标移动事件，实现窗口拖动"""
        # 只有当drag_position有值时才移动窗口
        if self.drag_position is not None:
            try:
                if a0 and a0.buttons() == Qt.MouseButton.LeftButton:
                    delta = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    # 防止过大移动造成窗口乱跳
                    if abs(delta.x() - self.drag_position.x()) < 100 and abs(delta.y() - self.drag_position.y()) < 100:
                        self.move(a0.globalPosition().toPoint() - self.drag_position)
            except Exception:
                pass

        super().mouseMoveEvent(a0)

    def keyPressEvent(self, a0):
        """处理键盘按键事件，支持ESC键关闭对话框"""
        if a0 and hasattr(a0, "key") and a0.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(a0)
