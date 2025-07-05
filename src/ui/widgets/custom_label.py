from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
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
        # 记录文本是否已经完整显示过
        self._hasCompleteScroll = False
        # 跟踪是否在暂停状态
        self._isPaused = False
        
    def setText(self, a0):
        """重写setText方法，重置滚动位置"""
        # 检查文本是否发生了变化
        if self.text() == a0:
            return
            
        super().setText(a0)
        # 重置滚动位置到最左边
        self._scrollPos = 0
        # 重置滚动方向为向左
        self._scrollDirection = 1
        # 重置完整滚动标志和暂停状态
        self._hasCompleteScroll = False
        self._isPaused = False
        # 停止当前滚动并检查新文本是否需要滚动
        if self._timerId is not None:
            self._stopScrolling()
        self._checkIfNeedsScroll()
        self.update()
    
    def _checkIfNeedsScroll(self):
        """检查是否需要滚动"""
        self._textWidth = self.fontMetrics().horizontalAdvance(self.text())
        # 只有当文本宽度超过标签宽度时才启用滚动效果，并且添加一些边距
        if self._textWidth > self.width() - 20:  # 减去一些边距
            if not self._animate:
                self._animate = True
                # 总是从最左侧开始，右侧留出边距
                self._scrollPos = 0
                # 设置滚动方向为向左（正数表示向左滚动）
                self._scrollDirection = 1
                # 重置完整滚动标志
                self._hasCompleteScroll = False
                self._isPaused = False
                # 启动滚动计时器
                self._startScrolling()
            elif self._timerId is None:
                # 如果需要滚动，但计时器未启动，则重新启动计时器
                # 保持当前的滚动位置和方向
                self._startScrolling()
        else:
            if self._animate:
                self._animate = False
                self._stopScrolling()
    
    def _startScrolling(self):
        """开始滚动"""
        if self._timerId is None:
            self._timerId = self.startTimer(self._animationSpeed)
            self._isPaused = False
    
    def _stopScrolling(self):
        """停止滚动"""
        if self._timerId is not None:
            self.killTimer(self._timerId)
            self._timerId = None
            self._scrollPos = 0
            self._hasCompleteScroll = False
            self._isPaused = False
            self.update()
    
    def _toggleDirection(self):
        """切换滚动方向"""
        # 标记滚动已完成一次完整周期
        self._hasCompleteScroll = True
        self._isPaused = False
        
        # 计算最大滚动位置
        max_scroll = self._textWidth + self._margin * 2 - self.width()
        max_scroll = max(0, max_scroll)
        
        if self._scrollDirection > 0:
            # 从向左滚动变为向右滚动
            # 确保已经滚动到最右边才切换方向
            if self._scrollPos >= max_scroll:
                self._scrollDirection = -1
            else:
                # 如果没有滚动完整，不要切换方向，继续滚动
                # 将位置设置为最大位置，确保所有文本都能展示
                self._scrollPos = max_scroll
                # 延迟切换方向，确保在最右侧停留足够时间
                self._pauseTimer.start(self._pauseAtEdge)
                self._isPaused = True
                return
        else:
            # 从向右滚动变为向左滚动
            # 确保已经滚动到最左边才切换方向
            if self._scrollPos <= 0:
                self._scrollDirection = 1
            else:
                # 如果没有滚动完整，不要切换方向，继续滚动
                # 将位置设置为0，确保所有文本都能展示
                self._scrollPos = 0
                # 延迟切换方向，确保在最左侧停留足够时间
                self._pauseTimer.start(self._pauseAtEdge)
                self._isPaused = True
                return
        
        # 确保滚动计时器继续工作
        if self._timerId is None:
            self._startScrolling()
    
    def resizeEvent(self, a0):
        """窗口大小变化时重新检查是否需要滚动"""
        super().resizeEvent(a0)
        # 重新计算文本宽度
        self._textWidth = self.fontMetrics().horizontalAdvance(self.text())
        
        # 当窗口宽度变化时，可能需要调整滚动状态
        prev_animate = self._animate
        self._checkIfNeedsScroll()
        
        # 如果从不需要滚动变为需要滚动，或者从需要滚动变为不需要滚动
        # 重置滚动位置和方向
        if prev_animate != self._animate:
            self._scrollPos = 0
            self._scrollDirection = 1
            self._hasCompleteScroll = False
            self._isPaused = False
    
    def timerEvent(self, a0):
        """处理定时器事件，更新滚动位置"""
        if a0 and a0.timerId() == self._timerId and not self._isPaused:
            # 计算滚动位置
            self._scrollPos += self._scrollDirection * self._scrollStep
            
            # 文本总长度减去标签宽度，得到需要滚动的最大距离
            max_scroll = self._textWidth + self._margin * 2 - self.width()
            max_scroll = max(0, max_scroll)  # 确保最大滚动距离不为负值
            
            # 检查是否到达边界
            if self._scrollDirection > 0 and self._scrollPos >= max_scroll:
                # 向左滚动到达最右边界
                self._scrollPos = max_scroll
                # 暂停滚动，显示完整的文本末尾
                self._isPaused = True
                # 暂停后会自动调用 _toggleDirection 方法切换方向并重启滚动
                self._pauseTimer.start(self._pauseAtEdge)
            elif self._scrollDirection < 0 and self._scrollPos <= 0:
                # 向右滚动到达最左边界
                self._scrollPos = 0
                # 暂停滚动，显示完整的文本开头
                self._isPaused = True
                # 暂停后会自动调用 _toggleDirection 方法切换方向并重启滚动
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
        
        # 计算最大滚动距离
        max_scroll = self._textWidth + self._margin * 2 - self.width()
        max_scroll = max(0, max_scroll)
        
        # 计算文本绘制位置，使用统一的计算逻辑
        if self._scrollDirection > 0:
            # 向左滚动 (从右向左)
            # 确保文本开始位置始终为左侧边距减去滚动位置
            text_x_pos = self._margin - self._scrollPos
        else:
            # 向右滚动 (从左向右)
            # 从文本最右边开始，逐渐向右移动
            text_x_pos = self.width() - self._textWidth - self._margin - (max_scroll - self._scrollPos)
        
        # 边界处理：确保文本不会滚动过头
        if self._scrollDirection > 0 and self._scrollPos >= max_scroll:
            # 已达到最右边界，停在最右边
            text_x_pos = self.width() - self._textWidth - self._margin
        elif self._scrollDirection < 0 and self._scrollPos <= 0:
            # 已达到最左边界，停在最左边
            text_x_pos = self._margin
        
        # 绘制文本
        painter.drawText(text_x_pos, 0, 
                        self._textWidth, self.height(),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        self.text())
    
    def setScrollingSettings(self, speed=30, pause_time=1500, scroll_step=1, margin=30):
        """自定义滚动参数
        
        Args:
            speed: 滚动速度，毫秒刷新间隔，值越小滚动越快
            pause_time: 在边缘停留的时间，毫秒
            scroll_step: 每次滚动的像素数
            margin: 文本边缘留白像素
        """
        self._animationSpeed = speed
        self._pauseAtEdge = pause_time
        self._scrollStep = scroll_step
        self._margin = margin
        
        # 如果正在滚动，则需要重新启动滚动计时器以应用新设置
        if self._animate and self._timerId is not None:
            self.killTimer(self._timerId)
            self._timerId = self.startTimer(self._animationSpeed)
        
        # 重新检查并启动滚动
        self._checkIfNeedsScroll()