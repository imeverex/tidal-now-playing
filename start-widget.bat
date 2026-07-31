@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo First run: setting up Python environment, this happens once...
    py -3.12 -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo.
        echo Could not find Python 3.12. Install it first: winget install --id Python.Python.3.12
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
    echo Setup done.
    echo.
)

echo Starting Tidal now-playing widget server...
echo Add this to OBS as a Browser Source: http://127.0.0.1:5959/overlay.html
echo Leave this window open while streaming. Close it to stop the widget.
echo.
".venv\Scripts\python.exe" nowplaying_server.py
pause
