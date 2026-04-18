@echo off
title Dacexy Agent v3 Installer
color 0D
echo.
echo  ============================================
echo    Dacexy Desktop Agent v3.0 - Installer
echo    Voice + AI Computer Control
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python not found. Downloading Python 3.11...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile '%TEMP%\python_setup.exe'"
    echo  Installing Python...
    %TEMP%\python_setup.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    echo  Python installed!
    timeout /t 3 >nul
)

echo  Upgrading pip...
python -m pip install --upgrade pip -q

echo  Installing core packages...
pip install pyautogui pillow websockets requests pyttsx3 SpeechRecognition numpy -q

echo  Installing PyAudio for microphone...
pip install pyaudio -q 2>nul
if %errorlevel% neq 0 (
    echo  Trying alternative PyAudio install...
    pip install pipwin -q
    pipwin install pyaudio -q 2>nul
    if %errorlevel% neq 0 (
        echo  Downloading PyAudio wheel...
        powershell -Command "Invoke-WebRequest -Uri 'https://files.pythonhosted.org/packages/PyAudio-0.2.14-cp311-cp311-win_amd64.whl' -OutFile '%TEMP%\PyAudio.whl'" 2>nul
        pip install %TEMP%\PyAudio.whl -q 2>nul
    )
)

echo  Installing system tray support...
pip install pystray -q

echo.
echo  Downloading Dacexy Agent...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\dacexy_agent.py'"

echo  Creating desktop shortcut...
set AGENT_PATH=%USERPROFILE%\dacexy_agent.py
set SHORTCUT=%USERPROFILE%\Desktop\Dacexy Agent.bat

echo @echo off > "%SHORTCUT%"
echo title Dacexy Desktop Agent >> "%SHORTCUT%"
echo echo Starting Dacexy Agent... >> "%SHORTCUT%"
echo python "%AGENT_PATH%" >> "%SHORTCUT%"
echo if %%errorlevel%% neq 0 pause >> "%SHORTCUT%"

echo  Creating startup shortcut (auto-start with Windows)...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DacexyAgent.bat
echo @echo off > "%STARTUP%"
echo start /min python "%AGENT_PATH%" >> "%STARTUP%"

echo.
echo  ============================================
echo    Installation Complete!
echo.
echo    Desktop shortcut: "Dacexy Agent"
echo    Auto-starts with Windows
echo.
echo    Say "Hey Dacexy" to activate voice control
echo  ============================================
echo.
set /p LAUNCH="Launch Dacexy Agent now? (y/n): "
if /i "%LAUNCH%"=="y" (
    start "" "%SHORTCUT%"
)
pause
