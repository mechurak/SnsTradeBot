import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellOnClosing(StrategyBase):
    NAME = "sell_on_closing"

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        logger.info("%s strategy created for %s", self.NAME, self.stock.name)

    def on_time(self, cur_time_str):
        logger.info("SellOnClosing. time: %s. %s", cur_time_str, self.stock.name)
        if self.is_queued:
            logger.info("is_queued. do nothing")
            return

        if self.stock.quantity > 0:
            logger.info("SellOnClosing!!!! order_quantity: %d", self.stock.quantity)
            self.stock.on_sell_signal(self, self.stock.quantity)
