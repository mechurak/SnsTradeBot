import logging
import sys
import unittest
from unittest.mock import Mock

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from sns_trade_bot.openapi.kiwoom import Kiwoom, KiwoomListener, ScreenNo, RequestName
from sns_trade_bot.model.model import Model, ModelListener, DataType

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TempKiwoomListener(KiwoomListener):
    def on_connect(self, err_code):
        logger.info("on_connect!!! in ui. err_code: %d", err_code)

    def on_receive_tr_data(self):
        logger.info("on_receive_tr_data")

    def on_receive_chejan_data(self):
        logger.info("on_receive_chejan_data")


class TempModelListener(ModelListener):
    def on_data_update(self, data_type: DataType):
        logger.info(f"on_data_update. {data_type}")


class TestKiwoom(unittest.TestCase):
    def setUp(self):
        logger.info('setup')
        self.app = QApplication(sys.argv)
        self.tempWindow = QMainWindow()
        self.tempManager = TempKiwoomListener()
        self.tempModelListener = TempModelListener()
        self.model = Model()
        self.model.set_listener(self.tempModelListener)
        self.kiwoom_api = Kiwoom(self.model)
        self.kiwoom_api.set_listener(self.tempManager)

    def tearDown(self):
        logger.info('tearDown')
        self.app.exit()

    def test_on_receive_tr_data_code_info(self):
        def temp_get_comm_data(tr_code, record_name, index, item_name):
            mock_dic = {
                '종목코드': '23333',
                '종목명': '테스트종목',
                '현재가': '-21000'
            }
            return mock_dic[item_name]
        self.kiwoom_api._get_comm_data = Mock(side_effect=temp_get_comm_data)

        self.kiwoom_api._on_receive_tr_data(ScreenNo.CODE.value, RequestName.CODE_INFO.value, 'opt10001', '', '0', '', '', '', '')

        self.assertIsNotNone(self.model.stock_dic['23333'])
        self.assertEqual(self.model.stock_dic['23333'].cur_price, 21000)


if __name__ == '__main__':
    unittest.main()
