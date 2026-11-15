@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv ".venv" >nul 2>&1
    if errorlevel 1 py -3 -m venv ".venv" >nul 2>&1
    if errorlevel 1 python -m venv ".venv" >nul 2>&1
    if errorlevel 1 goto build_error
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto build_error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name FilmReviewer main.py
if errorlevel 1 goto build_error

echo Windows app ready: dist\FilmReviewer\FilmReviewer.exe
echo Keep the entire FilmReviewer folder together when moving it.
pause
exit /b 0

:build_error
echo Build failed. Install Python 3.12, check your internet connection, and try again.
pause
exit /b 1
