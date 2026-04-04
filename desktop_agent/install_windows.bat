

@echo off
echo ====================================
echo    Dacexy Desktop Agent Installer
echo ====================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Downloading Python 3.11...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo Python installed successfully.
)

echo.
echo Installing Dacexy Agent dependencies...
pip install requests pyautogui pillow websockets SpeechRecognition pyttsx3 keyboard mouse psutil >nul 2>&1
echo Dependencies installed.

echo.
echo Downloading Dacexy Agent...
curl -o dacexy_agent.py https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py

echo.
set /p TOKEN="Enter your Dacexy Agent Token (from Settings page): "

echo {"token": "%TOKEN%", "server": "https://dacexy-backend-v7ku.onrender.com"} > config.json

echo.
echo Starting Dacexy Agent...
echo The agent will run in the background.
echo Say "Hey Dacexy" to activate voice commands.
echo.
python dacexy_agent.py
pause
