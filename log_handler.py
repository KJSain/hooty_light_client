import logging
from PySide6.QtWidgets import (QPlainTextEdit)
from PySide6.QtCore import (Signal, QObject)


# Edit the logs in the text window
class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MyLog(QObject):
    signal = Signal(str)

    def __init__(self):
        super().__init__()


# Log handler for the Job Runner
class RunnableLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log = MyLog()

    def emit(self, record):
        msg = self.format(record)
        self.log.signal.emit(msg)
