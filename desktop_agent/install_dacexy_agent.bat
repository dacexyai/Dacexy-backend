@echo off
if /I "%~1"=="--relaunched" goto :MAIN
chcp 65001 >nul 2>&1
start "Dacexy Desktop Agent - Installer" cmd /k "%~f0" --relaunched
exit /b

:MAIN
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Dacexy Desktop Agent - Installer
color 0A

echo.
echo  ===================================================
echo   DACEXY Desktop Agent - Installer
echo  ===================================================
echo.

set "ADIR=%USERPROFILE%\DacexyAgent"
set "APY=%ADIR%\dacexy_agent.py"
set "SBAT=%ADIR%\start_dacexy.bat"
set "ALOG=%ADIR%\install_log.txt"

if not exist "%ADIR%" mkdir "%ADIR%"
if not exist "%ADIR%\logs" mkdir "%ADIR%\logs"
if not exist "%ADIR%\data" mkdir "%ADIR%\data"
if not exist "%ADIR%\agent_reports" mkdir "%ADIR%\agent_reports"
if not exist "%ADIR%\agent_screenshots" mkdir "%ADIR%\agent_screenshots"

echo Dacexy Install Log %DATE% %TIME% > "%ALOG%"
echo  Installing to: %ADIR%
echo.

echo [1/7] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :NO_PYTHON
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  OK: %%i
goto :PY_OK

:NO_PYTHON
echo  Python is not installed or not on PATH.
echo  Install Python 3.11+ from https://www.python.org/downloads/
echo  During install, tick "Add Python to PATH", then run this installer again.
pause
exit /b 1

:PY_OK
echo.
echo [2/7] Copying agent files...
if not exist "%~dp0dacexy_agent.py" (
    echo  ERROR: dacexy_agent.py must be next to this installer.
    pause
    exit /b 1
)
copy /y "%~dp0dacexy_agent.py" "%APY%" >nul
if exist "%~dp0requirements.txt" copy /y "%~dp0requirements.txt" "%ADIR%\requirements.txt" >nul
if exist "%~dp0.env.example" copy /y "%~dp0.env.example" "%ADIR%\.env.example" >nul
if not exist "%ADIR%\.env" if exist "%ADIR%\.env.example" copy /y "%ADIR%\.env.example" "%ADIR%\.env" >nul
python -m py_compile "%APY%" >>"%ALOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Agent file failed Python compile. See %ALOG%
    pause
    exit /b 1
)
echo  OK: Agent installed.

echo.
echo [3/7] Installing Python packages...
python -m pip install --upgrade pip --quiet --no-warn-script-location >>"%ALOG%" 2>&1
if exist "%ADIR%\requirements.txt" (
    python -m pip install -r "%ADIR%\requirements.txt" --quiet --no-warn-script-location >>"%ALOG%" 2>&1
) else (
    python -m pip install pyautogui pillow websockets requests pyttsx3 psutil pyperclip plyer pygetwindow keyboard speechrecognition beautifulsoup4 lxml selenium webdriver-manager pdfplumber openpyxl pandas python-dotenv pypdf python-docx --quiet --no-warn-script-location >>"%ALOG%" 2>&1
)
echo  Package install attempted. Optional packages may be skipped if Windows blocks them.

echo.
echo [4/7] Creating launcher...
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title Dacexy Agent
echo color 0A
echo set PYTHONIOENCODING=utf-8
echo set PYTHONUTF8=1
echo cd /d "%ADIR%"
echo echo  Dacexy Agent starting...
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
echo  OK: %SBAT%

echo.
echo [5/7] Creating desktop shortcut...
set "VTMP=%TEMP%\dacexy_shortcut.vbs"
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk"^)
echo oLink.TargetPath = "%SBAT%"
echo oLink.WorkingDirectory = "%ADIR%"
echo oLink.Description = "Dacexy AI Desktop Agent"
echo oLink.IconLocation = "shell32.dll,15"
echo oLink.Save
) > "%VTMP%"
cscript /nologo "%VTMP%" >nul 2>&1
del "%VTMP%" >nul 2>&1
echo  OK: Desktop shortcut created.

echo.
echo [6/7] Optional cloud/dashboard token...
echo  If your dashboard gives an access token, paste it here.
echo  Otherwise press Enter and the agent will run local-only.
set /p DX_TOKEN="  Token: "
if not "%DX_TOKEN%"=="" (
    cd /d "%ADIR%"
    python "%APY%" --text --no-voice --no-cloud --token "%DX_TOKEN%" --command "health" >>"%ALOG%" 2>&1
    echo  OK: Token saved to %%USERPROFILE%%\.dacexy_agent.json
) else (
    echo  Skipped token setup.
)

echo.
echo [7/7] Autostart...
set /p AUTOSTART="  Start Dacexy automatically on Windows login? (y/N): "
if /i "%AUTOSTART%"=="y" (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /t REG_SZ /d "\"%SBAT%\"" /f >nul 2>&1
    echo  OK: Autostart enabled.
) else (
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DacexyAgent" /f >nul 2>&1
    echo  Autostart skipped.
)

echo.
echo  ===================================================
echo   Installation Complete
echo  ===================================================
echo.
echo  Start from Desktop: Dacexy Agent
echo  Installed at:       %ADIR%
echo  Log file:           %ALOG%
echo.
echo  Commands to try:
echo    open youtube
echo    organize my desktop
echo    process invoices
echo    pending payments
echo    reply to my whatsapp messages
echo    find leads for my product
echo    take a screenshot
echo    ocr screen
echo    list windows
echo    set cloud token YOUR_TOKEN
echo.
set /p RUN_NOW="  Launch agent now? (Y/n): "
if /i "%RUN_NOW%"=="n" goto :END
if /i "%RUN_NOW%"=="no" goto :END
start "Dacexy Agent" "%SBAT%"

:END
echo.
echo  Press any key to close installer.
pause >nul
exit /b 0
