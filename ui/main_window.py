import logging
import sys
import os
from abc import abstractmethod, ABC
from PyQt5.QtWidgets import *
from PyQt5 import uic

logger = logging.getLogger(__name__)


class MyListener:
    @abstractmethod
    def btn1_clicked(self):
        pass

    @abstractmethod
    def btn2_clicked(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "MainWindow.ui")
        self.ui = uic.loadUi(abspath, self)
        self.listener = None

    def set_listener(self, the_listener):
        self.listener = the_listener
        self.btn1.clicked.connect(self.listener.btn1_clicked)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    class TempListener(MyListener):
        def btn1_clicked(self):
            logger.info("btn1_clicked")
            pass

        def btn2_clicked(self):
            logger.info("btn2_clicked")
            pass

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    listener = TempListener()
    mainWindow.set_listener(listener)
    mainWindow.show()
    sys.exit(app.exec_())
