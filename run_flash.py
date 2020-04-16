# reference: https://wikidocs.net/5856
import logging
import sys
import time
import os
from datetime import datetime

from pywinauto import application
from pywinauto import timings
from keys import KIWOOM_PW, CERT_PW


# Setup root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s[%(levelname)8s](%(filename)20s:%(lineno)-4s %(funcName)-35s) %(message)s')
LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
file_name = LOG_DIR + "/" + datetime.now().strftime("%Y%m%d-%H%M%S_flash") + ".log"

file_handler = logging.FileHandler(file_name, "a", "utf-8")
stream_handler = logging.StreamHandler(stream=sys.stdout)
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.info(f'file_name: {file_name}')

# Run KiwoomFlash3
app = application.Application()
app.start('C:/KiwoomFlash3/Bin/NKMiniStarter.exe')

title = '번개3 Login'
dlg = timings.wait_until_passes(20, 0.5, lambda: app.window(title=title))
logger.info(dlg)

pass_ctrl = dlg.Edit2
pass_ctrl.set_focus()
pass_ctrl.set_edit_text(KIWOOM_PW)

cert_ctrl = dlg.Edit3
cert_ctrl.set_focus()
cert_ctrl.set_edit_text(CERT_PW)

btn_ctrl = dlg.Button0
btn_ctrl.click()
logger.info('로그인 클릭')

time.sleep(180)
logger.info('taskkill...')
os.system("taskkill /im nkmini.exe")
logger.info('after taskkill')
