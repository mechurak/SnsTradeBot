import logging
import sys
import unittest
from sns_trade_bot.model.model import Model, Stock

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_order_queue(self):
        self.assertTrue(True)
        stock0001 = self.model.get_stock('0001')
        stock0001.name = '테스트종목'
        stock0002 = self.model.get_stock('0002')
        stock0002.name = 'temp종목'

        # when
        stock0001.on_buy_signal('temp_buy_strategy', 10)
        stock0001.on_sell_signal('temp_sell_strategy', 15)

        # then
        self.assertEqual(2, self.model.order_queue.qsize())
        item = self.model.order_queue.get()
        self.assertEqual('temp_buy_strategy', item.strategy_name)
        self.assertEqual(10, item.quantity)
        item = self.model.order_queue.get()
        self.assertEqual('temp_sell_strategy', item.strategy_name)
        self.assertEqual(15, item.quantity)


if __name__ == '__main__':
    unittest.main()
