import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyOnClosing(StrategyBase):
    NAME = 'buy_on_closing'
    DEFAULT_BUDGET = 300  # 천원
    DEFAULT_PARAM = {'budget': DEFAULT_BUDGET}
    TARGET_TIME = '152500'

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.budget = BuyOnClosing.DEFAULT_BUDGET
        if 'budget' in the_param_dic:
            self.budget = the_param_dic['budget']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {'budget': self.budget}

    def on_time(self, cur_time_str):
        if cur_time_str != self.TARGET_TIME:
            return

        logger.info(f'BuyOnClosing. time:{cur_time_str}. {self.stock.name}')
        if self.stock.remained_buy_qty:
            logger.info(f'remained_buy_qty:{self.stock.remained_buy_qty}. do nothing')
            return

        order_qty = (self.budget * 1000) // self.stock.cur_price
        logger.info(f'budget:{self.budget}, order_qty:{self.stock.order_qty}')

        if order_qty <= 0:
            logger.info(f'order_qty:{order_qty}, qty:{self.stock.qty}. do nothing')
            return

        logger.info(f'BuyOnClosing!!!! order_qty:{order_qty}')
        self.stock.on_buy_signal(self.NAME, order_qty)
        self.enabled = False
