import sys
import os
import logging
from abc import ABC
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.main_window import MyListener
from openapi.kiwoom import Kiwoom
import slack.run
import threading

# Setup root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s (%(funcName)s)] %(message)s')
LOG_DIR = "log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
file_name = LOG_DIR + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"

file_handler = logging.FileHandler(file_name, "a", "utf-8")
stream_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class Manager(MyListener):
    def account_changed(self, the_account):
        logger.info("account_changed. the_account: %s", the_account)
        pass

    def balance_btn_clicked(self):
        logger.info("balance_btn_clicked")
        pass


if __name__ == "__main__":
    logger.info("===== Start SnsTradeBot ======")

    # Run slackbot
    sys.path.append(os.getcwd() + "\\slack")
    t = threading.Thread(target=slack.run.start)
    t.start()

    app = QApplication(sys.argv)
    manager = Manager()
    main_window = MainWindow()
    main_window.set_listener(manager)

    kiwoom_api = Kiwoom()
    kiwoom_api.comm_connect()

    main_window.show()
    sys.exit(app.exec_())
