import logging
import os
import sys
from abc import abstractmethod

from PyQt5 import uic
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class MyListener:
    @abstractmethod
    def account_changed(self, the_account):
        pass

    @abstractmethod
    def balance_btn_clicked(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "MainWindow.ui")
        self.ui = uic.loadUi(abspath, self)
        self.listener = None

    def set_listener(self, the_listener):
        self.listener = the_listener
        self.combo_account.currentTextChanged.connect(self.listener.account_changed)
        self.btn_balance.clicked.connect(self.listener.balance_btn_clicked)

    def set_account_list(self, the_account_list, the_cur_account):
        self.combo_account.clear()
        self.combo_account.addItems(the_account_list)
        self.combo_account.setCurrentIndex(self.ui.combo_account.findText(the_cur_account))


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    class TempListener(MyListener):
        def account_changed(self, the_account):
            logger.info("account_changed. the_account: %s", the_account)
            pass

        def balance_btn_clicked(self):
            logger.info("balance_btn_clicked")
            pass

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    listener = TempListener()
    mainWindow.set_listener(listener)
    mainWindow.set_account_list(['5055378411', '5075289111'], '5055378411')
    mainWindow.show()
    sys.exit(app.exec_())
