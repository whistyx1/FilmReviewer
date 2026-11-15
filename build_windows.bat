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

set "APP_EXE=%CD%\dist\FilmReviewer\FilmReviewer.exe"
if not exist "%APP_EXE%" goto build_error

echo Build complete. Launching Film Reviewer...
echo Keep the entire dist\FilmReviewer folder together when moving it.
start "" "%APP_EXE%"
if errorlevel 1 goto launch_error
exit /b 0

:launch_error
echo The build succeeded, but Windows could not launch the app.
echo Open dist\FilmReviewer\FilmReviewer.exe manually and check for errors.
pause
exit /b 1

:build_error
echo Build failed. Read the error messages above, then try again.
pause
exit /b 1
