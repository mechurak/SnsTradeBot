import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from sns_trade_bot.ui.main_window import MainWindow, UiListener
from sns_trade_bot.openapi.kiwoom import Kiwoom
from sns_trade_bot.model.model import Model, HoldType, ModelListener, DataType
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


class Manager(UiListener, ModelListener):
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
        self.kiwoom_api.tr_account_detail()

    def btn_interest_balance_clicked(self):
        logger.info('btn_interest_balance_clicked')
        interest_code_list = self.model.get_code_list(HoldType.INTEREST)
        self.kiwoom_api.tr_multi_code_detail(interest_code_list)

    def btn_real_clicked(self):
        logger.info('btn_real_clicked')
        target_code_list = self.model.get_code_list(HoldType.TARGET)
        self.kiwoom_api.set_real_reg(target_code_list)

    def btn_code_add_clicked(self, code):
        logger.info(f'btn_code_add_clicked. code: {code}')
        self.kiwoom_api.tr_code_info(code)

    def btn_refresh_condition_list_clicked(self):
        logger.info("btn_refresh_condition_list_clicked")
        self.kiwoom_api.tr_load_condition_list()

    def btn_query_condition_clicked(self, condition):
        logger.info(f'btn_query_condition_clicked. {condition.index} {condition.name}')
        self.kiwoom_api.tr_check_condition(condition)

    # ModelListener
    def on_data_updated(self, data_type: DataType):
        pass

    def on_buy_signal(self, code: str, qty: int):
        logger.info(f'on_buy_signal!! code:{code}, qty:{qty}')
        self.kiwoom_api.tr_buy_order(code, qty)

    def on_sell_signal(self, code: str, qty: int):
        logger.info(f'on_sell_signal!! code:{code}, qty:{qty}')
        self.kiwoom_api.tr_sell_order(code, qty)


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
    model.add_listener(manager)
    main_window.set_listener(manager)
    kiwoom_api.tr_connect()

    main_window.show()
    sys.exit(app.exec_())
