import os
import sys
import logging
import time
from datetime import datetime

from PyQt5.QtWidgets import *
from sns_trade_bot.model.model import Model, DataType, ModelListener
from sns_trade_bot.openapi.kiwoom_internal import KiwoomOcx
from sns_trade_bot.openapi.kiwoom_event import KiwoomEventHandler

logger = logging.getLogger(__name__)

TR_REQ_TIME_INTERVAL = 0.2


class Kiwoom:
    model: Model
    ocx: KiwoomOcx
    handler: KiwoomEventHandler

    def __init__(self, the_model):
        super().__init__()
        self.model = the_model
        self.ocx = KiwoomOcx(self.model)
        self.handler = KiwoomEventHandler(self.model, self.ocx)
        self.ocx.set_event_handler(self.handler)

    def comm_connect(self):
        self.ocx.comm_connect()

    def get_master_code_name(self, code):
        return self.ocx.get_master_code_name(code)

    def get_connect_state(self):
        return self.get_connect_state()

    def get_condition_load_async(self):
        """HTS 에 저장된 condition 불러옴

        :return: 1(성공)
        :callback: _on_receive_condition_ver()
        """
        return self.ocx.get_condition_load_async()

    def send_condition_async(self, screen_num: str, condition_name: str, condition_index: int, query_type: int):
        """ condition 만족하는 종목 조회 or 실시간 등록

        :param screen_num:
        :param condition_name:
        :param condition_index:
        :param query_type: 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
        :return: 성공 1, 실패 0
        :callback: _on_receive_tr_condition()
        """
        return self.ocx.send_condition_async(screen_num, condition_name, condition_index, query_type)

    def comm_kw_rq_data_async(self, the_code_list: list):
        """ 복수종목조회 Tran 을 서버로 송신한다
        :callback: _on_receive_tr_data()
        """
        self.ocx.comm_kw_rq_data_async(the_code_list)

    def set_real_reg(self, the_code_list: list):
        self.ocx.set_real_reg(the_code_list)

    def request_account_detail(self):
        self.ocx.request_account_detail()

    def request_code_info(self, the_code):
        self.ocx.request_code_info(the_code)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s(%(funcName)s)] %(message)s')
    LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    file_name = LOG_DIR + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    file_handler = logging.FileHandler(file_name, "a", "utf-8")
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


    class TempModelListener(ModelListener):
        def on_data_updated(self, data_type: DataType):
            logger.info(f"on_data_updated. {data_type}")
            event_loop.exit()

    app = QApplication(sys.argv)
    tempWindow = QMainWindow()
    tempModelListener = TempModelListener()
    model = Model()
    model.set_listener(tempModelListener)
    kiwoom_api = Kiwoom(model)

    from PyQt5.QtCore import QEventLoop
    event_loop = QEventLoop()

    kiwoom_api.comm_connect()
    event_loop.exec_()

    kiwoom_api.get_condition_load_async()
    event_loop.exec_()

    condition_name_dic = model.get_condition_name_dic()
    kiwoom_api.send_condition_async('1111', condition_name_dic[1], 1, 0)
    event_loop.exec_()

    input_code_list = ['004540', '005360', '053110']
    kiwoom_api.comm_kw_rq_data_async(input_code_list)
    event_loop.exec_()

    kiwoom_api.set_real_reg(input_code_list)

    time.sleep(2)
    logger.info('test done!')
    app.exit(0)
