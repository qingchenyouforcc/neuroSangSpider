from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QColorDialog
from qfluentwidgets import (
    FluentIcon,
    GroupHeaderCardWidget,
    SpinBox,
    SwitchButton,
    PushButton,
    InfoBar,
    InfoBarPosition,
)

from src.i18n import t
from src.app_context import app_context
from src.config import cfg


def _qcolor_to_rgba_list(color: QColor) -> list[int]:
    return [color.red(), color.green(), color.blue(), color.alpha()]


def _rgba_list_to_qcolor(rgba: list[int]) -> QColor:
    r, g, b, a = (rgba + [255, 255, 255, 255])[:4]
    return QColor(int(r), int(g), int(b), int(a))


class AcrylicSettingsCard(GroupHeaderCardWidget):
    """亚克力效果设置卡片"""

    def __init__(self, parent: QWidget | None = None):  # pyright: ignore[reportIncompatibleVariableOverride]
        super().__init__(parent)
        self.setTitle(t("settings.acrylic_title", "亚克力效果"))

        # 开关
        self.enableSwitch = SwitchButton(self)
        self.enableSwitch.setChecked(bool(cfg.acrylic_enabled.value))
        self.enableSwitch.checkedChanged.connect(self.on_enable_changed)

        # 模糊半径
        self.blurSpin = SpinBox(self)
        self.blurSpin.setRange(0, 64)
        self.blurSpin.setValue(int(cfg.acrylic_blur_radius.value))
        self.blurSpin.valueChanged.connect(self.on_blur_changed)

        # Tint 颜色按钮
        self.tintBtn = PushButton(self)
        self.tintBtn.setText(t("settings.acrylic_tint", "色调（Tint）"))
        self.tintBtn.clicked.connect(self.on_pick_tint)

        # Luminosity 颜色按钮
        self.lumiBtn = PushButton(self)
        self.lumiBtn.setText(t("settings.acrylic_lum", "亮度（Luminosity）"))
        self.lumiBtn.clicked.connect(self.on_pick_lumi)

        # 添加到卡片分组
        self.addGroup(
            FluentIcon.ALBUM,
            t("settings.acrylic_enable", "启用亚克力效果"),
            t("settings.acrylic_enable_desc", "在主页“正在播放”卡片上使用基于封面的亚克力背景"),
            self.enableSwitch,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.acrylic_blur", "模糊半径"),
            t("settings.acrylic_blur_desc", "调整亚克力背景的模糊强度（0-64）"),
            self.blurSpin,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.acrylic_tint", "色调（Tint）"),
            t("settings.acrylic_tint_desc", "设置亚克力背景的色调颜色（支持透明度）"),
            self.tintBtn,
        )
        self.addGroup(
            FluentIcon.BRUSH,
            t("settings.acrylic_lum", "亮度（Luminosity）"),
            t("settings.acrylic_lum_desc", "设置亚克力背景的亮度蒙版颜色（支持透明度）"),
            self.lumiBtn,
        )

    # --- slots ---
    def on_enable_changed(self, checked: bool):
        cfg.acrylic_enabled.value = bool(checked)
        cfg.save()
        InfoBar.success(
            t("common.settings_success", "设置成功"),
            t(
                "settings.acrylic_enable_to",
                "已{status}亚克力背景",
                status=t("common.enabled", "启用") if checked else t("common.disabled", "禁用"),
            ),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1200,
        )

    def on_blur_changed(self, value: int):
        cfg.acrylic_blur_radius.value = int(value)
        cfg.save()
        InfoBar.success(
            t("common.settings_success", "设置成功"),
            t("settings.acrylic_blur_set", "已将亚克力模糊半径设为 {value}", value=value),
            parent=app_context.main_window,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1200,
        )

    def on_pick_tint(self):
        rgba = list(cfg.acrylic_tint_rgba.value)
        color = _rgba_list_to_qcolor(rgba)
        new_color = QColorDialog.getColor(
            initial=color,
            parent=self,
            title=t("settings.acrylic_tint"),
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if new_color.isValid():
            cfg.acrylic_tint_rgba.value = _qcolor_to_rgba_list(new_color)
            cfg.save()
            InfoBar.success(
                t("common.settings_success", "设置成功"),
                t("settings.acrylic_tint_set", "已更新亚克力色调"),
                parent=app_context.main_window,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1200,
            )

    def on_pick_lumi(self):
        rgba = list(cfg.acrylic_luminosity_rgba.value)
        color = _rgba_list_to_qcolor(rgba)
        new_color = QColorDialog.getColor(
            initial=color,
            parent=self,
            title=t("settings.acrylic_lum"),
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if new_color.isValid():
            cfg.acrylic_luminosity_rgba.value = _qcolor_to_rgba_list(new_color)
            cfg.save()
            InfoBar.success(
                t("common.settings_success", "设置成功"),
                t("settings.acrylic_lum_set", "已更新亚克力亮度蒙版"),
                parent=app_context.main_window,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1200,
            )
