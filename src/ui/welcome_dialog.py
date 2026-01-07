from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from qfluentwidgets import BodyLabel, ComboBox, PushButton, CardWidget, isDarkTheme
from loguru import logger
import os

from src.config import cfg
from src.i18n.i18n import set_lang

# 定义首次运行标记文件路径
FIRST_RUN_MARKER = os.path.join(os.path.expanduser("~"), ".nspd", "first_run")


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if isDarkTheme():
            bg_color = "#2D2D30"
            color = "#FFFFFF"
        else:
            bg_color = "#FFFFFF"
            color = "#000000"

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.card = CardWidget(self)
        self.card.setStyleSheet(f"""
            CardWidget {{
                background-color: {bg_color};
                color: {color};
                border: none;
                border-radius: 8px;
            }}
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)

        self.title_label = BodyLabel("选择显示语言\nSelect Language", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        self.language_combo = ComboBox(self)
        self.language_combo.setStyleSheet(f"ComboBox {{ color: {color}; }}")
        self.language_combo.addItems(["English", "简体中文-Simplified Chinese"])

        self.ok_button = PushButton("OK-确认", self)
        self.ok_button.clicked.connect(self.accept)

        self.card_layout.addWidget(self.title_label)
        self.card_layout.addWidget(self.language_combo)
        self.card_layout.addWidget(self.ok_button)

        self.main_layout.addWidget(self.card)

        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2, parent.y() + (parent.height() - self.height()) // 2
            )

    def get_selected_language(self):
        """获取选择的语言"""
        languages = {"English": "en_US", "简体中文-Simplified Chinese": "zh_CN"}
        selected_text = self.language_combo.currentText()
        return languages.get(selected_text, "zh_CN")

    def save_language_preference(self, language_code):
        """保存语言偏好设置"""
        cfg.language.value = language_code
        cfg.save()

        config_dir = os.path.dirname(FIRST_RUN_MARKER)
        os.makedirs(config_dir, exist_ok=True)

        # 创建首次运行标记文件
        with open(FIRST_RUN_MARKER, "w") as f:
            f.write("completed")

    def accept(self):
        """确认选择并保存设置"""
        language_code = self.get_selected_language()
        self.save_language_preference(language_code)

        result = set_lang(language_code)
        if result is None:
            logger.warning(
                f"无法在程序初次启动时应用语言设置：{language_code}\n"
                f"因为 app_context.i18n_manager 还未完成加载 (这似乎不应该出现)"
            )
        elif result is False:
            logger.warning(f"无法在程序初次启动时应用语言设置：{language_code} (可能是不支持的语言)")

        super().accept()

    @staticmethod
    def is_first_run():
        """检查是否为首次运行"""
        return not os.path.exists(FIRST_RUN_MARKER)


def show_welcome_dialog(parent=None):
    """显示欢迎对话框"""
    dialog = WelcomeDialog(parent)
    return dialog.exec()
