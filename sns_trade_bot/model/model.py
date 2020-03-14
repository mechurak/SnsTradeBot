import enum
import logging
import os
import json
import queue
from abc import abstractmethod

logger = logging.getLogger(__name__)


class DataType(enum.Enum):
    COMBO_ACCOUNT = 0
    TABLE_BALANCE = 1
    TABLE_CONDITION = 4
    TABLE_TEMP_STOCK = 5


class ModelListener:
    @abstractmethod
    def on_data_updated(self, data_type: DataType):
        pass

    def on_buy_signal(self, code: str,  qty: int):
        pass

    def on_sell_signal(self, code: str,  qty: int):
        pass


class Stock:
    def __init__(self, the_listener: ModelListener, the_code: str, the_name: str = 'UNDEFINED', the_cur_price: int = 0):
        self.listener = the_listener
        self.code = the_code  # 종목코드
        self.name = the_name  # 종목명
        self.cur_price = the_cur_price  # 현재가
        self.buy_price: int = 0  # 매입가
        self.quantity: int = 0  # 보유수량
        self.earning_rate: float = 0.0  # 수익률
        self.buy_strategy_dic: dict = {}
        self.sell_strategy_dic: dict = {}
        self.target_quantity: int = 0  # 목표보유수량

    def __str__(self):
        return f'({self.code} {self.name} {self.cur_price} {self.buy_price} {self.quantity} ' \
               f'{list(self.buy_strategy_dic.keys())} {list(self.sell_strategy_dic.keys())} {self.target_quantity})'

    def get_dic(self):
        ret = {
            "code": self.code,
            "name": self.name,
            "buy_strategy_dic": {},
            "sell_strategy_dic": {},
            "target_quantity": self.target_quantity
        }
        for k, v in self.buy_strategy_dic.items():
            ret['buy_strategy_dic'][k] = v.get_param_dic()
        for k, v in self.sell_strategy_dic.items():
            ret['sell_strategy_dic'][k] = v.get_param_dic()
        return ret

    def add_buy_strategy(self, the_strategy_name, the_param_dic):
        from sns_trade_bot.strategy.buy_just_buy import BuyJustBuy
        from sns_trade_bot.strategy.buy_on_opening import BuyOnOpening
        if the_strategy_name == 'buy_just_buy':
            self.buy_strategy_dic[the_strategy_name] = BuyJustBuy(self, the_param_dic)
        elif the_strategy_name == 'buy_on_opening':
            self.buy_strategy_dic[the_strategy_name] = BuyOnOpening(self, the_param_dic)
        else:
            logger.error(f'unknown buy strategy "{the_strategy_name}" for "{self.name}"')

    def add_sell_strategy(self, the_strategy_name, the_param_dic):
        from sns_trade_bot.strategy.sell_on_closing import SellOnClosing
        from sns_trade_bot.strategy.sell_stop_loss import SellStopLoss
        from sns_trade_bot.strategy.sell_on_condition import SellOnCondition
        if the_strategy_name == 'sell_on_closing':
            self.sell_strategy_dic[the_strategy_name] = SellOnClosing(self, the_param_dic)
        elif the_strategy_name == 'sell_stop_loss':
            self.sell_strategy_dic[the_strategy_name] = SellStopLoss(self, the_param_dic)
        elif the_strategy_name == 'sell_on_condition':
            self.sell_strategy_dic[the_strategy_name] = SellOnCondition(self, the_param_dic)
        else:
            logger.error(f'unknown sell strategy "{the_strategy_name}" for "{self.name}"')

    def on_buy_signal(self, the_strategy_name: str, the_order_quantity: int):
        logger.info(f'buy_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_quantity}')
        self.listener.on_buy_signal(self.code, the_order_quantity)

    def on_sell_signal(self, the_strategy_name: str, the_order_quantity: int):
        logger.info(f'sell_signal!! {self.name}. strategy:{the_strategy_name}, qty:{the_order_quantity}')
        self.listener.on_sell_signal(self.code, the_order_quantity)


class Condition:
    def __init__(self, index, name):
        self.index = index  # 인덱스
        self.name = name  # 조건명
        self.signal_type = None
        self.enabled = False


class HoldType(enum.Enum):
    INTEREST = 0
    HOLDING = 1
    TARGET = 2
    ALL = 10


class Model:
    SAVE_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../my_stock_list.json')

    order_queue: queue.Queue

    def __init__(self):
        self.account = '1234'
        self.account_list = ['1234', '4567']
        self.condition_list = [Condition(1, 'temp1'), Condition(2, 'temp2')]
        self.stock_dic = {}
        self.temp_stock_list = []
        self.listener_list = []
        self.order_queue = queue.Queue()
        self.selected_code_list = []

    def __str__(self):
        ret_str = '====== UserData =======\n'
        ret_str += f' - account: {self.account}, {self.account_list}\n'
        ret_str += f' - stock_dic[{len(self.stock_dic)}]:\n'
        for k, v in self.stock_dic.items():
            ret_str += f'  {k}: {v}\n'
        return ret_str

    def print(self):
        logger.info('====== UserData =======')
        logger.info(f' - account: {self.account}, {self.account_list}')
        logger.info(f' - stock_dic[{len(self.stock_dic)}]:')
        for k, v in self.stock_dic.items():
            logger.info(f'  {k}: {v}')

    def add_listener(self, the_listener: ModelListener):
        self.listener_list.append(the_listener)

    def save(self):
        logger.info('save')
        f = open(Model.SAVE_FILE_PATH, "w", encoding='utf8')
        stock_list = []
        for k, v in self.stock_dic.items():
            stock_list.append(v.get_dic())
        data = json.dumps(stock_list, ensure_ascii=False, indent=4)
        f.write(data)
        f.close()

    def load(self):
        logger.info('load')
        f = open(Model.SAVE_FILE_PATH, "r", encoding='utf8')
        stock_list = json.load(f)
        logger.info(stock_list)
        for loaded_stock in stock_list:
            stock = self.get_stock(loaded_stock['code'])
            stock.name = loaded_stock['name']
            stock.target_quantity = loaded_stock['target_quantity']
            for k, v in loaded_stock['buy_strategy_dic'].items():
                stock.add_buy_strategy(k, v)
            for k, v in loaded_stock['sell_strategy_dic'].items():
                stock.add_sell_strategy(k, v)
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_BALANCE)

    def get_stock(self, the_code) -> Stock:
        if the_code not in self.stock_dic:
            self.stock_dic[the_code] = Stock(self.order_queue, the_code)
            logger.debug("new code '%s'. create new stock", the_code)
        return self.stock_dic[the_code]

    def remove_stock(self, the_code):
        if the_code not in self.stock_dic:
            logger.error(f'unexpected code:{the_code}')
        del self.stock_dic[the_code]

    def get_code_list(self, the_hold_type):
        if the_hold_type == HoldType.ALL:
            return self.stock_dic.keys()
        code_list = []
        if the_hold_type == HoldType.INTEREST:
            for stock in self.stock_dic.values():
                if stock.quantity == 0:
                    code_list.append(stock.code)
        elif the_hold_type == HoldType.HOLDING:
            for stock in self.stock_dic.values():
                if stock.quantity > 0:
                    code_list.append(stock.code)
        elif the_hold_type == HoldType.TARGET:
            for stock in self.stock_dic.values():
                code_list.append(stock.code)  # For now, append all codes for test
                # TODO: Append the code that has strategy
                # if len(stock.buy_strategy_dic) or len(stock.sell_strategy_dic):
                #     code_list.append(stock.code)
        return code_list

    def set_account_list(self, the_account_list):
        self.account_list = the_account_list
        self.account = the_account_list[0]
        for listener in self.listener_list:
            listener.on_data_updated(DataType.COMBO_ACCOUNT)

    def set_account(self, the_account: str):
        assert the_account in self.account_list, 'unexpected account!!!'
        self.account = the_account

    def set_condition_list(self, the_condition_dic):
        self.condition_list = []
        for index, name in the_condition_dic.items():
            self.condition_list.append(Condition(index, name))
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_CONDITION)

    def get_condition_name_dic(self):
        ret_dic = {}
        for condition in self.condition_list:
            ret_dic[condition.index] = condition.name
        return ret_dic

    def set_temp_stock_list(self, temp_stock_list: list):
        self.temp_stock_list = temp_stock_list
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_TEMP_STOCK)

    def add_all_temp_stock(self):
        for stock in self.temp_stock_list:
            if stock.code not in self.stock_dic:
                self.stock_dic[stock.code] = stock
        self.temp_stock_list = []
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_BALANCE)
            listener.on_data_updated(DataType.TABLE_TEMP_STOCK)

    def set_updated(self, the_data_type: DataType):
        for listener in self.listener_list:
            listener.on_data_updated(the_data_type)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    model = Model()
    stock0001 = model.get_stock('0001')
    stock0001.name = '테스트종목'
    stock0002 = model.get_stock('0002')
    stock0002.name = 'temp종목'
    logger.info(model)
    stock0001.add_buy_strategy('buy_just_buy', {})
    stock0001.add_buy_strategy('buy_on_opening', {})
    logger.info(model)
    stock0001.add_sell_strategy('sell_on_closing', {})
    stock0001.add_sell_strategy('sell_stop_loss', {})
    stock0001.add_sell_strategy('sell_on_condition', {})
    stock0002.add_sell_strategy('sell_stop_loss', {'threshold': -0.05})
    model.save()
    # model.load()
    # stock0001 = model.get_stock('0001')
    # stock0001.add_buy_strategy('temp_strategy', {})
    # stock0001.add_buy_strategy('buy_on_opening', {})
    logger.info(model)
