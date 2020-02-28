import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellOnCondition(StrategyBase):
    NAME = 'sell_on_condition'
    DEFAULT_THRESHOLD = 0.01  # 1% 이상 수익이 아니라면 팔지 않음

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.threshold = SellOnCondition.DEFAULT_THRESHOLD
        if 'threshold' in the_param_dic:
            self.threshold = the_param_dic['threshold']
        logger.info("%s strategy created for %s", self.NAME, self.stock.name)

    @staticmethod
    def get_default_param_dic():
        return {"threshold": SellOnCondition.DEFAULT_THRESHOLD}

    def get_param_dic(self):
        return {"threshold": self.threshold}

    def on_condition(self, the_index, the_name):
        logger.info("index: %d, condition_name: %s, 종목명: %s", the_index, the_name, self.stock.종목명)
        if self.is_queued:
            logger.info("is_queued. do nothing")
            return

        if self.stock.quantity == 0:
            logger.info("quantity == 0. do nothing")
            return

        earning_rate = self.stock.get_return_rate()
        logger.info("name: %s, earning_rate: %f, cur_price: %d, buy_price: %d, quantity: %d", self.stock.name, earning_rate, self.stock.cur_price, self.stock.buy_price, self.stock.quantity)

        if earning_rate > self.threshold:
            logger.info("ConditionSell!!!! %s name: %s, quantity: %d. earning_rate: %f > threshold: %f", the_name, self.stock.name, self.stock.quantity, earning_rate, self.threshold)
            self.stock.on_sell_signal(self, self.stock.quantity)
