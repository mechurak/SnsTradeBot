import logging

from sns_trade_bot.model.model import Model, DataType, Stock
from sns_trade_bot.openapi.kiwoom_common import ScreenNo, RqName, EventHandler, TrResultKey
from sns_trade_bot.openapi.kiwoom_internal import KiwoomOcx

logger = logging.getLogger(__name__)


class KiwoomEventHandler(EventHandler):
    model: Model
    ocx: KiwoomOcx

    def __init__(self, the_model, the_ocx):
        self.model = the_model
        self.ocx = the_ocx

    def on_event_connect(self, err_code):
        if err_code == 0:
            logger.info("connected")
            account_num = self.ocx.get_login_info('ACCNO')
            account_num = account_num[:-1]
            account_list = account_num.split(";")
            logger.info("account_list: %s", account_list)
            self.model.set_account_list(account_list)
        else:
            logger.info("disconnected")

    def on_receive_tr_data(self, screen_no: str, rq_name: str, tr_code: str, record_name: str, pre_next: str, unused1,
                           unused2, unused3, unused4):
        logger.debug(
            f'screen_no:{screen_no}, rq_name:{rq_name}, tr_code:{tr_code}, record_name:{record_name}, '
            f'pre_next:{pre_next}, unused1:{unused1}, unused2:{unused2}, unused3:{unused3}, unused4:{unused4}')

        if rq_name == RqName.INTEREST_CODE.value:
            count = self.ocx.get_repeat_cnt(tr_code)
            for i in range(count):
                self.print_tr_data(tr_code, record_name, i, TrResultKey.INTEREST_CODE_MULTI)
                code = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')
                price_str = self.ocx.get_comm_data(tr_code, record_name, i, '현재가')
                price = int(price_str)
                price = price if price >= 0 else price * (-1)
                stock = self.model.get_stock(code)
                stock.name = name
                stock.cur_price = price
                logger.info(f'code:{code}, name:{name}, price:{price}')
            self.ocx.disconnect_real_data(ScreenNo.INTEREST)
            self.model.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RqName.BALANCE.value:
            self.print_tr_data(tr_code, record_name, 0, TrResultKey.BALANCE_SINGLE)
            account_name = self.ocx.get_comm_data(tr_code, record_name, 0, '계좌명')
            cur_balance_str = self.ocx.get_comm_data(tr_code, record_name, 0, '유가잔고평가액')
            cash_str = self.ocx.get_comm_data(tr_code, record_name, 0, '예수금')
            cash2_str = self.ocx.get_comm_data(tr_code, record_name, 0, 'D+2추정예수금')
            buy_total_str = self.ocx.get_comm_data(tr_code, record_name, 0, '총매입금액')
            print_count_str = self.ocx.get_comm_data(tr_code, record_name, 0, '출력건수')
            cur_balance = int(cur_balance_str)
            cash = int(cash_str)
            cash2 = int(cash2_str)
            buy_total = int(buy_total_str)
            print_count = int(print_count_str)
            count = self.ocx.get_repeat_cnt(tr_code)
            logger.info(f'account_name:{account_name}, cur_balance:{cur_balance}, cash:{cash}, cash2:{cash2}, '
                        f'buy_total:{buy_total}, print_count:{print_count}, count:{count}')
            for i in range(count):
                self.print_tr_data(tr_code, record_name, 0, TrResultKey.BALANCE_MULTI)
                code_raw = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')  # A096530
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')  # 씨젠
                quantity_str = self.ocx.get_comm_data(tr_code, record_name, i, '보유수량')  # 000000000010
                buy_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '평균단가')  # 000000037650
                cur_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '현재가')  # 000000037200
                earning_rate_str = self.ocx.get_comm_data(tr_code, record_name, i, '손익율')  # -00000014688
                code = code_raw[1:]  # Remove 'A'
                quantity = int(quantity_str)
                buy_price = int(buy_price_str)
                cur_price = int(cur_price_str)
                earning_rate = float(earning_rate_str) / 10000
                logger.info(f'code:{code}, name:{name}, quantity:{quantity}, buy_price:{buy_price}, '
                            f'cur_price:{cur_price}, earning_rate:{earning_rate}')
                stock = self.model.get_stock(code)
                stock.name = name
                stock.cur_price = cur_price
                stock.quantity = quantity
                stock.buy_price = buy_price
                stock.earning_rate = earning_rate
            self.model.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RqName.CODE_INFO.value:
            self.print_tr_data(tr_code, record_name, 0, TrResultKey.CODE_SINGLE)
            code = self.ocx.get_comm_data(tr_code, record_name, 0, '종목코드').strip()
            name = self.ocx.get_comm_data(tr_code, record_name, 0, '종목명').strip()
            price_str = self.ocx.get_comm_data(tr_code, record_name, 0, '현재가').strip()
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

    def on_receive_real_data(self, code: str, real_type: str, real_data: str):
        logger.debug(f"code:{code} real_type:{real_type} real_data:{real_data}")
        if real_type == '장시작시간':
            # TODO: Trigger time related strategy
            pass
        elif real_type == '주식체결':
            price_str = self.ocx.get_comm_real_data(code, 10)
            cur_price = int(price_str)
            cur_price = cur_price if cur_price >= 0 else cur_price * (-1)
            stock = self.model.get_stock(code)
            stock.cur_price = cur_price
            for strategy in stock.sell_strategy_dic.values():
                strategy.on_price_updated()
            for strategy in stock.buy_strategy_dic.values():
                strategy.on_price_updated()

    def on_receive_msg(self, scr_no: str, rq_name: str, tr_code: str, msg: str):
        logger.info(f'scr_no:{scr_no}, rq_name:{rq_name}, tr_code:{tr_code}, msg:{msg}')

    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터를 받은 시점을 알려준다

        :param gubun: 체결구분 (0:접수/체결 , 1:국내주식 잔고통보, 4:파생상품 잔고통보)
        :param item_cnt: 아이템 개수
        :param fid_list: 데이터리스트 (';'로 구분)
        """
        logger.info(f'gubun:{gubun}, item_cnt:{item_cnt}, fid_list:{fid_list}')
        fid_str_list = fid_list.split(";")
        for fid_str in fid_str_list:
            ret = self.ocx.get_chejan_data(int(fid_str))
            logger.debug(f'  {fid_str}: {ret}')

        order_id = self.ocx.get_chejan_data(9203)  # 주문번호
        code = self.ocx.get_chejan_data(9001)  # 종목코드,업종코드
        code = code[1:]  # Remove 'A'
        name = self.ocx.get_chejan_data(302)  # 종목명

        if gubun == '0':  # 주문접수 or 주문체결
            status = self.ocx.get_chejan_data(913)  # 주문상태 ('접수' or '체결')
            order_type = self.ocx.get_chejan_data(913)  # 매도수구분 ('1':매도, '2':매수)
            time_str = self.ocx.get_chejan_data(908)  # 주문/체결시간 (HHMMSSMS)
            if status == '체결':
                logger.info('체결 신호!!!')
                if order_type == '2':  # 매수
                    # TODO: 종목 실시간 등록 및 조건식 실시간 재적용(?)
                    pass
        elif gubun == '1':  # 잔고통보
            qty = int(self.ocx.get_chejan_data(930))  # 보유수량
            if qty == 0:
                logger.info(f'{name}({code}) 청산 완료!!')
                self.model.remove_stock(code)
                self.ocx.set_real_remove(ScreenNo.REAL.value, code)

    def on_receive_condition_ver(self, ret: int, msg: str):
        logger.debug(f'ret: {ret}, msg: {msg}')  # ret: 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
        condition_name_dic = self.ocx.get_condition_name_list()
        logger.debug(condition_name_dic)
        self.model.set_condition_list(condition_name_dic)

    def on_receive_tr_condition(self, scr_no, str_code_list, str_condition_name, index, has_next):
        logger.debug(f'{scr_no} {str_code_list} {str_condition_name} {index} {has_next}')
        code_list_str = str_code_list[:-1]  # 마지막 ";" 제거
        code_list = code_list_str.split(';')
        logger.debug("code_list: %s", code_list)
        temp_stock_list = []
        for code in code_list:
            name = self.ocx.get_master_code_name([code])
            temp_stock_list.append(Stock(self.model.order_queue, code, name))
            logger.debug("code: %s, name: %s", code, name)
        self.model.set_temp_stock_list(temp_stock_list)

    def print_tr_data(self, tr_code, record_name, index, item_list):
        logger.debug(f'---- tr_code: {tr_code}, record_name: {record_name}, index: {index}')
        for item in item_list:
            out_str = self.ocx.get_comm_data(tr_code, record_name, index, item)
            logger.debug(f'"{item}" : "{out_str}"')
