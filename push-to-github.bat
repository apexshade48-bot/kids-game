@echo off
cd /d "%~dp0"
title Push Word Stars to GitHub

where gh >nul 2>&1
if errorlevel 1 (
  echo GitHub CLI not found. Install from: https://cli.github.com/
  pause
  exit /b 1
)

echo.
echo Step 1: GitHub login
echo --------------------
gh auth status >nul 2>&1
if errorlevel 1 (
  echo A browser window will open. Log in as apexshade48-bot
  gh auth login --hostname github.com --git-protocol https --web
)

echo.
echo Step 2: Create repo if needed and push
echo ----------------------------------------
gh repo view apexshade48-bot/Web-app >nul 2>&1
if errorlevel 1 (
  echo Creating repo apexshade48-bot/Web-app ...
  gh repo create apexshade48-bot/Web-app --public --source=. --remote=origin --push
) else (
  echo Pushing to existing repo ...
  git push -u origin main
)

if errorlevel 1 (
  echo.
  echo Push failed. Make sure:
  echo   1. You are logged into GitHub as apexshade48-bot
  echo   2. Repo exists: https://github.com/apexshade48-bot/Web-app
  pause
  exit /b 1
)

echo.
echo SUCCESS! Code is live at:
echo https://github.com/apexshade48-bot/Web-app
pause