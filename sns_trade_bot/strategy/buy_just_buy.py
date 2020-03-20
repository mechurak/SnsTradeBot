import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyJustBuy(StrategyBase):
    NAME = 'buy_just_buy'
    DEFAULT_PARAM = {}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def on_price_updated(self):
        logger.info('JustBuy')
        if self.is_queued:
            logger.info('is_queued. do nothing')
            return

        if self.stock.target_qty == 0 or self.stock.target_qty <= self.stock.qty:
            logger.info(f'target_qty:{self.stock.target_qty}, qty:{self.stock.qty}. do nothing')
            return

        order_qty = self.stock.target_qty - self.stock.qty
        logger.info(f'JustBuy!!!! order_qty:{order_qty}')
        self.stock.on_buy_signal(self, order_qty)
