import enum


class ScreenNo(enum.Enum):
    REAL = '2222'  # 실시간 조회
    INTEREST = '3333'  # 관심종목 조회
    BALANCE = '4444'  # 계좌평가현황요청
    CODE = '5555'  # 주식기본정보요청


class RequestName(enum.Enum):
    MULTI_CODE_QUERY = 'RQ_MULTI_CODE_QUERY'  # 관심종목정보요청 (OPTKWFID)
    BALANCE = 'RQ_BALANCE'  # 계좌평가현황요청 (OPW00004)
    CODE_INFO = 'RQ_CODE_INFO'  # 주식기본정보요청 (opt10001)


class EventHandler:
    def event_connect(self, err_code):
        pass

    def on_receive_tr_data(self, screen_no: str, rq_name: str, tr_code: str, record_name: str, pre_next: str, unused1,
                           unused2, unused3, unused4):
        pass

    def on_receive_real_data(self, code: str, real_type: str, real_data: str):
        pass

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        pass

    def on_receive_condition_ver(self, ret: int, msg: str):
        pass

    def on_receive_tr_condition(self, scr_no, str_code_list, str_condition_name, index, has_next):
        pass
