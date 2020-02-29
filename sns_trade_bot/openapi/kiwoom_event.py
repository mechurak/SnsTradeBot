import logging

from sns_trade_bot.model.model import Model, DataType, Stock
from sns_trade_bot.openapi.kiwoom_common import ScreenNo, RequestName, EventHandler
from sns_trade_bot.openapi.kiwoom_internal import KiwoomOcx

logger = logging.getLogger(__name__)


class KiwoomEventHandler(EventHandler):
    model: Model
    ocx: KiwoomOcx

    def __init__(self, the_model, the_ocx):
        self.model = the_model
        self.ocx = the_ocx

    def event_connect(self, err_code):
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

        if rq_name == RequestName.MULTI_CODE_QUERY.value:
            count = self.ocx.get_repeat_cnt(tr_code)
            for i in range(count):
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
        elif rq_name == RequestName.BALANCE.value:
            account_name = self.ocx.get_comm_data(tr_code, record_name, 0, '계좌명')
            cur_balance_str = self.ocx.get_comm_data(tr_code, record_name, 0, '유가잔고평가액')
            cash_str = self.ocx.get_comm_data(tr_code, record_name, 0, '예수금')
            buy_total_str = self.ocx.get_comm_data(tr_code, record_name, 0, '총매입금액')
            print_count_str = self.ocx.get_comm_data(tr_code, record_name, 0, '출력건수')
            cur_balance = int(cur_balance_str)
            cash = int(cash_str)
            buy_total = int(buy_total_str)
            print_count = int(print_count_str)
            count = self.ocx.get_repeat_cnt(tr_code)
            logger.info(f'account_name:{account_name}, cur_balance:{cur_balance}, cash:{cash}, buy_total:{buy_total}, '
                        f'print_count:{print_count}, count:{count}')
            for i in range(count):
                code = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')
                quantity = self.ocx.get_comm_data(tr_code, record_name, i, '보유수량')
                buy_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '평균단가')
                cur_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '현재가')
                earning_rate_str = self.ocx.get_comm_data(tr_code, record_name, i, '손익율')
                logger.debug(f'code:{code}, name:{name}, quantity:{quantity}, buy_price_str:{buy_price_str}, '
                             f'cur_price_str:{cur_price_str}, earning_rate_str:{earning_rate_str}')
                buy_price = int(buy_price_str)
                cur_price = int(cur_price_str)
                cur_price = cur_price if cur_price >= 0 else cur_price * (-1)
                earning_rate = float(earning_rate_str) / 100
                stock = self.model.get_stock(code)
                stock.name = name
                stock.cur_price = cur_price
                stock.quantity = quantity
                stock.buy_price = buy_price
                logger.info(f'code:{code}, name:{name}, quantity:{quantity}, buy_price:{buy_price}, '
                            f'cur_price:{cur_price}, earning_rate:{earning_rate}')
            self.model.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RequestName.CODE_INFO.value:
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

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        logger.info(f'gubun:{gubun}, item_cnt:{item_cnt}, fid_list:{fid_list}')
        logger.info(self.ocx.get_chejan_data(9203))
        logger.info(self.ocx.get_chejan_data(302))
        logger.info(self.ocx.get_chejan_data(900))
        logger.info(self.ocx.get_chejan_data(901))

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
            temp_stock_list.append(Stock(code, name))
            logger.debug("code: %s, name: %s", code, name)
        self.model.set_temp_stock_list(temp_stock_list)
