import os
import queue
import sys
import logging
import threading
import time
from datetime import datetime
from typing import List

from PyQt5.QtWidgets import *
from sns_trade_bot.model.data_manager import DataManager, DataType, ModelListener
from sns_trade_bot.model.condition import Condition, SignalType
from sns_trade_bot.kiwoom.common import Job, RqName, ScnNo
from sns_trade_bot.kiwoom.internal import KiwoomOcx
from sns_trade_bot.kiwoom.event import KiwoomEventHandler
from sns_trade_bot.slack.webhook import MsgSender

logger = logging.getLogger(__name__)


class Kiwoom:
    data_manager: DataManager
    ocx: KiwoomOcx
    handler: KiwoomEventHandler

    def __init__(self, the_data_manager):
        super().__init__()
        self.data_manager = the_data_manager
        self.ocx = KiwoomOcx(self.data_manager)
        self.tr_queue = queue.Queue()
        self.handler = KiwoomEventHandler(self.data_manager, self.ocx, self.tr_queue)
        self.ocx.set_event_handler(self.handler)

        worker_thread = threading.Thread(target=self.worker_run)
        worker_thread.daemon = True
        worker_thread.start()
        logger.info('start worker_thread')

    def worker_run(self):
        while True:
            job = self.tr_queue.get()
            logger.debug(f'{job.fn.__name__}{job.args}.')
            ret = job()
            logger.info(f'{job.fn.__name__}{job.args}. ret:{ret}')
            time.sleep(0.2)
            self.tr_queue.task_done()

    def tr_connect(self):
        job = Job(self.ocx.comm_connect)
        logger.debug(f'tr_connect(). put')
        self.tr_queue.put(job)

    def load_cond_list(self):
        ret = self.ocx.get_condition_load()
        logger.debug(f'get_condition_load(). ret: {ret}')

    def check_cond(self, cond: Condition):
        query_type = 0  # 일반조회
        ret = self.ocx.send_condition(ScnNo.CONDITION.value, cond.name, cond.index, query_type)
        logger.debug(f'send_condition(0). ret: {ret}')

    def register_cond_list(self, cond_list: List[Condition]):
        query_type = 1  # 실시간조회
        for cond in cond_list:
            ret = self.ocx.send_condition(ScnNo.CONDITION.value, cond.name, cond.index, query_type)
            logger.debug(f'send_condition(1). ret: {ret}')

    def tr_multi_code_detail(self, the_code_list: List[str]):
        """ 복수 종목에 대한 기본 정보 요청
        """
        job = Job(self._request_multi_code_info, the_code_list)
        logger.debug(f'tr_multi_code_detail(). put')
        self.tr_queue.put(job)

    def set_real_reg(self, the_code_list: List[str]):
        code_list_str = ';'.join(the_code_list)
        fid_list = "9001;10;13"  # 종목코드,업종코드;현재가;누적거래량
        real_type = "0"  # 0: 최초 등록, 1: 같은 화면에 종목 추가
        self.ocx.set_real_reg(ScnNo.REAL.value, code_list_str, fid_list, real_type)

    def tr_account_detail(self):
        job = Job(self._request_account_detail)
        logger.debug(f'tr_account_detail(). put')
        self.tr_queue.put(job)

    def tr_code_info(self, the_code: str):
        job = Job(self._request_code_info, the_code)
        logger.debug(f'tr_code_info(). put')
        self.tr_queue.put(job)

    def tr_buy_order(self, the_code: str, the_qty: int):
        logger.debug(f'tr_buy_order(). the_code:{the_code}, the_qty:{the_qty}')
        order_type = 1  # 신규매수
        price = 0
        hoga_gb = '03'  # 시장가
        org_order_no = ''
        job = Job(self.ocx.send_order, RqName.ORDER.value, ScnNo.ORDER.value, self.data_manager.account, order_type,
                  the_code, the_qty, price, hoga_gb, org_order_no)
        logger.debug(f'tr_buy_order(). put')
        self.tr_queue.put(job)

        msg = f'매수주문!! `{self.ocx.get_master_code_name(the_code)}`({the_code}) {the_qty}주'
        send_msg_job = Job(MsgSender.send_msg, msg)
        self.tr_queue.put(send_msg_job)
        logger.debug(f'tr_buy_order(). put send_msg')

    def tr_sell_order(self, the_code: str, the_qty: int):
        logger.debug(f'tr_sell_order(). the_code:{the_code}, the_qty:{the_qty}')
        order_type = 2  # 신규매도
        price = 0
        hoga_gb = '03'  # 시장가
        org_order_no = ''
        job = Job(self.ocx.send_order, RqName.ORDER.value, ScnNo.ORDER.value, self.data_manager.account, order_type,
                  the_code, the_qty, price, hoga_gb, org_order_no)
        logger.debug(f'tr_sell_order(). put')
        self.tr_queue.put(job)

        msg = f'매도주문!! `{self.ocx.get_master_code_name(the_code)}`({the_code}) {the_qty}주'
        send_msg_job = Job(MsgSender.send_msg, msg)
        self.tr_queue.put(send_msg_job)
        logger.debug(f'tr_sell_order(). put send_msg')

    def _request_account_detail(self):
        logger.info(f'account: {self.data_manager.account}')
        self.ocx.set_input_value('계좌번호', self.data_manager.account)
        self.ocx.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.ocx.set_input_value('상장폐지조회구분', '0')  # 0:전체, 1: 상장폐지종목제외
        self.ocx.set_input_value('비밀번호입력매체구분', '00')  # 고정값?
        tr_code = 'OPW00004'  # 계좌평가현황요청
        is_next = 0  # 연속조회요청 여부 (0:조회 , 2:연속)
        return self.ocx.comm_rq_data(RqName.BALANCE.value, tr_code, is_next, ScnNo.BALANCE.value)

    def _request_code_info(self, the_code: str):
        logger.info(f'code: {the_code}')
        self.ocx.set_input_value('종목코드', the_code)
        tr_code = 'opt10001'  # 주식기본정보요청
        is_next = 0
        return self.ocx.comm_rq_data(RqName.CODE_INFO.value, tr_code, is_next, ScnNo.CODE.value)

    def _request_multi_code_info(self, the_code_list: List[str]):
        logger.debug(f'the_code_list: {the_code_list}')
        count = len(the_code_list)
        if count == 0:
            logger.error('code_list is empty!!')
            return -1
        code_list_str = ";".join(the_code_list)  # 종목리스트
        is_next = 0  # 연속조회요청 여부
        code_count = count  # 종목개수
        type_flag = 0  # 조회구분 (0: 주식관심종목정보 , 선물옵션관심종목정보)
        rq_name = RqName.INTEREST_CODE.value  # 사용자구분 명
        scn_no = ScnNo.INTEREST.value  # 화면변호
        return self.ocx.comm_kw_rq_data(code_list_str, is_next, code_count, type_flag, rq_name, scn_no)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s[%(levelname)8s](%(filename)20s:%(lineno)-4s %(funcName)-35s) %(message)s')
    LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    file_name = LOG_DIR + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    file_handler = logging.FileHandler(file_name, "a", "utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)
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
    data_manager = DataManager()
    data_manager.add_listener(tempModelListener)
    kiwoom_manager = Kiwoom(data_manager)

    from PyQt5.QtCore import QEventLoop

    event_loop = QEventLoop()

    kiwoom_manager.tr_connect()
    event_loop.exec_()

    kiwoom_manager.load_cond_list()
    event_loop.exec_()

    target_condition = data_manager.cond_dic[3]
    kiwoom_manager.check_cond(target_condition)
    event_loop.exec_()

    input_code_list = ['004540', '005360', '053110']
    kiwoom_manager.tr_multi_code_detail(input_code_list)
    event_loop.exec_()

    kiwoom_manager.set_real_reg(input_code_list)

    time.sleep(2)
    logger.info('test done!')
    app.exit(0)
