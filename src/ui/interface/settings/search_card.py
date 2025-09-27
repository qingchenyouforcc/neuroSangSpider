from collections.abc import Iterable

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
    SwitchButton,
)

from i18n import t
from src.app_context import app_context
from src.bili_api import get_up_name, get_up_names
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
        self._layout.setContentsMargins(30, 10, 30, 30)
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
        except Exception:
            logger.exception("删除列表项时发生错误")

    def on_add_item(self) -> None:
        if item := self.add_item():
            self.add_btn(item)
            self.refresh_layout()

    def add_btn(self, text: str):
        try:
            btn = PushButton(text)
            btn.clicked.connect(lambda: self.on_remove_item(btn))
            self._layout.addWidget(btn)
        except Exception as e:
            logger.error(f"添加按钮失败: {e}")

    def refresh_layout(self):
        logger.info(t("settings.layout_updated"))
        self._layout.removeWidget(self.addWordBtn)
        self._layout.addWidget(self.addWordBtn)
        self._layout.update()
        self.update()

    def create_mbox(self, title: str, message: str):
        """创建一个消息框"""
        mbox = MessageBoxBase(app_context.main_window)
        titleLabel = SubtitleLabel(title, self)
        mbox.viewLayout.addWidget(titleLabel)

        lineEdit = LineEdit(self)
        lineEdit.setPlaceholderText(message)
        lineEdit.setClearButtonEnabled(True)
        mbox.viewLayout.addWidget(lineEdit)

        mbox.yesButton.setText(t("common.ok"))
        mbox.cancelButton.setText(t("common.cancel"))
        mbox.setMinimumWidth(600)
        return mbox, lineEdit

    def remove_item(self, item: str) -> None:
        raise NotImplementedError

    def add_item(self) -> str | None:
        raise NotImplementedError


class SwitchFilterEditWidget(CardGroupWidget):
    """过滤器开关组件"""

    def __init__(self, parent: QWidget):
        super().__init__(
            FluentIcon.FILTER,
            t("settings.filter_switch_title"),
            t("settings.filter_switch_desc"),
            parent,
        )
        self.switch = SwitchButton(parent=self)
        self.switch.setChecked(cfg.enable_filter.value)
        self.switch.checkedChanged.connect(self.on_checked_changed)
        self.hBoxLayout.addWidget(self.switch)

    def on_checked_changed(self, checked: bool):
        cfg.enable_filter.value = checked
        cfg.save()
        InfoBar.success(
            t("common.settings_success"),
            t("settings.filter_status", status=t("common.enabled") if checked else t("common.disabled")),
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=app_context.main_window,
            duration=1500,
        )


class FilterEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            FluentIcon.SEARCH,
            t("settings.filter_title"),
            t("settings.filter_desc"),
            parent,
            cfg.filter_list.value,
        )

    def remove_item(self, item: str) -> None:
        try:
            cfg.filter_list.value.remove(item)
            cfg.save()
            logger.info(f"当前过滤器列表为 {cfg.filter_list}")
        except Exception:
            logger.exception("删除过滤词时发生错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox(t("settings.add_filter_word"), t("settings.filter_word_placeholder"))
            if not mbox.exec():
                return None
            word = line_edit.text().strip()
            if not word:
                InfoBar.error(
                    t("common.error"),
                    t("settings.filter_word_empty"),
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=app_context.main_window,
                )
                return None
            if word in cfg.filter_list.value:
                InfoBar.error(
                    t("common.error"),
                    t("settings.filter_word_exists"),
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=app_context.main_window,
                )
                return None
            else:
                cfg.filter_list.value.append(word)
                cfg.save()
                logger.info(f"当前过滤器列表为 {cfg.filter_list.value}")
                super().add_btn(word)
                super().refresh_layout()
                return word
        except Exception:
            logger.exception("添加过滤词时发生错误")
            return None


class UpListEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        self.names = get_up_names(cfg.up_list.value)
        super().__init__(
            FluentIcon.PEOPLE,
            t("settings.up_list_title"),
            t("settings.up_list_desc"),
            parent,
            self.names.values(),
        )

    def remove_item(self, item: str) -> None:
        try:
            user_id = next(uid for uid, name in self.names.items() if name == item)
            cfg.up_list.value.remove(user_id)
            cfg.save()
            del self.names[user_id]
            logger.info(f"当前UP主列表为 {cfg.up_list.value}")
        except Exception:
            logger.exception("删除UP主时发生错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox(t("settings.add_up_title"), t("settings.add_up_placeholder"))
            if not mbox.exec():
                return None

            text = line_edit.text().strip()
            if not text:
                InfoBar.error(
                    t("common.error"),
                    t("settings.up_uid_empty"),
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=app_context.main_window,
                )
                return None

            try:
                uid = int(text)
            except ValueError:
                InfoBar.error(
                    t("common.error"),
                    t("settings.up_uid_format_error"),
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=app_context.main_window,
                )
                return None

            if uid not in cfg.up_list.value:
                cfg.up_list.value.append(uid)
            cfg.save()
            logger.info(f"当前UP主列表为 {cfg.up_list.value}")

            self.names[uid] = get_up_name(uid)
            super().add_btn(self.names[uid])
            super().refresh_layout()
            return self.names[uid]
        except Exception:
            logger.exception("添加UP主时发生错误")
            return None


class BlackListEditWidget(ListEditWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            FluentIcon.CLOSE,
            t("settings.blacklist_title"),
            t("settings.blacklist_desc"),
            parent,
            cfg.black_author_list.value,
        )

    def remove_item(self, item: str) -> None:
        try:
            cfg.black_author_list.value.remove(item)
            cfg.save()
            logger.info(f"当前黑名单列表为 {cfg.black_author_list}")
        except Exception:
            logger.exception("删除黑名单UP主时发生错误")

    def add_item(self) -> str | None:
        try:
            mbox, line_edit = self.create_mbox(
                t("settings.add_blacklist_title"), t("settings.add_blacklist_placeholder")
            )
            if not mbox.exec():
                return None

            text = line_edit.text().strip()
            if not text:
                InfoBar.error(
                    t("common.error"),
                    t("settings.blacklist_keyword_empty"),
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    parent=app_context.main_window,
                )
                return None

            if text not in cfg.black_author_list.value:
                cfg.black_author_list.value.append(text)
            cfg.save()
            logger.info(f"当前黑名单列表为 {cfg.black_author_list.value}")
            super().add_btn(text)
            super().refresh_layout()
            return text
        except Exception:
            logger.exception("添加黑名单UP主时发生错误")
            return None


class SearchSettingsCard(GroupHeaderCardWidget):
    """搜索设置卡片"""

    def __init__(self) -> None:  # pyright:ignore[reportIncompatibleVariableOverride]
        super().__init__()

        self.setTitle(t("settings.search_settings_title"))
        self.vBoxLayout.addWidget(SwitchFilterEditWidget(self))
        self.vBoxLayout.addWidget(FilterEditWidget(self))
        self.vBoxLayout.addWidget(UpListEditWidget(self))
        self.vBoxLayout.addWidget(BlackListEditWidget(self))
