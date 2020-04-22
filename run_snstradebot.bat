@echo on
call %MINICONDA_PATH%\Scripts\activate.bat
:: bat 파일 위치
cd "%~dp0\sns_trade_bot"
set PYTHONPATH=%PYTHONPATH%;%~dp0
python main.py