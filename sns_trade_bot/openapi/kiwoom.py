import enum
import os
import sys
import logging
import time
from abc import abstractmethod
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from sns_trade_bot.model.model import Model, DataType
from sns_trade_bot.model.model import Stock
from sns_trade_bot.model.model import ModelListener

logger = logging.getLogger(__name__)

TR_REQ_TIME_INTERVAL = 0.2


class ScreenNo(enum.Enum):
    REAL = '2222'  # 실시간 조회
    INTEREST = '3333'  # 관심종목 조회
    BALANCE = '4444'  # 계좌평가현황요청
    CODE = '5555'  # 주식기본정보요청


class RequestName(enum.Enum):
    MULTI_CODE_QUERY = 'RQ_MULTI_CODE_QUERY'  # 관심종목 조회
    BALANCE = 'RQ_BALANCE'  # 계좌평가현황요청 (OPW00004)
    CODE_INFO = 'RQ_CODE_INFO'  # 주식기본정보요청 (opt10001)


class KiwoomListener:
    """
    Notify kiwoom events to UI
    """

    @abstractmethod
    def on_receive_tr_data(self):
        pass

    @abstractmethod
    def on_receive_chejan_data(self):
        pass


class Kiwoom(QAxWidget):
    model: Model
    listener: KiwoomListener
    login_event_loop = None
    tr_event_loop = None
    temp_event_loop = None

    def __init__(self, the_model):
        super().__init__()
        self.model = the_model
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrCondition.connect(self._on_receive_tr_condition)
        self.OnReceiveConditionVer.connect(self._on_receive_condition_ver)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def set_listener(self, the_listener):
        self.listener = the_listener

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            logger.info("connected")
            account_num = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            account_num = account_num[:-1]
            account_list = account_num.split(";")
            logger.info("account_list: %s", account_list)
            self.model.set_account_list(account_list)
        else:
            logger.info("disconnected")
        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_condition_name_list(self):
        condition_name_list_str = self.dynamicCall("GetConditionNameList()")
        condition_name_list_str = condition_name_list_str[:-1]  # Remove last ';'
        condition_name_list = condition_name_list_str.split(';')
        ret_dic = {}
        for name_with_index in condition_name_list:
            temp_list = name_with_index.split('^')
            ret_dic[int(temp_list[0])] = temp_list[1]
        return ret_dic

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rq_name: RequestName, tr_code: str, is_next: int, screen_no: ScreenNo):
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)",
                               [rq_name.value, tr_code, is_next, screen_no.value])
        logger.info(f'CommRqData(). ret: {ret}')
        if ret == 0:
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()

    def _get_comm_real_data(self, code: str, fid: int) -> str:
        ret = self.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return ret.strip()

    def _get_comm_data(self, tr_code: str, record_name: str, index: int, item_name: str) -> str:
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               [tr_code, record_name, index, item_name])
        return ret.strip()

    def _get_repeat_cnt(self, tr_code: str, rq_name: str):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
        return ret

    def _on_receive_tr_data(self, screen_no: str, rq_name: str, tr_code: str, record_name: str, pre_next: str, unused1,
                            unused2, unused3, unused4):
        logger.debug(
            f'screen_no:{screen_no}, rq_name:{rq_name}, tr_code:{tr_code}, record_name:{record_name}, '
            f'pre_next:{pre_next}, unused1:{unused1}, unused2:{unused2}, unused3:{unused3}, unused4:{unused4}')
        if pre_next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rq_name == RequestName.MULTI_CODE_QUERY.value:
            count = self._get_repeat_cnt(tr_code, rq_name)
            for i in range(count):
                code = self._get_comm_data(tr_code, record_name, i, '종목코드')
                name = self._get_comm_data(tr_code, record_name, i, '종목명')
                price_str = self._get_comm_data(tr_code, record_name, i, '현재가')
                price = int(price_str)
                price = price if price >= 0 else price * (-1)
                stock = self.model.get_stock(code)
                stock.name = name
                stock.cur_price = price
                logger.info(f'code:{code}, name:{name}, price:{price}')
            self.disconnect_real_data(ScreenNo.INTEREST)
            self.model.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RequestName.BALANCE.value:
            # TODO:
            name = self._get_comm_data(tr_code, record_name, 0, '계좌명')
            cur_price = self._get_comm_data(tr_code, record_name, 0, '유가잔고평가액')
            cash = self._get_comm_data(tr_code, record_name, 0, '예수금')
            count = self._get_repeat_cnt(tr_code, rq_name)
            buy_total = self._get_comm_data(tr_code, record_name, 0, '총매입금액')
            logger.info(f'name:{name}, cur_price:{cur_price}, cash:{cash}, count:{count}, buy_total:{buy_total}')
            for i in range(count):
                code = self._get_comm_data(tr_code, record_name, i, '종목코드')
                name = self._get_comm_data(tr_code, record_name, i, '종목명')
                buy_price_str = self._get_comm_data(tr_code, record_name, i, '평균단가')
                price_str = self._get_comm_data(tr_code, record_name, i, '현재가')
                logger.info(f'code:{code}, name:{name}, buy_price_str:{buy_price_str}, price:{price_str}')
            self.disconnect_real_data(ScreenNo.INTEREST)
            self.model.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RequestName.CODE_INFO.value:
            code = self._get_comm_data(tr_code, record_name, 0, '종목코드').strip()
            name = self._get_comm_data(tr_code, record_name, 0, '종목명').strip()
            price_str = self._get_comm_data(tr_code, record_name, 0, '현재가').strip()
            if code and name and price_str:
                price = int(price_str)
                price = price if price >= 0 else price * (-1)
                stock = self.model.get_stock(code)
                stock.name = name
                stock.cur_price = price
                logger.info(f'code:{code}, name:{name}, price:{price}')
                self.model.set_updated(DataType.TABLE_BALANCE)
            else:
                logger.error("error!!")
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _on_receive_real_data(self, code: str, real_type: str, real_data: str):
        logger.debug(f"code:{code} real_type:{real_type} real_data:{real_data}")
        if real_type == '장시작시간':
            # TODO: Trigger time related strategy
            pass
        elif real_type == '주식체결':
            price_str = self._get_comm_real_data(code, 10)
            cur_price = int(price_str)
            cur_price = cur_price if cur_price >= 0 else cur_price * (-1)
            stock = self.model.get_stock(code)
            stock.cur_price = cur_price
            for strategy in stock.sell_strategy_dic.values():
                strategy.on_price_updated()
            for strategy in stock.buy_strategy_dic.values():
                strategy.on_price_updated()

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        logger.info(gubun)
        logger.info(self.get_chejan_data(9203))
        logger.info(self.get_chejan_data(302))
        logger.info(self.get_chejan_data(900))
        logger.info(self.get_chejan_data(901))

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def get_condition_load_async(self):
        """HTS 에 저장된 condition 불러옴

        :return: 1(성공)
        :callback: _on_receive_condition_ver()
        """
        ret = self.dynamicCall("GetConditionLoad()")
        logger.debug("ret: %d", ret)
        self.temp_event_loop = QEventLoop()
        self.temp_event_loop.exec_()
        return ret

    def _on_receive_condition_ver(self, lRet, sMsg):
        logger.debug("%d %s", lRet, sMsg)
        self.temp_event_loop.exit()

    def send_condition_async(self, screen_num, condition_name, condition_index, query_type):
        """ condition 만족하는 종목 조회 or 실시간 등록

        :param query_type: 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
        :callback: _on_receive_tr_condition()
        """
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)", screen_num, condition_name, condition_index,
                               query_type)
        return ret

    def _on_receive_tr_condition(self, scr_no, str_code_list, str_condition_name, index, has_next):
        logger.debug(f'{scr_no} {str_code_list} {str_condition_name} {index} {has_next}')
        code_list_str = str_code_list[:-1]  # 마지막 ";" 제거
        code_list = code_list_str.split(';')
        logger.debug("code_list: %s", code_list)
        temp_stock_list = []
        for code in code_list:
            name = self.get_master_code_name([code])
            temp_stock_list.append(Stock(code, name))
            logger.debug("code: %s, name: %s", code, name)
        self.model.set_temp_stock_list(temp_stock_list)

    def comm_kw_rq_data_async(self, the_code_list: list):
        """ 복수종목조회 Tran 을 서버로 송신한다
        :callback: _on_receive_tr_data()
        """
        logger.debug(f'comm_kw_rq_data() {the_code_list}')
        count = len(the_code_list)
        if count == 0:
            logger.error('code_list is empty!!')
            return -1
        code_list_str = ";".join(the_code_list)  # 종목리스트
        is_next = 0  # 연속조회요청 여부
        code_count = count  # 종목개수
        type_flag = 0  # 조회구분 (0: 주식관심종목정보 , 선물옵션관심종목정보)
        rq_name = RequestName.MULTI_CODE_QUERY.value  # 사용자구분 명
        screen_no = ScreenNo.INTEREST.value  # 화면변허
        ret = self.dynamicCall("CommKwRqData(QString, int, int, int, QString, QString)",
                               [code_list_str, is_next, code_count, type_flag, rq_name, screen_no])
        logger.info(f'CommKwRqData(). ret: {ret}')  # 0: 정상처리
        return ret

    def set_real_reg(self, the_code_list: list):
        logger.debug(f'set_real_reg() {the_code_list}')
        code_list_str = ';'.join(the_code_list)
        fid = "9001;10;13"  # 종목코드,업종코드;현재가;누적거래량
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                               [ScreenNo.REAL.value, code_list_str, fid, "1"])  # "1" 종목 추가, "0" 기존 종목은 제외
        logger.info(f'call set_real_reg(). ret: {ret}')
        return ret

    def set_real_remove(self, the_code):
        logger.info("the_code %s", the_code)
        ret = self.dynamicCall("SetRealRemove(QString, QString)", [ScreenNo.REAL.value, the_code])
        logger.info(f'SetRealRemove(). ret: {ret}')

    def disconnect_real_data(self, screen_no: ScreenNo):
        ret = self.dynamicCall("DisconnectRealData(QString)", [screen_no.value])
        logger.info(f'DisconnectRealData(). ret: {ret}')

    def request_account_detail(self):
        logger.info(f'account: {self.model.account}')
        self.set_input_value('계좌번호', self.model.account)
        self.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.set_input_value('상장폐지조회구분', '0')  # 0:전체, 1: 상장폐지종목제외
        self.set_input_value('비밀번호입력매체구분', '00')  # 고정값?
        tr_code = 'OPW00004'  # 계좌평가현황요청
        is_next = 0  # 연속조회요청 여부 (0:조회 , 2:연속)
        self.comm_rq_data(RequestName.BALANCE,  tr_code,  is_next, ScreenNo.BALANCE)

    def request_code_info(self, the_code):
        logger.info(f'code: {the_code}')
        self.set_input_value('종목코드', the_code)
        tr_code = 'opt10001'  # 주식기본정보요청
        is_next = 0
        self.comm_rq_data(RequestName.CODE_INFO, tr_code, is_next, ScreenNo.CODE)


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


    app = QApplication(sys.argv)
    tempWindow = QMainWindow()
    tempManager = TempKiwoomListener()
    tempModelListener = TempModelListener()
    model = Model()
    model.set_listener(tempModelListener)
    kiwoom_api = Kiwoom(model)
    kiwoom_api.set_listener(tempManager)

    kiwoom_api.comm_connect()

    kiwoom_api.get_condition_load_async()
    condition_name_dic = kiwoom_api.get_condition_name_list()
    logger.debug(condition_name_dic)

    kiwoom_api.send_condition_async('1111', condition_name_dic[1], 1, 0)

    input_code_list = ['004540', '005360', '053110']
    kiwoom_api.comm_kw_rq_data_async(input_code_list)

    time.sleep(1)

    kiwoom_api.set_real_reg(input_code_list)

    tempWindow.show()
    sys.exit(app.exec_())
