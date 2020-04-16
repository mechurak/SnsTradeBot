@echo on
call C:\ProgramData\Miniconda3\Scripts\activate.bat
:: bat 파일 위치
cd "%~dp0\sns_trade_bot"
set PYTHONPATH=%PYTHONPATH%;%~dp0
python main.py
pause