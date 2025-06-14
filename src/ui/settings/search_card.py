import traceback

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import (
    CardGroupWidget,
    FlowLayout,
    FluentIcon,
    GroupHeaderCardWidget,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBoxBase,
    PushButton,
    SubtitleLabel,
    ToolButton,
)

from src.config import cfg


class SearchSettingsCard(GroupHeaderCardWidget):
    """搜索设置卡片"""

    # noinspection PyTypeChecker
    def __init__(self) -> None:  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__()

        self.setTitle("搜索设置")
        self.flow_container = QWidget()

        self.init_filter_card()
        self.__init_widget()

    def init_filter_card(self):
        """初始化过滤器卡片"""
        self.filterLayout = FlowLayout(self.flow_container, needAni=True)
        self.filterLayout.setContentsMargins(30, 30, 30, 30)

        for word in set(cfg.filter_list):
            word_btn = PushButton(word)
            word_btn.clicked.connect(self.remove_filter_word)
            self.filterLayout.addWidget(word_btn)

        self.addWordBtn = ToolButton()
        self.addWordBtn.setIcon(FluentIcon.ADD)
        self.addWordBtn.clicked.connect(self.add_filter_word)
        self.filterLayout.addWidget(self.addWordBtn)

        self.filterInfo = CardGroupWidget(
            FluentIcon.SEARCH,
            "调整过滤器",
            "搜索结果只会显示符合过滤条件的歌曲(单击删除)",
            self,
        )
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')

    def __init_widget(self):
        self.vBoxLayout.addWidget(self.filterInfo, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.flow_container)

    def remove_filter_word(self):
        try:
            word_btn = self.sender()
            assert isinstance(word_btn, PushButton)

            cfg.filter_list.remove(word_btn.text())
            logger.info(f"当前过滤器列表为{cfg.filter_list}")
            self.filterLayout.removeWidget(word_btn)
            word_btn.deleteLater()

            # 强制刷新布局，确保及时更新
            self.filterLayout.update()
            self.update()
        except Exception as e:
            logger.error(e)

    # noinspection PyTypeChecker
    def add_filter_word(self):
        try:
            mbox = MessageBoxBase(cfg.MAIN_WINDOW)

            titleLabel = SubtitleLabel("添加过滤词", self)
            wordLineEdit = LineEdit(self)

            wordLineEdit.setPlaceholderText("输入你要添加的过滤词")
            wordLineEdit.setClearButtonEnabled(True)

            # add widget to view layout
            mbox.viewLayout.addWidget(titleLabel)
            mbox.viewLayout.addWidget(wordLineEdit)

            # change the text of button
            mbox.yesButton.setText("添加")
            mbox.cancelButton.setText("取消")

            mbox.setMinimumWidth(350)

            if mbox.exec():
                word: str = wordLineEdit.text().strip()
                if not word:
                    InfoBar.error(
                        "错误",
                        "请输入要添加的过滤词",
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        parent=cfg.MAIN_WINDOW,
                    )
                    return
                if word in cfg.filter_list:
                    InfoBar.error(
                        "错误",
                        "该过滤词已存在",
                        position=InfoBarPosition.BOTTOM_RIGHT,
                        parent=cfg.MAIN_WINDOW,
                    )
                    return
                else:
                    cfg.filter_list.append(word)
                    logger.info(f"当前过滤器列表为{cfg.filter_list}")
                    word_btn = PushButton(word)
                    word_btn.clicked.connect(self.remove_filter_word)
                    self.filterLayout.addWidget(word_btn)
                    self.filterLayout.removeWidget(self.addWordBtn)
                    self.filterLayout.addWidget(self.addWordBtn)
                    self.filterLayout.update()
                    self.update()
                    return

        except Exception as e:
            logger.error(f"添加过滤词错误：错误内容:{e}，错误类型:{type(e)}\n错误位置:{traceback.format_exc()}")
            return
