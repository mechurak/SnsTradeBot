import logging
import os
import sys
from sns_trade_bot.model.model import Model, ModelListener, DataType
from abc import abstractmethod

from PyQt5 import uic
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class MyListener:
    """
    Listen user action
    """

    @abstractmethod
    def account_changed(self, the_account):
        pass

    @abstractmethod
    def btn_balance_clicked(self):
        pass

    @abstractmethod
    def btn_interest_balance_clicked(self):
        pass

    @abstractmethod
    def btn_real_clicked(self):
        pass

    @abstractmethod
    def btn_code_add_clicked(self, code):
        pass

    @abstractmethod
    def btn_refresh_condition_list_clicked(self):
        pass

    @abstractmethod
    def btn_query_condition_clicked(self, condition):
        pass


class MainWindow(QMainWindow, ModelListener):
    model: Model
    ui = None
    listener = None

    combo_account = None
    btn_balance: QPushButton
    btn_interest_balance: QPushButton
    btn_real: QPushButton
    btn_code_add: QPushButton

    btn_refresh_condition: QPushButton
    table_condition = None

    btn_load: QPushButton
    btn_save: QPushButton
    btn_print: QPushButton

    def __init__(self, the_model):
        super().__init__()
        self.model = the_model
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "MainWindow.ui")
        self.ui = uic.loadUi(abspath, self)
        self.model.set_listener(self)
        self.btn_load.clicked.connect(self.model.load)
        self.btn_save.clicked.connect(self.model.save)
        self.btn_print.clicked.connect(self.model.print)
        self.btn_temp_code_add.clicked.connect(self.model.add_all_temp_stock)

    def set_listener(self, the_listener):
        self.listener = the_listener
        self.combo_account.currentTextChanged.connect(self.listener.account_changed)
        self.btn_balance.clicked.connect(self.listener.btn_balance_clicked)
        self.btn_interest_balance.clicked.connect(self.listener.btn_interest_balance_clicked)
        self.btn_real.clicked.connect(self.listener.btn_real_clicked)
        self.btn_code_add.clicked.connect(self._on_btn_code_add_clicked)
        self.btn_refresh_condition.clicked.connect(self.listener.btn_refresh_condition_list_clicked)

    def _on_btn_code_add_clicked(self):
        code = self.edit_code.text()
        self.listener.btn_code_add_clicked(code)
        self.edit_code.setText('')

    def on_data_update(self, data_type: DataType):
        logger.info(f"data_type: {data_type}")
        if data_type == DataType.COMBO_ACCOUNT:
            self.combo_account.clear()
            self.combo_account.addItems(self.model.account_list)
            self.combo_account.setCurrentIndex(self.ui.combo_account.findText(self.model.account))
        elif data_type == DataType.TABLE_BALANCE:
            self.is_user_changing_balance = False
            header = ["종목코드", "종목명", "현재가", "매입가", "보유수량", "목표보유수량", "수익률", "매수전략", "매도전략"]
            self.table_balance.clear()
            self.table_balance.setColumnCount(len(header))
            self.table_balance.setHorizontalHeaderLabels(header)
            self.table_balance.setRowCount(len(self.model.stock_dic))
            for i, stock in enumerate(self.model.stock_dic.values()):
                self.table_balance.setItem(i, 0, QTableWidgetItem(stock.code))
                self.table_balance.setItem(i, 1, QTableWidgetItem(stock.name))
                self.table_balance.setItem(i, 2, QTableWidgetItem(str(stock.cur_price)))
                self.table_balance.setItem(i, 3, QTableWidgetItem(str(stock.buy_price)))
                self.table_balance.setItem(i, 4, QTableWidgetItem(str(stock.quantity)))
                self.table_balance.setItem(i, 5, QTableWidgetItem(str(stock.target_quantity)))
                self.table_balance.setItem(i, 6, QTableWidgetItem(str(stock.earning_rate)))
                self.table_balance.setItem(i, 7, QTableWidgetItem(str(list(stock.buy_strategy_dic.keys()))))
                self.table_balance.setItem(i, 8, QTableWidgetItem(str(list(stock.buy_strategy_dic.keys()))))
            self.is_user_changing_balance = True
        elif data_type == DataType.TABLE_CONDITION:
            header = ["인덱스", "조건명", "신호종류", "적용유무", "요청버튼"]
            self.table_condition.setColumnCount(len(header))
            self.table_condition.setHorizontalHeaderLabels(header)
            self.table_condition.setRowCount(len(self.model.condition_list))
            for i, condition in enumerate(self.model.condition_list):
                def btn_callback(c):
                    return lambda: self.listener.btn_query_condition_clicked(c)

                self.table_condition.setItem(i, 0, QTableWidgetItem(str(condition.index)))
                self.table_condition.setItem(i, 1, QTableWidgetItem(condition.name))
                self.table_condition.setItem(i, 2, QTableWidgetItem(condition.signal_type))
                self.table_condition.setItem(i, 3, QTableWidgetItem(condition.enabled))
                button = QPushButton('조회 및 요청')
                button.clicked.connect(btn_callback(condition))
                self.table_condition.setCellWidget(i, 4, button)
        elif data_type == DataType.TABLE_TEMP_STOCK:
            header = ["종목코드", "종목명"]
            self.table_temp_stock.setColumnCount(len(header))
            self.table_temp_stock.setHorizontalHeaderLabels(header)
            self.table_temp_stock.setRowCount(len(self.model.temp_stock_list))
            for i, stock in enumerate(self.model.temp_stock_list):
                self.table_temp_stock.setItem(i, 0, QTableWidgetItem(stock.code))
                self.table_temp_stock.setItem(i, 1, QTableWidgetItem(stock.name))
        else:
            logger.error(f"unexpected data_type: {data_type}")


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)


    class TempListener(MyListener):
        def account_changed(self, the_account):
            logger.info("account_changed. the_account: %s", the_account)

        def btn_balance_clicked(self):
            logger.info('btn_balance_clicked')

        def btn_interest_balance_clicked(self):
            logger.info('btn_interest_balance_clicked')

        def btn_real_clicked(self):
            logger.info('btn_real_clicked')

        def btn_code_add_clicked(self, code):
            logger.info(f'btn_code_add_clicked. code: {code}')

        def btn_refresh_condition_list_clicked(self):
            logger.info("btn_refresh_condition_list_clicked")

        def btn_query_condition_clicked(self, condition):
            logger.info(f'btn_query_condition_clicked. {condition.index} {condition.name}')


    app = QApplication(sys.argv)
    model = Model()
    mainWindow = MainWindow(model)
    listener = TempListener()
    mainWindow.set_listener(listener)
    model.set_account_list(['123', '678'])
    mainWindow.show()
    sys.exit(app.exec_())
