import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellOnCondition(StrategyBase):
    NAME = 'sell_on_condition'
    DEFAULT_THRESHOLD = 1.0  # 1% 이상 수익이 아니라면 팔지 않음
    DEFAULT_PARAM = {'threshold': DEFAULT_THRESHOLD}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.threshold = SellOnCondition.DEFAULT_THRESHOLD
        if 'threshold' in the_param_dic:
            self.threshold = the_param_dic['threshold']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {'threshold': self.threshold}

    def on_condition(self, the_index, the_name):
        logger.info(f'index:{the_index}, condition_name:{the_name}, 종목명:{self.stock.name}')
        if self.is_queued:
            logger.info('is_queued. do nothing')
            return

        if self.stock.quantity == 0:
            logger.info('quantity == 0. do nothing')
            return

        if self.stock.earning_rate > self.threshold:
            logger.info(f'ConditionSell!!!! {the_name} name:{self.stock.name}, quantity:{self.stock.quantity}, '
                        f'earning_rate:{self.stock.earning_rate:0.2f} > threshold:{self.threshold}')
            self.stock.on_sell_signal(self, self.stock.quantity)
