import logging

from PyQt5.QAxContainer import *
from sns_trade_bot.model.model import Model
from sns_trade_bot.openapi.kiwoom_common import ScreenNo, RequestName, EventHandler

logger = logging.getLogger(__name__)


class KiwoomOcx(QAxWidget):
    model: Model

    def __init__(self, the_model):
        super().__init__()
        self.model = the_model
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def set_event_handler(self, event_handler: EventHandler):
        self.OnEventConnect.connect(event_handler.event_connect)
        self.OnReceiveTrCondition.connect(event_handler.on_receive_tr_condition)
        self.OnReceiveConditionVer.connect(event_handler.on_receive_condition_ver)
        self.OnReceiveTrData.connect(event_handler.on_receive_tr_data)
        self.OnReceiveRealData.connect(event_handler.on_receive_real_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")

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

    def set_input_value(self, item: str, value: str):
        self.dynamicCall("SetInputValue(QString, QString)", item, value)

    def comm_rq_data(self, rq_name: RequestName, tr_code: str, is_next: int, screen_no: ScreenNo):
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)",
                               [rq_name.value, tr_code, is_next, screen_no.value])
        logger.info(f'CommRqData(). ret: {ret}')

    def get_comm_real_data(self, code: str, fid: int) -> str:
        ret = self.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return ret.strip()

    def get_comm_data(self, tr_code: str, record_name: str, index: int, item_name: str) -> str:
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               [tr_code, record_name, index, item_name])
        return ret.strip()

    def get_repeat_cnt(self, tr_code: str):
        target_record = {
            'OPTKWFID': '관심종목정보',  # 관심종목정보요청
            'OPW00004': '종목별계좌평가현황',  # 계좌평가현황요청
        }
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, target_record[tr_code])
        return ret

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def get_condition_load_async(self):
        """HTS 에 저장된 condition 불러옴

        :return: 1(성공)
        :callback: on_receive_condition_ver()
        """
        ret = self.dynamicCall("GetConditionLoad()")
        logger.debug("ret: %d", ret)
        return ret

    def send_condition_async(self, screen_num: str, condition_name: str, condition_index: int, query_type: int):
        """ condition 만족하는 종목 조회 or 실시간 등록

        :param screen_num:
        :param condition_name:
        :param condition_index:
        :param query_type: 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
        :return: 성공 1, 실패 0
        :callback: _on_receive_tr_condition()
        """
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)", screen_num, condition_name, condition_index,
                               query_type)
        if ret != 1:
            logger.error(f'ret: {ret}')
        return ret

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
        self.comm_rq_data(RequestName.BALANCE, tr_code, is_next, ScreenNo.BALANCE)

    def request_code_info(self, the_code):
        logger.info(f'code: {the_code}')
        self.set_input_value('종목코드', the_code)
        tr_code = 'opt10001'  # 주식기본정보요청
        is_next = 0
        self.comm_rq_data(RequestName.CODE_INFO, tr_code, is_next, ScreenNo.CODE)
