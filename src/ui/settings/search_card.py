from collections.abc import Iterable
import contextlib

from loguru import logger
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


class ListEditWidget(CardGroupWidget):
    def __init__(
        self,
        icon: FluentIcon,
        title: str,
        description: str,
        parent: QWidget,
        initial_content: Iterable[object],
    ) -> None:
        super().__init__(icon, title, description, parent)

        flow_container = QWidget(self)
        self._layout = FlowLayout(flow_container, needAni=True)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.addWidget(flow_container)

        for item in initial_content:
            self.add_btn(str(item))

        self.addWordBtn = ToolButton()
        self.addWordBtn.setIcon(FluentIcon.ADD)
        self.addWordBtn.clicked.connect(self.add_item)
        self._layout.addWidget(self.addWordBtn)

    def on_remove_item(self, btn: PushButton) -> None:
        try:
            self.remove_item(btn.text())
            self._layout.removeWidget(btn)
            btn.deleteLater()
            self.refresh_layout()
        except Exception as e:
            logger.error(e)

    def on_add_item(self) -> None:
        if item := self.add_item():
            self.add_btn(item)
            self.refresh_layout()

    def add_btn(self, text: str):
        btn = PushButton(text)
        btn.clicked.connect(lambda: self.on_remove_item(btn))
        self._layout.addWidget(btn)

    def refresh_layout(self):
        with contextlib.suppress(Exception):
            self._layout.removeWidget(self.addWordBtn)
        self._layout.addWidget(self.addWordBtn)
        self._layout.update()
        self.update()

    def create_mbox(self, title: str, message: str):
        """创建一个消息框"""
        mbox = MessageBoxBase(cfg.main_window)
        titleLabel = SubtitleLabel(title, self)
        mbox.viewLayout.addWidget(titleLabel)

        lineEdit = LineEdit(self)
        lineEdit.setPlaceholderText(message)
        lineEdit.setClearButtonEnabled(True)
        mbox.viewLayout.addWidget(lineEdit)

        mbox.yesButton.setText("确定")
        mbox.cancelButton.setText("取消")
        mbox.setMinimumWidth(350)
        return mbox, lineEdit

    def remove_item(self, item: str) -> None:
        raise NotImplementedError

    def add_item(self) -> str | None:
        raise NotImplementedError


class FilterEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            FluentIcon.SEARCH,
            "调整过滤器",
            "搜索结果只会显示符合过滤条件的歌曲(单击删除)",
            parent,
            cfg.filter_list.value,
        )

    def remove_item(self, item: str) -> None:
        try:
            cfg.filter_list.value.remove(item)
            cfg.save()
            logger.info(f"当前过滤器列表为 {cfg.filter_list}")
        except Exception:
            logger.exception("删除过滤词错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox("添加过滤词", "输入你要添加的过滤词")
            if not mbox.exec():
                return None
            word = line_edit.text().strip()
            if not word:
                InfoBar.error(
                    "错误",
                    "请输入要添加的过滤词",
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=cfg.main_window,
                )
                return None
            if word in cfg.filter_list.value:
                InfoBar.error(
                    "错误",
                    "该过滤词已存在",
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=cfg.main_window,
                )
                return None
            else:
                cfg.filter_list.value.append(word)
                cfg.save()
                logger.info(f"当前过滤器列表为 {cfg.filter_list.value}")
                return word
        except Exception:
            logger.exception("添加过滤词错误")
            return None


class UpListEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            FluentIcon.PEOPLE,
            "UP主列表",
            "获取歌曲列表时查找的UP主列表（单击删除）",
            parent,
            cfg.up_list.value,
        )

    def remove_item(self, item: str) -> None:
        try:
            cfg.up_list.value.remove(int(item))
            cfg.save()
            logger.info(f"当前UP主列表为 {cfg.up_list}")
        except Exception:
            logger.exception("删除UP主错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox("添加UP主", "输入需要添加的UP主UID")
            if not mbox.exec():
                return None

            text = line_edit.text().strip()
            if not text:
                InfoBar.error(
                    "错误",
                    "请输入要添加的UP主UID",
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=cfg.main_window,
                )
                return None

            try:
                uid = int(text)
            except ValueError:
                InfoBar.error(
                    "错误",
                    "请输入正确的UID格式",
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=cfg.main_window,
                )
                return None
            if uid not in cfg.up_list.value:
                cfg.up_list.value.append(uid)
            cfg.save()
            logger.info(f"当前UP主列表为 {cfg.up_list.value}")
            return text
        except Exception:
            logger.exception("添加UP主错误")
            return None


class BlackListEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            FluentIcon.CLOSE,
            "黑名单",
            "在搜索结果中排除这些UP主的歌曲（单击删除）",
            parent,
            cfg.black_author_list.value,
        )

    def remove_item(self, item: str) -> None:
        try:
            cfg.black_author_list.value.remove(item)
            cfg.save()
            logger.info(f"当前黑名单列表为 {cfg.black_author_list}")
        except Exception:
            logger.exception("删除黑名单UP主错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox("添加黑名单UP主", "输入需要添加的UP主关键词")
            if not mbox.exec():
                return None

            text = line_edit.text().strip()
            if not text:
                InfoBar.error(
                    "错误",
                    "请输入要添加的UP主关键词",
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=cfg.main_window,
                )
                return None

            if text not in cfg.black_author_list.value:
                cfg.black_author_list.value.append(text)
            cfg.save()
            logger.info(f"当前黑名单列表为 {cfg.black_author_list.value}")
            return text
        except Exception:
            logger.exception("添加黑名单UP主错误")
            return None


class SearchSettingsCard(GroupHeaderCardWidget):
    """搜索设置卡片"""

    def __init__(self) -> None:  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__()

        self.setTitle("搜索设置")
        self.vBoxLayout.addWidget(FilterEditWidget(self))
        self.vBoxLayout.addWidget(UpListEditWidget(self))
        self.vBoxLayout.addWidget(BlackListEditWidget(self))
