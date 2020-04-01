import logging
from typing import List

from PyQt5.QAxContainer import *
from sns_trade_bot.model.data_manager import DataManager
from sns_trade_bot.kiwoom.common import ScreenNo, RqName, EventHandler

logger = logging.getLogger(__name__)


class KiwoomOcx(QAxWidget):
    data_manager: DataManager

    def __init__(self, the_data_manager):
        super().__init__()
        self.data_manager = the_data_manager
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def set_event_handler(self, event_handler: EventHandler):
        self.OnEventConnect.connect(event_handler.on_event_connect)
        self.OnReceiveTrCondition.connect(event_handler.on_receive_tr_condition)
        self.OnReceiveConditionVer.connect(event_handler.on_receive_condition_ver)
        self.OnReceiveTrData.connect(event_handler.on_receive_tr_data)
        self.OnReceiveRealData.connect(event_handler.on_receive_real_data)
        self.OnReceiveMsg.connect(event_handler.on_receive_msg)
        self.OnReceiveChejanData.connect(event_handler.on_receive_chejan_data)
        self.OnReceiveRealCondition.connect(event_handler.on_receive_real_condition)

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

    def get_master_code_name(self, code: str) -> str:
        """종목코드의 한글명을 반환한다.

        :param code: 종목코드
        :return: 종목한글명
        """
        name = self.dynamicCall("GetMasterCodeName(QString)", [code])
        return name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, item: str, value: str):
        self.dynamicCall("SetInputValue(QString, QString)", item, value)

    def comm_rq_data(self, rq_name: RqName, tr_code: str, is_next: int, screen_no: ScreenNo):
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

    def send_order(self, rq_name: str, screen_no: str, acc_no: str, order_type: int, code: str, qty: int, price: int,
                   hoga_gb: str, org_order_no: str) -> int:
        """주식 주문을 서버로 전송한다.

        시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시간외, 장후시간외 주문시
        주문가격을 입력하지 않습니다.

        관련 이벤트: on_receive_tr_data, on_receive_msg, on_receive_chejan_data

        :param rq_name: 사용자 구분 요청 명
        :param screen_no: 화면번호[4]
        :param acc_no: 계좌번호[10]
        :param order_type: 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
        :param code: 주식종목코드
        :param qty: 주문수량
        :param price: 주문단가
        :param hoga_gb: 호가구분 (00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가,
            10:지정가IOC, 13:시장가IOC, 16:최유리IOC, 20:지정가FOK, 23:시장가FOK, 26:최유리FOK, 61:장전시간외종가,
            62:시간외단일가, 81:장후시간외종가)
        :param org_order_no: 원주문번호
        :return: 0 if successful, otherwise negative value.
        """
        return self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                [rq_name, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no])

    def get_chejan_data(self, fid: int) -> str:
        """체결잔고 데이터를 반환한다.

        :param fid: 체결잔고 아이템
        :return: 수신 데이터
        """
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret.strip()

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def get_condition_load(self):
        """HTS 에 저장된 condition 불러옴

        :return: 1(성공)
        :callback: on_receive_condition_ver()
        """
        ret = self.dynamicCall("GetConditionLoad()")
        logger.debug("ret: %d", ret)
        return ret

    def send_condition(self, screen_num: str, condition_name: str, condition_index: int, query_type: int) -> int:
        """ condition 만족하는 종목 조회 or 실시간 등록

        :param screen_num:
        :param condition_name:
        :param condition_index:
        :param query_type: 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
        :return: 성공 1, 실패 0
        :callback: _on_receive_tr_condition()
        """
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)",
                               [screen_num, condition_name, condition_index, query_type])
        if ret != 1:
            logger.error(f'ret: {ret}')
        return ret

    def comm_kw_rq_data(self, the_code_list: List[str]):
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
        rq_name = RqName.INTEREST_CODE.value  # 사용자구분 명
        screen_no = ScreenNo.INTEREST.value  # 화면변허
        ret = self.dynamicCall("CommKwRqData(QString, int, int, int, QString, QString)",
                               [code_list_str, is_next, code_count, type_flag, rq_name, screen_no])
        logger.info(f'CommKwRqData(). ret: {ret}')  # 0: 정상처리
        return ret

    def set_real_reg(self, screen_no: str, code_list_str: str, fid_list_str: str, real_type: str) -> int:
        """실시간 등록을 한다.

        real_type 을 "0" 으로 하면 같은 화면에서 다른 종목 코드로 실시간 등록을 하게 되면 마지막에 사용한 종목코드만
        실시간 등록이 되고, 기존에 있던 종목은 실시간이 자동 해지됨.
        "1"로 하면 같은 화면에서 다른 종목을 추가할 경우, 기존에 등록한 종목도 함께 실시간 시세를 받을 수 있음.
        꼭 같은 화면이어야 하고 최초 실시간 등록은 "0"으로 하고 이후부터 "1"로 등록해야 함.

        :param screen_no: 실시간 등록한 화면 번호
        :param code_list_str: 실시간 등록한 종목코드 (복수 종목 가능 - "종목1;종목2;종목3;...")
        :param fid_list_str: 실시간 등록할 FID ("FID1;FID2;FID3;...")
        :param real_type: "1": 종목 추가, "0": 기존 종목은 제외
        :return: 0: 정상처리
        """
        logger.debug(f'set_real_reg(). code_list_str:"{code_list_str}", fid_list_str:"{fid_list_str}"')
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                               [screen_no, code_list_str, fid_list_str, real_type])
        logger.info(f'set_real_reg(). ret: {ret}')
        return ret

    def set_real_remove(self, scr_no: str, del_code: str):
        """종목별 실시간 해제(SetRealReg()로 등록한 종목만 실시간 해제 가능)

        :param scr_no: 실시간 해제할 화면 번호
        :param del_code: 실시간 해제할 종목
        """
        ret = self.dynamicCall("SetRealRemove(QString, QString)", [scr_no, del_code])
        logger.info(f'SetRealRemove(). ret: {ret}')

    def disconnect_real_data(self, screen_no: ScreenNo):
        ret = self.dynamicCall("DisconnectRealData(QString)", [screen_no.value])
        logger.info(f'DisconnectRealData(). ret: {ret}')

    def request_account_detail(self):
        logger.info(f'account: {self.data_manager.account}')
        self.set_input_value('계좌번호', self.data_manager.account)
        self.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.set_input_value('상장폐지조회구분', '0')  # 0:전체, 1: 상장폐지종목제외
        self.set_input_value('비밀번호입력매체구분', '00')  # 고정값?
        tr_code = 'OPW00004'  # 계좌평가현황요청
        is_next = 0  # 연속조회요청 여부 (0:조회 , 2:연속)
        self.comm_rq_data(RqName.BALANCE, tr_code, is_next, ScreenNo.BALANCE)

    def request_code_info(self, the_code: str):
        logger.info(f'code: {the_code}')
        self.set_input_value('종목코드', the_code)
        tr_code = 'opt10001'  # 주식기본정보요청
        is_next = 0
        self.comm_rq_data(RqName.CODE_INFO, tr_code, is_next, ScreenNo.CODE)