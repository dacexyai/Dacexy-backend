@echo off
title Dacexy Desktop Agent Installer
echo.
echo  ██████╗  █████╗  ██████╗███████╗██╗  ██╗██╗   ██╗
echo  ██╔══██╗██╔══██╗██╔════╝██╔════╝╚██╗██╔╝╚██╗ ██╔╝
echo  ██║  ██║███████║██║     █████╗   ╚███╔╝  ╚████╔╝ 
echo  ██║  ██║██╔══██║██║     ██╔══╝   ██╔██╗   ╚██╔╝  
echo  ██████╔╝██║  ██║╚██████╗███████╗██╔╝ ██╗   ██║   
echo  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝   
echo.
echo  Desktop Agent Installer v3.0
echo  ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Installing Python...
    echo Please download Python from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during install.
    pause
    start https://python.org/downloads
    exit /b 1
)

echo [OK] Python found.
echo.

:: Install dependencies
echo [1/4] Installing dependencies...
pip install websockets pyautogui requests pillow speechrecognition pyaudio psutil --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

:: Create agent folder
echo [2/4] Setting up agent folder...
if not exist "%USERPROFILE%\DacexyAgent" mkdir "%USERPROFILE%\DacexyAgent"

:: Download the agent script
echo [3/4] Downloading Dacexy Agent...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py'"
if errorlevel 1 (
    echo [ERROR] Failed to download agent. Check your internet connection.
    pause
    exit /b 1
)
echo [OK] Agent downloaded.
echo.

:: Ask for token
echo [4/4] Setup Token
echo.
echo  To get your token:
echo  1. Go to https://dacexy.vercel.app/login
echo  2. Login to your account
echo  3. Open DevTools (F12) - Application - Local Storage
echo  4. Copy the value of 'token'
echo.
set /p TOKEN="Paste your Dacexy token here: "

:: Save token
echo %TOKEN% > "%USERPROFILE%\DacexyAgent\token.txt"

:: Create desktop shortcut to launch agent
echo.
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\Dacexy Agent.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "python" >> %SCRIPT%
echo oLink.Arguments = "%USERPROFILE%\DacexyAgent\dacexy_agent.py" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Description = "Dacexy Desktop Agent" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

:: Launch agent
echo.
echo ================================
echo  Installation Complete!
echo  Launching Dacexy Agent now...
echo ================================
echo.
cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
