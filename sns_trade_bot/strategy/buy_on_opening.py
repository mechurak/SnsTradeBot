import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class BuyOnOpening(StrategyBase):
    NAME = 'buy_on_opening'
    DEFAULT_BUDGET = 30  # 만원
    DEFAULT_PARAM = {'budget': DEFAULT_BUDGET}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.budget = BuyOnOpening.DEFAULT_BUDGET
        if 'budget' in the_param_dic:
            self.budget = the_param_dic['budget']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {'budget': self.budget}

    def on_tr_data(self, current_price):
        # TODO: 동시호가때 너무 올랐을 경우 대비 필요함 (현재가에 몇 프로 더해서 계산?)
        self.stock.target_quantity = (self.budget * 10000) // self.stock.cur_price
        logger.info(f'budget:{self.budget}, target_quantity:{self.stock.target_quantity}')

    def on_time(self, cur_time_str):
        logger.info(f'BuyOnOpening. time:{cur_time_str}. {self.stock.name}')
        if self.is_queued:
            logger.info('is_queued. do nothing')
            return

        if not self.stock.target_quantity:
            return

        order_quantity = self.stock.target_quantity - self.stock.quantity

        if self.stock.target_quantity == 0 or order_quantity <= 0:
            logger.info(f'target_quantity:{self.stock.target_quantity}, quantity:{self.stock.quantity}. do nothing')
            return

        logger.info(f'BuyOnOpening!!!! order_quantity:{order_quantity}')
        self.stock.on_buy_signal(self, order_quantity)
