@echo off
title Dacexy Agent Installer
echo.
echo  ============================================
echo    Dacexy Desktop Agent - Windows Installer
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    %TEMP%\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    echo Python installed!
)

echo Installing dependencies...
pip install pyautogui pillow websockets requests pystray -q

echo Downloading Dacexy Agent...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\dacexy_agent.py'"

:: Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT=%USERPROFILE%\Desktop\Dacexy Agent.bat
echo @echo off > "%SHORTCUT%"
echo python "%USERPROFILE%\dacexy_agent.py" >> "%SHORTCUT%"
echo pause >> "%SHORTCUT%"

echo.
echo  ============================================
echo    Installation Complete!
echo    Double-click "Dacexy Agent" on your desktop
echo  ============================================
echo.
pause
