@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Install Node.js 18 or newer, then open this file again.
  pause
  exit /b 1
)
echo Open http://localhost:4173/ in your browser.
node tools/dev-server.mjs
pause
