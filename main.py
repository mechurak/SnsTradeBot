import sys
import os
import logging
from abc import ABC
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.main_window import MyListener
from openapi.kiwoom import Kiwoom
from openapi.kiwoom import KiwoomListener
from model.model import Model
import slack.run
import threading

# Setup root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s| %(filename)s :%(lineno)s (%(funcName)s)] %(message)s')
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


class Manager(MyListener, KiwoomListener):
    def __init__(self, the_model, the_main_window):
        self.model = the_model
        self.main_window = the_main_window

    # MyListener
    def account_changed(self, the_account):
        logger.info("account_changed. the_account: %s", the_account)

    def btn_balance_clicked(self):
        logger.info("btn_balance_clicked")

    def btn_refresh_condition_list_clicked(self):
        logger.info("btn_refresh_condition_list_clicked")

    def btn_query_condition_clicked(self, condition):
        logger.info(f'btn_query_condition_clicked. {condition.index} {condition.name}')

    # KiwoomListener
    def on_connect(self, err_code):
        logger.info("on_connect!!! in ui. err_code: %d", err_code)
        self.main_window.update_account()

    def on_receive_tr_data(self):
        logger.info("on_receive_tr_data")

    def on_receive_chejan_data(self):
        logger.info("on_receive_chejan_data")


if __name__ == "__main__":
    logger.info("===== Start SnsTradeBot ======")

    # Run slackbot
    sys.path.append(os.getcwd() + "\\slack")
    t = threading.Thread(target=slack.run.start)
    t.start()

    app = QApplication(sys.argv)
    model = Model()
    main_window = MainWindow(model)
    manager = Manager(model, main_window)
    main_window.set_listener(manager)

    kiwoom_api = Kiwoom(model)
    kiwoom_api.set_listener(manager)
    kiwoom_api.comm_connect()

    main_window.show()
    sys.exit(app.exec_())
