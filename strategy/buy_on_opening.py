import logging
from strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyOnOpening(StrategyBase):
    NAME = 'buy_on_opening'
    DEFAULT_BUDGET = 30  # 만원

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.budget = BuyOnOpening.DEFAULT_BUDGET
        if 'budget' in the_param_dic:
            self.budget = the_param_dic['budget']
        logger.info("%s strategy created for %s", self.NAME, self.stock.name)

    @staticmethod
    def get_default_param_dic():
        return {"budget": BuyOnOpening.DEFAULT_BUDGET}

    def get_param_dic(self):
        return {"budget": self.budget}

    def on_tr_data(self, current_price):
        # TODO: 동시호가때 너무 올랐을 경우 대비 필요함 (현재가에 몇 프로 더해서 계산?)
        self.stock.target_quantity = (self.budget * 10000) // self.stock.cur_price
        logger.info("budget: %d, target_quantity: %d", self.budget, self.stock.target_quantity)

    def on_time(self, cur_time_str):
        logger.info("BuyOnOpening. time: %s. %s", cur_time_str, self.stock.name)
        if self.is_queued:
            logger.info("is_queued. do nothing")
            return

        if not self.stock.target_quantity:
            return

        order_quantity = self.stock.target_quantity - self.stock.quantity

        if self.stock.target_quantity == 0 or order_quantity <= 0:
            logger.info("target_quantity: %d, quantity: %d. do nothing", self.stock.target_quantity, self.stock.quantity)
            return

        logger.info("BuyOnOpening!!!! order_quantity: %d", order_quantity)
        self.stock.on_buy_signal(self, order_quantity)
