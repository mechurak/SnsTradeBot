import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellJustSell(StrategyBase):
    NAME = 'sell_just_sell'
    DEFAULT_QTY_PERCENT = 100
    DEFAULT_PARAM = {'qty_percent': DEFAULT_QTY_PERCENT}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.qty_percent = SellJustSell.DEFAULT_QTY_PERCENT
        if 'qty_percent' in the_param_dic:
            self.qty_percent = the_param_dic['qty_percent']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def on_price_updated(self):
        logger.info('JustSell')
        if self.stock.remained_sell_qty:
            logger.info(f'remained_buy_qty:{self.stock.remained_sell_qty}. do nothing')
            return

        order_qty = self.stock.qty * self.qty_percent // 100
        if order_qty == 0:
            logger.warning(f'order_qty:{order_qty}, qty:{self.stock.qty}, qty_percent:{self.qty_percent}. do nothing')
            return
        logger.info(f'JustSell!!!! order_qty:{order_qty}, qty:{self.stock.qty}, qty_percent:{self.qty_percent}')
        self.stock.on_sell_signal(self.NAME, order_qty)
        self.enabled = False
