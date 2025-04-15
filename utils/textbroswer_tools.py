def append_text(self, text):
    """未启用"""
    # 插入纯文本
    self.textBrowser.insertPlainText(text + "\n")  # 自动换行符可选
