import logging
import sys
import unittest
from unittest.mock import Mock

from PyQt5.QtWidgets import *
from sns_trade_bot.kiwoom.manager import Kiwoom
from sns_trade_bot.kiwoom.common import ScnNo, RqName
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
        logger.info(f'on_data_update. {data_type}')

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
        self.kiwoom_manager = Kiwoom(self.data_manager)

    def tearDown(self):
        logger.info('tearDown')
        self.app.exit()

    def test_on_receive_chejan_data(self):
        logger.info('test for test_on_receive_chejan_data()')

        def temp_get_chejan_data(fid):
            mock_dic = {
                9201: '5323492810',
                9001: 'A123420',
                917: '00',
                916: '00000000',
                302: '선데이토즈',
                10: '+12450',
                930: '24',
                931: '12448',
                932: '298750',
                933: '24',
                945: '24',
                946: '2',
                950: '0',
                951: '0',
                27: '+12450',
                28: '+12300',
                307: '11800',
                8019: '0.00',
                957: '0',
                958: '0',
                918: '00000000',
                990: '0',
                991: '0.00',
                992: '0',
                993: '0.00',
                959: '0',
                924: '0',
                10010: '-11750',
                25: '2',
                11: '+650',
                12: '5.51',
                306: '-8300',
                305: '+15300',
                970: '10',
            }
            return mock_dic[fid] if fid in mock_dic.keys() else ''

        self.kiwoom_manager.ocx.get_chejan_data = Mock(side_effect=temp_get_chejan_data)
        stock = self.data_manager.get_stock('123420')
        stock.name = '선데이토즈'
        stock.qty = 0

        # when
        self.kiwoom_manager.handler.on_receive_chejan_data('1', 34, '9201;9001;917;916;302;10;930;931;932;933;945;946;950;951;27;28;307;8019;957;958;918;990;991;992;993;959;924;10010;25;11;12;306;305;970')

        # then
        self.assertAlmostEqual(24, stock.qty)

