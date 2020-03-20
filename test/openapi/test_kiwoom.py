import logging
import sys
import time
import unittest
from unittest.mock import Mock

from PyQt5.QtWidgets import *
from sns_trade_bot.openapi.kiwoom import Kiwoom
from sns_trade_bot.model.data_manager import DataManager, ModelListener, DataType

logger = logging.getLogger()
logger.level = logging.DEBUG
if not logger.hasHandlers():
    stream_handler = logging.StreamHandler(sys.stdout)
    f = logging.Formatter('%(asctime)s[%(levelname)8s](%(filename)20s:%(lineno)-4s %(funcName)-35s) %(message)s')
    stream_handler.setFormatter(f)
    logger.addHandler(stream_handler)


class TempModelListener(ModelListener):
    def on_data_updated(self, data_type: DataType):
        logger.info(f"on_data_update. {data_type}")

    def on_buy_signal(self, code: str, qty: int):
        logger.info(f'on_buy_signal. {code} {qty}')

    def on_sell_signal(self, code: str, qty: int):
        logger.info(f'on_sell_signal. {code} {qty}')


class TestKiwoom(unittest.TestCase):
    def setUp(self):
        logger.info('setup')
        self.app = QApplication(sys.argv)
        self.tempWindow = QMainWindow()
        self.tempModelListener = TempModelListener()
        self.data_manager = DataManager()
        self.data_manager.add_listener(self.tempModelListener)
        self.kiwoom_api = Kiwoom(self.data_manager)

    def tearDown(self):
        logger.info('tearDown')
        self.app.exit()

    def test_job_queue(self):
        logger.info('test for job_queue()')

        def temp_send_order(rq_name: str, screen_no: str, acc_no: str, order_type: int, code: str, qty: int, price: int,
                   hoga_gb: str, org_order_no: str):
            logger.info(f'send_order(). order_type:{order_type}, code:{code}, qty:{qty}')
            return 1

        self.kiwoom_api.ocx.send_order = Mock(side_effects=temp_send_order)
        self.kiwoom_api.ocx.send_order.__name__ = 'temp_send_order'

        stock0001 = self.data_manager.get_stock('0001')
        stock0001.name = '테스트종목'
        stock0002 = self.data_manager.get_stock('0002')
        stock0002.name = 'temp종목'

        # when
        self.kiwoom_api.tr_buy_order('0001', 3)
        self.kiwoom_api.tr_sell_order('0002', 2)

        # when
        time.sleep(3)

        # then
        self.kiwoom_api.ocx.send_order.assert_called()
        logger.info(f'buy_order call_count: {self.kiwoom_api.ocx.send_order.call_count}')


if __name__ == '__main__':
    unittest.main()
