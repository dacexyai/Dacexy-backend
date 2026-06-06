@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer v14.0 ULTIMATE
color 0A

echo.
echo  ═══════════════════════════════════════════════════════════
echo    DACEXY Desktop Agent v14.0 ULTIMATE
echo    World's Most Powerful AI Desktop Agent
echo    Voice Control  ^|  Vision  ^|  Email  ^|  Social  ^|  Browser
echo  ═══════════════════════════════════════════════════════════
echo.

goto :main

:main

:: ── Step 1: Check Python ──────────────────────────────────────────────────────
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

    timeout /t 25 /nobreak >nul

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

:: ── Step 2: Create agent folder ──────────────────────────────────────────────
echo.
echo [2/5] Creating Dacexy folder...
if not exist "%USERPROFILE%\DacexyAgent" (
    mkdir "%USERPROFILE%\DacexyAgent"
)
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install all packages ─────────────────────────────────────────────
echo.
echo [3/5] Installing packages (first run: 3-5 minutes)...
echo  This installs AI, vision, browser, voice, and automation libraries.
echo.

python -m pip install --upgrade pip --quiet

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
    imap-tools ^
    cryptography ^
    pywin32 ^
    --quiet

if errorlevel 1 (
    echo.
    echo  WARNING: Some packages had issues. Retrying essential packages...
    python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard
    if errorlevel 1 (
        echo.
        echo  ERROR: Core package installation failed.
        echo  Check your internet connection and try again.
        pause
        exit /b 1
    )
)

:: Try PyAudio (may need special handling)
python -m pip install PyAudio --quiet 2>nul
if errorlevel 1 (
    python -m pip install pipwin --quiet 2>nul
    python -m pipwin install pyaudio --quiet 2>nul
)

echo  OK: All packages installed

:: ── Step 4: Download Dacexy Agent ────────────────────────────────────────────
echo.
echo [4/5] Downloading Dacexy Agent v14.0 ULTIMATE...

if exist "%USERPROFILE%\DacexyAgent\dacexy_agent.py" (
    del "%USERPROFILE%\DacexyAgent\dacexy_agent.py"
)

powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py' -UseBasicParsing; Write-Host '  OK: Agent downloaded successfully' } catch { Write-Host '  ERROR: Download failed -' $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo  ERROR: Could not download agent script.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

:: Clear old session token so user logs in fresh
if exist "%USERPROFILE%\.dacexy_agent.json" (
    echo  Clearing old session...
    del "%USERPROFILE%\.dacexy_agent.json"
    echo  OK: Session cleared
)

:: ── Step 5: Create desktop shortcut ──────────────────────────────────────────
echo.
echo [5/5] Creating desktop shortcut...

set SCRIPT="%TEMP%\dacexy_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> %SCRIPT%
echo oLink.TargetPath = "cmd.exe" >> %SCRIPT%
echo oLink.Arguments = "/k python %USERPROFILE%\DacexyAgent\dacexy_agent.py" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Description = "Dacexy Desktop Agent v14.0 ULTIMATE" >> %SCRIPT%
echo oLink.IconLocation = "shell32.dll,15" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo  OK: Shortcut created on your Desktop

:: ── DONE ─────────────────────────────────────────────────────────────────────
echo.
echo  ═══════════════════════════════════════════════════════════
echo    Installation Complete! Launching Dacexy Agent...
echo  ═══════════════════════════════════════════════════════════
echo.
echo  HOW TO USE:
echo.
echo  1. LOGIN: Enter your Dacexy email and password when prompted.
echo.
echo  2. VOICE COMMANDS (hands-free control):
echo     Say any of these wake words, then your command:
echo       "Hey Dacexy, ..."
echo       "Dacexy, ..."
echo       "Assistant, ..."
echo.
echo  3. EXAMPLE VOICE COMMANDS:
echo     Hey Dacexy, take a screenshot
echo     Hey Dacexy, open Chrome and go to google.com
echo     Hey Dacexy, search for latest AI news
echo     Hey Dacexy, send bulk emails to my list
echo     Hey Dacexy, post to LinkedIn
echo     Hey Dacexy, what's on my screen
echo     Hey Dacexy, system info
echo     Hey Dacexy, what time is it
echo     Hey Dacexy, open Notepad and type Hello World
echo     Hey Dacexy, take notes from screen
echo.
echo  4. SHELL COMMANDS (type directly):
echo     bulk email       - Send 1000+ emails
echo     whatsapp bulk    - Send bulk WhatsApp messages
echo     twitter post     - Post to Twitter/X
echo     linkedin post    - Post to LinkedIn
echo     instagram post   - Post to Instagram
echo     youtube upload   - Upload to YouTube
echo     tiktok post      - Post to TikTok
echo     post all         - Post to ALL platforms at once
echo     browser [url]    - Open URL in Chrome
echo     google [query]   - Google search
echo     research [topic] - Deep research with AI
echo     screenshot       - Capture screen
echo     ocr              - Read text from screen
echo     detect ui        - Detect buttons/forms
echo     plan [task]      - AI plans + executes task
echo     swarm [task]     - 10-agent AI swarm
echo     memory           - Show AI memory
echo     skills           - Show learned skills
echo     sysinfo          - System health
echo     jobs             - Scheduled jobs
echo     backup [folder]  - Backup folder
echo     organize [folder]- Auto-organize files
echo     stop             - Emergency stop
echo.
echo  5. KEYBOARD SHORTCUTS:
echo     Ctrl+Shift+D  = Status check
echo     Ctrl+Shift+S  = Screenshot
echo     Ctrl+Shift+E  = Emergency Stop
echo     Ctrl+Shift+M  = Memory summary
echo     Ctrl+Shift+V  = Toggle voice on/off
echo     Ctrl+Shift+H  = Health check
echo     Ctrl+Shift+I  = Skills and memory info
echo.
echo  6. The agent runs 24/7 in the background.
echo     It starts automatically every time Windows starts.
echo.
echo  ═══════════════════════════════════════════════════════════
echo.
pause

cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
