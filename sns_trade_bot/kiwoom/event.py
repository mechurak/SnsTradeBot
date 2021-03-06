import logging
import sys
from typing import List

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from sns_trade_bot.model.data_manager import DataManager, DataType, HoldType
from sns_trade_bot.model.stock import Stock
from sns_trade_bot.model.condition import Condition, SignalType
from sns_trade_bot.kiwoom.common import Job, ScnNo, RqName, EventHandler, TrResultKey, Fid, TrCode
from sns_trade_bot.kiwoom.internal import KiwoomOcx

logger = logging.getLogger(__name__)


class KiwoomEventHandler(EventHandler):
    data_manager: DataManager
    ocx: KiwoomOcx

    def __init__(self, the_data_manager, the_ocx, the_tr_queue, the_on_connect):
        self.data_manager = the_data_manager
        self.ocx = the_ocx
        self.tr_queue = the_tr_queue
        self.on_connect_callback = the_on_connect
        self.is_closing_called: bool = False

    def on_event_connect(self, err_code):
        if err_code == 0:
            logger.info("connected")
            account_num = self.ocx.get_login_info('ACCNO')
            account_num = account_num[:-1]
            account_list = account_num.split(";")
            logger.info("account_list: %s", account_list)
            self.data_manager.set_account_list(account_list)

            # Let manager know
            self.on_connect_callback()
        else:
            logger.info("disconnected")

    def on_receive_tr_data(self, screen_no: str, rq_name: str, tr_code: str, record_name: str, pre_next: str, unused1,
                           unused2, unused3, unused4):
        logger.debug(
            f'screen_no:"{screen_no}", rq_name:"{rq_name}", tr_code:"{tr_code}", record_name:"{record_name}", '
            f'pre_next:"{pre_next}", unused1:"{unused1}", unused2:"{unused2}", unused3:"{unused3}", '
            f'unused4:"{unused4}"')

        if rq_name == RqName.INTEREST_CODE.value:
            count = self.ocx.get_repeat_cnt(tr_code, '관심종목정보')
            for i in range(count):
                self.print_tr_data(tr_code, record_name, i, TrResultKey.INTEREST_CODE_MULTI)
                code = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')
                price_str = self.ocx.get_comm_data(tr_code, record_name, i, '현재가')
                price = int(price_str)
                price = price if price >= 0 else price * (-1)
                stock = self.data_manager.get_stock(code)
                stock.name = name
                stock.cur_price = price
                logger.info(f'{name}({code}) price:"{price}"')
            self.ocx.disconnect_real_data(ScnNo.INTEREST.value)
            self.data_manager.set_updated(DataType.TABLE_BALANCE)
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
            count = self.ocx.get_repeat_cnt(tr_code, '종목별계좌평가현황')
            logger.info(f'account_name:"{account_name}", cur_balance:{cur_balance}, cash:{cash}, cash2:{cash2}, '
                        f'buy_total:{buy_total}, print_count:{print_count}, count:{count}')
            for i in range(count):
                self.print_tr_data(tr_code, record_name, i, TrResultKey.BALANCE_MULTI)
                code_raw = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')  # A096530
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')  # 씨젠
                qty_str = self.ocx.get_comm_data(tr_code, record_name, i, '보유수량')  # 000000000010
                buy_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '평균단가')  # 000000037650
                cur_price_str = self.ocx.get_comm_data(tr_code, record_name, i, '현재가')  # 000000037200
                earning_rate_str = self.ocx.get_comm_data(tr_code, record_name, i, '손익율')  # -00000014688
                code = code_raw[1:]  # Remove 'A'
                qty = int(qty_str)
                buy_price = int(buy_price_str)
                cur_price = int(cur_price_str)
                earning_rate = float(earning_rate_str) / 10000
                logger.info(f'{name}({code}) qty:{qty}, buy_price:{buy_price}, cur_price:{cur_price}, '
                            f'earning_rate:{earning_rate}')
                stock = self.data_manager.get_stock(code)
                stock.name = name
                stock.cur_price = cur_price
                stock.qty = qty
                stock.buy_price = buy_price
                stock.earning_rate = earning_rate
            self.data_manager.set_updated(DataType.TABLE_BALANCE)
        elif rq_name == RqName.CODE_INFO.value:
            self.print_tr_data(tr_code, record_name, 0, TrResultKey.CODE_SINGLE)
            code = self.ocx.get_comm_data(tr_code, record_name, 0, '종목코드').strip()
            name = self.ocx.get_comm_data(tr_code, record_name, 0, '종목명').strip()
            price_str = self.ocx.get_comm_data(tr_code, record_name, 0, '현재가').strip()
            if code and name and price_str:
                price = int(price_str)
                price = price if price >= 0 else price * (-1)
                stock = self.data_manager.get_stock(code)
                stock.name = name
                stock.cur_price = price
                logger.info(f'{name}({code}) price:{price}')
                self.data_manager.set_updated(DataType.TABLE_BALANCE)
            else:
                logger.error("error!!")
        elif rq_name == RqName.ORDER.value:
            order_id = self.ocx.get_comm_data(tr_code, record_name, 0, '주문번호').strip()
            logger.info(f'order_id:"{order_id}"')
            # TODO: Handle error case (empty order_id)
        elif rq_name == RqName.당일손익상세요청.value:
            single_dic = {}
            self.print_tr_data(tr_code, record_name, 0, TrResultKey.TODAY_SINGLE)
            당일실현손익_str: str = self.ocx.get_comm_data(tr_code, record_name, 0, '당일실현손익').strip()
            single_dic['당일실현손익'] = 당일실현손익_str
            count = self.ocx.get_repeat_cnt(tr_code, '당일실현손익상세')
            logger.info(f'당일실현손익:"{당일실현손익_str}",  count:{count}')
            multi_dic = {}
            for i in range(count):
                self.print_tr_data(tr_code, record_name, i, TrResultKey.TODAY_MULTI)
                name = self.ocx.get_comm_data(tr_code, record_name, i, '종목명')
                code = self.ocx.get_comm_data(tr_code, record_name, i, '종목코드')
                cur_dic = {
                    '매입단가': self.ocx.get_comm_data(tr_code, record_name, i, '매입단가'),
                    '체결가': self.ocx.get_comm_data(tr_code, record_name, i, '체결가'),
                    '체결량': self.ocx.get_comm_data(tr_code, record_name, i, '체결량'),
                    '당일매도손익': self.ocx.get_comm_data(tr_code, record_name, i, '당일매도손익'),
                    '손익율': self.ocx.get_comm_data(tr_code, record_name, i, '손익율')
                }
                multi_dic[f'{name}({code})'] = cur_dic
            from sns_trade_bot.slack.webhook import MsgSender
            send_today_job = Job(MsgSender.send_multi_dic_msg, single_dic, multi_dic)
            self.tr_queue.put(send_today_job)

    def on_receive_real_data(self, code: str, real_type: str, real_data: str):
        logger.debug(f'code:"{code}", real_type:"{real_type}", real_data:"{real_data}"')
        if real_type == '장시작시간':
            cur_time_str = self.ocx.get_comm_real_data(code, 20)
            if cur_time_str == '084000':
                logger.info("장시작시간 20분전. 1초 후 계좌정보 확인")
                QTimer().singleShot(1000, self._request_account_detail)  # ms 후에 함수 실행
                logger.info("장시작시간 20분전. 10초 후 slack 메시지 발송")
                QTimer().singleShot(10000, self._send_account_to_slack)

            elif cur_time_str == '085000':
                logger.info("장시작시간 10분전. set_real_reg")
                target_code_list = self.data_manager.get_code_list(HoldType.TARGET)
                self._set_real_reg(target_code_list)

            elif cur_time_str == '085900':
                for stock in self.data_manager.stock_dic.values():
                    if stock.remained_buy_qty == 0:
                        for strategy in stock.buy_strategy_dic.values():
                            if strategy.enabled:
                                strategy.on_time(cur_time_str)

            elif cur_time_str == '152100':
                self._request_account_detail()

            elif cur_time_str == '152200':
                self._check_buy_on_closing_cond()

            elif cur_time_str == '152300':
                self._request_multi_code_info()

            elif cur_time_str == "152800":  # 15시 28분.
                for stock in self.data_manager.stock_dic.values():
                    if stock.remained_buy_qty == 0:
                        for strategy in stock.buy_strategy_dic.values():
                            if strategy.enabled:
                                strategy.on_time(cur_time_str)

            elif cur_time_str == '152900':
                logger.info("장마감시간 1분전. 180초 후 계좌정보 확인")
                QTimer().singleShot(180000, self._request_today_earning)
                logger.info("장마감시간 1분전. 200초 후 계좌정보 확인")
                QTimer().singleShot(200000, self._request_account_detail)
                logger.info("장마감시간 1분전. 220초 후 slack 메시지 발송")
                QTimer().singleShot(220000, self._send_account_to_slack)
                logger.info("장마감시간 1분전. 240초 후 전략 정리 후 save")
                QTimer().singleShot(240000, self.arrange_strategy)
                logger.info("장마감시간 1분전. 300초 후 프로그램 종료")
                QTimer().singleShot(300000, self._exit)

        elif real_type == '주식체결':
            price_str = self.ocx.get_comm_real_data(code, Fid.현재가.value)
            cur_price = int(price_str)
            cur_price = cur_price if cur_price >= 0 else cur_price * (-1)

            stock = self.data_manager.get_stock(code)
            stock.cur_price = cur_price
            stock.update_earning_rate()

            if stock.qty > 0 and stock.remained_sell_qty == 0:
                for strategy in stock.sell_strategy_dic.values():
                    if strategy.enabled:
                        strategy.on_price_updated()
            if stock.remained_buy_qty == 0:
                for strategy in stock.buy_strategy_dic.values():
                    if strategy.enabled:
                        strategy.on_price_updated()

            # 장마감 동시호가 시간 되기 전 (3시 18분경)
            cur_time_str = self.ocx.get_comm_real_data(code, Fid.체결시간.value)
            cur_time = int(cur_time_str)
            if self.is_closing_called is False and 151800 < cur_time < 151805:
                logger.info(f'is_closing_called:{self.is_closing_called}. cur_time:{cur_time}')
                for stock in self.data_manager.stock_dic.values():
                    if stock.qty > 0 and stock.remained_sell_qty == 0:
                        for strategy in stock.sell_strategy_dic.values():
                            if strategy.enabled:
                                strategy.on_time(cur_time_str)
                self.is_closing_called = True
                logger.info(f'is_closing_called:{self.is_closing_called}. cur_time:{cur_time}')

    def on_receive_msg(self, scr_no: str, rq_name: str, tr_code: str, msg: str):
        logger.info(f'scr_no:"{scr_no}", rq_name:"{rq_name}", tr_code:"{tr_code}", msg:"{msg}"')

    def on_receive_chejan_data(self, gubun: str, item_cnt: int, fid_list: str):
        """체결 데이터를 받은 시점을 알려준다

        :param gubun: 체결구분 (0:접수/체결 , 1:국내주식 잔고통보, 4:파생상품 잔고통보)
        :param item_cnt: 아이템 개수
        :param fid_list: 데이터리스트 (';'로 구분)
        """
        logger.info(f'gubun:"{gubun}", item_cnt:{item_cnt}, fid_list:"{fid_list}"')
        fid_str_list = fid_list.split(";")
        for fid_str in fid_str_list:
            fid = int(fid_str)
            ret = self.ocx.get_chejan_data(fid)
            key_str = f'{Fid(fid).name}({fid})' if fid in Fid.__members__.values() else f'UNKNOWN({fid_str})'
            logger.debug(f'  {key_str}: "{ret}"')

        code = self.ocx.get_chejan_data(Fid.종목코드.value)
        code = code[1:]  # Remove 'A'
        name = self.ocx.get_chejan_data(Fid.종목명.value)

        if gubun == '0':  # 주문접수 or 주문체결
            order_id = self.ocx.get_chejan_data(Fid.주문번호.value)
            status = self.ocx.get_chejan_data(Fid.주문상태.value)  # '접수' or '체결'
            order_type = self.ocx.get_chejan_data(Fid.매도수구분.value)  # '1':매도, '2':매수
            time_str = self.ocx.get_chejan_data(Fid.주문_체결시간.value)  # 주문/체결시간 (HHMMSSMS)
            time = int(time_str)
            if status == '접수':
                logger.info(
                    f'{name}({code}) 주문접수. order_id:"{order_id}", order_type:"{order_type}", time_str:"{time_str}"')
            if status == '체결':
                remained_qty = self.ocx.get_chejan_data(Fid.미체결수량.value)
                remained_qty = int(remained_qty)
                logger.info(f'{name}({code}) 주문체결. order_id:"{order_id}", order_type:"{order_type}", '
                            f'time_str:"{time_str}", remained_qty:{remained_qty}')
                stock = self.data_manager.get_stock(code)

                if order_type == '1':  # 매도
                    stock.remained_sell_qty = remained_qty

                if order_type == '2':  # 매수
                    stock.remained_buy_qty = remained_qty
                    # TODO: 종목 실시간 등록 및 조건식 실시간 재적용(?)

                if remained_qty == 0 and 90100 < time < 151400:
                    from sns_trade_bot.slack.webhook import MsgSender
                    send_balance_job = Job(MsgSender.send_balance, list(self.data_manager.stock_dic.values()))
                    self.tr_queue.put(send_balance_job)

        elif gubun == '1':  # 잔고통보
            qty = int(self.ocx.get_chejan_data(Fid.보유수량.value))
            order_type = self.ocx.get_chejan_data(Fid.매도_매수구분.value)  # '1':매도, '2':매수
            buy_price = int(self.ocx.get_chejan_data(Fid.매입단가.value))
            logger.info(f'{name}({code}) 잔고통보. order_type:"{order_type}", qty:{qty}, buy_price:{buy_price}')
            stock = self.data_manager.get_stock(code)
            stock.qty = qty
            stock.buy_price = buy_price
            if qty == 0:
                logger.info(f'{name}({code}) 청산 완료!!')
                # TODO: 매수 전략 다른 게 있으면, 계속 실시간 받아야 함.
                self.ocx.set_real_remove(ScnNo.REAL.value, code)
                self.data_manager.remove_stock(code)

    def on_receive_real_condition(self, code: str, event_type: str, cond_name: str, cond_index: str):
        """조검검색 실시간 편입, 이탈 종목을 받을 시점을 알려준다.

        :param code: 종목코드
        :param event_type: 편입("I"), 이탈("D")
        :param cond_name: 조건명
        :param cond_index: 조건명 인덱스
        """
        logger.debug(f'code:{code}, type:{event_type}, cond_name:{cond_name}, cond_index:{cond_index}')
        condition: Condition = self.data_manager.get_cond(int(cond_index))

        if condition.signal_type == SignalType.SELL and event_type == 'I':  # 매도 조건식 편입
            if code not in self.data_manager.stock_dic:
                logger.warning(f'보유 종목 아님. {code}')
                return
            stock = self.data_manager.get_stock(code)
            for sell_strategy in stock.sell_strategy_dic.values():
                if sell_strategy.enabled:
                    sell_strategy.on_condition(int(cond_index), cond_name)

        elif condition.signal_type == SignalType.BUY and event_type == "I":  # 매수 조건식 편입
            pass

    def on_receive_condition_ver(self, ret: int, msg: str):
        logger.debug(f'ret:{ret}, msg:"{msg}"')  # ret: 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
        condition_name_list_str = self.ocx.get_condition_name_list()
        if len(condition_name_list_str) == 0:
            logger.warning(f'len(condition_name_list_str): {len(condition_name_list_str)}')
            return
        logger.debug(f'condition_name_list_str: {condition_name_list_str}')
        if condition_name_list_str[-1] == ';':
            condition_name_list_str = condition_name_list_str[:-1]  # Remove last ';'
        condition_name_list = condition_name_list_str.split(';')
        cond_name_dic = {}
        for name_with_index in condition_name_list:
            temp_list = name_with_index.split('^')
            cond_name_dic[int(temp_list[0])] = temp_list[1]
        logger.debug(f'cond_name_dic: {cond_name_dic}')
        self.data_manager.set_cond_dic(cond_name_dic)

    def on_receive_tr_condition(self, scr_no: str, code_list_str: str, cond_name, index: int, has_next: int):
        logger.debug(f'scr_no:"{scr_no}", code_list_str:"{code_list_str}", cond_name:"{cond_name}",  index:{index}, '
                     f'has_next:{has_next}')
        if len(code_list_str) == 0:
            return

        code_list_str = code_list_str[:-1]  # 마지막 ";" 제거
        code_list = code_list_str.split(';')
        logger.debug("code_list: %s", code_list)
        temp_stock_list = []
        for code in code_list:
            if len(code) == 0:
                continue
            name = self.ocx.get_master_code_name(code)
            temp_stock_list.append(Stock(self.data_manager.listener_list, code, name))
            logger.debug(f'  {name}({code})')
        self.data_manager.set_temp_stock_list(temp_stock_list)
        if scr_no == ScnNo.COND_BUY.value:
            from sns_trade_bot.strategy.buy_on_closing import BuyOnClosing
            for i, stock in enumerate(temp_stock_list):
                # TODO: 후보 종목들을 특정 필드로 정렬해서 개수 제한 (예수금 상황도 확인 필요)
                if i > 10:
                    logger.warning('too many temp_stock. skip further stocks')
                    break
                param_dic = BuyOnClosing.DEFAULT_PARAM
                stock.add_buy_strategy('buy_on_closing', param_dic)
            logger.info('invoke add_all_temp_stock()')
            self.data_manager.add_all_temp_stock()

    def print_tr_data(self, tr_code, record_name, index, item_list):
        logger.debug(f'---- tr_code:"{tr_code}", record_name:"{record_name}", index:{index}')
        for item in item_list:
            out_str = self.ocx.get_comm_data(tr_code, record_name, index, item)
            logger.debug(f'  "{item}" : "{out_str}"')

    # TODO: Reduce duplicated function
    def _request_account_detail(self):
        logger.info(f'account: {self.data_manager.account}')
        self.ocx.set_input_value('계좌번호', self.data_manager.account)
        self.ocx.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.ocx.set_input_value('상장폐지조회구분', '0')  # 0:전체, 1: 상장폐지종목제외
        self.ocx.set_input_value('비밀번호입력매체구분', '00')  # 고정값?
        tr_code = 'OPW00004'  # 계좌평가현황요청
        is_next = 0  # 연속조회요청 여부 (0:조회 , 2:연속)
        return self.ocx.comm_rq_data(RqName.BALANCE.value, tr_code, is_next, ScnNo.BALANCE.value)

    # TODO: Reduce duplicated function
    def _request_today_earning(self):
        logger.info(f'account: {self.data_manager.account}')
        self.ocx.set_input_value('계좌번호', self.data_manager.account)
        self.ocx.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.ocx.set_input_value('종목코드', '')  # 전문 조회할 종목코드
        is_next = 0  # 연속조회요청 여부 (0:조회 , 2:연속)
        return self.ocx.comm_rq_data(RqName.당일손익상세요청.value, TrCode.당일손익상세요청.value, is_next,
                                     ScnNo.당일손익상세요청.value)

    # TODO: Reduce duplicated function
    def _request_multi_code_info(self):
        the_code_list = self.data_manager.get_code_list(HoldType.INTEREST)
        logger.debug(f'the_code_list: {the_code_list}')
        count = len(the_code_list)
        if count == 0:
            logger.error('code_list is empty!!')
            return -1
        code_list_str = ";".join(the_code_list)  # 종목리스트
        is_next = 0  # 연속조회요청 여부
        code_count = count  # 종목개수
        type_flag = 0  # 조회구분 (0: 주식관심종목정보 , 선물옵션관심종목정보)
        rq_name = RqName.INTEREST_CODE.value  # 사용자구분 명
        scn_no = ScnNo.INTEREST.value  # 화면변호
        return self.ocx.comm_kw_rq_data(code_list_str, is_next, code_count, type_flag, rq_name, scn_no)

    def _send_account_to_slack(self):
        from sns_trade_bot.slack.webhook import MsgSender
        MsgSender.send_balance(list(self.data_manager.stock_dic.values()))

    # TODO: Make it private
    def arrange_strategy(self):
        for stock in self.data_manager.stock_dic.values():
            if stock.qty > 0:
                logger.debug(f'clear buy_strategy_dic of {stock.name}')
                stock.buy_strategy_dic.clear()
                if 'sell_stop_loss' not in stock.sell_strategy_dic.keys():
                    logger.debug(f'add sell_stop_loss to {stock.name}')
                    from sns_trade_bot.strategy.sell_stop_loss import SellStopLoss
                    stock.sell_strategy_dic['sell_stop_loss'] = SellStopLoss(stock, SellStopLoss.DEFAULT_PARAM)
        self.data_manager.set_updated(DataType.TABLE_BALANCE)
        self.data_manager.save()

    def _exit(self):
        logger.info('exit SnsTradeBot')
        # TODO: Pass app?
        app.quit()

    def _set_real_reg(self, the_code_list: List[str]):
        code_list_str = ';'.join(the_code_list)
        fid_list = "9001;10;13"  # 종목코드,업종코드;현재가;누적거래량
        real_type = "0"  # 0: 최초 등록, 1: 같은 화면에 종목 추가
        self.ocx.set_real_reg(ScnNo.REAL.value, code_list_str, fid_list, real_type)

    def _check_buy_on_closing_cond(self):
        for cond in self.data_manager.cond_dic.values():
            if cond.signal_type is SignalType.BUY_ON_CLOSING:
                query_type = 0  # 일반조회
                logger.info(f'send_condition(0). ScnNo.COND_BUY. index:{cond.index}, name:{cond.name}')
                ret = self.ocx.send_condition(ScnNo.COND_BUY.value, cond.name, cond.index, query_type)
                logger.debug(f'send_condition(0). ret: {ret}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
