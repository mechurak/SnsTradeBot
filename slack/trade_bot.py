# coding=utf-8
# reference : https://github.com/lins05/slackbot
import json
import re
from slackbot.bot import listen_to


@listen_to('Hello', re.IGNORECASE)
def hello(msg):
    msg.reply("World!!")


@listen_to('help', re.IGNORECASE)
def cmd(msg):
    ret_msg = [
        "balance",
        "history",
        "status",
        "sell all"
    ]
    msg.send("command list\n" + json.dumps(ret_msg, indent=2))


@listen_to('test', re.IGNORECASE)
def test(msg):
    attachments = [{
        "blocks": [
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Approve"
                        },
                        "style": "primary",
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Deny"
                        },
                        "style": "danger",
                        "value": "click_me_123"
                    }
                ]
            }
        ]
    }]
    msg.send_webapi('', json.dumps(attachments))
