@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv ".venv" >nul 2>&1
    if errorlevel 1 py -3 -m venv ".venv" >nul 2>&1
    if errorlevel 1 python -m venv ".venv" >nul 2>&1
    if errorlevel 1 goto setup_error
)

".venv\Scripts\python.exe" -c "import PyQt6.QtWidgets" >nul 2>&1
if errorlevel 1 (
    echo Installing Film Reviewer dependencies...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_error
)

start "" ".venv\Scripts\pythonw.exe" "%CD%\main.py"
exit /b 0

:setup_error
echo Setup failed. Install Python 3.12, check your internet connection, and try again.
pause
exit /b 1
