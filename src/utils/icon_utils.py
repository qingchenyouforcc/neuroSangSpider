from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt
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
