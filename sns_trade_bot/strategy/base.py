import logging

logger = logging.getLogger(__name__)


class StrategyBase:
    NAME = 'strategy_base'
    DEFAULT_PARAM = {}
    BUY_STRATEGY_LIST = ['buy_just_buy', 'buy_on_opening']
    SELL_STRATEGY_LIST = ['sell_on_closing', 'sell_on_condition', 'sell_stop_loss']

    def __init__(self, the_stock, the_param_dic):
        self.stock = the_stock
        self.is_queued = False
        logger.info("StrategyBase. %s, %s", the_stock.name, str(the_param_dic))

    @staticmethod
    def get_default_param_dic():
        """
        to provide UI module with default param
        """
        return {}

    def get_param_dic(self):
        return {}

    def on_price_updated(self):
        pass

    def on_condition(self, the_index, the_name):
        pass

    def on_time(self, cur_time_str):
        pass

    def on_tr_data(self, current_price):
        pass
