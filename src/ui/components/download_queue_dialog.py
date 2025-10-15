"""下载队列对话框

显示下载队列状态和进度的UI组件。
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
    QListWidget,
    QListWidgetItem,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    ProgressBar,
    PrimaryPushButton,
    PushButton,
    TitleLabel,
    BodyLabel,
    StrongBodyLabel,
    CardWidget,
    IconWidget,
    TransparentToolButton,
    isDarkTheme,
    InfoBar,
    InfoBarPosition,
)

from src.i18n import t
from src.core.download_queue import DownloadQueueManager, DownloadTask


class QueueStatusWidget(CardWidget):
    """队列状态卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("queueStatusCard")
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        self.title_label = StrongBodyLabel(t("search.queue_status"))
        layout.addWidget(self.title_label)

        # 状态标签容器
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)

        self.pending_label = BodyLabel(t("search.pending_tasks", count=0))
        self.active_label = BodyLabel(t("search.active_tasks", count=0))
        self.completed_label = BodyLabel(t("search.completed_tasks", count=0))
        self.failed_label = BodyLabel(t("search.failed_tasks", count=0))

        status_layout.addWidget(self.pending_label)
        status_layout.addWidget(self.active_label)
        status_layout.addWidget(self.completed_label)
        status_layout.addWidget(self.failed_label)

        layout.addLayout(status_layout)

        # 根据主题设置颜色
        self._update_colors()

    def _update_colors(self):
        """根据主题更新颜色"""
        if isDarkTheme():
            self.title_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        else:
            self.title_label.setStyleSheet("color: #1F1F1F; font-weight: bold;")

    def update_status(self, status: dict):
        """更新状态显示

        Args:
            status: 状态字典
        """
        self.pending_label.setText(t("search.pending_tasks", count=status.get("pending", 0)))
        self.active_label.setText(t("search.active_tasks", count=status.get("active", 0)))
        self.completed_label.setText(t("search.completed_tasks", count=status.get("completed", 0)))
        self.failed_label.setText(t("search.failed_tasks", count=status.get("failed", 0)))
        self._update_colors()


class DownloadQueueDialog(QDialog):
    """下载队列对话框 - Fluent Design 风格"""

    def __init__(self, queue_manager: DownloadQueueManager, parent=None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.setWindowTitle(t("search.download_queue"))
        self.setFixedSize(650, 600)  # 增大窗口以容纳任务列表

        # 设置无边框窗口，保留任务栏按钮
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 设置模态
        self.setModal(False)  # 非模态，不阻塞主窗口

        self.setObjectName("downloadQueueDialog")

        self._setup_ui()
        self._connect_signals()

        # 定时更新状态
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_status)

    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # 卡片容器
        self.card = CardWidget(self)
        self.card.setObjectName("downloadQueueCard")

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.card.setGraphicsEffect(shadow)

        # 设置卡片样式
        self._update_card_style()

        # 卡片内容布局
        content_layout = QVBoxLayout(self.card)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        # 图标
        self.icon = IconWidget(FIF.DOWNLOAD, self.card)
        self.icon.setFixedSize(32, 32)

        # 标题和描述
        title_content = QVBoxLayout()
        title_content.setSpacing(4)
        self.title_label = TitleLabel(t("search.download_queue"), self.card)
        self.desc_label = BodyLabel(t("search.queue_status"), self.card)
        title_content.addWidget(self.title_label)
        title_content.addWidget(self.desc_label)

        title_layout.addWidget(self.icon)
        title_layout.addLayout(title_content, 1)

        # 关闭按钮
        self.close_btn = TransparentToolButton(FIF.CLOSE, self.card)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(title_layout)

        # 分隔线
        self.separator = QWidget(self.card)
        self.separator.setFixedHeight(1)
        self._update_separator_style()
        content_layout.addWidget(self.separator)

        # 状态卡片
        self.status_widget = QueueStatusWidget(self.card)
        content_layout.addWidget(self.status_widget)

        # 进度条
        self.progress_bar = ProgressBar(self.card)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        content_layout.addWidget(self.progress_bar)

        # 进度文本
        self.progress_label = BodyLabel(t("search.queue_empty"), self.card)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.progress_label)

        # 任务列表标题
        task_list_title = StrongBodyLabel(t("search.task_list"), self.card)
        content_layout.addWidget(task_list_title)

        # 任务列表
        self.task_list = QListWidget(self.card)
        self.task_list.setMaximumHeight(150)
        self.task_list.setObjectName("taskListWidget")
        self._update_task_list_style()
        content_layout.addWidget(self.task_list)

        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.start_btn = PrimaryPushButton(t("search.start_queue"), self.card)
        self.start_btn.setIcon(FIF.PLAY)
        self.start_btn.clicked.connect(self._on_start_clicked)

        self.clear_btn = PushButton(t("search.clear_queue"), self.card)
        self.clear_btn.setIcon(FIF.DELETE)
        self.clear_btn.clicked.connect(self._on_clear_clicked)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()

        content_layout.addLayout(btn_layout)

        # 将卡片添加到主布局
        main_layout.addWidget(self.card)

    def _update_task_list_style(self):
        """更新任务列表样式"""
        if isDarkTheme():
            self.task_list.setStyleSheet("""
                QListWidget {
                    background-color: rgb(32, 32, 32);
                    border: 1px solid rgb(58, 58, 58);
                    border-radius: 6px;
                    padding: 4px;
                    color: #FFFFFF;
                }
                QListWidget::item {
                    padding: 6px;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: rgb(45, 45, 45);
                }
            """)
        else:
            self.task_list.setStyleSheet("""
                QListWidget {
                    background-color: rgb(245, 245, 245);
                    border: 1px solid rgb(229, 229, 229);
                    border-radius: 6px;
                    padding: 4px;
                    color: #1F1F1F;
                }
                QListWidget::item {
                    padding: 6px;
                    border-radius: 4px;
                    margin: 2px;
                }
                QListWidget::item:hover {
                    background-color: rgb(235, 235, 235);
                }
            """)

    def _update_card_style(self):
        """更新卡片样式"""
        if isDarkTheme():
            bg_color = "rgb(39, 39, 39)"
            border_color = "rgb(58, 58, 58)"
        else:
            bg_color = "rgb(252, 252, 252)"
            border_color = "rgb(229, 229, 229)"

        self.card.setStyleSheet(f"""
            CardWidget#downloadQueueCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

    def _update_separator_style(self):
        """更新分隔线样式"""
        if isDarkTheme():
            self.separator.setStyleSheet("background-color: rgba(255, 255, 255, 30);")
        else:
            self.separator.setStyleSheet("background-color: rgba(0, 0, 0, 30);")

    def _connect_signals(self):
        """连接信号"""
        self.queue_manager.task_started.connect(self._on_task_started)
        self.queue_manager.task_completed.connect(self._on_task_completed)
        self.queue_manager.task_failed.connect(self._on_task_failed)
        self.queue_manager.queue_completed.connect(self._on_queue_completed)

    def _update_status(self):
        """更新状态显示"""
        status = self.queue_manager.get_status()
        self.status_widget.update_status(status)

        # 更新进度条
        total = status.get("total", 0)
        completed = status.get("completed", 0)
        failed = status.get("failed", 0)

        if total > 0:
            progress = int((completed + failed) / total * 100)
            self.progress_bar.setValue(progress)

            current = completed + failed
            self.progress_label.setText(t("search.queue_downloading", current=current, total=total))
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText(t("search.queue_empty"))

        # 更新任务列表
        self._update_task_list()

        # 更新按钮状态
        is_running = status.get("is_running", False)

        self.start_btn.setEnabled(not is_running and status.get("pending", 0) > 0)
        self.clear_btn.setEnabled(not is_running)

    def _update_task_list(self):
        """更新任务列表显示"""
        self.task_list.clear()

        all_tasks = self.queue_manager.get_all_tasks()

        # 显示等待中的任务
        for task in all_tasks["pending"]:
            icon = "⏳"
            text = f"{icon} {task.title[:40]}... ({task.bvid})"
            item = QListWidgetItem(text)
            item.setForeground(QColor("#FFB800") if isDarkTheme() else QColor("#D68000"))
            self.task_list.addItem(item)

        # 显示下载中的任务
        for task in all_tasks["active"]:
            icon = "⬇️"
            text = f"{icon} {task.title[:40]}... ({task.bvid})"
            item = QListWidgetItem(text)
            item.setForeground(QColor("#00A0E9") if isDarkTheme() else QColor("#0078D4"))
            self.task_list.addItem(item)

        # 显示最近完成的任务（最多5个）
        for task in all_tasks["completed"][-5:]:
            icon = "✅"
            text = f"{icon} {task.title[:40]}... ({task.bvid})"
            item = QListWidgetItem(text)
            item.setForeground(QColor("#10C010") if isDarkTheme() else QColor("#107C10"))
            self.task_list.addItem(item)

        # 显示最近失败的任务（最多3个）
        for task in all_tasks["failed"][-3:]:
            icon = "❌"
            text = f"{icon} {task.title[:40]}... ({task.bvid})"
            item = QListWidgetItem(text)
            item.setForeground(QColor("#E81123") if isDarkTheme() else QColor("#D13438"))
            self.task_list.addItem(item)

    def _on_start_clicked(self):
        """开始下载按钮点击"""
        if not self.queue_manager.is_running:
            self.queue_manager.start()
            self.start_btn.setEnabled(False)

    def _on_clear_clicked(self):
        """清空队列按钮点击"""
        # 清空所有任务
        cleared = self.queue_manager.clear_all()
        if cleared > 0:
            InfoBar.success(
                title=t("common.success"),
                content=t("search.queue_cleared", count=cleared),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        self._update_status()

    def _on_task_started(self, task: DownloadTask):
        """任务开始"""
        self._update_status()

    def _on_task_completed(self, task: DownloadTask):
        """任务完成"""
        self._update_status()

    def _on_task_failed(self, task: DownloadTask):
        """任务失败"""
        self._update_status()

    def _on_queue_completed(self):
        """队列完成"""
        status = self.queue_manager.get_status()
        self.progress_label.setText(
            t(
                "search.queue_completed",
                success=status.get("completed", 0),
                failed=status.get("failed", 0),
            )
        )
        # 队列完成后重新启用开始按钮（如果还有待处理任务）
        self._update_status()

    def showEvent(self, event):  # type: ignore[override]
        """显示事件"""
        super().showEvent(event)
        # 更新主题样式
        self._update_card_style()
        self._update_separator_style()
        self._update_task_list_style()
        self.status_widget._update_colors()
        # 窗口显示时启动定时器并立即更新一次
        self._update_status()
        self.update_timer.start(500)

    def hideEvent(self, event):  # type: ignore[override]
        """隐藏事件"""
        super().hideEvent(event)
        # 窗口隐藏时停止定时器
        self.update_timer.stop()

    def closeEvent(self, event):  # type: ignore[override]
        """关闭事件"""
        # 停止定时器
        self.update_timer.stop()
        # 隐藏而不是关闭
        self.hide()
        event.ignore()

    def mousePressEvent(self, event):  # type: ignore[override]
        """鼠标按下事件 - 支持拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录鼠标按下位置
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):  # type: ignore[override]
        """鼠标移动事件 - 支持拖动"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "drag_position"):
            # 移动窗口
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
