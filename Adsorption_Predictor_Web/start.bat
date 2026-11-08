@echo off
rem =====================================================================
rem  Biochar Adsorption Predictor - launcher
rem
rem  This file is deliberately ASCII-only. A .bat containing non-ASCII
rem  text breaks when cmd.exe reads the file under a different codepage
rem  than the one it was saved in - the parser splits Chinese strings into
rem  garbage commands. User-facing Chinese output is printed by app.py,
rem  which handles encoding correctly.
rem
rem  Usage:  start.bat
rem          start.bat --port 8766
rem          start.bat --port 8766 --no-browser
rem =====================================================================

chcp 65001 >nul
setlocal
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

echo ======================================================================
echo   Biochar Adsorption Predictor - starting local service
echo ======================================================================
echo.

rem ---------------------------------------------------------------------
rem  Find a usable interpreter. Every candidate is verified by actually
rem  importing the dependencies, so we never launch into a broken shell.
rem  Only portable candidates are listed here - no other machine's absolute
rem  path is baked in. To add your own, set the PYTHON environment variable,
rem  or append a "call :try" line below.
rem ---------------------------------------------------------------------
set "PYEXE="
call :try "%PYTHON%"
call :try "%~dp0.venv\Scripts\python.exe"
call :try "%USERPROFILE%\.conda\envs\tf\python.exe"
call :try "python"

if not defined PYEXE (
  echo.
  echo [ERROR] No Python interpreter with the required packages was found.
  echo.
  echo   Option 1 - install dependencies, then run this script again:
  echo       pip install -r requirements.txt
  echo.
  echo   Option 2 - point at your interpreter explicitly:
  echo       set PYTHON=D:\path\to\python.exe
  echo.
  echo   Option 3 - create a local virtual environment:
  echo       python -m venv .venv
  echo       .venv\Scripts\pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

echo.
echo Loading models, please wait ...
echo Close this window or press Ctrl+C to stop the service.
echo.

"%PYEXE%" app.py %*
set "EXITCODE=%errorlevel%"

echo.
if not "%EXITCODE%"=="0" (
  echo [INFO] Service exited with code %EXITCODE%.
  echo        If the port is already in use, try:  start.bat --port 8766
)
pause
exit /b %EXITCODE%

rem ---------------------------------------------------------------------
rem  :try <interpreter>  - accept the first candidate that can import all
rem  dependencies; keep the existing choice if one was already accepted.
rem ---------------------------------------------------------------------
:try
if defined PYEXE exit /b 0
if "%~1"=="" exit /b 0
"%~1" -c "import flask, joblib, numpy, pandas, sklearn, xgboost, catboost" >nul 2>nul
if not errorlevel 1 (
  set "PYEXE=%~1"
  echo [OK]   Using interpreter: %~1
) else (
  echo [skip] %~1  -- missing dependencies or unavailable
)
exit /b 0
