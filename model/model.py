import logging
import os
import json

logger = logging.getLogger(__name__)


class Stock:
    code = '00000'  # 종목코드
    name = 'UNKNOWN'  # 종목명
    cur_price = 0  # 현재가
    buy_price = 0  # 매입가
    quantity = 0  # 보유수량
    earning_rate = 0.0  # 수익률
    buy_strategy_list = []
    sell_strategy_list = []
    target_quantity = 0  # 목표보유수량

    def __init__(self, the_code):
        self.code = the_code

    def __str__(self):
        return f'({self.code} {self.name} {self.cur_price} {self.buy_price} {self.quantity} {self.target_quantity})'

    def get_dic(self):
        ret = {
            "code": self.code,
            "name": self.name,
            "target_quantity": self.target_quantity
        }
        return ret


class Condition:
    index = -1  # 인덱스
    name = 'temp'  # 조건명
    signal_type = None
    enabled = False


class Model:
    SAVE_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../my_stock_list.json')

    account = '1234'
    account_list = ['1234', '4567']
    condition_list = []
    stock_dic = {}

    def __init__(self):
        pass

    def __str__(self):
        ret_str = '====== UserData =======\n'
        ret_str += f' - account: {self.account}, {self.account_list}\n'
        ret_str += f' - stock_dic[{len(self.stock_dic)}]:\n'
        for k, v in self.stock_dic.items():
            ret_str += f'  {k}: {v}\n'
        return ret_str

    def save(self):
        f = open(Model.SAVE_FILE_PATH, "w", encoding='utf8')
        stock_list = []
        for k, v in self.stock_dic.items():
            stock_list.append(v.get_dic())
        data = json.dumps(stock_list, ensure_ascii=False, indent=4)
        f.write(data)
        f.close()

    def load(self):
        f = open(Model.SAVE_FILE_PATH, "r", encoding='utf8')
        stock_list = json.load(f)
        logger.info(stock_list)
        for loaded_stock in stock_list:
            stock = self.get_stock(loaded_stock['code'])
            stock.name = loaded_stock['name']
            stock.target_quantity = loaded_stock['target_quantity']

    def get_stock(self, the_code):
        if the_code not in self.stock_dic:
            self.stock_dic[the_code] = Stock(the_code)
            logger.debug("new code '%s'. create new stock", the_code)
        return self.stock_dic[the_code]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    model = Model()
    # modelManager.get_stock('0001')
    logger.info(model)
    # modelManager.save()
    model.load()
    logger.info(model)
