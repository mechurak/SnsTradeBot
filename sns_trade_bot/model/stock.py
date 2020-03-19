import logging

logger = logging.getLogger(__name__)


class Stock:
    def __init__(self, the_listener_list: list, the_code: str, the_name: str = 'UNDEFINED', the_cur_price: int = 0):
        self.listener_list = the_listener_list
        self.code = the_code  # 종목코드
        self.name = the_name  # 종목명
        self.cur_price = the_cur_price  # 현재가
        self.buy_price: int = 0  # 매입가
        self.quantity: int = 0  # 보유수량
        self.earning_rate: float = 0.0  # 수익률 (%)
        self.buy_strategy_dic: dict = {}
        self.sell_strategy_dic: dict = {}
        self.target_quantity: int = 0  # 목표보유수량

    def __str__(self):
        return f'({self.code} {self.name} {self.cur_price} {self.buy_price} {self.quantity} ' \
               f'{list(self.buy_strategy_dic.keys())} {list(self.sell_strategy_dic.keys())} {self.target_quantity})'

    def get_dic(self):
        ret = {
            "code": self.code,
            "name": self.name,
            "buy_strategy_dic": {},
            "sell_strategy_dic": {},
            "target_quantity": self.target_quantity
        }
        for k, v in self.buy_strategy_dic.items():
            ret['buy_strategy_dic'][k] = v.get_param_dic()
        for k, v in self.sell_strategy_dic.items():
            ret['sell_strategy_dic'][k] = v.get_param_dic()
        return ret

    def add_buy_strategy(self, the_strategy_name, the_param_dic):
        from sns_trade_bot.strategy.buy_just_buy import BuyJustBuy
        from sns_trade_bot.strategy.buy_on_opening import BuyOnOpening
        if the_strategy_name == 'buy_just_buy':
            self.buy_strategy_dic[the_strategy_name] = BuyJustBuy(self, the_param_dic)
        elif the_strategy_name == 'buy_on_opening':
            self.buy_strategy_dic[the_strategy_name] = BuyOnOpening(self, the_param_dic)
        else:
            logger.error(f'unknown buy strategy "{the_strategy_name}" for "{self.name}"')

    def add_sell_strategy(self, the_strategy_name, the_param_dic):
        from sns_trade_bot.strategy.sell_on_closing import SellOnClosing
        from sns_trade_bot.strategy.sell_stop_loss import SellStopLoss
        from sns_trade_bot.strategy.sell_on_condition import SellOnCondition
        if the_strategy_name == 'sell_on_closing':
            self.sell_strategy_dic[the_strategy_name] = SellOnClosing(self, the_param_dic)
        elif the_strategy_name == 'sell_stop_loss':
            self.sell_strategy_dic[the_strategy_name] = SellStopLoss(self, the_param_dic)
        elif the_strategy_name == 'sell_on_condition':
            self.sell_strategy_dic[the_strategy_name] = SellOnCondition(self, the_param_dic)
        else:
            logger.error(f'unknown sell strategy "{the_strategy_name}" for "{self.name}"')

    def on_buy_signal(self, the_strategy_name: str, the_order_quantity: int):
        logger.info(f'buy_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_quantity}')
        for listener in self.listener_list:
            listener.on_buy_signal(self.code, the_order_quantity)

    def on_sell_signal(self, the_strategy_name: str, the_order_quantity: int):
        logger.info(f'sell_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_quantity}')
        for listener in self.listener_list:
            listener.on_sell_signal(self.code, the_order_quantity)

    def get_cur_earning_rate(self) -> float:
        if not self.buy_price:
            return 0

        # 매수수수료 = 매입금액 * 매체수수료(0.015 %)(10 원미만 절사)
        매수수수료 = (self.buy_price * self.quantity) * 0.00015
        매수수수료 = int(매수수수료 // 10) * 10  # (10원 미만 절사)

        # 매도수수료 = 현재가 * 수량 * 매체수수료(0.015 %)(10 원미만 절사)
        매도수수료 = self.cur_price * self.quantity * 0.00015
        매도수수료 = int(매도수수료 // 10) * 10  # (10원 미만 절사)

        # 제세금 = 현재가 * 수량 * 0.3 % (원미만 절사)
        세금 = int(self.cur_price * self.quantity * 0.003)

        # 평가금액 = (현재가 * 수량) - 매수가계산 수수료 - 매도가계산 수수료 - 제세금 가계산
        평가금액 = (self.cur_price * self.quantity) - 매수수수료 - 매도수수료 - 세금

        # 평가손익 = 평가금액 - 매입금액
        평가손익 = 평가금액 - (self.buy_price * self.quantity)

        earning_rate = 평가손익 / (self.buy_price * self.quantity) * 100

        return earning_rate
