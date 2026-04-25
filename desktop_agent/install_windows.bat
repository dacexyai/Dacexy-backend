@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer
color 0A

echo.
echo  ================================
echo   DACEXY Desktop Agent v3.0
echo   Installer for Windows
echo  ================================
echo.

:: Keep window open on any error
if "%1"=="--elevated" goto :main
goto :main

:main

:: Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed!
    echo.
    echo  Please do this:
    echo  1. Go to https://python.org/downloads
    echo  2. Download Python 3.11 or newer
    echo  3. During install, CHECK the box that says "Add Python to PATH"
    echo  4. After installing, run this file again
    echo.
    start https://python.org/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  OK: %%i

:: Create folder
echo.
echo [2/5] Creating agent folder...
if not exist "%USERPROFILE%\DacexyAgent" (
    mkdir "%USERPROFILE%\DacexyAgent"
)
echo  OK: %USERPROFILE%\DacexyAgent

:: Install packages
echo.
echo [3/5] Installing packages (this may take 2-3 minutes on first run)...
python -m pip install --upgrade pip --quiet
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil --quiet
if errorlevel 1 (
    echo.
    echo  WARNING: Some packages failed. Trying again...
    python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil
)
echo  OK: Packages installed

:: Download agent
echo.
echo [4/5] Downloading Dacexy Agent script...
powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host ' OK: Agent downloaded' } catch { Write-Host ' ERROR: Download failed -' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo  ERROR: Could not download agent script.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

:: Create desktop shortcut
echo.
echo [5/5] Creating desktop shortcut...
set SCRIPT="%TEMP%\dacexy_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> %SCRIPT%
echo oLink.TargetPath = "cmd.exe" >> %SCRIPT%
echo oLink.Arguments = "/k python %USERPROFILE%\DacexyAgent\dacexy_agent.py" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Description = "Dacexy Desktop Agent" >> %SCRIPT%
echo oLink.IconLocation = "shell32.dll,15" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo  OK: Shortcut created on Desktop

:: Done
echo.
echo  ================================
echo   Installation Complete!
echo  ================================
echo.
echo  Launching Dacexy Agent now...
echo  It will ask for your email and password.
echo  Get your token from: dacexy.vercel.app/settings
echo.
echo  (A shortcut has been added to your Desktop
echo   for next time — just double-click it)
echo.
pause

:: Launch
cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
