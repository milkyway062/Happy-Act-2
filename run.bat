@echo off
cd /d "%~dp0"

echo Checking dependencies...
py -3.14 -c "import cv2, numpy, keyboard" 2>nul
if errorlevel 1 (
    echo Some dependencies are missing. Installing now, please wait...
    echo.
    py -3.14 -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        echo Make sure you have an internet connection and Python 3.14 is installed.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Verifying installation...
    py -3.14 -c "import cv2, numpy, keyboard" 2>_err.tmp
    if errorlevel 1 (
        echo ERROR: One or more dependencies could not be installed:
        echo.
        type _err.tmp
        del _err.tmp 2>nul
        echo.
        pause
        exit /b 1
    )
    del _err.tmp 2>nul
    echo All dependencies installed successfully!
    echo.
)

echo Launching macro...
start "HappyMacro" pyw -3.14 gui.py
