import sys
import logging
from abc import abstractmethod
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *


logger = logging.getLogger(__name__)

TR_REQ_TIME_INTERVAL = 0.2


class KiwoomListener:
    """
    Notify kiwoom events to UI
    """
    @abstractmethod
    def on_connect(self, err_code):
        pass

    @abstractmethod
    def on_receive_tr_data(self):
        pass

    @abstractmethod
    def on_receive_chejan_data(self):
        pass


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._event_connect)
        self.listener = None

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
        else:
            logger.info("disconnected")
        self.login_event_loop.exit()
        if self.listener:
            self.listener.on_connect(err_code)

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

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

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

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


if __name__ == "__main__":
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

    app = QApplication(sys.argv)
    tempWindow = QMainWindow()
    tempManager = TempKiwoomListener()
    kiwoom_api = Kiwoom()
    kiwoom_api.set_listener(tempManager)

    kiwoom_api.comm_connect()
    code_list = kiwoom_api.get_code_list_by_market('10')
    for code in code_list:
        logger.info(code)
    logger.info(kiwoom_api.get_master_code_name("000660"))
    tempWindow.show()
    sys.exit(app.exec_())