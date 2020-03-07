import enum


class ScreenNo(enum.Enum):
    REAL = '2222'  # 실시간 조회
    INTEREST = '3333'  # 관심종목 조회
    BALANCE = '4444'  # 계좌평가현황요청
    CODE = '5555'  # 주식기본정보요청


class RqName(enum.Enum):
    INTEREST_CODE = 'RQ_MULTI_CODE_QUERY'  # 관심종목정보요청 (OPTKWFID)
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


class TrResultKey:
    BALANCE_SINGLE = [
        '계좌명',
        '지점명',
        '예수금',
        'D+2추정예수금',
        '유가잔고평가액',
        '예탁자산평가액',
        '총매입금액',
        '추정예탁자산',
        '매도담보대출금',
        '당일투자원금',
        '당월투자원금',
        '누적투자원금',
        '당일투자손익',
        '당월투자손익',
        '누적투자손익',
        '당일손익율',
        '당월손익율',
        '누적손익율',
        '출력건수'
    ]
    BALANCE_MULTI = [
        '종목코드',
        '종목명',
        '보유수량',
        '평균단가',
        '현재가',
        '평가금액',
        '손익금액',
        '손익율',
        '대출일',
        '매입금액',
        '결제잔고',
        '전일매수수량',
        '전일매도수량',
        '금일매수수량',
        '금일매도수량'
    ]
    CODE_SINGLE = [
        '종목코드',
        '종목명',
        '결산월',
        '액면가',
        '자본금',
        '상장주식',
        '신용비율',
        '연중최고',
        '연중최저',
        '시가총액',
        '시가총액비중',
        '외인소진률',
        '대용가',
        'PER',
        'EPS',
        'ROE',
        'PBR',
        'EV',
        'BPS',
        '매출액',
        '영업이익',
        '당기순이익',
        '250최고',
        '250최저',
        '시가',
        '고가',
        '상한가',
        '하한가',
        '기준가',
        '예상체결가',
        '예상체결수량',
        '250최고가일',
        '250최고가대비율',
        '250최저가일',
        '250최저가대비율',
        '현재가',
        '대비기호',
        '전일대비',
        '등락율',
        '거래량',
        '거래대비',
        '액면가단위',
        '유통주식',
        '유통비율'
    ]
    INTEREST_CODE_MULTI = [  # OPTKWFID
        '종목코드',
        '종목명',
        '현재가',
        '기준가',
        '전일대비',
        '전일대비기호',
        '등락율',
        '거래량',
        '거래대금',
        '체결량',
        '체결강도',
        '전일거래량대비',
        '매도호가',
        '매수호가',
        '매도1차호가',
        '매도2차호가',
        '매도3차호가',
        '매도4차호가',
        '매도5차호가',
        '매수1차호가',
        '매수2차호가',
        '매수3차호가',
        '매수4차호가',
        '매수5차호가',
        '상한가',
        '하한가',
        '시가',
        '고가',
        '저가',
        '종가',
        '체결시간',
        '예상체결가',
        '예상체결량',
        '자본금',
        '액면가',
        '시가총액',
        '주식수',
        '호가시간',
        '일자',
        '우선매도잔량',
        '우선매수잔량',
        '우선매도건수',
        '우선매수건수',
        '총매도잔량',
        '총매수잔량',
        '패리티',
        '기어링',
        '손익분기',
        '자본지지',
        'ELW행사가',
        '전환비율',
        'ELW만기일',
        '미결제약정',
        '미결제전일대비',
        '이론가',
        '내재변동성',
        '델타',
        '감마',
        '쎄타',
        '베가',
        '로'
    ]