import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from sns_trade_bot.ui.main_window import MainWindow, UiListener
from sns_trade_bot.openapi.kiwoom import Kiwoom, KiwoomListener
from sns_trade_bot.model.model import Model, HoldType
import sns_trade_bot.slack.run
import threading

# Setup root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
file_name = LOG_DIR + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"

file_handler = logging.FileHandler(file_name, "a", "utf-8")
stream_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.info(f'file_name: {file_name}')


class Manager(UiListener, KiwoomListener):
    model: Model
    main_window: MainWindow
    kiwoom_api: Kiwoom

    def __init__(self, the_model, the_main_window, the_kiwoom_api):
        self.model = the_model
        self.main_window = the_main_window
        self.kiwoom_api = the_kiwoom_api

    # UiListener
    def account_changed(self, the_account):
        logger.info("account_changed. the_account: %s", the_account)
        self.model.set_account(the_account)

    def btn_balance_clicked(self):
        logger.info("btn_balance_clicked")
        self.kiwoom_api.request_account_detail()

    def btn_interest_balance_clicked(self):
        logger.info('btn_interest_balance_clicked')
        interest_code_list = self.model.get_code_list(HoldType.INTEREST)
        self.kiwoom_api.comm_kw_rq_data_async(interest_code_list)

    def btn_real_clicked(self):
        logger.info('btn_real_clicked')
        target_code_list = self.model.get_code_list(HoldType.TARGET)
        self.kiwoom_api.set_real_reg(target_code_list)

    def btn_code_add_clicked(self, code):
        logger.info(f'btn_code_add_clicked. code: {code}')
        self.kiwoom_api.request_code_info(code)

    def btn_refresh_condition_list_clicked(self):
        logger.info("btn_refresh_condition_list_clicked")
        ret = self.kiwoom_api.get_condition_load_async()
        assert ret == 1, "get_condition_load_async() failed"
        condition_name_dic = self.kiwoom_api.get_condition_name_list()
        logger.debug(condition_name_dic)
        self.model.set_condition_list(condition_name_dic)

    def btn_query_condition_clicked(self, condition):
        logger.info(f'btn_query_condition_clicked. {condition.index} {condition.name}')
        self.kiwoom_api.send_condition_async('1111', condition.name, condition.index, 0)

    # KiwoomListener
    def on_stock_quantity_changed(self, code: str):
        logger.info(f'on_stock_quantity_changed. code: {code}')


if __name__ == "__main__":
    logger.info("===== Start SnsTradeBot ======")

    # Run slackbot
    sys.path.append(os.getcwd() + "\\slack")
    t = threading.Thread(target=sns_trade_bot.slack.run.start)
    t.start()

    app = QApplication(sys.argv)
    model = Model()
    main_window = MainWindow(model)
    kiwoom_api = Kiwoom(model)

    manager = Manager(model, main_window, kiwoom_api)

    main_window.set_listener(manager)
    kiwoom_api.set_listener(manager)
    kiwoom_api.comm_connect()

    main_window.show()
    sys.exit(app.exec_())
