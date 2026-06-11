@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v22.0 - Installer
color 0A

set AGENT_DIR=%USERPROFILE%\DacexyAgent
set AGENT_PY=%AGENT_DIR%\dacexy_agent.py
set START_BAT=%AGENT_DIR%\start_dacexy.bat
set LOG=%AGENT_DIR%\install_log.txt
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo  ===================================================
echo   DACEXY Desktop Agent v22.0 - Installer
echo   Real Jarvis. Actually works.
echo  ===================================================
echo.
echo  [INFO] Log will be saved to: %AGENT_DIR%\install_log.txt
echo.

:: ─────────────────────────────────────────────────────────────────────────
:: Create folders first (needed for log)
:: ─────────────────────────────────────────────────────────────────────────
if not exist "%AGENT_DIR%"              mkdir "%AGENT_DIR%"
if not exist "%AGENT_DIR%\logs"         mkdir "%AGENT_DIR%\logs"
if not exist "%AGENT_DIR%\data"         mkdir "%AGENT_DIR%\data"
if not exist "%AGENT_DIR%\screenshots"  mkdir "%AGENT_DIR%\screenshots"

echo [Dacexy Installer - %DATE% %TIME%] > "%LOG%"

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 1: Check Python
:: ─────────────────────────────────────────────────────────────────────────
echo [1/8] Checking Python...
echo [1/8] Checking Python >> "%LOG%"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :INSTALL_PYTHON

for /f "tokens=*" %%i in ('python --version 2^>^&1') do (
    echo  OK: %%i
    echo  OK: %%i >> "%LOG%"
)
goto :PYTHON_READY

:INSTALL_PYTHON
echo  Python not found. Downloading Python 3.11.9 (this may take 2-3 minutes)...
echo  Python not found - downloading >> "%LOG%"

powershell -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference='SilentlyContinue';" ^
  "try {" ^
  "  Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing;" ^
  "  Write-Host '  Download complete.'" ^
  "} catch {" ^
  "  Write-Host ('  DOWNLOAD FAILED: ' + $_.Exception.Message);" ^
  "  exit 1" ^
  "}" 2>>"%LOG%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Could not download Python automatically.
    echo  Please install Python 3.11 manually from: https://python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    echo  Then re-run this installer.
    echo.
    echo  ERROR: Python download failed >> "%LOG%"
    pause
    exit /b 1
)

echo  Installing Python silently (takes ~1 minute)...
"%TEMP%\py_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1
echo  Waiting for Python setup to finish...
timeout /t 30 /nobreak >nul
if exist "%TEMP%\py_setup.exe" del "%TEMP%\py_setup.exe" >nul 2>&1

:: Refresh PATH for Python
set "PY_LOCAL=%LOCALAPPDATA%\Programs\Python\Python311"
set "PY_SCRIPTS=%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
if exist "%PY_LOCAL%\python.exe" (
    set "PATH=%PY_LOCAL%;%PY_SCRIPTS%;%PATH%"
)

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Python installed but not found in PATH.
    echo  Please CLOSE this window and re-open it as Administrator,
    echo  then run this installer again.
    echo.
    echo  ERROR: Python not in PATH after install >> "%LOG%"
    pause
    exit /b 1
)

echo  Python installed successfully!
echo  Python installed OK >> "%LOG%"

:PYTHON_READY

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 2: Upgrade pip silently
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [2/8] Upgrading pip...
echo [2/8] Upgrading pip >> "%LOG%"
python -m pip install --upgrade pip --quiet --no-warn-script-location >>"%LOG%" 2>&1
echo  OK: pip upgraded

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 3: Install core packages one by one (safe, shows progress)
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [3/8] Installing packages (first time: 5-10 minutes, please wait)...
echo [3/8] Installing packages >> "%LOG%"
echo  Each package will be shown. Errors are non-fatal - agent auto-retries.
echo.

call :INSTALL_PKG pyautogui
call :INSTALL_PKG pillow
call :INSTALL_PKG websockets
call :INSTALL_PKG requests
call :INSTALL_PKG pyttsx3
call :INSTALL_PKG numpy
call :INSTALL_PKG psutil
call :INSTALL_PKG pyperclip
call :INSTALL_PKG plyer
call :INSTALL_PKG pygetwindow
call :INSTALL_PKG keyboard
call :INSTALL_PKG speechrecognition
call :INSTALL_PKG beautifulsoup4
call :INSTALL_PKG selenium
call :INSTALL_PKG webdriver-manager

echo.
echo  Installing PyAudio for Jarvis voice control...
echo  Installing PyAudio >> "%LOG%"
python -m pip install PyAudio --quiet --no-warn-script-location >>"%LOG%" 2>&1
python -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  PyAudio direct install failed. Trying pipwin fallback...
    python -m pip install pipwin --quiet --no-warn-script-location >>"%LOG%" 2>&1
    python -m pipwin install pyaudio >>"%LOG%" 2>&1
    python -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [!] PyAudio: FAILED - voice control will be DISABLED
        echo  [!] PyAudio failed >> "%LOG%"
        echo      Fix later: pip install PyAudio
    ) else (
        echo  [+] PyAudio: OK - Jarvis voice control ENABLED
        echo  [+] PyAudio OK >> "%LOG%"
    )
) else (
    echo  [+] PyAudio: OK - Jarvis voice control ENABLED
    echo  [+] PyAudio OK >> "%LOG%"
)

goto :PACKAGES_DONE

:INSTALL_PKG
set PKG=%~1
echo  Installing %PKG%...
python -m pip install %PKG% --quiet --no-warn-script-location >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [!] %PKG%: WARNING - failed, agent will retry on first run
    echo  [!] %PKG% FAILED >> "%LOG%"
) else (
    echo  [+] %PKG%: OK
    echo  [+] %PKG% OK >> "%LOG%"
)
exit /b 0

:PACKAGES_DONE

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 4: Setup agent file
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [4/8] Setting up agent file...
echo [4/8] Agent file setup >> "%LOG%"

:: Check if agent.py exists next to this installer
if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%AGENT_PY%" >nul 2>&1
    echo  OK: Agent copied from installer folder
    echo  Agent copied from installer folder >> "%LOG%"
    goto :AGENT_FILE_READY
)

:: Already installed?
if exist "%AGENT_PY%" (
    echo  OK: Agent file already present
    echo  Agent file already present >> "%LOG%"
    goto :AGENT_FILE_READY
)

:: Try to download from backend
echo  Agent file not found. Downloading from Dacexy servers...
echo  Downloading agent >> "%LOG%"
powershell -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference='SilentlyContinue';" ^
  "try {" ^
  "  Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%AGENT_PY%' -UseBasicParsing;" ^
  "  Write-Host '  OK: Agent downloaded'" ^
  "} catch {" ^
  "  Write-Host ('  FAILED: ' + $_.Exception.Message);" ^
  "  exit 1" ^
  "}" 2>>"%LOG%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ============================================================
    echo  ERROR: Could not find or download dacexy_agent.py
    echo  ============================================================
    echo  Please:
    echo    1. Go to dacexy.vercel.app/settings  or  /download
    echo    2. Download  dacexy_agent.py
    echo    3. Place it in the SAME folder as this installer
    echo    4. Run this installer again
    echo  ============================================================
    echo.
    echo  ERROR: Agent file not found >> "%LOG%"
    pause
    exit /b 1
)

:AGENT_FILE_READY

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 5: Create start_dacexy.bat (the launcher the agent and autostart use)
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [5/8] Creating launcher...
echo [5/8] Creating launcher >> "%LOG%"

(
    echo @echo off
    echo chcp 65001 ^>nul 2^>^&1
    echo title Dacexy Agent v22.0
    echo color 0A
    echo set PYTHONIOENCODING=utf-8
    echo set PYTHONUTF8=1
    echo cd /d "%AGENT_DIR%"
    echo echo.
    echo echo  Starting Dacexy Agent v22.0...
    echo echo  Press Ctrl+C to stop.
    echo echo.
    echo :LOOP
    echo python "%AGENT_PY%"
    echo set ERR=%%ERRORLEVEL%%
    echo if %%ERR%% EQU 0 ^(
    echo     echo.
    echo     echo  Agent stopped cleanly. Press any key to exit.
    echo     pause
    echo     exit /b 0
    echo ^)
    echo echo.
    echo echo  Agent stopped with code %%ERR%%. Restarting in 5 seconds...
    echo echo  Press Ctrl+C to cancel restart.
    echo timeout /t 5 /nobreak ^>nul
    echo goto :LOOP
) > "%START_BAT%"

echo  OK: Launcher created at %START_BAT%
echo  Launcher created >> "%LOG%"

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 6: Shortcuts and autostart
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [6/8] Creating shortcuts and autostart...
echo [6/8] Shortcuts >> "%LOG%"

:: Desktop shortcut
set "VBS_TMP=%TEMP%\dacexy_sc_%RANDOM%.vbs"
(
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo sLinkFile = "%USERPROFILE%\Desktop\Dacexy Agent.lnk"
    echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
    echo oLink.TargetPath = "%START_BAT%"
    echo oLink.WorkingDirectory = "%AGENT_DIR%"
    echo oLink.Description = "Dacexy AI Desktop Agent v22.0"
    echo oLink.IconLocation = "shell32.dll,15"
    echo oLink.Save
) > "%VBS_TMP%"
cscript /nologo "%VBS_TMP%" >nul 2>&1
if exist "%VBS_TMP%" del "%VBS_TMP%" >nul 2>&1
echo  OK: Desktop shortcut created
echo  Desktop shortcut OK >> "%LOG%"

:: Autostart registry (run start_dacexy.bat on Windows startup)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%START_BAT%\"" /f >nul 2>&1
echo  OK: Autostart on login registered
echo  Autostart OK >> "%LOG%"

:: Clear old auth token so user must log in fresh
python -c "import json; from pathlib import Path; f=Path.home()/'.dacexy_agent.json'; d=json.loads(f.read_text()) if f.exists() else {}; d.pop('access_token',None); f.write_text(json.dumps(d,indent=2))" >nul 2>&1

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 7: Capability check
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [7/8] Checking what is working...
echo [7/8] Capability check >> "%LOG%"
echo.

python -c "import pyautogui; print('  [+] Mouse and keyboard control')" 2>nul
python -c "from PIL import ImageGrab; print('  [+] Screenshot')" 2>nul
python -c "import pyaudio; print('  [+] Jarvis voice control (say: Dacexy, Jarvis, Computer)')" 2>nul
python -c "from selenium import webdriver; print('  [+] Browser automation (Instagram, LinkedIn, Facebook)')" 2>nul
python -c "from bs4 import BeautifulSoup; print('  [+] Web scraping and lead finder')" 2>nul
python -c "import smtplib; print('  [+] Email engine (bulk send, auto-send)')" 2>nul
python -c "import psutil; print('  [+] System info (CPU, RAM, disk)')" 2>nul
python -c "import websockets; print('  [+] Cloud dashboard connection')" 2>nul

:: ─────────────────────────────────────────────────────────────────────────
:: STEP 8: Summary and instructions
:: ─────────────────────────────────────────────────────────────────────────
echo.
echo [8/8] Installation complete!
echo [8/8] Installation complete >> "%LOG%"
echo.
echo  ===================================================
echo   DACEXY v22.0 - Successfully Installed!
echo  ===================================================
echo.
echo  HOW TO START:
echo    - Double-click "Dacexy Agent" shortcut on your Desktop
echo    - OR run: %START_BAT%
echo    - The agent starts automatically when Windows boots
echo.
echo  FIRST TIME: The agent will ask you to log in with your
echo  Dacexy account (same email and password you use on
echo  dacexy.vercel.app). Make sure you are registered first.
echo.
echo  VOICE CONTROL - just say any wake word:
echo    "Dacexy"   "Hey Dacexy"   "Jarvis"   "Computer"
echo.
echo  EXAMPLE COMMANDS:
echo    "open youtube"
echo    "search lofi music on youtube"
echo    "what time is it"
echo    "take a screenshot"
echo    "open chrome"
echo    "send email to boss@gmail.com saying hello"
echo    "configure email"     <- to enable bulk auto-send
echo.
echo  DASHBOARD: dacexy.vercel.app - control from anywhere
echo  LOGS:      %AGENT_DIR%\install_log.txt
echo.
echo  ===================================================
echo.

:: Ask if user wants to launch now
set /p LAUNCH_NOW="  Launch Dacexy Agent now? (Y/n): "
if /i "%LAUNCH_NOW%"=="n" goto :SKIP_LAUNCH
if /i "%LAUNCH_NOW%"=="no" goto :SKIP_LAUNCH

echo.
echo  Starting Dacexy Agent in a new window...
echo  The login prompt will appear there.
echo.
start "Dacexy Agent v22.0" /min "%START_BAT%"
echo  Agent is running in the background!
echo  Check your taskbar for "Dacexy Agent v22.0" window.
goto :DONE

:SKIP_LAUNCH
echo.
echo  You can start the agent any time from the Desktop shortcut.

:DONE
echo.
echo  Press any key to close this installer.
echo  Installer done >> "%LOG%"
pause >nul
exit /b 0
