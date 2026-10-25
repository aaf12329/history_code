@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 goto missing_node
where npm >nul 2>nul
if errorlevel 1 goto missing_node
node -e "if(Number(process.versions.node.split('.')[0]) < 24) { console.error('Node.js 24 or newer is required.'); process.exit(1); }"
if errorlevel 1 goto failed
if exist "node_modules\.package-lock.json" goto preview
call npm ci --no-audit --no-fund
if errorlevel 1 goto failed
:preview
echo Starting frontend preview only. Open the Local URL printed below.
echo Keep this window open. Press Ctrl+C to stop.
call npm run dev
set "PREVIEW_EXIT=%ERRORLEVEL%"
pause
exit /b %PREVIEW_EXIT%
:missing_node
echo Please install Node.js 24 or newer, including npm, then run this file again.
pause
exit /b 1
:failed
set "PREVIEW_EXIT=%ERRORLEVEL%"
echo Preview setup failed. Read the error above, fix it and retry.
pause
exit /b %PREVIEW_EXIT%
