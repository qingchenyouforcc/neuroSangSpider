from __future__ import annotations

from typing import Callable, Any

from PyQt6.QtCore import Qt, QObject, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from qfluentwidgets import qconfig, isDarkTheme
from src.utils.file import get_resource_path


def get_colored_icon(path: str, color: QColor | str) -> QIcon:
    """
    Load an icon from path and colorize it with the given color.
    Works for SVG and PNG.
    """

    # Ensure color is QColor
    if isinstance(color, str):
        color = QColor(color)

    # Load pixmap
    # If path is relative, get resource path
    full_path = get_resource_path(path)
    pixmap = QPixmap(full_path)

    if pixmap.isNull():
        return QIcon(full_path)  # Fallback

    # Create a new pixmap for the colored version
    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(colored_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw the original pixmap
    painter.drawPixmap(0, 0, pixmap)

    # Fill with color using SourceIn composition mode (keeps alpha, replaces color)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), color)

    painter.end()

    return QIcon(colored_pixmap)


class ThemeChangeBinder(QObject):
    """Bind a callback to QFluentWidgets theme changes.

    The binder is parented to `owner` so it gets cleaned up automatically.
    """

    def __init__(self, owner: QObject, callback: Callable[[], None]):
        super().__init__(owner)
        self._callback = callback
        qconfig.themeChanged.connect(self._on_theme_changed)
        self._on_theme_changed()

    def _on_theme_changed(self, *args: Any, **kwargs: Any) -> None:
        try:
            self._callback()
        except Exception:
            # best-effort update; avoid crashing UI
            pass


def bind_colored_svg_icon(
    target: QObject,
    svg_path: str,
    *,
    icon_size: QSize | None = None,
    light_color: str | QColor = "black",
    dark_color: str | QColor = "white",
) -> ThemeChangeBinder:
    """Colorize an SVG icon based on current theme and keep it updated."""

    def apply() -> None:
        color = dark_color if isDarkTheme() else light_color

        # duck-typing: most Qt buttons/widgets provide setIcon/setIconSize
        if hasattr(target, "setIcon"):
            target.setIcon(get_colored_icon(svg_path, color))  # type: ignore[attr-defined]
        if icon_size is not None and hasattr(target, "setIconSize"):
            target.setIconSize(icon_size)  # type: ignore[attr-defined]

    return ThemeChangeBinder(target, apply)
