import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellStopLoss(StrategyBase):
    NAME = 'sell_stop_loss'
    DEFAULT_THRESHOLD = -3.0  # unit: %
    DEFAULT_FROM_TOP = -1.5  # unit: %
    DEFAULT_PARAM = {
        'threshold': DEFAULT_THRESHOLD,
        'from_top': DEFAULT_FROM_TOP,
    }

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        self.threshold = SellStopLoss.DEFAULT_THRESHOLD
        self.from_top = SellStopLoss.DEFAULT_FROM_TOP
        if 'threshold' in the_param_dic:
            self.threshold = the_param_dic['threshold']
        if 'from_top' in the_param_dic:
            self.from_top = the_param_dic['from_top']
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def get_param_dic(self):
        return {
            'threshold': self.threshold,
            'from_top': self.from_top
        }

    def on_price_updated(self):
        if self.stock.remained_sell_qty:
            logger.info(f'remained_buy_qty:{self.stock.remained_sell_qty}. do nothing')
            return

        if self.stock.qty == 0:
            logger.debug('qty == 0. do nothing')
            return

        if self.stock.cur_price > self.stock.top_price:
            self.stock.top_price = self.stock.cur_price

        cur_from_top = (self.stock.cur_price - self.stock.top_price) / self.stock.top_price * 100

        if self.stock.earning_rate < self.threshold:
            logger.info(f'StopLoss!!!! name:{self.stock.name}, qty:{self.stock.qty}. cur_price:{self.stock.cur_price}, '
                        f'buy_price:{self.stock.buy_price}, '
                        f'earning_rate:{self.stock.earning_rate:0.2f} < threshold:{self.threshold}')
            self.stock.on_sell_signal(self.NAME, self.stock.qty)

        elif cur_from_top < self.from_top:
            logger.info(f'FromTop!!!! name:{self.stock.name}, qty:{self.stock.qty}. cur_price:{self.stock.cur_price}, '
                        f'buy_price:{self.stock.buy_price}, '
                        f'cur_from_top:{cur_from_top:0.2f} < from_top:{self.from_top}')
            self.stock.on_sell_signal(self.NAME, self.stock.qty)

