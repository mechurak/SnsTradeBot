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
    def on_stock_quantity_changed(self, code):
        logger.info(f'on_stock_quantity_changed. code: {code}')


class TempModelListener(ModelListener):
    def on_data_updated(self, data_type: DataType):
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
        logger.info('test for _on_receive_tr_data() (RQ_CODE_INFO)')

        def temp_get_comm_data(tr_code, record_name, index, item_name):
            mock_dic = {
                '종목코드': '23333',
                '종목명': '테스트종목',
                '현재가': '-21000'
            }
            return mock_dic[item_name]

        self.kiwoom_api._get_comm_data = Mock(side_effect=temp_get_comm_data)

        # when
        self.kiwoom_api._on_receive_tr_data(ScreenNo.CODE.value, RequestName.CODE_INFO.value, 'opt10001', '', '0', '',
                                            '', '', '')

        # then
        self.assertIsNotNone(self.model.stock_dic['23333'])
        self.assertEqual(self.model.stock_dic['23333'].cur_price, 21000)

    def test_on_receive_tr_data_balance(self):
        logger.info('test for _on_receive_tr_data() (RQ_BALANCE)')

        def temp_get_comm_data(tr_code, record_name, index, item_name):
            mock_dic_list = [
                {
                    '계좌명': '',
                    '지점명': '',
                    '예수금': '000050000000',
                    'D+2추정예수금': '000050000000',
                    '유가잔고평가액': '000000000000',
                    '예탁자산평가액': '000050000000',
                    '총매입금액': '000000000000',
                    '추정예탁자산': '000050000000',
                    '매도담보대출금': '000000000000',
                    '당일투자원금': '000000000000',
                    '당월투자원금': '000000000000',
                    '누적투자원금': '000000000000',
                    '당일투자손익': '000000000000',
                    '당월투자손익': '000000000000',
                    '누적투자손익': '000000000000',
                    '당일손익율': '000000000000',
                    '당월손익율': '000000000000',
                    '누적손익율': '000000000000',
                    '출력건수': '0002',  # TODO: Check real data
                    # 멀티데이터
                    '종목코드': '005930',
                    '종목명': '삼성전자',
                    '보유수량': '2',
                    '평균단가': '55900',
                    '현재가': '-54200',
                    '손익율': '-3.04'
                }, {
                    '종목코드': '180640',
                    '종목명': '한진칼',
                    '보유수량': '2',
                    '평균단가': '65000',
                    '현재가': '67200',
                    '손익율': '3.38'
                }
            ]
            return mock_dic_list[index][item_name]

        self.kiwoom_api._get_comm_data = Mock(side_effect=temp_get_comm_data)
        self.kiwoom_api._get_repeat_cnt = Mock(return_value=2)

        # when
        self.kiwoom_api._on_receive_tr_data(ScreenNo.BALANCE.value, RequestName.BALANCE.value, 'OPW00004', '', '0', '',
                                            '', '', '')

        # then
        self.assertIsNotNone(self.model.stock_dic['005930'])
        self.assertEqual(self.model.stock_dic['005930'].cur_price, 54200)


if __name__ == '__main__':
    unittest.main()
