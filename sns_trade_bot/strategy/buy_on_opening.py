import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyOnOpening(StrategyBase):
    NAME = 'buy_on_opening'
    DEFAULT_BUDGET = 300  # 천원
    DEFAULT_PARAM = {'budget': DEFAULT_BUDGET}
    TARGET_TIME = '085500'

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.budget = BuyOnOpening.DEFAULT_BUDGET
        if 'budget' in the_param_dic:
            self.budget = the_param_dic['budget']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {'budget': self.budget}

    def on_time(self, cur_time_str):
        if cur_time_str != self.TARGET_TIME:
            return

        logger.info(f'BuyOnOpening. time:"{cur_time_str}". {self.stock.name}({self.stock.code}), '
                    f' cur_price:{self.stock.cur_price}, qty:{self.stock.qty}')

        order_qty = (self.budget * 1000) // self.stock.cur_price
        logger.info(f'budget:{self.budget}, order_qty:{order_qty}')

        if order_qty <= 0:
            logger.info(f'qty:{self.stock.qty}. do nothing')
            return

        logger.info(f'BuyOnOpening!!!! order_qty:{order_qty}')
        self.stock.on_buy_signal(self.NAME, order_qty)
        self.enabled = False
