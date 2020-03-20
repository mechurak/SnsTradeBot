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

        if self.stock.target_quantity == 0 or self.stock.target_quantity <= self.stock.quantity:
            logger.info(f'target_quantity:{self.stock.target_quantity}, quantity:{self.stock.quantity}. do nothing')
            return

        order_quantity = self.stock.target_quantity - self.stock.quantity
        logger.info(f'JustBuy!!!! order_quantity:{order_quantity}')
        self.stock.on_buy_signal(self, order_quantity)
