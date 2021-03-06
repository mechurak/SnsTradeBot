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

    def test_on_receive_tr_data_code_info(self):
        logger.info('test for _on_receive_tr_data() (RQ_CODE_INFO)')

        def temp_get_comm_data(tr_code, record_name, index, item_name):
            mock_dic = {
                '종목코드': '23333',
                '종목명': '테스트종목',
                '현재가': '-21000'
            }
            return mock_dic[item_name] if item_name in mock_dic.keys() else ''

        self.kiwoom_manager.ocx.get_comm_data = Mock(side_effect=temp_get_comm_data)

        # when
        self.kiwoom_manager.handler.on_receive_tr_data(ScnNo.CODE.value, RqName.CODE_INFO.value, 'opt10001', '',
                                                   '0', '', '', '', '')

        # then
        self.assertIsNotNone(self.data_manager.stock_dic['23333'])
        self.assertEqual(self.data_manager.stock_dic['23333'].cur_price, 21000)

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
                    '출력건수': '0002',
                    # 멀티데이터
                    '종목코드': 'A005930',
                    '종목명': '삼성전자',
                    '보유수량': '2',
                    '평균단가': '55900',
                    '현재가': '54200',
                    '손익율': '-30400'
                }, {
                    '종목코드': 'A096530',
                    '종목명': '씨젠',
                    '보유수량': '000000000010',
                    '평균단가': '000000037650',
                    '현재가': '000000037200',
                    '손익율': '-00000014688'
                }
            ]
            return mock_dic_list[index][item_name] if item_name in mock_dic_list[index].keys() else ''

        self.kiwoom_manager.ocx.get_comm_data = Mock(side_effect=temp_get_comm_data)
        self.kiwoom_manager.ocx.get_repeat_cnt = Mock(return_value=2)

        # when
        self.kiwoom_manager.handler.on_receive_tr_data(ScnNo.BALANCE.value, RqName.BALANCE.value, 'OPW00004', '',
                                                   '0', '', '', '', '')

        # then
        self.assertIsNotNone(self.data_manager.stock_dic['005930'])
        self.assertEqual(self.data_manager.stock_dic['005930'].cur_price, 54200)
        self.assertEqual(self.data_manager.stock_dic['005930'].earning_rate, -3.04)
        self.assertIsNotNone(self.data_manager.stock_dic['096530'])
        self.assertEqual(self.data_manager.stock_dic['096530'].cur_price, 37200)
        self.assertEqual(self.data_manager.stock_dic['096530'].earning_rate, -1.4688)


if __name__ == '__main__':
    unittest.main()
