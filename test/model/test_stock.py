import logging
import sys
import unittest
from sns_trade_bot.model.data_manager import DataManager

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TestStock(unittest.TestCase):
    def setUp(self):
        self.data_manager = DataManager()

    def test_add_strategy(self):
        stock = self.data_manager.get_stock('000001')
        stock.name = 'temp_stock'
        stock.add_buy_strategy('buy_just_buy', {})
        stock.on_buy_signal('buy_just_buy', 10)

    def test_get_cur_earning_rate(self):
        # code: 033230, name: 인성정보, quantity: 100, buy_price: 2915, cur_price: 2020, earning_rate: -30.9005
        stock = self.data_manager.get_stock('000001')
        stock.buy_price = 2915
        stock.cur_price = 2020
        stock.quantity = 100

        stock.update_earning_rate()
        logger.info(f'earning_rate:{stock.earning_rate:0.2f} %')

        self.assertAlmostEqual(-30.9005, stock.earning_rate, delta=0.1)

        # code:096530, name:씨젠, quantity:1, buy_price:37650, cur_price:67200, earning_rate:78.0133
        stock = self.data_manager.get_stock('000001')
        stock.buy_price = 37650
        stock.cur_price = 67200
        stock.quantity = 1

        stock.update_earning_rate()
        logger.info(f'earning_rate: {stock.earning_rate:0.2f} %')

        self.assertAlmostEqual(78.0133, stock.earning_rate, delta=0.1)


if __name__ == '__main__':
    unittest.main()
