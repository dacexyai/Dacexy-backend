@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer
color 0A

echo.
echo  ================================
echo   DACEXY Desktop Agent v15.0
echo   Installer for Windows
echo  ================================
echo.

goto :main

:main

:: ── Step 1: Check Python, auto-install silently if missing ──────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
echo.
echo  Python not found. Downloading Python 3.11 automatically...
echo  Please wait, this takes 2-3 minutes on first run...
echo.

powershell -Command "try { Write-Host '  Downloading Python 3.11.9...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe' -UseBasicParsing; Write-Host '  Download complete.' } catch { Write-Host '  ERROR: Could not download Python:' $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo  ERROR: Could not download Python automatically.
    echo  Please install Python manually from https://python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    start https://python.org/downloads
    pause
    exit /b 1
)

echo  Installing Python silently (1-2 minutes)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

timeout /t 20 /nobreak >nul

if exist "%TEMP%\python_installer.exe" del "%TEMP%\python_installer.exe"

:: Refresh PATH in current session
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%b"
set "PATH=%SYSPATH%;%USERPATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python installed but PATH needs terminal restart.
    echo  Please close this window and run the installer again.
    echo.
    pause
    exit /b 1
)
echo  Python installed successfully!
echo.

)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i

:: ── Step 2: Create folder ───────────────────────────────────────────────────
echo.
echo [2/5] Creating agent folder...
if not exist "%USERPROFILE%\DacexyAgent" (
mkdir "%USERPROFILE%\DacexyAgent"
)
if not exist "%USERPROFILE%\DacexyAgent\logs" mkdir "%USERPROFILE%\DacexyAgent\logs"
if not exist "%USERPROFILE%\DacexyAgent\data" mkdir "%USERPROFILE%\DacexyAgent\data"
if not exist "%USERPROFILE%\DacexyAgent\plugins" mkdir "%USERPROFILE%\DacexyAgent\plugins"
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ────────────────────────────────────────────────
echo.
echo [3/5] Installing packages (first run may take 5-10 minutes)...
python -m pip install --upgrade pip --quiet
python -m pip install pyautogui pillow "websockets>=10.0" requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard selenium webdriver-manager opencv-python pytesseract schedule aiohttp aiofiles rich colorama python-docx openpyxl pandas cryptography packaging --quiet
if errorlevel 1 (
echo.
echo  WARNING: Some packages failed quietly. Retrying key packages...
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard
if errorlevel 1 (
echo.
echo  ERROR: Package installation failed. Check your internet connection.
pause
exit /b 1
)
)
echo  OK: All packages installed

:: Install PyAudio for voice support
echo  Installing PyAudio for voice support...
python -m pip install PyAudio --quiet >nul 2>&1
if errorlevel 1 (
    python -m pip install pipwin --quiet >nul 2>&1
    python -m pipwin install pyaudio >nul 2>&1
)
python -c "import pyaudio" >nul 2>&1
if errorlevel 1 (
    echo  NOTE: PyAudio not installed - voice will be disabled. Agent still works fully.
) else (
    echo  OK: PyAudio installed - voice enabled
)

:: ── Step 4: Download agent script ──────────────────────────────────────────
echo.
echo [4/5] Downloading Dacexy Agent script...

:: Check if agent already exists next to this installer
if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%USERPROFILE%\DacexyAgent\dacexy_agent.py" >nul
    echo  OK: Agent copied from installer package
    goto :AGENT_READY
)

if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    echo  OK: Agent already present
    goto :AGENT_READY
)

powershell -Command "try { Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host ' OK: Agent downloaded' } catch { Write-Host ' WARN: Download failed -' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
echo.
echo  WARNING: Could not download agent script from server.
echo  Please place dacexy_agent.py in: %USERPROFILE%\DacexyAgent\
echo  Then run this installer again.
echo.
pause
exit /b 1
)

:AGENT_READY
:: Copy this installer into agent folder for autostart
copy /y "%~f0" "%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat" >nul 2>&1

:: Clear old session token so fresh login happens
if exist "%USERPROFILE%\.dacexy_agent.json" (
    python -c "
import json
from pathlib import Path
f = Path.home() / '.dacexy_agent.json'
try:
    d = json.loads(f.read_text(encoding='utf-8'))
    d.pop('access_token', None)
    f.write_text(json.dumps(d, indent=2), encoding='utf-8')
except:
    pass
" >nul 2>&1
)

:: ── Step 5: Create desktop shortcut + autostart ────────────────────────────
echo.
echo [5/5] Creating desktop shortcut and autostart...

set "BAT_PATH=%USERPROFILE%\DacexyAgent\install_dacexy_agent.bat"
set "SC_PATH=%USERPROFILE%\Desktop\Dacexy Agent.lnk"
set "SCRIPT=%TEMP%\dacexy_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut("%SC_PATH%") >> "%SCRIPT%"
echo oLink.TargetPath = "%BAT_PATH%" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> "%SCRIPT%"
echo oLink.Description = "Dacexy Desktop Agent v15.0" >> "%SCRIPT%"
echo oLink.IconLocation = "shell32.dll,15" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"
cscript /nologo "%SCRIPT%"
del "%SCRIPT%"
echo  OK: Shortcut created on Desktop

:: Register autostart via registry
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%BAT_PATH%\"" /f >nul 2>&1
echo  OK: Autostart registered - runs on every Windows startup

:: ── Done ────────────────────────────────────────────────────────────────────
echo.
echo  ================================
echo   Installation Complete!
echo  ================================
echo.
echo  Launching Dacexy Agent now...
echo.
echo  LOGIN: Enter your Dacexy email and password.
echo.
echo  VOICE CONTROL (Hey Dacexy):
echo   - Say "Hey Dacexy" anytime to activate
echo   - Then say your command out loud
echo   - Examples:
echo     "Hey Dacexy, open Chrome"
echo     "Hey Dacexy, take a screenshot"
echo     "Hey Dacexy, what time is it"
echo.
echo  The agent runs 24/7. Control from: dacexy.vercel.app/dashboard
echo.
pause

:AGENT_LOOP
cd "%USERPROFILE%\DacexyAgent"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo  Dacexy Agent stopped cleanly.
    pause
    exit /b 0
)

if %EXIT_CODE% EQU 2 (
    echo  Session expired. Clearing login and restarting...
    python -c "
import json
from pathlib import Path
f = Path.home() / '.dacexy_agent.json'
if f.exists():
    try:
        d = json.loads(f.read_text())
        d.pop('access_token', None)
        f.write_text(json.dumps(d, indent=2))
    except: pass
" >nul 2>&1
    goto :AGENT_LOOP
)

echo.
echo  Agent stopped (code: %EXIT_CODE%). Restarting in 5 seconds...
echo  Press Ctrl+C to cancel.
timeout /t 5 /nobreak >nul
goto :AGENT_LOOP
