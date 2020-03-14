import os
import queue
import sys
import logging
import threading
import time
from datetime import datetime

from PyQt5.QtWidgets import *
from sns_trade_bot.model.model import Model, DataType, ModelListener, Condition
from sns_trade_bot.openapi.kiwoom_common import RqName, ScreenNo
from sns_trade_bot.openapi.kiwoom_internal import KiwoomOcx
from sns_trade_bot.openapi.kiwoom_event import KiwoomEventHandler

logger = logging.getLogger(__name__)


class Job:
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.fn(*self.args, **self.kwargs)


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

        self.tr_queue = queue.Queue()
        t = threading.Thread(target=self.tr_worker)
        t.daemon = True
        t.start()

    def tr_worker(self):
        while True:
            f = self.tr_queue.get()
            ret = f()
            logger.info(f'{f.fn.__name__}{f.args}. ret:{ret}')
            self.tr_queue.task_done()
            time.sleep(0.2)

    def tr_connect(self):
        # self.ocx.comm_connect()
        job = Job(self.ocx.comm_connect)
        logger.info(f'tr_connect(). put')
        self.tr_queue.put(job)

    def get_master_code_name(self, code):
        return self.ocx.get_master_code_name(code)

    def get_connect_state(self):
        return self.ocx.get_connect_state()

    def tr_load_condition_list(self):
        """HTS 에 저장된 condition 불러옴

        :return: 1(성공)
        :callback: _on_receive_condition_ver()
        """
        # return self.ocx.get_condition_load_async()
        job = Job(self.ocx.get_condition_load_async)
        logger.info(f'tr_load_condition_list(). put')
        self.tr_queue.put(job)

    def tr_check_condition(self, condition: Condition):
        query_type = 0  # 일반조회
        # return self.ocx.send_condition_async(ScreenNo.CONDITION.value, condition.name, condition.index, query_type)
        job = Job(self.ocx.send_condition_async, ScreenNo.CONDITION.value, condition.name, condition.index, query_type)
        logger.info(f'tr_check_condition(). put')
        self.tr_queue.put(job)

    def tr_register_condition(self, condition: Condition):
        query_type = 1  # 실시간조회
        # return self.ocx.send_condition_async(ScreenNo.CONDITION.value, condition.name, condition.index, query_type)
        job = Job(self.ocx.send_condition_async, ScreenNo.CONDITION.value, condition.name, condition.index, query_type)
        logger.info(f'tr_register_condition(). put')
        self.tr_queue.put(job)

    def tr_multi_code_detail(self, the_code_list: list):
        """ 복수 종목에 대한 기본 정보 요청
        """
        # self.ocx.comm_kw_rq_data_async(the_code_list)
        job = Job(self.ocx.comm_kw_rq_data_async, the_code_list)
        logger.info(f'tr_multi_code_detail(). put')
        self.tr_queue.put(job)

    def set_real_reg(self, the_code_list: list):
        self.ocx.set_real_reg(the_code_list)

    def tr_account_detail(self):
        # self.ocx.request_account_detail()
        job = Job(self.ocx.request_account_detail)
        logger.info(f'tr_account_detail(). put')
        self.tr_queue.put(job)

    def tr_code_info(self, the_code):
        # self.ocx.request_code_info(the_code)
        job = Job(self.ocx.request_code_info, the_code)
        logger.info(f'tr_code_info(). put')
        self.tr_queue.put(job)

    def tr_buy_order(self, the_code, the_quantity):
        logger.info(f'tr_buy_order(). the_code:{the_code}, the_quantity:{the_quantity}')
        order_type = 1  # 신규매수
        price = 0
        hoga_gb = '03'  # 시장가
        org_order_no = ''
        # self.ocx.send_order(RqName.ORDER.value, ScreenNo.ORDER.value, self.model.account, order_type, the_code,
        #                     the_quantity, price, hoga_gb, org_order_no)
        job = Job(self.ocx.send_order, RqName.ORDER.value, ScreenNo.ORDER.value, self.model.account, order_type,
                  the_code, the_quantity, price, hoga_gb, org_order_no)
        logger.info(f'tr_buy_order(). put')
        self.tr_queue.put(job)

    def tr_sell_order(self, the_code, the_quantity):
        logger.info(f'tr_sell_order(). the_code:{the_code}, the_quantity:{the_quantity}')
        order_type = 2  # 신규매도
        price = 0
        hoga_gb = '03'  # 시장가
        org_order_no = ''
        # self.ocx.send_order(RqName.ORDER.value, ScreenNo.ORDER.value, self.model.account, order_type, the_code,
        #                     the_quantity, price, hoga_gb, org_order_no)
        job = Job(self.ocx.send_order, RqName.ORDER.value, ScreenNo.ORDER.value, self.model.account, order_type,
                  the_code, the_quantity, price, hoga_gb, org_order_no)
        logger.info(f'tr_sell_order(). put')
        self.tr_queue.put(job)


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

        def on_buy_signal(self, code: str, qty: int):
            logger.info(f'on_buy_signal. code:{code}, qty:{qty}')

        def on_sell_signal(self, code: str, qty: int):
            logger.info(f'on_sell_signal. code:{code}, qty:{qty}')


    app = QApplication(sys.argv)
    tempWindow = QMainWindow()
    tempModelListener = TempModelListener()
    model = Model()
    model.add_listener(tempModelListener)
    kiwoom_api = Kiwoom(model)

    from PyQt5.QtCore import QEventLoop

    event_loop = QEventLoop()

    kiwoom_api.tr_connect()
    event_loop.exec_()

    kiwoom_api.tr_load_condition_list()
    event_loop.exec_()

    target_condition = model.condition_list[0]
    kiwoom_api.tr_check_condition(target_condition)
    event_loop.exec_()

    input_code_list = ['004540', '005360', '053110']
    kiwoom_api.tr_multi_code_detail(input_code_list)
    event_loop.exec_()

    kiwoom_api.set_real_reg(input_code_list)

    time.sleep(2)
    logger.info('test done!')
    app.exit(0)
