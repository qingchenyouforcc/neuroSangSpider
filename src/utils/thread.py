from collections.abc import Callable
from PyQt6.QtCore import QThread, pyqtSignal


class SimpleThread(QThread):
    task_finished: pyqtSignal = pyqtSignal(object)

    def __init__(self, call: Callable[[], object]) -> None:
        super().__init__(None)
        self.call = call

    def run(self):
        self.task_finished.emit(self.call())
