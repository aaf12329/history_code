@echo off
rem =====================================================================
rem  Biochar Adsorption Predictor - one-click deployment
rem
rem  Creates a virtual environment in the project root and installs the
rem  dependencies listed in deploy.json. Afterwards start.bat will pick
rem  up .venv automatically, so no manual activation is needed.
rem
rem  This file is deliberately ASCII-only: a .bat containing non-ASCII
rem  text breaks when cmd.exe reads the file under a different codepage.
rem  All Chinese output is printed by deploy.py instead.
rem
rem  Usage:  deploy.bat
rem          deploy.bat --dry-run          show commands, change nothing
rem          deploy.bat --recreate         rebuild the environment
rem          deploy.bat --index-url https://pypi.org/simple
rem =====================================================================

chcp 65001 >nul
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

echo ======================================================================
echo   Biochar Adsorption Predictor - deploying local environment
echo ======================================================================
echo.

rem ---------------------------------------------------------------------
rem  Find a Python interpreter to bootstrap with. Only the standard
rem  library is required here - dependencies get installed into .venv.
rem ---------------------------------------------------------------------
set "BOOT="
call :try "%PYTHON%"
call :try "py"
call :try "python"

if not defined BOOT (
  echo [ERROR] No usable Python interpreter was found.
  echo.
  echo   Install Python 3.9 or newer from https://www.python.org/downloads/
  echo   and make sure "Add python.exe to PATH" is checked during setup.
  echo.
  echo   If Python is installed but not on PATH, set it explicitly:
  echo       set PYTHON=D:\path\to\python.exe
  echo   then run this script again.
  echo.
  pause
  exit /b 1
)

echo [OK]   Bootstrapping with: %BOOT%
echo.

"%BOOT%" deploy.py %*
set "EXITCODE=%errorlevel%"

echo.
if "%EXITCODE%"=="0" (
  echo [DONE] Environment ready. Double-click start.bat to launch the service.
) else (
  echo [FAIL] Deployment did not finish. See the messages above.
  echo        Config file: deploy.json
)
echo.
pause
exit /b %EXITCODE%

rem ---------------------------------------------------------------------
rem  :try <interpreter>  - accept the first candidate that runs and is
rem  Python 3.9+. Keeps an already accepted candidate.
rem ---------------------------------------------------------------------
:try
if defined BOOT exit /b 0
if "%~1"=="" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 set "BOOT=%~1"
exit /b 0
