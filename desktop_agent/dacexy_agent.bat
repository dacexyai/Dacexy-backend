@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer
color 0A

echo.
echo  ================================
echo   DACEXY Desktop Agent v3.1
echo   Installer for Windows
echo  ================================
echo.

goto :main

:main

:: ── Step 1: Check Python ────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed!
    echo.
    echo  Please do this:
    echo  1. Go to https://python.org/downloads
    echo  2. Download Python 3.11 or newer
    echo  3. During install, CHECK the box "Add Python to PATH"
    echo  4. After installing, run this file again
    echo.
    start https://python.org/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  OK: %%i

:: ── Step 2: Create folder ───────────────────────────────────────
echo.
echo [2/5] Creating agent folder...
if not exist "%USERPROFILE%\DacexyAgent" (
    mkdir "%USERPROFILE%\DacexyAgent"
)
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ────────────────────────────────────
echo.
echo [3/5] Installing packages (first run may take 2-3 minutes)...
python -m pip install --upgrade pip --quiet
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil --quiet
if errorlevel 1 (
    echo.
    echo  WARNING: Some packages failed to install quietly. Retrying with output...
    python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil
    if errorlevel 1 (
        echo.
        echo  ERROR: Package installation failed. Check your internet connection.
        pause
        exit /b 1
    )
)
echo  OK: Packages installed

:: ── Step 4: Download agent script ──────────────────────────────
echo.
echo [4/5] Downloading Dacexy Agent script...

:: FIX: delete any old/cached agent script first so we always get the latest
if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    del "%USERPROFILE%\DacexyAgent\dacexy_agent.py"
)

powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host ' OK: Agent downloaded' } catch { Write-Host ' ERROR: Download failed -' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo  ERROR: Could not download agent script.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

:: ── FIX: Delete saved token so user is always asked to log in fresh ──
:: This prevents "Authentication failed" from a stale/expired token.
if exist "%USERPROFILE%\.dacexy_agent.json" (
    echo  Clearing old session token...
    del "%USERPROFILE%\.dacexy_agent.json"
    echo  OK: Old token cleared - you will be asked to log in
)

:: ── Step 5: Create desktop shortcut ────────────────────────────
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

:: ── Done ────────────────────────────────────────────────────────
echo.
echo  ================================
echo   Installation Complete!
echo  ================================
echo.
echo  Launching Dacexy Agent now...
echo  It will ask for your Dacexy email and password.
echo.
echo  NOTE: If you see "Auth failed" again after logging in,
echo        your account password may have changed - just
echo        enter your credentials again and it will work.
echo.
echo  A shortcut has been added to your Desktop for next time.
echo.
pause

:: Launch
cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
