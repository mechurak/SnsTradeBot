import enum
import logging
import os
import json
import sys
from abc import abstractmethod
from typing import Dict, List

from sns_trade_bot.model.stock import Stock
from sns_trade_bot.model.condition import Condition, SignalType


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

    @abstractmethod
    def on_buy_signal(self, code: str, qty: int):
        pass

    @abstractmethod
    def on_sell_signal(self, code: str, qty: int):
        pass


class HoldType(enum.Enum):
    INTEREST = 0
    HOLDING = 1
    TARGET = 2
    ALL = 10


class DataManager:
    SAVE_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../my_stock_list.json')

    def __init__(self):
        self.account: str = '1234'
        self.account_list: List[str] = ['1234', '4567']
        self.cond_dic: Dict[int, Condition] = {1: Condition(1, 'temp1'), 2: Condition(2, 'temp2')}
        self.stock_dic: Dict[str, Stock] = {}
        self.temp_stock_list: List[Stock] = []
        self.listener_list: List[ModelListener] = []
        self.selected_code_list: List[str] = []

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
        logger.info(f' - cond_dic[{len(self.cond_dic)}]:')
        for k, v in self.cond_dic.items():
            logger.info(f'  {k}: {v}')
        # from sns_trade_bot.slack.webhook import MsgSender
        # MsgSender.send_balance(list(self.stock_dic.values()))

    def add_listener(self, the_listener: ModelListener):
        self.listener_list.append(the_listener)

    def save(self):
        logger.info('save')
        f = open(DataManager.SAVE_FILE_PATH, "w", encoding='utf8')
        stock_list = []
        for k, v in self.stock_dic.items():
            stock_list.append(v.get_dic())
        data = json.dumps(stock_list, ensure_ascii=False, indent=4)
        f.write(data)
        f.close()

    def load(self):
        logger.info('load')
        f = open(DataManager.SAVE_FILE_PATH, "r", encoding='utf8')
        stock_list = json.load(f)
        logger.info(stock_list)
        for loaded_stock in stock_list:
            stock = self.get_stock(loaded_stock['code'])
            stock.name = loaded_stock['name']
            stock.target_qty = loaded_stock['target_qty']
            for k, v in loaded_stock['buy_strategy_dic'].items():
                stock.add_buy_strategy(k, v)
            for k, v in loaded_stock['sell_strategy_dic'].items():
                stock.add_sell_strategy(k, v)
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_BALANCE)

    def get_stock(self, the_code) -> Stock:
        if the_code not in self.stock_dic:
            self.stock_dic[the_code] = Stock(self.listener_list, the_code)
            logger.debug(f'new code {the_code}. create new Stock')
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
                if stock.qty == 0:
                    code_list.append(stock.code)
        elif the_hold_type == HoldType.HOLDING:
            for stock in self.stock_dic.values():
                if stock.qty > 0:
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

    def set_cond_dic(self, cond_name_dic: Dict[int, str]):
        remained_cond_index_set = set(self.cond_dic.keys())
        for index, name in cond_name_dic.items():
            self.cond_dic[index] = self.get_cond(index)
            self.cond_dic[index].name = name
            if index in remained_cond_index_set:
                remained_cond_index_set.remove(index)
        for index in remained_cond_index_set:
            logger.debug(f'Remove remained index {index}:{self.cond_dic[index].name} from cond_dic.')
            del self.cond_dic[index]
        for listener in self.listener_list:
            listener.on_data_updated(DataType.TABLE_CONDITION)

    def get_cond(self, the_index: int) -> Condition:
        if the_index not in self.cond_dic:
            self.cond_dic[the_index] = Condition(the_index, 'UNDEFINED')
            logger.debug(f'new index {the_index}. create new Condition')
        return self.cond_dic[the_index]

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
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s[%(levelname)8s](%(filename)20s:%(lineno)-4s %(funcName)-35s) %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    data_manager = DataManager()
    stock0001 = data_manager.get_stock('0001')
    stock0001.name = '테스트종목'
    stock0002 = data_manager.get_stock('0002')
    stock0002.name = 'temp종목'
    logger.info(data_manager)
    stock0001.add_buy_strategy('buy_just_buy', {})
    stock0001.add_buy_strategy('buy_on_opening', {})
    logger.info(data_manager)
    stock0001.add_sell_strategy('sell_on_closing', {})
    stock0001.add_sell_strategy('sell_stop_loss', {})
    stock0001.add_sell_strategy('sell_on_condition', {})
    stock0002.add_sell_strategy('sell_stop_loss', {'threshold': -0.05})
    data_manager.save()
    # data_manager.load()
    # stock0001 = data_manager.get_stock('0001')
    # stock0001.add_buy_strategy('temp_strategy', {})
    # stock0001.add_buy_strategy('buy_on_opening', {})
    logger.info(data_manager)
