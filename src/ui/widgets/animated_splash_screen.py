"""自定义 GIF 动画启动画面"""

from pathlib import Path
from loguru import logger
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication


class AnimatedSplashScreen(QWidget):
    """支持帧动画的启动画面"""

    def __init__(self, frames_dir: Path, parent=None, frame_delay: int = 100, loop_count: int = 1):
        """
        初始化动画启动画面

        Args:
            frames_dir: 包含动画帧图片的目录路径
            parent: 父窗口
            frame_delay: 每帧之间的延迟时间（毫秒）
            loop_count: 动画循环次数，0 表示无限循环，默认 1 次
        """
        super().__init__(parent)

        self.frames_dir = frames_dir
        self.frame_delay = frame_delay
        self.loop_count = loop_count
        self.current_frame = 0
        self.current_loop = 0
        self.frames = []
        self._parent = parent

        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 创建布局和标签
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(False)
        layout.addWidget(self.label)

        # 加载动画帧
        self._load_frames()

        # 创建定时器用于帧切换
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)

    def _load_frames(self):
        """加载所有动画帧"""
        # 查找所有 f*.png 文件并按数字排序
        frame_files = sorted(self.frames_dir.glob("f*.png"), key=lambda x: int(x.stem[1:]))

        if not frame_files:
            raise ValueError(f"在 {self.frames_dir} 中未找到动画帧文件")

        logger.info(f"找到 {len(frame_files)} 个动画帧文件")

        # 加载每一帧
        for frame_file in frame_files:
            pixmap = QPixmap(str(frame_file))
            if not pixmap.isNull():
                self.frames.append(pixmap)
                logger.debug(f"加载帧: {frame_file.name}, 大小: {pixmap.width()}x{pixmap.height()}")

        if self.frames:
            # 设置窗口大小为第一帧的大小
            first_frame = self.frames[0]
            # 根据图片大小调整窗口
            self.setFixedSize(first_frame.size())
            # 设置标签大小与图片一致
            self.label.setFixedSize(first_frame.size())
            self.label.setPixmap(first_frame)
            # 强制更新显示
            self.label.update()
            self.update()
            logger.info(f"启动画面大小: {first_frame.width()}x{first_frame.height()}, 共 {len(self.frames)} 帧")

    def _next_frame(self):
        """切换到下一帧"""
        if not self.frames:
            return

        self.current_frame = (self.current_frame + 1) % len(self.frames)

        # 检查是否完成了一轮循环
        if self.current_frame == 0:
            self.current_loop += 1
            logger.debug(f"完成第 {self.current_loop} 轮动画")

            # 如果达到循环次数，关闭启动画面
            if self.loop_count > 0 and self.current_loop >= self.loop_count:
                logger.info(f"动画播放完成（{self.loop_count} 轮），关闭启动画面")
                self.finish()
                return

        logger.debug(f"切换到第 {self.current_frame} 帧")
        self.label.setPixmap(self.frames[self.current_frame])
        # 强制刷新显示
        self.label.repaint()  # 使用 repaint() 代替 update() 强制立即重绘

    def _center_on_parent(self):
        """在父窗口或屏幕中居中"""
        # 优先在屏幕中居中
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            self.move(
                screen_geometry.center().x() - self.width() // 2, screen_geometry.center().y() - self.height() // 2
            )
        # 如果有父窗口且已经显示，则在父窗口中居中
        elif self._parent and isinstance(self._parent, QWidget) and self._parent.isVisible():
            parent_rect = self._parent.geometry()
            self.move(parent_rect.center().x() - self.width() // 2, parent_rect.center().y() - self.height() // 2)

    def show(self):
        """显示启动画面并开始播放动画"""
        # 在显示前居中
        self._center_on_parent()
        super().show()
        # 强制刷新显示
        self.raise_()
        self.activateWindow()
        # 强制处理事件以确保窗口显示
        QApplication.processEvents()

        if self.loop_count > 0:
            logger.info(f"启动画面已显示，开始播放动画（帧延迟: {self.frame_delay}ms, 循环: {self.loop_count} 次）")
        else:
            logger.info(f"启动画面已显示，开始播放动画（帧延迟: {self.frame_delay}ms, 无限循环）")

        # 启动动画定时器
        if self.frames:
            self.timer.start(self.frame_delay)
            logger.debug("动画定时器已启动")

    def finish(self):
        """关闭启动画面"""
        logger.info("关闭启动画面")
        self.timer.stop()
        self.close()

        # 如果有父窗口，显示父窗口和播放器窗口
        if self._parent and isinstance(self._parent, QWidget):
            logger.info("显示主窗口")
            self._parent.show()

            # 显示播放器窗口（如果存在）
            player_bar = getattr(self._parent, "player_bar", None)
            if player_bar:
                logger.info("显示播放器窗口")
                player_bar.show()
