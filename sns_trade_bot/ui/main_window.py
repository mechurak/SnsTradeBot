import logging
import os
import sys
from sns_trade_bot.model.data_manager import DataManager, ModelListener, DataType
from sns_trade_bot.model.condition import Condition, SignalType
from sns_trade_bot.strategy.base import StrategyBase
from abc import abstractmethod

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot

logger = logging.getLogger(__name__)


class UiListener:
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
    def combo_signal_type_changed(self, condition, signal_type_index):
        pass

    @abstractmethod
    def btn_query_condition_clicked(self, condition):
        pass

    @abstractmethod
    def btn_register_condition_list_clicked(self):
        pass

    @abstractmethod
    def btn_test_clicked(self):
        pass


class MainWindow(QMainWindow, ModelListener):
    data_manager: DataManager
    ui = None
    listener = None

    combo_account = None
    btn_balance: QPushButton
    btn_interest_balance: QPushButton
    btn_real: QPushButton
    btn_code_add: QPushButton
    btn_stock_remove: QPushButton

    btn_refresh_condition: QPushButton
    table_condition = None

    btn_load: QPushButton
    btn_save: QPushButton
    btn_print: QPushButton
    btn_test: QPushButton

    def __init__(self, the_data_manager):
        super().__init__()
        self.data_manager = the_data_manager
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "MainWindow.ui")
        self.ui = uic.loadUi(abspath, self)
        self.data_manager.add_listener(self)
        self.btn_load.clicked.connect(self.data_manager.load)
        self.btn_save.clicked.connect(self.data_manager.save)
        self.btn_print.clicked.connect(self.data_manager.print)
        self.btn_code_add.clicked.connect(self._on_btn_code_add_clicked)
        self.btn_stock_remove.clicked.connect(self._on_btn_stock_remove_clicked)
        self.btn_temp_code_add.clicked.connect(self.data_manager.add_all_temp_stock)
        self.combo_buy.addItems(StrategyBase.BUY_STRATEGY_LIST)
        self.combo_sell.addItems(StrategyBase.SELL_STRATEGY_LIST)
        self.selected_balance = []

    def set_listener(self, the_listener):
        self.listener = the_listener
        self.combo_account.currentTextChanged.connect(self.listener.account_changed)
        self.btn_balance.clicked.connect(self.listener.btn_balance_clicked)
        self.btn_interest_balance.clicked.connect(self.listener.btn_interest_balance_clicked)
        self.btn_real.clicked.connect(self.listener.btn_real_clicked)
        self.btn_refresh_condition.clicked.connect(self.listener.btn_refresh_condition_list_clicked)
        self.btn_register_condition.clicked.connect(self.listener.btn_register_condition_list_clicked)
        self.btn_test.clicked.connect(self.listener.btn_test_clicked)

    def _on_btn_code_add_clicked(self):
        code = self.edit_code.text()
        self.listener.btn_code_add_clicked(code)
        self.edit_code.setText('')

    def _on_btn_stock_remove_clicked(self):
        items = self.table_balance.selectedItems()
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                self.data_manager.remove_stock(code)
                logger.info(f'remove {code}')
        self.data_manager.set_updated(DataType.TABLE_BALANCE)

    @pyqtSlot(str)
    def on_combo_buy_strategy_changed(self, strategy):
        logger.info(f'on_combo_buy_strategy_changed: {strategy}')
        from sns_trade_bot.strategy.buy_just_buy import BuyJustBuy
        from sns_trade_bot.strategy.buy_on_opening import BuyOnOpening
        from sns_trade_bot.strategy.buy_on_closing import BuyOnClosing
        if strategy == "buy_just_buy":
            default_param = BuyJustBuy.DEFAULT_PARAM
        elif strategy == "buy_on_opening":
            default_param = BuyOnOpening.DEFAULT_PARAM
        elif strategy == "buy_on_closing":
            default_param = BuyOnClosing.DEFAULT_PARAM
        else:
            return
        self.ui.txt_buy_param.setText(str(default_param))

    @pyqtSlot(str)
    def on_combo_sell_strategy_changed(self, strategy):
        logger.info(f'on_combo_sell_strategy_changed: {strategy}')
        from sns_trade_bot.strategy.sell_on_closing import SellOnClosing
        from sns_trade_bot.strategy.sell_on_condition import SellOnCondition
        from sns_trade_bot.strategy.sell_stop_loss import SellStopLoss
        from sns_trade_bot.strategy.sell_just_sell import SellJustSell
        if strategy == "sell_on_closing":
            default_param = SellOnClosing.DEFAULT_PARAM
        elif strategy == "sell_on_condition":
            default_param = SellOnCondition.DEFAULT_PARAM
        elif strategy == "sell_stop_loss":
            default_param = SellStopLoss.DEFAULT_PARAM
        elif strategy == "sell_just_sell":
            default_param = SellJustSell.DEFAULT_PARAM
        else:
            return
        self.ui.txt_sell_param.setText(str(default_param))

    @pyqtSlot()
    def on_btn_buy_strategy_add_clicked(self):
        strategy_str = self.combo_buy.currentText()
        logger.info(self.txt_buy_param.text())
        param_dic = eval(self.txt_buy_param.text())
        logger.info(f"전략: {strategy_str}, param_dic: {param_dic}")

        items = self.table_balance.selectedItems()
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                stock = self.data_manager.get_stock(code)
                stock.add_buy_strategy(strategy_str, param_dic)
                logger.info(f'{code}: {strategy_str}')
        self.data_manager.set_updated(DataType.TABLE_BALANCE)

    @pyqtSlot()
    def on_btn_sell_strategy_add_clicked(self):
        strategy_str = self.combo_sell.currentText()
        logger.info(self.txt_sell_param.text())
        param_dic = eval(self.txt_sell_param.text())
        logger.info(f"전략: {strategy_str}, param_dic: {param_dic}")

        items = self.table_balance.selectedItems()
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                stock = self.data_manager.get_stock(code)
                stock.add_sell_strategy(strategy_str, param_dic)
                logger.info(f'{code}: {strategy_str}')
        self.data_manager.set_updated(DataType.TABLE_BALANCE)
        pass

    @pyqtSlot()
    def on_btn_buy_strategy_clear_clicked(self):
        logger.info('on_btn_buy_strategy_clear_clicked')
        items = self.table_balance.selectedItems()
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                stock = self.data_manager.get_stock(code)
                stock.buy_strategy_dic.clear()
        self.data_manager.set_updated(DataType.TABLE_BALANCE)

    @pyqtSlot()
    def on_btn_sell_strategy_clear_clicked(self):
        logger.info('on_btn_sell_strategy_clear_clicked')
        items = self.table_balance.selectedItems()
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                stock = self.data_manager.get_stock(code)
                stock.sell_strategy_dic.clear()
        self.data_manager.set_updated(DataType.TABLE_BALANCE)

    @pyqtSlot()
    def on_table_balance_selection_changed(self):
        items = self.table_balance.selectedItems()
        self.data_manager.selected_code_list = []
        for item in items:
            if item.column() == 0:  # 종목코드
                code = item.text()
                self.data_manager.selected_code_list.append(code)
                logger.debug(f'{code}: {item.row()} {item.column()} {item.text()}')

    @pyqtSlot(QTableWidgetItem)
    def on_table_balance_item_changed(self, item):
        if item.column() == 5:  # 목표보유수량
            row = item.row()
            target_qty = int(item.text())
            code_item = self.table_balance.item(row, 0)
            code = code_item.text()
            stock = self.data_manager.get_stock(code)
            stock.target_qty = target_qty

    # ModelListener
    def on_buy_signal(self, code: str, qty: int):
        pass

    def on_sell_signal(self, code: str, qty: int):
        pass

    def on_data_updated(self, data_type: DataType):
        logger.debug(f"data_type: {data_type}")
        if data_type == DataType.COMBO_ACCOUNT:
            self.combo_account.clear()
            self.combo_account.addItems(self.data_manager.account_list)
            self.combo_account.setCurrentIndex(self.ui.combo_account.findText(self.data_manager.account))
        elif data_type == DataType.TABLE_BALANCE:
            header = ["종목코드", "종목명", "현재가", "매입가", "보유수량", "목표보유수량", "수익률", "매수전략", "매도전략"]
            self.table_balance.setSortingEnabled(False)
            self.table_balance.clear()
            self.table_balance.setColumnCount(len(header))
            self.table_balance.setHorizontalHeaderLabels(header)
            self.table_balance.setRowCount(len(self.data_manager.stock_dic))
            for i, stock in enumerate(self.data_manager.stock_dic.values()):
                self.table_balance.setItem(i, 0, QTableWidgetItem(stock.code))
                self.table_balance.setItem(i, 1, QTableWidgetItem(stock.name))
                self.table_balance.setItem(i, 2, QTableWidgetItem(str(stock.cur_price)))
                self.table_balance.setItem(i, 3, QTableWidgetItem(str(stock.buy_price)))
                self.table_balance.setItem(i, 4, QTableWidgetItem(str(stock.qty)))
                self.table_balance.setItem(i, 5, QTableWidgetItem(str(stock.target_qty)))
                self.table_balance.setItem(i, 6, QTableWidgetItem(str(stock.earning_rate)))
                self.table_balance.setItem(i, 7, QTableWidgetItem(str(list(stock.buy_strategy_dic.keys()))))
                self.table_balance.setItem(i, 8, QTableWidgetItem(str(list(stock.sell_strategy_dic.keys()))))
            self.table_balance.setSortingEnabled(True)
        elif data_type == DataType.TABLE_CONDITION:
            header = ["인덱스", "조건명", "신호종류", "요청버튼"]
            self.table_condition.setColumnCount(len(header))
            self.table_condition.setHorizontalHeaderLabels(header)
            self.table_condition.setRowCount(len(self.data_manager.cond_dic))
            for i, condition in enumerate(self.data_manager.cond_dic.values()):
                def combo_callback(c):
                    return lambda signal_index: self.listener.combo_signal_type_changed(c, signal_index)

                def btn_callback(c):
                    return lambda: self.listener.btn_query_condition_clicked(c)

                self.table_condition.setItem(i, 0, QTableWidgetItem(str(condition.index)))
                self.table_condition.setItem(i, 1, QTableWidgetItem(condition.name))

                combo = QComboBox()
                combo.addItems(SignalType.__members__.keys())
                combo.setCurrentText(condition.signal_type.name)
                combo.currentIndexChanged.connect(combo_callback(condition))
                self.table_condition.setCellWidget(i, 2, combo)

                button = QPushButton('조회 및 요청')
                button.clicked.connect(btn_callback(condition))
                self.table_condition.setCellWidget(i, 3, button)

        elif data_type == DataType.TABLE_TEMP_STOCK:
            header = ["종목코드", "종목명"]
            self.table_temp_stock.setColumnCount(len(header))
            self.table_temp_stock.setHorizontalHeaderLabels(header)
            self.table_temp_stock.setRowCount(len(self.data_manager.temp_stock_list))
            for i, stock in enumerate(self.data_manager.temp_stock_list):
                self.table_temp_stock.setItem(i, 0, QTableWidgetItem(stock.code))
                self.table_temp_stock.setItem(i, 1, QTableWidgetItem(stock.name))
        else:
            logger.error(f"unexpected data_type: {data_type}")


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    f = logging.Formatter('%(asctime)s[%(levelname)8s](%(filename)20s:%(lineno)-4s %(funcName)-35s) %(message)s')
    stream_handler.setFormatter(f)
    logger.addHandler(stream_handler)

    data_manager = DataManager()


    class TempListener(UiListener):
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
            data_manager.get_stock(code)
            data_manager.set_updated(DataType.TABLE_BALANCE)

        def btn_refresh_condition_list_clicked(self):
            logger.info("btn_refresh_condition_list_clicked")

        def combo_signal_type_changed(self, condition, signal_type_index):
            logger.info(f'combo_signal_type_changed. {condition}: {signal_type_index}')
            condition.signal_type = SignalType(signal_type_index)

        def btn_query_condition_clicked(self, condition):
            logger.info(f'btn_query_condition_clicked. {condition.index} {condition.name}')

        def btn_register_condition_list_clicked(self):
            logger.info("btn_register_condition_list_clicked")

        def btn_test_clicked(self):
            logger.info("btn_test_clicked")


    app = QApplication(sys.argv)
    mainWindow = MainWindow(data_manager)
    listener = TempListener()
    mainWindow.set_listener(listener)
    data_manager.set_account_list(['123', '678'])
    stock0001 = data_manager.get_stock('0001')
    stock0001.name = '테스트종목'
    stock0002 = data_manager.get_stock('0002')
    stock0002.name = 'temp종목'
    data_manager.set_updated(DataType.TABLE_BALANCE)
    data_manager.set_updated(DataType.TABLE_CONDITION)
    mainWindow.show()
    sys.exit(app.exec_())
