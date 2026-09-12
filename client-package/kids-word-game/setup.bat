@echo off
cd /d "%~dp0"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Setup done! Run: python app.py
echo On this PC: http://localhost:5000
echo On tablet/phone: use the Wi-Fi link shown in the terminal
pause
