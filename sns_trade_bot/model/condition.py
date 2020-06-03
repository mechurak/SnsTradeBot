import enum


class SignalType(enum.Enum):
    UNDEFINED = 0
    BUY = 1
    SELL = 2
    BUY_ON_CLOSING = 3


class Condition:
    def __init__(self, index, name):
        self.index = index  # 인덱스
        self.name = name  # 조건명
        self.signal_type: SignalType = SignalType.UNDEFINED

    def __str__(self):
        return f'({self.index} {self.name} {self.signal_type.name})'

    def get_dic(self):
        ret = {
            "index": self.index,
            "name": self.name,
            "signal_type": self.signal_type.name
        }
        return ret
