from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPixmap


def rounded_pixmap(pix: QPixmap, radius: int) -> QPixmap:
    """将 QPixmap 裁剪为圆角矩形。"""
    if pix.isNull():
        return pix
    w, h = pix.width(), pix.height()
    rounded = QPixmap(w, h)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(0.0, 0.0, float(w), float(h), float(radius), float(radius))
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pix)
    painter.end()
    return rounded
