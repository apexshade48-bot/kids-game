@echo off
cd /d "%~dp0"
title Word Stars Server

if not exist "venv\" (
  echo Creating virtual environment...
  python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

if not exist ".env" (
  echo.
  echo NOTE: Copy .env.example to .env and set SECRET_KEY before going live.
  echo.
)

REM Allow tablets/phones on Wi-Fi to reach port 5000
netsh advfirewall firewall delete rule name="Word Stars Game Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="Word Stars Game Port 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

echo.
echo ============================================
echo   WORD STARS
echo ============================================
echo.
echo   On THIS computer:
echo     http://127.0.0.1:5000
echo.
echo   On TABLET / PHONE (same Wi-Fi):
echo     Open Chrome or Safari and type the
echo     Wi-Fi link printed below after start.
echo.
echo   Do NOT use localhost on the tablet.
echo   Keep this window OPEN while playing.
echo ============================================
echo.

python app.py
pause
