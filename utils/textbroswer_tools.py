from PyQt6.QtWidgets import QTextBrowser

def append_text(self, text):
    # 插入纯文本
    self.textBrowser.insertPlainText(text + "\n")  # 自动换行符可选