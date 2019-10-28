import logging
from datetime import datetime


class Singleton:
    __instance = None

    @classmethod
    def __get_instance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__get_instance
        return cls.__instance


class MyLogger(Singleton):
    def __init__(self):
        self._logger = logging.getLogger("SnsTradeBot")
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s (%(funcName)s) %(message)s')

        log_dir = "log"
        import os
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_name = log_dir + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
        file_handler = logging.FileHandler(file_name, "a", "utf-8")
        stream_handler = logging.StreamHandler()

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(stream_handler)

    def logger(self):
        return self._logger
