@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v17.0 Installer
color 0A

echo.
echo  ===================================================
echo   DACEXY Desktop Agent v17.0 - FULLY WORKING
echo   Installer for Windows
echo  ===================================================
echo.

:: ── Step 1: Check Python ─────────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 goto :NOPYTHON
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i
goto :HASPYTHON

:NOPYTHON
echo  Python not found. Downloading Python 3.11...
powershell -Command "try { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_installer.exe' -UseBasicParsing; Write-Host '  Downloaded.' } catch { Write-Host '  FAILED: ' $_.Exception.Message; exit 1 }"
if errorlevel 1 goto :PYDOWNLOADFAIL
echo  Installing Python silently...
"%TEMP%\py_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
timeout /t 20 /nobreak >nul
if exist "%TEMP%\py_installer.exe" del "%TEMP%\py_installer.exe" >nul 2>&1
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto :PYINSTALLFAIL
echo  Python installed!
goto :HASPYTHON

:PYDOWNLOADFAIL
echo  ERROR: Could not download Python.
echo  Install from: https://python.org/downloads  (check "Add to PATH")
pause & exit /b 1

:PYINSTALLFAIL
echo  Python installed but PATH not updated. Close and rerun installer.
pause & exit /b 1

:HASPYTHON

:: ── Step 2: Create folders ────────────────────────────────────────────
echo.
echo [2/6] Creating folders...
if not exist "%USERPROFILE%\DacexyAgent"         mkdir "%USERPROFILE%\DacexyAgent"
if not exist "%USERPROFILE%\DacexyAgent\logs"    mkdir "%USERPROFILE%\DacexyAgent\logs"
if not exist "%USERPROFILE%\DacexyAgent\data"    mkdir "%USERPROFILE%\DacexyAgent\data"
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ──────────────────────────────────────────
echo.
echo [3/6] Installing packages (5-10 minutes first time)...
python -m pip install --upgrade pip --quiet --no-warn-script-location >nul 2>&1

echo  Installing core packages...
python -m pip install pyautogui pillow websockets requests pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard speechrecognition --quiet --no-warn-script-location
if errorlevel 1 (
    echo  Some failed - retrying individually...
    for %%p in (pyautogui pillow websockets requests pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard speechrecognition) do (
        python -m pip install %%p --quiet --no-warn-script-location >nul 2>&1
    )
)
echo  OK: Core packages

echo  Installing Selenium for browser automation...
python -m pip install selenium webdriver-manager --quiet --no-warn-script-location >nul 2>&1
python -c "from selenium import webdriver" >nul 2>&1
if errorlevel 1 (
    echo  NOTE: Selenium failed - social media posting via browser won't work
) else (
    echo  OK: Selenium installed - social media auto-posting ready
)

echo  Installing PyAudio for voice control...
python -m pip install PyAudio --quiet --no-warn-script-location >nul 2>&1
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo  Trying pipwin method for PyAudio...
    python -m pip install pipwin --quiet --no-warn-script-location >nul 2>&1
    python -m pipwin install pyaudio >nul 2>&1
)
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo  NOTE: PyAudio failed - voice will be disabled. Text commands still work.
    echo  To fix: download PyAudio wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo  Then run: pip install PyAudio-0.2.14-cp311-cp311-win_amd64.whl
) else (
    echo  OK: PyAudio installed - voice control enabled
)

:: ── Step 4: Setup agent file ─────────────────────────────────────────
echo.
echo [4/6] Setting up agent...

if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%USERPROFILE%\DacexyAgent\dacexy_agent.py" >nul
    echo  OK: Agent copied from installer folder
    goto :AGENT_READY
)
if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    echo  OK: Agent already present
    goto :AGENT_READY
)

echo  Downloading agent...
powershell -Command "try { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host '  OK: Downloaded' } catch { Write-Host '  WARN: ' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo  Agent not found! Please:
    echo  1. Go to dacexy.vercel.app/settings
    echo  2. Download dacexy_agent.py
    echo  3. Put it in: %USERPROFILE%\DacexyAgent\
    echo  4. Run this installer again
    pause & exit /b 1
)

:AGENT_READY
copy /y "%~f0" "%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat" >nul 2>&1

:: Clear old token for fresh login
python -c "import json; from pathlib import Path; f=Path.home()/'.dacexy_agent.json'; d=json.loads(f.read_text()) if f.exists() else {}; d.pop('access_token',None); f.write_text(json.dumps(d,indent=2))" >nul 2>&1

echo  OK: Agent ready at %USERPROFILE%\DacexyAgent\dacexy_agent.py

:: ── Step 5: Shortcuts + autostart ────────────────────────────────────
echo.
echo [5/6] Creating shortcuts...

set "BAT=%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat"

set "VBS=%TEMP%\dx_sc.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> "%VBS%"
echo oLink.TargetPath = "%BAT%" >> "%VBS%"
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> "%VBS%"
echo oLink.Description = "Dacexy AI Desktop Agent v17.0" >> "%VBS%"
echo oLink.IconLocation = "shell32.dll,15" >> "%VBS%"
echo oLink.Save >> "%VBS%"
cscript /nologo "%VBS%" >nul 2>&1
del "%VBS%" >nul 2>&1
echo  OK: Desktop shortcut created

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%BAT%\"" /f >nul 2>&1
echo  OK: Autostart on Windows startup

:: ── Step 6: Summary ──────────────────────────────────────────────────
echo.
echo [6/6] Checking capabilities...
python -c "import pyautogui; print('  OK: Mouse/keyboard control')" 2>nul
python -c "from PIL import ImageGrab; print('  OK: Screenshot')" 2>nul
python -c "import pyaudio; print('  OK: Voice control')" 2>nul
python -c "from selenium import webdriver; print('  OK: Browser automation (Instagram/LinkedIn/Facebook)')" 2>nul
python -c "import smtplib; print('  OK: Email sending')" 2>nul

echo.
echo  ===================================================
echo   Installation Complete!
echo  ===================================================
echo.
echo  WHAT THIS AGENT CAN DO:
echo    - Open any website or app
echo    - Search Google and YouTube
echo    - Send emails (configure SMTP for auto-send)
echo    - Post to Instagram, LinkedIn, Facebook
echo    - Send WhatsApp messages (via Web)
echo    - Take screenshots
echo    - Control volume, windows, keyboard
echo    - Write and read files
echo    - Voice control (say 'Dacexy' or 'Computer')
echo    - Everything controlled from dacexy.vercel.app
echo.
echo  LOGIN: Enter your Dacexy email and password below.
echo.
echo  VOICE WAKE WORDS: "Dacexy" / "Computer" / "Hey Dacexy"
echo.
echo  FOR REAL EMAIL SENDING: After login, say or type:
echo    configure smtp
echo  Then enter your Gmail + App Password.
echo.
pause

:AGENT_LOOP
cd /d "%USERPROFILE%\DacexyAgent"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo. & echo  Agent stopped cleanly.
    pause & exit /b 0
)

echo.
echo  Agent stopped (code %EXIT_CODE%). Restarting in 5 seconds...
echo  Press Ctrl+C to cancel.
timeout /t 5 /nobreak >nul
goto :AGENT_LOOP
