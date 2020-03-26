from typing import List

import requests
from keys import webhook_url
from sns_trade_bot.model.stock import Stock


class MsgSender:
    @staticmethod
    def send_balance(stock_list: List[Stock]):
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "현재잔고"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }

        for stock in stock_list:
            block = {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f'`{stock.name}` ({stock.code})'
                    },
                    {
                        "type": "mrkdwn",
                        "text": f'현재가: {stock.cur_price}, 매입가: {stock.buy_price}'
                    },
                    {
                        "type": "mrkdwn",
                        "text": f'수량: {stock.qty}, 수익율: {stock.earning_rate:.1f}%'
                    }
                ]
            }
            payload['blocks'].append(block)
            payload['blocks'].append({"type": "divider"})

        requests.post(webhook_url, json=payload)

    @staticmethod
    def send_msg(msg):
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": msg
                    }
                }
            ]
        }
        requests.post(webhook_url, json=payload)


if __name__ == "__main__":
    temp_stock_list = []

    stock1 = Stock([], '12345', '테스트종목1', 12000)
    stock1.buy_price = 10000
    stock1.qty = 10
    stock1.earning_rate = 20
    temp_stock_list.append(stock1)

    stock2 = Stock([], '45677', '테스트종목2', 90000)
    stock2.buy_price = 100000
    stock2.qty = 10
    stock2.earning_rate = -10
    temp_stock_list.append(stock2)

    MsgSender.send_balance(temp_stock_list)
    # send_order_result('test', 1, 10000)
