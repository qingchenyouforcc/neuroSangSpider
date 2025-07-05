from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter
from qfluentwidgets import isDarkTheme


class ScrollingLabel(QLabel):
    """滚动文本标签，当文本超过标签宽度时自动滚动"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(False)  # 禁用自动换行
        self._scrollPos = 0
        self._scrollDirection = 1  # 1表示向左滚动，-1表示向右滚动
        self._margin = 30  # 滚动边缘留白
        self._timerId = None
        self._animate = False
        self._animationSpeed = 30  # 毫秒，调整更平滑
        self._pauseAtEdge = 1500  # 在边缘暂停的毫秒数
        self._scrollStep = 1  # 每次滚动的像素数
        self._pauseTimer = QTimer(self)
        self._pauseTimer.setSingleShot(True)
        self._pauseTimer.timeout.connect(self._toggleDirection)
        
        # 缓存完整文本宽度
        self._textWidth = 0
        
    def setText(self, a0):
        """重写setText方法，重置滚动位置"""
        super().setText(a0)
        self._scrollPos = 0
        self._scrollDirection = 1
        self._checkIfNeedsScroll()
        self.update()
    
    def _checkIfNeedsScroll(self):
        """检查是否需要滚动"""
        self._textWidth = self.fontMetrics().horizontalAdvance(self.text())
        # 只有当文本宽度超过标签宽度时才启用滚动效果，并且添加一些边距
        if self._textWidth > self.width() - 20:  # 减去一些边距
            if not self._animate:
                self._animate = True
                self._startScrolling()
                # 从左边开始
                self._scrollPos = 0
                self._scrollDirection = 1
        else:
            if self._animate:
                self._animate = False
                self._stopScrolling()
    
    def _startScrolling(self):
        """开始滚动"""
        if self._timerId is None:
            self._timerId = self.startTimer(self._animationSpeed)
    
    def _stopScrolling(self):
        """停止滚动"""
        if self._timerId is not None:
            self.killTimer(self._timerId)
            self._timerId = None
            self._scrollPos = 0
            self.update()
    
    def _toggleDirection(self):
        """切换滚动方向"""
        self._scrollDirection *= -1
    
    def resizeEvent(self, a0):
        """窗口大小变化时重新检查是否需要滚动"""
        super().resizeEvent(a0)
        self._checkIfNeedsScroll()
    
    def timerEvent(self, a0):
        """处理定时器事件，更新滚动位置"""
        if a0 and a0.timerId() == self._timerId:
            # 计算滚动位置
            self._scrollPos += self._scrollDirection * self._scrollStep
            
            # 检查是否到达边界
            if self._scrollDirection > 0 and self._scrollPos >= self._textWidth - self.width() + self._margin:
                # 到达右边界
                self._scrollPos = self._textWidth - self.width() + self._margin
                self._pauseTimer.start(self._pauseAtEdge)
            elif self._scrollDirection < 0 and self._scrollPos <= 0:
                # 到达左边界
                self._scrollPos = 0
                self._pauseTimer.start(self._pauseAtEdge)
                
            self.update()
    
    def paintEvent(self, a0):
        """自定义绘制事件，实现文本滚动效果"""
        if not self._animate:
            # 如果不需要滚动，正常绘制，但保持文本居中
            painter = QPainter(self)
            if a0:
                painter.setClipRect(a0.rect())
            
            # 根据当前主题设置颜色
            if isDarkTheme():
                painter.setPen(Qt.GlobalColor.white)
            else:
                painter.setPen(Qt.GlobalColor.black)
                
            # 居中绘制文本
            rect = a0.rect() if a0 else self.rect()
            painter.drawText(rect, 
                            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                            self.text())
            return
        
        painter = QPainter(self)
        if a0:
            painter.setClipRect(a0.rect())
        
        # 根据当前主题设置颜色
        if isDarkTheme():
            painter.setPen(Qt.GlobalColor.white)
        else:
            painter.setPen(Qt.GlobalColor.black)
        
        # 设置字体样式
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # 设置抗锯齿，使文本更平滑
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # 绘制滚动的文本，并添加一些边距
        text_x_pos = self.width() - self._scrollPos
        painter.drawText(text_x_pos, 0, 
                        self._textWidth, self.height(),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        self.text())