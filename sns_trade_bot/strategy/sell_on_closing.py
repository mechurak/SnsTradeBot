import logging
from sns_trade_bot.strategy.base import StrategyBase

logger = logging.getLogger(__name__)


class SellOnClosing(StrategyBase):
    NAME = 'sell_on_closing'

    def __init__(self, the_stock, the_param_dic):
        super().__init__(the_stock, the_param_dic)
        logger.info(f'{self.NAME} strategy created for {self.stock.name}')

    def on_time(self, cur_time_str):
        logger.info(f'SellOnClosing. time:{cur_time_str}. {self.stock.name}')
        if self.stock.remained_sell_qty:
            logger.info(f'remained_buy_qty:{self.stock.remained_sell_qty}. do nothing')
            return

        if self.stock.qty > 0:
            logger.info(f'SellOnClosing!!!! order_qty:{self.stock.qty}')
            self.stock.on_sell_signal(self.NAME, self.stock.qty)
            self.enabled = False
