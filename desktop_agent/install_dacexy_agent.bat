@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer v14.0
color 0A

echo.
echo  ═══════════════════════════════════════════════════════
echo    DACEXY Desktop Agent v14.0 ULTIMATE — Installer
echo  ═══════════════════════════════════════════════════════
echo.

:: ── Step 1: Check Python ──────────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found. Downloading Python 3.11.9...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe' -UseBasicParsing"
    if errorlevel 1 (
        echo  ERROR: Could not download Python. Check internet connection.
        pause
        exit /b 1
    )
    echo  Installing Python silently...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    timeout /t 30 /nobreak >nul
    del "%TEMP%\python_installer.exe" >nul 2>&1
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%b"
    set "PATH=%SYSPATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;C:\Python311;C:\Python311\Scripts"
    python --version >nul 2>&1
    if errorlevel 1 (
        echo  Python installed. Please close and re-run this installer.
        pause
        exit /b 0
    )
    echo  Python installed OK.
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i

:: ── Step 2: Create folders ────────────────────────────────────────────
echo.
echo [2/6] Creating folders...
if not exist "%USERPROFILE%\DacexyAgent" mkdir "%USERPROFILE%\DacexyAgent"
if not exist "%USERPROFILE%\DacexyAgent\logs" mkdir "%USERPROFILE%\DacexyAgent\logs"
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ──────────────────────────────────────────
echo.
echo [3/6] Installing Python packages (3-5 minutes first time)...
python -m pip install --upgrade pip --quiet --no-warn-script-location

python -m pip install ^
    pyautogui ^
    pillow ^
    websockets ^
    requests ^
    speechrecognition ^
    pyttsx3 ^
    numpy ^
    psutil ^
    pyperclip ^
    plyer ^
    pygetwindow ^
    keyboard ^
    selenium ^
    webdriver-manager ^
    pytesseract ^
    opencv-python ^
    schedule ^
    aiohttp ^
    aiofiles ^
    rich ^
    colorama ^
    python-docx ^
    openpyxl ^
    pandas ^
    cryptography ^
    pywin32 ^
    --quiet --no-warn-script-location

if errorlevel 1 (
    echo  WARNING: Some packages failed. Installing essential ones individually...
    python -m pip install pyautogui --quiet
    python -m pip install pillow --quiet
    python -m pip install websockets --quiet
    python -m pip install requests --quiet
    python -m pip install pyttsx3 --quiet
    python -m pip install psutil --quiet
    python -m pip install pyperclip --quiet
    python -m pip install pygetwindow --quiet
)

:: Try PyAudio separately (often needs special handling)
python -m pip install PyAudio --quiet --no-warn-script-location 2>nul
if errorlevel 1 (
    python -m pip install pipwin --quiet --no-warn-script-location 2>nul
    python -m pipwin install pyaudio --quiet 2>nul
)

echo  OK: Packages installed

:: ── Step 4: Download agent ────────────────────────────────────────────
echo.
echo [4/6] Downloading Dacexy Agent...
if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    del "%USERPROFILE%\DacexyAgent\dacexy_agent.py"
)

powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host '  OK: Downloaded' } catch { Write-Host ('  ERROR: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo.
    echo  ERROR: Could not download agent script.
    echo  Trying backup method...
    python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py', r'%USERPROFILE%\DacexyAgent\dacexy_agent.py'); print('  OK: Downloaded via Python')"
    if errorlevel 1 (
        echo  ERROR: All download methods failed. Check internet connection.
        pause
        exit /b 1
    )
)

if not exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    echo  ERROR: Agent file not found after download.
    pause
    exit /b 1
)
echo  OK: Agent file ready

:: Clear old token so fresh login is required
if exist "%USERPROFILE%\.dacexy_agent.json" (
    del "%USERPROFILE%\.dacexy_agent.json"
    echo  OK: Old session cleared
)

:: ── Step 5: Create launcher scripts ──────────────────────────────────
echo.
echo [5/6] Creating launchers...

:: Create a robust launch script that keeps window open on error
(
echo @echo off
echo title Dacexy Desktop Agent v14.0
echo color 0A
echo cd /d "%USERPROFILE%\DacexyAgent"
echo echo Starting Dacexy Desktop Agent v14.0...
echo echo Log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo echo.
echo python dacexy_agent.py ^>^> "%USERPROFILE%\DacexyAgent\logs\startup.log" 2^>^&1
echo if errorlevel 1 (
echo     echo.
echo     echo ════════════════════════════════════════════
echo     echo  Dacexy Agent exited with an error.
echo     echo  Check log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo     echo ════════════════════════════════════════════
echo     echo.
echo     type "%USERPROFILE%\DacexyAgent\logs\startup.log"
echo     echo.
echo     pause
echo ^)
) > "%USERPROFILE%\DacexyAgent\launch_dacexy.bat"

:: Create desktop shortcut pointing to launch script
set SCRIPT="%TEMP%\dacexy_sc.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> %SCRIPT%
echo oLink.TargetPath = "%USERPROFILE%\DacexyAgent\launch_dacexy.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Description = "Dacexy Desktop Agent v14.0 ULTIMATE" >> %SCRIPT%
echo oLink.IconLocation = "shell32.dll,15" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo  OK: Desktop shortcut created

:: ── Step 6: Register autostart ────────────────────────────────────────
echo.
echo [6/6] Registering autostart...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%USERPROFILE%\DacexyAgent\launch_dacexy.bat\"" /f >nul 2>&1
echo  OK: Will auto-start with Windows

:: ── Done ─────────────────────────────────────────────────────────────
echo.
echo  ═══════════════════════════════════════════════════════
echo    Installation Complete!
echo  ═══════════════════════════════════════════════════════
echo.
echo  Launching Dacexy Agent now...
echo  (If a login prompt appears, enter your Dacexy email + password)
echo.
echo  If the window closes unexpectedly, check:
echo  %USERPROFILE%\DacexyAgent\logs\startup.log
echo.
pause

start "" "%USERPROFILE%\DacexyAgent\launch_dacexy.bat"
