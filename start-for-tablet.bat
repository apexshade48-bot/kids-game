@echo off
:: Run this on the PC so the tablet can open Word Stars on Wi-Fi.
:: Right-click -> Run as administrator  (needed for firewall)

cd /d "%~dp0"
title Word Stars - Tablet Mode

echo.
echo ================================================
echo   WORD STARS - START FOR TABLET
echo ================================================
echo.

:: Open Windows Firewall for port 5000 (all network profiles)
netsh advfirewall firewall delete rule name="Word Stars Game Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="Word Stars Game Port 5000" dir=in action=allow protocol=TCP localport=5000 profile=any >nul 2>&1
if %ERRORLEVEL%==0 (
  echo [OK] Firewall: port 5000 allowed
) else (
  echo [!] Firewall rule may need Administrator.
  echo     Right-click this file -^> Run as administrator
  echo.
)

:: Optional: mark Wi-Fi as Private if allowed
powershell -NoProfile -Command "try { Get-NetConnectionProfile | Where-Object InterfaceAlias -like '*Wi-Fi*' | Set-NetConnectionProfile -NetworkCategory Private; Write-Host '[OK] Wi-Fi profile set to Private' } catch { Write-Host '[i] Could not change Wi-Fi to Private (OK to ignore)' }"

if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo.
echo Starting server...
echo Keep this window OPEN while the tablet is playing.
echo.
echo On THIS PC:     http://127.0.0.1:5000
echo On TABLET:      use the Wi-Fi link printed below
echo                 (NOT localhost)
echo ================================================
echo.

python -u app.py
echo.
echo Server stopped.
pause
