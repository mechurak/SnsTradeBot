import logging
import sys
import time
import unittest
from unittest.mock import Mock

from PyQt5.QtWidgets import *
from sns_trade_bot.openapi.kiwoom import Kiwoom
from sns_trade_bot.model.model import Model, ModelListener, DataType

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TempModelListener(ModelListener):
    def on_data_updated(self, data_type: DataType):
        logger.info(f"on_data_update. {data_type}")


class TestKiwoom(unittest.TestCase):
    def setUp(self):
        logger.info('setup')
        self.app = QApplication(sys.argv)
        self.tempWindow = QMainWindow()
        self.tempModelListener = TempModelListener()
        self.model = Model()
        self.model.set_listener(self.tempModelListener)
        self.kiwoom_api = Kiwoom(self.model)

    def tearDown(self):
        logger.info('tearDown')
        self.app.exit()

    def test_job_queue(self):
        logger.info('test for job_queue()')

        def temp_buy_order(the_code, the_quantity):
            logger.info(f'temp_buy_order(). the_code:{the_code}, the_quantity:{the_quantity}')
            return None

        def temp_sell_order(the_code, the_quantity):
            logger.info(f'temp_sell_order(). the_code:{the_code}, the_quantity:{the_quantity}')
            return None

        self.kiwoom_api.tr_buy_order = Mock(side_effects=temp_buy_order)
        self.kiwoom_api.tr_sell_order = Mock(side_effects=temp_sell_order)

        stock0001 = self.model.get_stock('0001')
        stock0001.name = '테스트종목'
        stock0002 = self.model.get_stock('0002')
        stock0002.name = 'temp종목'
        stock0001.on_buy_signal('temp_buy_strategy', 10)
        stock0001.on_sell_signal('temp_sell_strategy', 15)
        stock0002.on_sell_signal('temp_sell_strategy2', 25)
        self.assertEqual(3, self.model.order_queue.qsize())

        # when
        time.sleep(3)

        # then
        self.kiwoom_api.tr_buy_order.assert_called()
        logger.info(f'buy_order call_count: {self.kiwoom_api.tr_buy_order.call_count}')
        self.kiwoom_api.tr_sell_order.assert_called()
        logger.info(f'sell_order call_count: {self.kiwoom_api.tr_sell_order.call_count}')


if __name__ == '__main__':
    unittest.main()
