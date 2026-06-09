@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent Installer
color 0A

echo.
echo  ================================
echo   DACEXY Desktop Agent v11.0
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
echo  OK: %USERPROFILE%\DacexyAgent

:: ── Step 3: Install packages ────────────────────────────────────────────────
echo.
echo [3/5] Installing packages (first run may take 2-3 minutes)...
python -m pip install --upgrade pip --quiet
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard --quiet
if errorlevel 1 (
echo.
echo  WARNING: Some packages failed quietly. Retrying...
python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil pyperclip plyer pygetwindow keyboard
if errorlevel 1 (
echo.
echo  ERROR: Package installation failed. Check your internet connection.
pause
exit /b 1
)
)
echo  OK: All packages installed

:: ── Step 4: Download agent script ──────────────────────────────────────────
echo.
echo [4/5] Downloading Dacexy Agent script...

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

:: Clear old session token
if exist "%USERPROFILE%.dacexy_agent.json" (
echo  Clearing old session token...
del "%USERPROFILE%.dacexy_agent.json"
echo  OK: Old token cleared
)

:: ── Step 5: Create desktop shortcut ────────────────────────────────────────
echo.
echo [5/5] Creating desktop shortcut...
set SCRIPT="%TEMP%\dacexy_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> %SCRIPT%
echo oLink.TargetPath = "cmd.exe" >> %SCRIPT%
echo oLink.Arguments = "/k python %USERPROFILE%\DacexyAgent\dacexy_agent.py" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Description = "Dacexy Desktop Agent v11.0" >> %SCRIPT%
echo oLink.IconLocation = "shell32.dll,15" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo  OK: Shortcut created on Desktop

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
echo  VOICE CONTROL (Siri-like):
echo   - Say "Hey Dacexy" anytime to activate
echo   - Then say your command out loud
echo   - Examples:
echo     "Hey Dacexy, open Chrome"
echo     "Hey Dacexy, search for weather today"
echo     "Hey Dacexy, take a screenshot"
echo     "Hey Dacexy, what time is it"
echo     "Hey Dacexy, type Hello World in Notepad"
echo.
echo  The agent runs 24/7 in the background.
echo  It starts automatically every time Windows starts.
echo.
pause

cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
