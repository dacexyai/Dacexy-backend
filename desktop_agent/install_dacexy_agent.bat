@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v25.0 Installer
color 0A

echo.
echo  ===================================================
echo   DACEXY Desktop Agent v25.0 - Installer
echo  ===================================================
echo.

set "ADIR=%USERPROFILE%\DacexyAgent"
set "APY=%USERPROFILE%\DacexyAgent\dacexy_agent.py"
set "SBAT=%USERPROFILE%\DacexyAgent\start_dacexy.bat"
set "ALOG=%USERPROFILE%\DacexyAgent\install_log.txt"

echo  Installing to: %ADIR%
echo.

if not exist "%ADIR%"              mkdir "%ADIR%"
if not exist "%ADIR%\logs"         mkdir "%ADIR%\logs"
if not exist "%ADIR%\data"         mkdir "%ADIR%\data"
if not exist "%ADIR%\screenshots"  mkdir "%ADIR%\screenshots"

echo Dacexy Install Log %DATE% %TIME% > "%ALOG%"

echo [1/8] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :GET_PYTHON
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i
goto :PY_OK

:GET_PYTHON
echo  Python not found. Downloading Python 3.11.9...
powershell -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py_setup.exe' -UseBasicParsing" >>"%ALOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Python download failed.
    echo  Go to python.org/downloads and install Python 3.11 then re-run.
    pause
    exit /b 1
)
echo  Installing Python...
"%TEMP%\py_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
timeout /t 30 /nobreak >nul
del "%TEMP%\py_setup.exe" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Close this window and re-run installer.
    pause
    exit /b 1
)
echo  Python installed OK!

:PY_OK

echo.
echo [2/8] Upgrading pip...
python -m pip install --upgrade pip --quiet --no-warn-script-location >>"%ALOG%" 2>&1
echo  OK

echo.
echo [3/8] Installing packages...
echo  (Each one shown below. Any failure is non-fatal.)
echo.

python -m pip install pyautogui         --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] pyautogui         || echo  [!] pyautogui failed
python -m pip install pillow            --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] pillow             || echo  [!] pillow failed
python -m pip install websockets        --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] websockets         || echo  [!] websockets failed
python -m pip install requests          --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] requests           || echo  [!] requests failed
python -m pip install pyttsx3           --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] pyttsx3            || echo  [!] pyttsx3 failed
python -m pip install numpy             --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] numpy              || echo  [!] numpy failed
python -m pip install psutil            --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] psutil             || echo  [!] psutil failed
python -m pip install pyperclip         --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] pyperclip          || echo  [!] pyperclip failed
python -m pip install plyer             --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] plyer              || echo  [!] plyer failed
python -m pip install pygetwindow       --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] pygetwindow        || echo  [!] pygetwindow failed
python -m pip install keyboard          --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] keyboard           || echo  [!] keyboard failed
python -m pip install speechrecognition --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] speechrecognition  || echo  [!] speechrecognition failed
python -m pip install beautifulsoup4    --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] beautifulsoup4     || echo  [!] beautifulsoup4 failed
python -m pip install lxml              --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] lxml               || echo  [!] lxml failed
python -m pip install selenium          --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] selenium           || echo  [!] selenium failed
python -m pip install webdriver-manager --quiet --no-warn-script-location >>"%ALOG%" 2>&1 && echo  [+] webdriver-manager  || echo  [!] webdriver-manager failed

echo.
echo  Installing PyAudio for voice control...
python -m pip install PyAudio --quiet --no-warn-script-location >>"%ALOG%" 2>&1
python -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    python -m pip install pipwin --quiet --no-warn-script-location >>"%ALOG%" 2>&1
    python -m pipwin install pyaudio >>"%ALOG%" 2>&1
    python -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [!] PyAudio failed - voice disabled, text commands still work
    ) else (
        echo  [+] PyAudio OK - voice enabled
    )
) else (
    echo  [+] PyAudio OK - voice enabled
)

echo.
echo [4/8] Setting up agent file...

rem --- PRIORITY 1: dacexy_agent.py right next to this installer ---
if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%APY%" >nul 2>&1
    echo  OK: Copied dacexy_agent.py from installer folder
    goto :AGENT_OK
)

rem --- PRIORITY 2: Already installed ---
if exist "%APY%" (
    echo  OK: Agent already present at %APY%
    goto :AGENT_OK
)

rem --- PRIORITY 3: Download from backend ---
echo  Downloading agent from Dacexy server...
powershell -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent' -OutFile '%APY%' -UseBasicParsing; Write-Host 'Downloaded OK' } catch { Write-Host ('FAIL: '+$_.Exception.Message); exit 1 }" >>"%ALOG%" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: dacexy_agent.py could not be downloaded.
    echo  Please place dacexy_agent.py in the same folder as this installer and re-run.
    pause
    exit /b 1
)
echo  OK: Agent downloaded from server

:AGENT_OK

rem Save a copy of this installer in the agent folder
copy /y "%~f0" "%ADIR%\install_dacexy_agent.bat" >nul 2>&1

rem Clear saved token so user logs in fresh
python -c "import json,pathlib; f=pathlib.Path.home()/'.dacexy_agent.json'; d=json.loads(f.read_text()) if f.exists() else {}; d.pop('access_token',None); f.write_text(json.dumps(d,indent=2))" >nul 2>&1

echo.
echo [5/8] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title Dacexy Agent v25.0
echo color 0A
echo set PYTHONIOENCODING=utf-8
echo set PYTHONUTF8=1
echo cd /d "%ADIR%"
echo echo  Dacexy Agent v25.0 starting...
echo echo  Press Ctrl+C to stop.
echo echo.
echo :LOOP
echo python "%APY%"
echo set ECODE=%%ERRORLEVEL%%
echo if %%ECODE%% EQU 0 goto :DONE
echo echo  Restarting in 5 seconds... Ctrl+C to cancel.
echo timeout /t 5 /nobreak ^>nul
echo goto :LOOP
echo :DONE
echo echo  Agent stopped cleanly.
echo pause
) > "%SBAT%"
echo  OK: Launcher created at %SBAT%

echo.
echo [6/8] Creating shortcuts and autostart...
set "VTMP=%TEMP%\dxsc.vbs"
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk"^)
echo oLink.TargetPath = "%SBAT%"
echo oLink.WorkingDirectory = "%ADIR%"
echo oLink.Description = "Dacexy AI Agent"
echo oLink.IconLocation = "shell32.dll,15"
echo oLink.Save
) > "%VTMP%"
cscript /nologo "%VTMP%" >nul 2>&1
del "%VTMP%" >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%SBAT%\"" /f >nul 2>&1
echo  OK: Desktop shortcut created, autostart on login registered

echo.
echo [7/8] Checking what works...
echo.
python -c "import pyautogui; print('  [+] Mouse and keyboard control')" 2>nul
python -c "from PIL import ImageGrab; print('  [+] Screenshot capture')" 2>nul
python -c "import pyaudio; print('  [+] Voice control')" 2>nul
python -c "from selenium import webdriver; print('  [+] Browser automation')" 2>nul
python -c "from bs4 import BeautifulSoup; print('  [+] Web scraping')" 2>nul
python -c "import websockets; print('  [+] Cloud dashboard connection')" 2>nul
python -c "import psutil; print('  [+] System info')" 2>nul
python -c "import smtplib; print('  [+] Email engine')" 2>nul

echo.
echo [8/8] Done!
echo.
echo  ===================================================
echo   DACEXY v25.0 - Installation Complete!
echo  ===================================================
echo.
echo  HOW TO START: Double-click "Dacexy Agent" on your Desktop
echo.
echo  FIRST RUN:   Log in with your dacexy.vercel.app account
echo  THEN TYPE:   configure email  (to enable bulk auto-send)
echo.
echo  WAKE WORDS:  Dacexy / Hey Dacexy / Jarvis / Computer
echo.
echo  EXAMPLE COMMANDS:
echo    open youtube
echo    search for AI news
echo    take a screenshot
echo    what time is it
echo    send email to boss@gmail.com saying hello
echo    configure email
echo    find leads for my product
echo    open chrome
echo    open calculator
echo    scroll down
echo    volume up
echo.
echo  DASHBOARD:   dacexy.vercel.app
echo  LOG FILE:    %ALOG%
echo.
echo  ===================================================
echo.
set /p RUN_NOW="  Launch agent now? (Y/n): "
if /i "%RUN_NOW%"=="n" goto :SKIP
if /i "%RUN_NOW%"=="no" goto :SKIP
echo.
echo  Opening agent in new window...
start "Dacexy Agent v25.0" "%SBAT%"
echo  Done! Login window is now open.
goto :END

:SKIP
echo  Start anytime from Desktop shortcut.

:END
echo.
echo  Press any key to close installer.
pause >nul
exit /b 0
