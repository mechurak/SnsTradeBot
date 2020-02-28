import logging
from strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellStopLoss(StrategyBase):
    NAME = 'sell_stop_loss'
    DEFAULT_THRESHOLD = -0.03

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.threshold = SellStopLoss.DEFAULT_THRESHOLD
        if 'threshold' in the_param_dic:
            self.threshold = the_param_dic['threshold']
        logger.info("%s strategy created for %s", self.NAME, self.stock.name)

    @staticmethod
    def get_default_param_dic():
        return {'threshold': SellStopLoss.DEFAULT_THRESHOLD}

    def get_param_dic(self):
        return {'threshold': self.threshold}

    def on_price_updated(self):
        logger.debug("StopLoss. %s", self.stock.name)
        if self.is_queued:
            logger.info("is_queued. do nothing")
            return

        if self.stock.quantity == 0:
            logger.debug("quantity == 0. do nothing")
            return

        earning_rate = self.stock.get_return_rate()
        logger.debug("name: %s, earning_rate: %f, cur_price: %d, buy_price: %d, quantity: %d", self.stock.name, earning_rate, self.stock.cur_price, self.stock.buy_price, self.stock.quantity)

        if earning_rate < self.threshold:
            logger.info("StopLoss!!!! name: %s, quantity: %d. earning_rate: %f < threshold: %f", self.stock.name, self.stock.quantity, earning_rate, self.threshold)
            self.stock.on_sell_signal(self.stock.quantity)
