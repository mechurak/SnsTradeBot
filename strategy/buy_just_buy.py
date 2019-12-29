import logging
from strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyJustBuy(StrategyBase):
    NAME = 'buy_just_buy'

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        logger.info("%s strategy created for %s", self.NAME, self.stock.name)

    def on_real_data(self, the_code, the_type, the_data):
        logger.info("JustBuy")
        if self.is_queued:
            logger.info("is_queued. do nothing")
            return

        if self.stock.target_quantity == 0 or self.stock.target_quantity <= self.stock.quantity:
            logger.info("target_quantity: %d, quantity: %d. do nothing", self.stock.target_quantity, self.stock.quantity)
            return

        order_quantity = self.stock.target_quantity - self.stock.quantity
        logger.info("JustBuy!!!! order_quantity: %d", order_quantity)
        self.stock.on_buy_signal(self, order_quantity)
