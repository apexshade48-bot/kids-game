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

echo Starting Word Stars...
python app.py
pause