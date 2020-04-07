import logging

logger = logging.getLogger(__name__)


class Stock:
    COMMISSION_FACTOR = 0.997  # 대략적으로 수수료 및 세금 고려

    def __init__(self, the_listener_list: list, the_code: str, the_name: str = 'UNDEFINED', the_cur_price: int = 0):
        self.listener_list = the_listener_list
        self.code = the_code  # 종목코드
        self.name = the_name  # 종목명
        self.cur_price = the_cur_price  # 현재가
        self.top_price = 0  # 보유중 최고가
        self.buy_price: int = 0  # 매입가
        self.qty: int = 0  # 보유수량
        self.earning_rate: float = 0.0  # 수익률 (%)
        self.buy_strategy_dic: dict = {}
        self.sell_strategy_dic: dict = {}
        self.target_qty: int = 0  # 목표보유수량
        self.remained_buy_qty: int = 0
        self.remained_sell_qty: int = 0

    def __str__(self):
        return f'({self.code} {self.name} {self.cur_price} {self.buy_price} {self.top_price} {self.qty} ' \
               f'{list(self.buy_strategy_dic.keys())} {list(self.sell_strategy_dic.keys())} {self.target_qty})'

    def get_dic(self):
        ret = {
            "code": self.code,
            "name": self.name,
            "buy_strategy_dic": {},
            "sell_strategy_dic": {},
            "target_qty": self.target_qty
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
        from sns_trade_bot.strategy.sell_just_sell import SellJustSell
        if the_strategy_name == 'sell_on_closing':
            self.sell_strategy_dic[the_strategy_name] = SellOnClosing(self, the_param_dic)
        elif the_strategy_name == 'sell_stop_loss':
            self.sell_strategy_dic[the_strategy_name] = SellStopLoss(self, the_param_dic)
        elif the_strategy_name == 'sell_on_condition':
            self.sell_strategy_dic[the_strategy_name] = SellOnCondition(self, the_param_dic)
        elif the_strategy_name == SellJustSell.NAME:
            self.sell_strategy_dic[the_strategy_name] = SellJustSell(self, the_param_dic)
        else:
            logger.error(f'unknown sell strategy "{the_strategy_name}" for "{self.name}"')

    def on_buy_signal(self, the_strategy_name: str, the_order_qty: int):
        logger.info(f'buy_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_qty}')
        for listener in self.listener_list:
            listener.on_buy_signal(self.code, the_order_qty)
        self.remained_buy_qty = the_order_qty

    def on_sell_signal(self, the_strategy_name: str, the_order_qty: int):
        logger.info(f'sell_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_qty}')
        for listener in self.listener_list:
            listener.on_sell_signal(self.code, the_order_qty)
        self.remained_sell_qty = the_order_qty

    def update_earning_rate(self):
        if self.qty == 0:
            self.earning_rate = 0.0
        else:
            self.earning_rate = (self.cur_price * self.COMMISSION_FACTOR - self.buy_price) / self.buy_price * 100
