import unittest
from sns_trade_bot.model.model import Model


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_1(self):
        self.assertTrue(True)
        stock0001 = self.model.get_stock('0001')
        stock0001.name = '테스트종목'
        stock0002 = self.model.get_stock('0002')
        stock0002.name = 'temp종목'


if __name__ == '__main__':
    unittest.main()
