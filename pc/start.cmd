@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto ready
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto failed
goto ready
:usepython
python -m venv .venv
if errorlevel 1 goto failed
:ready
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:launch
".venv\Scripts\python.exe" desktop.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Please install Python 3.10-3.12 64-bit from python.org and try again.
echo If dependencies failed, check the error above and your internet connection.
pause
exit /b 1
