@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v22.0 Installer
color 0A

echo.
echo  ===================================================
echo   DACEXY Desktop Agent v22.0 - Installer
echo   Real Jarvis. Actually works.
echo  ===================================================
echo.

set "AGENT_DIR=%USERPROFILE%\DacexyAgent"
set "AGENT_PY=%USERPROFILE%\DacexyAgent\dacexy_agent.py"
set "START_BAT=%USERPROFILE%\DacexyAgent\start_dacexy.bat"
set "LOG_FILE=%USERPROFILE%\DacexyAgent\install_log.txt"

echo  [INFO] Installing to: %AGENT_DIR%
echo.

:: Step 0: Create folders
if not exist "%AGENT_DIR%"             mkdir "%AGENT_DIR%"
if not exist "%AGENT_DIR%\logs"        mkdir "%AGENT_DIR%\logs"
if not exist "%AGENT_DIR%\data"        mkdir "%AGENT_DIR%\data"
if not exist "%AGENT_DIR%\screenshots" mkdir "%AGENT_DIR%\screenshots"

echo Dacexy Install Log > "%LOG_FILE%"
echo Date: %DATE% %TIME% >> "%LOG_FILE%"

:: Step 1: Check Python
echo [1/8] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :INSTALL_PYTHON

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i
goto :PYTHON_READY

:INSTALL_PYTHON
echo  Python not found. Downloading Python 3.11.9...
echo  (This may take 2-3 minutes. Please wait.)
echo Python not found - downloading >> "%LOG_FILE%"
powershell -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing; Write-Host '  Downloaded OK' } catch { Write-Host ('  FAILED: ' + $_.Exception.Message); exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Could not download Python.
    echo  Please install Python 3.11 from: https://python.org/downloads
    echo  Check "Add Python to PATH" then re-run this installer.
    echo Python download failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo  Installing Python silently (1-2 minutes)...
"%TEMP%\py_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1
timeout /t 30 /nobreak >nul
if exist "%TEMP%\py_setup.exe" del "%TEMP%\py_setup.exe" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Python installed but PATH not updated.
    echo  Close this window and re-run the installer.
    echo Python PATH error >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo  Python installed successfully!
echo Python installed OK >> "%LOG_FILE%"

:PYTHON_READY

:: Step 2: Upgrade pip
echo.
echo [2/8] Upgrading pip...
python -m pip install --upgrade pip --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
echo  OK: pip upgraded

:: Step 3: Install packages one by one
echo.
echo [3/8] Installing packages (5-10 min first time, please wait)...
echo.

echo  Installing pyautogui...
python -m pip install pyautogui --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] pyautogui: OK) else (echo  [!] pyautogui: failed - will retry at first run)

echo  Installing pillow...
python -m pip install pillow --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] pillow: OK) else (echo  [!] pillow: failed - will retry at first run)

echo  Installing websockets...
python -m pip install websockets --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] websockets: OK) else (echo  [!] websockets: failed - will retry at first run)

echo  Installing requests...
python -m pip install requests --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] requests: OK) else (echo  [!] requests: failed - will retry at first run)

echo  Installing pyttsx3...
python -m pip install pyttsx3 --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] pyttsx3: OK) else (echo  [!] pyttsx3: failed - will retry at first run)

echo  Installing numpy...
python -m pip install numpy --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] numpy: OK) else (echo  [!] numpy: failed - will retry at first run)

echo  Installing psutil...
python -m pip install psutil --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] psutil: OK) else (echo  [!] psutil: failed - will retry at first run)

echo  Installing pyperclip...
python -m pip install pyperclip --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] pyperclip: OK) else (echo  [!] pyperclip: failed - will retry at first run)

echo  Installing plyer...
python -m pip install plyer --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] plyer: OK) else (echo  [!] plyer: failed - will retry at first run)

echo  Installing pygetwindow...
python -m pip install pygetwindow --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] pygetwindow: OK) else (echo  [!] pygetwindow: failed - will retry at first run)

echo  Installing keyboard...
python -m pip install keyboard --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] keyboard: OK) else (echo  [!] keyboard: failed - will retry at first run)

echo  Installing speechrecognition...
python -m pip install speechrecognition --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] speechrecognition: OK) else (echo  [!] speechrecognition: failed - will retry at first run)

echo  Installing beautifulsoup4...
python -m pip install beautifulsoup4 --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] beautifulsoup4: OK) else (echo  [!] beautifulsoup4: failed - will retry at first run)

echo  Installing selenium...
python -m pip install selenium --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] selenium: OK) else (echo  [!] selenium: failed - will retry at first run)

echo  Installing webdriver-manager...
python -m pip install webdriver-manager --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
if %ERRORLEVEL% EQU 0 (echo  [+] webdriver-manager: OK) else (echo  [!] webdriver-manager: failed - will retry at first run)

echo  Installing PyAudio (for Jarvis voice)...
python -m pip install PyAudio --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
python -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  PyAudio direct failed. Trying pipwin...
    python -m pip install pipwin --quiet --no-warn-script-location >>"%LOG_FILE%" 2>&1
    python -m pipwin install pyaudio >>"%LOG_FILE%" 2>&1
    python -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [!] PyAudio: FAILED - voice will be disabled. Text commands still work.
    ) else (
        echo  [+] PyAudio: OK - Jarvis voice ENABLED
    )
) else (
    echo  [+] PyAudio: OK - Jarvis voice ENABLED
)

:: Step 4: Setup agent file
echo.
echo [4/8] Setting up agent file...
if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%AGENT_PY%" >nul 2>&1
    echo  OK: Agent copied from installer folder
    goto :AGENT_READY
)
if exist "%AGENT_PY%" (
    echo  OK: Agent already present
    goto :AGENT_READY
)
echo  Downloading agent from Dacexy servers...
powershell -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%AGENT_PY%' -UseBasicParsing; Write-Host '  OK: Downloaded' } catch { Write-Host ('  FAILED: ' + $_.Exception.Message); exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ============================================================
    echo  ERROR: dacexy_agent.py not found.
    echo  Please:
    echo    1. Go to dacexy.vercel.app - download dacexy_agent.py
    echo    2. Put it in the same folder as this installer
    echo    3. Run this installer again
    echo  ============================================================
    pause
    exit /b 1
)

:AGENT_READY
copy /y "%~f0" "%AGENT_DIR%\install_dacexy_agent.bat" >nul 2>&1
python -c "import json; from pathlib import Path; f=Path.home()/'.dacexy_agent.json'; d=json.loads(f.read_text()) if f.exists() else {}; d.pop('access_token',None); f.write_text(json.dumps(d,indent=2))" >nul 2>&1

:: Step 5: Create start_dacexy.bat launcher
echo.
echo [5/8] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title Dacexy Agent v22.0
echo color 0A
echo set PYTHONIOENCODING=utf-8
echo set PYTHONUTF8=1
echo cd /d "%AGENT_DIR%"
echo echo.
echo echo  Dacexy Agent v22.0 - Starting...
echo echo  Press Ctrl+C to stop.
echo echo.
echo :LOOP
echo python "%AGENT_PY%"
echo set ERR=%%ERRORLEVEL%%
echo if %%ERR%% EQU 0 goto :CLEAN_STOP
echo echo.
echo echo  Agent stopped ^(code %%ERR%%%%). Restarting in 5 seconds...
echo echo  Press Ctrl+C to cancel.
echo timeout /t 5 /nobreak ^>nul
echo goto :LOOP
echo :CLEAN_STOP
echo echo.
echo echo  Agent stopped cleanly.
echo pause
echo exit /b 0
) > "%START_BAT%"
echo  OK: Launcher created

:: Step 6: Shortcuts and autostart
echo.
echo [6/8] Creating shortcuts and autostart...

set "VBS_TMP=%TEMP%\dacexy_sc.vbs"
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk"^)
echo oLink.TargetPath = "%START_BAT%"
echo oLink.WorkingDirectory = "%AGENT_DIR%"
echo oLink.Description = "Dacexy AI Desktop Agent v22.0"
echo oLink.IconLocation = "shell32.dll,15"
echo oLink.Save
) > "%VBS_TMP%"
cscript /nologo "%VBS_TMP%" >nul 2>&1
if exist "%VBS_TMP%" del "%VBS_TMP%" >nul 2>&1
echo  OK: Desktop shortcut created

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%START_BAT%\"" /f >nul 2>&1
echo  OK: Autostart on Windows login registered

:: Step 7: Capability check
echo.
echo [7/8] Checking capabilities...
echo.
python -c "import pyautogui; print('  [+] Mouse and keyboard control')" 2>nul
python -c "from PIL import ImageGrab; print('  [+] Screenshot')" 2>nul
python -c "import pyaudio; print('  [+] Jarvis voice control (say: Dacexy / Jarvis / Computer)')" 2>nul
python -c "from selenium import webdriver; print('  [+] Browser automation (Instagram, LinkedIn, Facebook)')" 2>nul
python -c "from bs4 import BeautifulSoup; print('  [+] Web scraping and lead finder')" 2>nul
python -c "import smtplib; print('  [+] Email engine (bulk send)')" 2>nul
python -c "import psutil; print('  [+] System info (CPU, RAM, disk)')" 2>nul
python -c "import websockets; print('  [+] Cloud dashboard connection')" 2>nul

:: Step 8: Done
echo.
echo [8/8] Installation complete!
echo.
echo  ===================================================
echo   DACEXY v22.0 - Successfully Installed!
echo  ===================================================
echo.
echo  HOW TO START:
echo    Double-click "Dacexy Agent" on your Desktop
echo    OR run: %START_BAT%
echo    Starts automatically when Windows boots.
echo.
echo  FIRST TIME: Agent will ask you to log in with your
echo  Dacexy account (same email + password as dacexy.vercel.app)
echo.
echo  CONFIGURE EMAIL after login by saying: configure email
echo  This enables bulk auto-send (1000s of emails automatically)
echo.
echo  WAKE WORDS: Dacexy / Hey Dacexy / Jarvis / Computer
echo.
echo  EXAMPLE COMMANDS:
echo    open youtube
echo    search lofi music on youtube
echo    take a screenshot
echo    what time is it
echo    send email to boss@gmail.com saying hello
echo    configure email
echo.
echo  DASHBOARD: dacexy.vercel.app
echo  LOGS: %LOG_FILE%
echo.
echo  ===================================================
echo.

set /p LAUNCH_NOW="  Launch Dacexy Agent now? (Y/n): "
if /i "%LAUNCH_NOW%"=="n" goto :SKIP_LAUNCH
if /i "%LAUNCH_NOW%"=="no" goto :SKIP_LAUNCH
echo.
echo  Starting agent in a new window...
start "Dacexy Agent v22.0" "%START_BAT%"
echo  Agent window opened! Login prompt will appear there.
goto :FINISH

:SKIP_LAUNCH
echo  Run "Dacexy Agent" from your Desktop when ready.

:FINISH
echo.
echo  Press any key to close this installer.
pause >nul
exit /b 0
