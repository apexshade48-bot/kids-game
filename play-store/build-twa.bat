@echo off
cd /d "%~dp0"

echo.
echo Word Stars — Play Store TWA build
echo Edit twa-manifest.json first: replace YOUR-HOST with your https site
echo (example host: word-stars.onrender.com  — no https://)
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo Install Node.js from https://nodejs.org/
  pause
  exit /b 1
)

where java >nul 2>&1
if errorlevel 1 (
  echo Install JDK 17 from https://adoptium.net/
  pause
  exit /b 1
)

call npm install -g @bubblewrap/cli
if errorlevel 1 (
  echo npm install failed
  pause
  exit /b 1
)

if not exist android.keystore (
  echo First run: Bubblewrap will ask to create a keystore. Save the password.
)

call bubblewrap update --manifest "%cd%\twa-manifest.json"
if errorlevel 1 (
  echo If update failed, try: bubblewrap init --manifest https://YOUR-HOST/static/manifest.json
  pause
  exit /b 1
)

call bubblewrap build
echo.
echo If it worked, upload app-release-bundle.aab in Play Console - Internal testing.
echo Then copy the keystore SHA-256 into ANDROID_CERT_SHA256 on your server.
pause
