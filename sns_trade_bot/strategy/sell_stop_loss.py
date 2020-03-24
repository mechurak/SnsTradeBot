import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellStopLoss(StrategyBase):
    NAME = 'sell_stop_loss'
    DEFAULT_THRESHOLD = -3.0  # unit: %
    DEFAULT_PARAM = {'threshold': DEFAULT_THRESHOLD}

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.threshold = SellStopLoss.DEFAULT_THRESHOLD
        if 'threshold' in the_param_dic:
            self.threshold = the_param_dic['threshold']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {'threshold': self.threshold}

    def on_price_updated(self):
        if self.is_queued:
            logger.info('is_queued. do nothing')
            return

        if self.stock.qty == 0:
            logger.debug('qty == 0. do nothing')
            return

        if self.stock.earning_rate < self.threshold:
            logger.info(f'StopLoss!!!! name:{self.stock.name}, qty:{self.stock.qty}. '
                        f'earning_rate:{self.stock.earning_rate:0.2f} < threshold:{self.threshold}')
            self.stock.on_sell_signal(self.NAME, self.stock.qty)
