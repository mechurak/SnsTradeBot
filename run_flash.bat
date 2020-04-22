@echo on
call %MINICONDA_PATH%\Scripts\activate.bat
:: pywinauto 모듈이 3.7.4 까지만 제대로 동작한다고 해서, 3.7.4로 가상환경 만들었음.
call conda activate py374
:: bat 파일 위치
cd "%~dp0"
python run_flash.py
call conda deactivate