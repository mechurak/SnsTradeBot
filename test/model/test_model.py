import logging
import sys
import unittest
from sns_trade_bot.model.model import Model

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_add_strategy(self):
        stock = self.model.get_stock('000001')
        stock.name = 'temp_stock'
        stock.add_buy_strategy('buy_just_buy', {})
        stock.on_buy_signal('buy_just_buy', 10)


if __name__ == '__main__':
    unittest.main()
