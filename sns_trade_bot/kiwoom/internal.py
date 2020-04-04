import logging

from PyQt5.QAxContainer import *
from sns_trade_bot.model.data_manager import DataManager
from sns_trade_bot.kiwoom.common import EventHandler

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

    def comm_connect(self) -> int:
        """1_로그인 윈도우를 실행한다.

        로그인이 성공하거나 실패하는 경우 OnEventConnect 이벤트가 발생하고 이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.

        :return: 0 - 성공, 음수값은 실패
        """
        ret = self.dynamicCall("CommConnect()")
        if ret < 0:
            logger.error(f'failed to CommConnect(). ret: {ret}')
        return ret

    def comm_rq_data(self, rq_name: str, tr_code: str, is_next: int, scn_no: str) -> int:
        """3_Tran을 서버로 송신한다.

        Ex) openApi.CommRqData( “RQ_1”, “OPT00001”, 0, “0101”);

        :param rq_name: 사용자구분 명
        :param tr_code: Tran명 입력
        :param is_next: 0:조회, 2:연속
        :param scn_no: 4자리의 화면번호
        :return: OP_ERR_NONE(0) - 정상처리
                 OP_ERR_SISE_OVERFLOW(-200) - 과도한 시세조회로 인한 통신불가
                 OP_ERR_RQ_STRUCT_FAIL(-201) - 입력 구조체 생성 실패
                 OP_ERR_RQ_STRING_FAIL(-202) - 요청전문 작성 실패
        """
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)",
                               [rq_name, tr_code, is_next, scn_no])
        logger.info(f'CommRqData(). ret: {ret}')
        return ret

    def get_login_info(self, tag: str) -> str:
        """4_로그인한 사용자 정보를 반환한다.

        BSTR sTag에 들어 갈 수 있는 값은 아래와 같음
        “ACCOUNT_CNT” – 전체 계좌 개수를 반환한다.
        "ACCNO" – 전체 계좌를 반환한다. 계좌별 구분은  ‘;’이다.
        “USER_ID” - 사용자  ID를 반환한다.
        “USER_NAME” – 사용자명을 반환한다.
        “KEY_BSECGB” – 키보드보안 해지여부. 0:정상, 1:해지
        “FIREW_SECGB” – 방화벽 설정 여부. 0:미설정, 1:설정, 2:해지
        Ex) openApi.GetLoginInfo(“ACCOUNT_CNT”)

        :param tag: 사용자 정보 구분 TAG값 (비고)
        :return: TAG값에 따른 데이터 반환
        """
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def send_order(self, rq_name: str, scn_no: str, acc_no: str, order_type: int, code: str, qty: int, price: int,
                   hoga_gb: str, org_order_no: str) -> int:
        """5_주식 주문을 서버로 전송한다.

        시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시간외, 장후시간외 주문시
        주문가격을 입력하지 않습니다.

        관련 이벤트: on_receive_tr_data, on_receive_msg, on_receive_chejan_data

        ex) 지정가 매수 - openApi.SendOrder(“RQ_1”, “0101”,“5015123410”, 1, “000660”, 10, 48500, “00”, “”);
            시장가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 0, “03”, “”);
            매수 정정 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 5, “000660”, 10, 49500, “00”, “1”);
            매수 취소 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 3, “000660”, 10, 0, “00”, “2”);

        :param rq_name: 사용자 구분 요청 명
        :param scn_no: 화면번호[4]
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
                                [rq_name, scn_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no])

    def set_input_value(self, item: str, value: str) -> None:
        """7_Tran 입력 값을 서버통신 전에 입력한다.

        Ex) openApi.SetInputValue(“종목코드”, “000660”);
        openApi.SetInputValue(“계좌번호”, “5015123401”);

        :param item: 아이템명
        :param value: 입력 값
        """
        self.dynamicCall("SetInputValue(QString, QString)", item, value)

    def disconnect_real_data(self, scn_no: str) -> None:
        """10_화면 내 모든 리얼데이터 요청을 제거한다.

        화면을 종료할 때 반드시 위 함수를 호출해야 한다.
        Ex) openApi.DisconnectRealData(“0101”);

        :param scn_no: 화면번호[4]
        """
        self.dynamicCall("DisconnectRealData(QString)", [scn_no])

    def get_repeat_cnt(self, tr_code: str, record_name: str) -> int:
        """11_레코드 반복횟수를 반환한다.

        Ex) openApi.GetRepeatCnt(“OPT00001”, “주식기본정보”);

        :param tr_code: Tran 명
        :param record_name: 레코드 명
        :return: 레코드의 반복횟수
        """
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, record_name)
        return ret

    def comm_kw_rq_data(self, arr_code: str, is_next: int, code_count: int, type_flag: int, rq_name: str,
                        scn_no: str) -> int:
        """12_복수종목조회 Tran 을 서버로 송신한다

        :param arr_code: 종목리스트 (종목간 구분은 ';' 이다.)
        :param is_next: 연속조회요청
        :param code_count: 종목개수
        :param type_flag: 조회구분 (0:주식관심종목정보, 3:선물옵션관심종목정보)
        :param rq_name: 사용자구분 명
        :param scn_no: 화면번호[4]
        :return: OP_ERR_NONE(0) - 정상처리
                 OP_ERR_RQ_STRING_FAIL(-202) - 요청전문 작성 실패
        """
        ret = self.dynamicCall("CommKwRqData(QString, int, int, int, QString, QString)",
                               [arr_code, is_next, code_count, type_flag, rq_name, scn_no])
        logger.info(f'CommKwRqData(). ret: {ret}')  # 0: 정상처리
        return ret

    def get_code_list_by_market(self, market: str) -> str:
        """14_시장구분에 따른 종목코드를 반환한다.

        sMarket – 0:장내,  3:ELW,  4:뮤추얼펀드,  5:신주인수권,  6:리츠, 8:ETF,  9:하이일드펀드,  10:코스닥,  30:K-OTC,
        50:코넥스(KONEX)

        :param market: 시장구분
        :return:
        """
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_connect_state(self) -> int:
        """15_현재접속상태를 반환한다.

        :return: 접속상태 (0:미연결,  1:연결완료)
        """
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def get_master_code_name(self, code: str) -> str:
        """16_종목코드의 한글명을 반환한다.

        장내외, 지수선옵, 주식선옵 검색 가능.

        :param code: 종목코드
        :return: 종목한글명
        """
        return self.dynamicCall("GetMasterCodeName(QString)", [code])

    def get_comm_data(self, tr_code: str, record_name: str, index: int, item_name: str) -> str:
        """24_수신 데이터를 반환한다.

        Ex)현재가출력  - openApi.GetCommData(“OPT00001”, “주식기본정보”, 0, “현재가”);

        :param tr_code: Tran 코드
        :param record_name: 레코드명
        :param index: 복수데이터 인덱스
        :param item_name: 아이템명
        :return: 수신 데이터
        """
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               [tr_code, record_name, index, item_name])
        return ret.strip()

    def get_comm_real_data(self, code: str, fid: int) -> str:
        """25_실시간 시세 데이터를 반환한다.

        Ex) 현재가출력  - openApi.GetCommRealData(“039490”, 10);
        참고) strCode는 OnReceiveRealData 첫번째 매개변수를 사용

        :param code: 종목코드
        :param fid: 실시간 아이템
        :return: 수신 데이터
        """
        ret = self.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return ret.strip()

    def get_chejan_data(self, fid: int) -> str:
        """26_체결잔고 데이터를 반환한다.

        Ex) 현재가출력 – openApi.GetChejanData(10);

        :param fid: 체결잔고 아이템
        :return: 수신 데이터
        """
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret.strip()

    def set_real_reg(self, scn_no: str, code_list_str: str, fid_list_str: str, real_type: str) -> int:
        """49_실시간 등록을 한다.

        real_type 을 "0" 으로 하면 같은 화면에서 다른 종목 코드로 실시간 등록을 하게 되면 마지막에 사용한 종목코드만
        실시간 등록이 되고, 기존에 있던 종목은 실시간이 자동 해지됨.
        "1"로 하면 같은 화면에서 다른 종목을 추가할 경우, 기존에 등록한 종목도 함께 실시간 시세를 받을 수 있음.
        꼭 같은 화면이어야 하고 최초 실시간 등록은 "0"으로 하고 이후부터 "1"로 등록해야 함.

        :param scn_no: 실시간 등록한 화면 번호
        :param code_list_str: 실시간 등록한 종목코드 (복수 종목 가능 - "종목1;종목2;종목3;...")
        :param fid_list_str: 실시간 등록할 FID ("FID1;FID2;FID3;...")
        :param real_type: "1": 종목 추가, "0": 기존 종목은 제외
        :return: 0: 정상처리
        """
        logger.debug(f'set_real_reg(). code_list_str:"{code_list_str}", fid_list_str:"{fid_list_str}"')
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                               [scn_no, code_list_str, fid_list_str, real_type])
        logger.info(f'set_real_reg(). ret: {ret}')
        return ret

    def set_real_remove(self, scn_no: str, del_code: str):
        """50_종목별 실시간 해제(SetRealReg()로 등록한 종목만 실시간 해제 가능)

        :param scn_no: 실시간 해제할 화면 번호
        :param del_code: 실시간 해제할 종목
        """
        ret = self.dynamicCall("SetRealRemove(QString, QString)", [scn_no, del_code])
        logger.info(f'SetRealRemove(). ret: {ret}')

    def get_condition_load(self) -> int:
        """51_서버에 저장된 사용자 조건식을 조회해서 임시로 파일에 저장.

        System 폴더에 아이디_NewSaveIndex.dat파일로 저장된다. Ocx가 종료되면 삭제시킨다.
        조건검색 사용시 이함수를 최소 한번은 호출해야 조건검색을 할 수 있다.
        영웅문에서 사용자 조건을 수정 및 추가하였을 경우에도 최신의 사용자 조건을 받고 싶으면 다시 조회해야한다.

        관련이벤트: on_receive_condition_ver()

        :return: 1(성공)
        """
        ret = self.dynamicCall("GetConditionLoad()")
        logger.debug("ret: %d", ret)
        return ret

    def get_condition_name_list(self) -> str:
        """52_조건검색 조건명 리스트를 받아온다.

        조건명 리스트를 구분(";")하여 받아온다. ex) 인덱스1^조건명1;인덱스2^조건명2;...

        :return: 조건명 리스트(인덱스^조건명)
        """
        return self.dynamicCall("GetConditionNameList()")

    def send_condition(self, scn_no: str, condition_name: str, condition_index: int, query_type: int) -> int:
        """53_조건검색 종목조회TR송신한다.

        단순 조건식에 맞는 종목을 조회하기 위해서는 조회구분을  0으로 하고,
        실시간 조건검색을 하기 위해서는 조회구분을  1로 한다.
        OnReceiveTrCondition으로 결과값이 온다.
        연속조회가 필요한 경우에는 응답받는 곳에서 연속조회 여부에 따라 연속조회를 송신하면된다.

        관련 이벤트: on_receive_tr_condition()

        :param scn_no: 화면번호
        :param condition_name: 조건명
        :param condition_index: 조건명인덱스
        :param query_type: 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
        :return: 성공 1, 실패 0
        """
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)",
                               [scn_no, condition_name, condition_index, query_type])
        if ret != 1:
            logger.error(f'ret: {ret}')
        return ret
