@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer
color 0A

echo.
echo  ================================
echo   DACEXY Desktop Agent v16.0
echo   Installer for Windows
echo  ================================
echo.

:: ── Step 1: Check Python ─────────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 goto :NOPYTHON
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i
goto :HASPYTHON

:NOPYTHON
echo  Python not found. Downloading Python 3.11...
powershell -Command "try { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_installer.exe' -UseBasicParsing; Write-Host '  Downloaded.' } catch { Write-Host '  FAILED:' $_.Exception.Message; exit 1 }"
if errorlevel 1 goto :PYDOWNLOADFAIL
echo  Installing Python silently...
"%TEMP%\py_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
timeout /t 20 /nobreak >nul
if exist "%TEMP%\py_installer.exe" del "%TEMP%\py_installer.exe" >nul 2>&1
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%b"
set "PATH=%SYSPATH%;%USERPATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto :PYINSTALLFAIL
echo  Python installed!
goto :HASPYTHON

:PYDOWNLOADFAIL
echo  ERROR: Could not download Python.
echo  Please install from: https://python.org/downloads
echo  Check "Add Python to PATH" during install, then run this again.
pause
exit /b 1

:PYINSTALLFAIL
echo  Python installed but PATH needs refresh.
echo  Close this window and run the installer again.
pause
exit /b 1

:HASPYTHON

:: ── Step 2: Create folders ────────────────────────────────────────────
echo.
echo [2/5] Creating folders...
if not exist "%USERPROFILE%\DacexyAgent"          mkdir "%USERPROFILE%\DacexyAgent"
if not exist "%USERPROFILE%\DacexyAgent\logs"     mkdir "%USERPROFILE%\DacexyAgent\logs"
if not exist "%USERPROFILE%\DacexyAgent\data"     mkdir "%USERPROFILE%\DacexyAgent\data"
if not exist "%USERPROFILE%\DacexyAgent\plugins"  mkdir "%USERPROFILE%\DacexyAgent\plugins"
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ──────────────────────────────────────────
echo.
echo [3/5] Installing packages (5-10 min first time)...
python -m pip install --upgrade pip --quiet --no-warn-script-location >nul 2>&1
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard --quiet --no-warn-script-location
if errorlevel 1 (
    echo  Some packages failed. Retrying individually...
    for %%p in (pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard) do (
        python -m pip install %%p --quiet --no-warn-script-location >nul 2>&1
    )
)
echo  OK: Core packages installed

echo  Installing PyAudio for voice...
python -m pip install PyAudio --quiet --no-warn-script-location >nul 2>&1
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    python -m pip install pipwin --quiet --no-warn-script-location >nul 2>&1
    python -m pipwin install pyaudio >nul 2>&1
)
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo  NOTE: PyAudio failed - voice will be disabled. Text commands still work.
) else (
    echo  OK: PyAudio installed - voice enabled
)

:: ── Step 4: Setup agent file ─────────────────────────────────────────
echo.
echo [4/5] Setting up agent...

if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%USERPROFILE%\DacexyAgent\dacexy_agent.py" >nul
    echo  OK: Agent copied from installer folder
    goto :AGENT_READY
)
if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    echo  OK: Agent already present
    goto :AGENT_READY
)

echo  Downloading agent from server...
powershell -Command "try { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host '  OK: Agent downloaded' } catch { Write-Host '  WARN: Could not download - ' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo  Agent file not found. Please:
    echo  1. Go to dacexy.vercel.app/settings
    echo  2. Download dacexy_agent.py
    echo  3. Put it in: %USERPROFILE%\DacexyAgent\
    echo  4. Run this installer again
    pause
    exit /b 1
)

:AGENT_READY
copy /y "%~f0" "%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat" >nul 2>&1
echo  OK: Agent ready

:: Clear old token so fresh login happens
echo import json > "%TEMP%\dx_clear.py"
echo from pathlib import Path >> "%TEMP%\dx_clear.py"
echo f = Path.home() / '.dacexy_agent.json' >> "%TEMP%\dx_clear.py"
echo if f.exists(): >> "%TEMP%\dx_clear.py"
echo     try: >> "%TEMP%\dx_clear.py"
echo         d = json.loads(f.read_text(encoding='utf-8')) >> "%TEMP%\dx_clear.py"
echo         d.pop('access_token', None) >> "%TEMP%\dx_clear.py"
echo         f.write_text(json.dumps(d, indent=2), encoding='utf-8') >> "%TEMP%\dx_clear.py"
echo     except: pass >> "%TEMP%\dx_clear.py"
python "%TEMP%\dx_clear.py" >nul 2>&1
del "%TEMP%\dx_clear.py" >nul 2>&1

:: ── Step 5: Shortcuts + autostart ────────────────────────────────────
echo.
echo [5/5] Creating shortcuts and autostart...

set "BAT=%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat"

set "VBS=%TEMP%\dx_sc.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> "%VBS%"
echo oLink.TargetPath = "%BAT%" >> "%VBS%"
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> "%VBS%"
echo oLink.Description = "Dacexy AI Desktop Agent v16.0" >> "%VBS%"
echo oLink.IconLocation = "shell32.dll,15" >> "%VBS%"
echo oLink.Save >> "%VBS%"
cscript /nologo "%VBS%" >nul 2>&1
del "%VBS%" >nul 2>&1
echo  OK: Desktop shortcut created

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%BAT%\"" /f >nul 2>&1
echo  OK: Autostart registered - runs on Windows startup

:: ── Done ─────────────────────────────────────────────────────────────
echo.
echo  ================================
echo   Installation Complete!
echo  ================================
echo.
echo  Launching Dacexy Agent now...
echo.
echo  LOGIN: Enter your Dacexy email and password.
echo.
echo  VOICE COMMANDS - say any of these to wake:
echo    "Dacexy"         - simplest
echo    "Hey Dacexy"     - classic
echo    "Computer"       - short
echo    "Hey Computer"   - alternative
echo.
echo  Then say your command, for example:
echo    "Open YouTube"
echo    "Open Chrome"
echo    "Send email to friend@gmail.com"
echo    "Search for weather today"
echo    "Take a screenshot"
echo    "What time is it"
echo.
echo  Control remotely: dacexy.vercel.app/dashboard
echo.
pause

:AGENT_LOOP
cd /d "%USERPROFILE%\DacexyAgent"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo  Agent stopped cleanly.
    pause
    exit /b 0
)

if %EXIT_CODE% EQU 2 goto :CLEAR_AND_RESTART

echo.
echo  Agent stopped (code %EXIT_CODE%). Restarting in 5 seconds...
echo  Press Ctrl+C to cancel.
timeout /t 5 /nobreak >nul
goto :AGENT_LOOP

:CLEAR_AND_RESTART
echo  Session expired. Clearing login...
echo import json > "%TEMP%\dx_clear2.py"
echo from pathlib import Path >> "%TEMP%\dx_clear2.py"
echo f = Path.home() / '.dacexy_agent.json' >> "%TEMP%\dx_clear2.py"
echo if f.exists(): >> "%TEMP%\dx_clear2.py"
echo     try: >> "%TEMP%\dx_clear2.py"
echo         d = json.loads(f.read_text()) >> "%TEMP%\dx_clear2.py"
echo         d.pop('access_token', None) >> "%TEMP%\dx_clear2.py"
echo         f.write_text(json.dumps(d, indent=2)) >> "%TEMP%\dx_clear2.py"
echo     except: pass >> "%TEMP%\dx_clear2.py"
python "%TEMP%\dx_clear2.py" >nul 2>&1
del "%TEMP%\dx_clear2.py" >nul 2>&1
goto :AGENT_LOOP
