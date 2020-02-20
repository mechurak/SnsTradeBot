import sys
import logging
from abc import abstractmethod
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from model.model import Model, DataType
from model.model import Stock
from model.model import ModelListener

logger = logging.getLogger(__name__)

TR_REQ_TIME_INTERVAL = 0.2


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

    RQ_MULTI_CODE_QUERY = 'MULTI_CODE_QUERY'

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

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

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
            f"screen_no:{screen_no} rq_name:{rq_name} tr_code:{tr_code} record_name:{record_name} pre_next:{pre_next} unused1:{unused1} unused2:{unused2} unused3:{unused3} unused4:{unused4}")
        if pre_next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rq_name == Kiwoom.RQ_MULTI_CODE_QUERY:
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
                logger.info(f'code:{code} name:{name} price:{price}')

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _on_receive_real_data(self, code: str, real_type: str, real_data: str):
        logger.debug(f"code:{code} real_type:{real_type} real_data:{real_data}")

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

    def comm_kw_rq_data(self, the_code_list: list):
        logger.debug(f'comm_kw_rq_data() {the_code_list}')
        code_list_str = ";".join(the_code_list)
        count = len(code_list_str)
        is_next = 0
        type_flag = 0
        rq_name = Kiwoom.RQ_MULTI_CODE_QUERY
        screen_no = '2222'
        """복수종목조회 Tran 을 서버로 송신한다
        @param  sArrCode 종목리스트
        @param  bNext 연속조회요청
        @param  nCodeCount 종목개수
        @param  nTypeFlag 조회구분
        @param  sRQName 사용자구분 명
        @param  sScreenNo 화면번호
        """
        ret = self.dynamicCall("CommKwRqData(QString, int, int, int, QString, QString)",
                               [code_list_str, is_next, count, type_flag, rq_name, screen_no])
        logger.info(f'ret: {ret}')
        return ret


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
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
    kiwoom_api.comm_kw_rq_data(input_code_list)

    tempWindow.show()
    sys.exit(app.exec_())
