# slackbot_settings.py should be located in PYTHONPATH

import logging
import sys

from slackbot.bot import Bot


def start():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s|%(filename)s:%(lineno)s (%(funcName)s)] %(message)s')
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    start()
