import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyJustBuy(StrategyBase):
    NAME = 'buy_just_buy'
    DEFAULT_BUDGET = 300  # 천원
    DEFAULT_PARAM = {'budget': DEFAULT_BUDGET}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.budget = BuyJustBuy.DEFAULT_BUDGET
        if 'budget' in the_param_dic:
            self.budget = the_param_dic['budget']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def on_price_updated(self):
        logger.info('JustBuy')
        if self.stock.remained_buy_qty:
            logger.info(f'remained_buy_qty:{self.stock.remained_buy_qty}. do nothing')
            return

        self.stock.target_qty = (self.budget * 1000) // self.stock.cur_price
        logger.info(f'budget:{self.budget}, target_qty:{self.stock.target_qty}')
        order_qty = self.stock.target_qty - self.stock.qty
        logger.info(f'JustBuy!!!! order_qty:{order_qty}')
        self.stock.on_buy_signal(self.NAME, order_qty)
