# This is code to tell a remote light that I made look like an Owl, to light up so my girlfriend would stop knocking
# on my door when I'm in a call
#
# Author: A homunculus

from PySide6.QtWidgets import (QLineEdit, QPushButton, QApplication, QVBoxLayout,
                               QPlainTextEdit, QMainWindow, QWidget)
from PySide6.QtCore import (QThreadPool, Slot)
from os import path
import sys, configparser
import runner


# Our main window for the hooty client!
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hooty Light Client")
        self.program_started = False
        self.log_text_box = QPlainTextEdit(self)
        self.log_text_box.setReadOnly(True)
        self.url = self.get_url_config()
        self.edit_url = QLineEdit(self.url)
        self.run_button = QPushButton("Run Hooty!")

        widgy = QWidget()
        layout = QVBoxLayout()
        widgy.setLayout(layout)
        layout.addWidget(self.log_text_box)
        layout.addWidget(self.edit_url)
        layout.addWidget(self.run_button)
        self.setLayout(layout)
        self.setCentralWidget(widgy)
        self.thread_pool = QThreadPool()

        # Create a runner
        self.runner = runner.JobRunner(self.edit_url.text())
        self.thread_pool.start(self.runner)

        self.runner.logHandler.log.signal.connect(self.write_log)

        # Run some actions when we press the hooty button!
        self.run_button.pressed.connect(lambda: self.runner.set_url(self.edit_url.text()))
        self.run_button.pressed.connect(lambda: self.write_url_config(self.edit_url.text()))
        self.run_button.pressed.connect(self.runner.clicked)
        self.run_button.pressed.connect(self.hooty_button_text)

        self.show()

    # Get the url from the config file if it is there
    def get_url_config(self):
        config = configparser.ConfigParser()
        if path.exists("hooty.ini"):
            try:
                config.read("hooty.ini")
                return config['DEFAULT']['url']
            except:
                return "url.example"
        else:
            return "url.example"

    # Write your url to the file!
    # TODO: Maybe I should only write if the url is a valid working one..
    def write_url_config(self, url):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {'url': url}
        with open('hooty.ini', 'w') as configfile:
            config.write(configfile)

    # Change some text!
    # TODO: Something something variables
    def hooty_button_text(self):
        if self.run_button.text() == "Run Hooty!":
            self.run_button.setText("Hooty is running!")
        else:
            self.run_button.setText("Run Hooty!")

    # First time we run our actual worker thread
    # No reason to run it immediately
    def run_thread(self):
        # Thread runner
        if self.program_started is False:
            self.thread_pool.start(self.runner)

    # Make sure we actually kill the worker
    def closeEvent(self, event):
        self.runner.exit()

    # writing to our log & scroll to the bottom
    @Slot(str)
    def write_log(self, log_text):
        self.log_text_box.appendPlainText(log_text)
        self.log_text_box.centerCursor()


# Main program
if __name__ == '__main__':
    app = QApplication([])
    w = MainWindow()
    sys.exit(app.exec_())
