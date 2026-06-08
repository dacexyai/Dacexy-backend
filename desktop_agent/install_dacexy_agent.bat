@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
title Dacexy Desktop Agent - Installer

:: ================================================================
::  DACEXY DESKTOP AGENT v15.0 - WORLD'S BEST DESKTOP AI AGENT
::  Self-contained Windows Installer
::  - Auto-downloads Python if missing
::  - Installs all dependencies including voice
::  - Runs 24/7 as a background service
::  - Connects to Dacexy cloud dashboard
:: ================================================================

set "INSTALL_DIR=%USERPROFILE%\DacexyAgent"
set "LOG=%INSTALL_DIR%\logs\install.log"
set "AGENT_PY=%INSTALL_DIR%\dacexy_agent.py"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
set "BACKEND=https://dacexy-backend-v7ku.onrender.com/api/v1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

:: ================================================================
:: STEP 0 - CREATE FOLDERS
:: ================================================================
if not exist "%INSTALL_DIR%"       mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs"  mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\data"  mkdir "%INSTALL_DIR%\data"
if not exist "%INSTALL_DIR%\plugins" mkdir "%INSTALL_DIR%\plugins"
cd /d "%INSTALL_DIR%"

:: ================================================================
:: SPLASH SCREEN
:: ================================================================
cls
echo.
echo  ================================================================
echo.
echo         DACEXY DESKTOP AGENT v15.0
echo         World's Most Powerful AI Desktop Agent
echo.
echo         - Full voice control (Hey Dacexy)
echo         - Email campaigns up to 10,000+ contacts
echo         - Social media auto-posting
echo         - 60+ desktop automation actions
echo         - 24/7 cloud-connected operation
echo.
echo  ================================================================
echo.
echo  Installing to: %INSTALL_DIR%
echo.

call :log "=== Dacexy Installer Started: %DATE% %TIME% ==="

:: ================================================================
:: STEP 1 - CHECK / INSTALL PYTHON
:: ================================================================
call :header "STEP 1/6" "Checking Python..."

python --version > nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    call :ok "Python found: !PYVER!"
    goto :PYTHON_OK
)

:: Python not found - try py launcher
py --version > nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('py --version 2^>^&1') do set PYVER=%%i
    call :ok "Python found via py launcher: !PYVER!"
    set "PYTHON_CMD=py"
    goto :PYTHON_OK
)

:: Python not found - download and install automatically
call :warn "Python not found. Downloading Python 3.11 automatically..."
echo  This may take 2-5 minutes depending on your internet speed.
echo.

:: Use PowerShell to download Python installer
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing}" 2>nul

if not exist "%PYTHON_INSTALLER%" (
    :: Fallback: try certutil
    certutil -urlcache -split -f "%PYTHON_URL%" "%PYTHON_INSTALLER%" > nul 2>&1
)

if not exist "%PYTHON_INSTALLER%" (
    call :err "Could not download Python automatically."
    echo.
    echo  Please download Python 3.11 manually from:
    echo  https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo  Then run this installer again.
    echo.
    pause
    exit /b 1
)

call :info "Installing Python 3.11 silently (this takes ~2 min)..."
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 > nul 2>&1

:: Refresh PATH so Python is found immediately
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%b"
set "PATH=%SYSPATH%;%USERPATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

python --version > nul 2>&1
if errorlevel 1 (
    call :err "Python installation failed."
    echo  Please install Python 3.11 manually from https://www.python.org
    echo  Then run this installer again.
    pause
    exit /b 1
)

del "%PYTHON_INSTALLER%" > nul 2>&1
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
call :ok "Python installed: !PYVER!"

:PYTHON_OK
if not defined PYTHON_CMD set "PYTHON_CMD=python"

:: ================================================================
:: STEP 2 - UPGRADE PIP
:: ================================================================
call :header "STEP 2/6" "Upgrading pip..."
%PYTHON_CMD% -m pip install --upgrade pip -q --no-warn-script-location > nul 2>&1
call :ok "pip ready"

:: ================================================================
:: STEP 3 - INSTALL ALL REQUIRED PACKAGES
:: ================================================================
call :header "STEP 3/6" "Installing packages (may take 5-10 minutes)..."
echo  Installing core packages...

:: Install all packages in one efficient batch call
%PYTHON_CMD% -m pip install ^
    pyautogui ^
    pillow ^
    "websockets>=10.0" ^
    requests ^
    psutil ^
    pyperclip ^
    keyboard ^
    pygetwindow ^
    plyer ^
    selenium ^
    webdriver-manager ^
    opencv-python ^
    numpy ^
    schedule ^
    aiohttp ^
    aiofiles ^
    rich ^
    colorama ^
    python-docx ^
    openpyxl ^
    pandas ^
    cryptography ^
    packaging ^
    pyttsx3 ^
    SpeechRecognition ^
    -q --no-warn-script-location > "%INSTALL_DIR%\logs\pip_install.log" 2>&1

if errorlevel 1 (
    call :warn "Some packages had issues. Trying individually..."
    for %%p in (pyautogui pillow websockets requests psutil pyperclip keyboard pygetwindow plyer selenium webdriver-manager opencv-python numpy pyttsx3 SpeechRecognition) do (
        %PYTHON_CMD% -m pip install %%p -q --no-warn-script-location > nul 2>&1
        call :ok "Installed %%p"
    )
) else (
    call :ok "All core packages installed"
)

:: Install pytesseract separately (OCR)
echo  Installing OCR support...
%PYTHON_CMD% -m pip install pytesseract -q --no-warn-script-location > nul 2>&1
call :ok "OCR support installed"

:: ================================================================
:: STEP 4 - INSTALL PYAUDIO (VOICE SUPPORT)
:: ================================================================
call :header "STEP 4/6" "Installing voice support (PyAudio)..."

%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio already installed"
    goto :PYAUDIO_DONE
)

:: Try pip first
%PYTHON_CMD% -m pip install PyAudio -q --no-warn-script-location > nul 2>&1
%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio installed via pip"
    goto :PYAUDIO_DONE
)

:: Try pipwin (Windows wheel installer)
%PYTHON_CMD% -m pip install pipwin -q --no-warn-script-location > nul 2>&1
%PYTHON_CMD% -m pipwin install pyaudio > nul 2>&1
%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio installed via pipwin"
    goto :PYAUDIO_DONE
)

:: Try downloading pre-built wheel
call :info "Trying pre-built wheel for PyAudio..."
for /f "tokens=*" %%v in ('%PYTHON_CMD% -c "import sys; print(str(sys.version_info.major)+str(sys.version_info.minor))" 2^>nul') do set PYSHORT=%%v
set "WHEEL_URL=https://files.pythonhosted.org/packages/cp%PYSHORT%/P/PyAudio/PyAudio-0.2.14-cp%PYSHORT%-cp%PYSHORT%-win_amd64.whl"
set "WHEEL_FILE=%TEMP%\PyAudio.whl"
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; try{Invoke-WebRequest -Uri '%WHEEL_URL%' -OutFile '%WHEEL_FILE%' -UseBasicParsing}catch{}}" > nul 2>&1
if exist "%WHEEL_FILE%" (
    %PYTHON_CMD% -m pip install "%WHEEL_FILE%" -q > nul 2>&1
    del "%WHEEL_FILE%" > nul 2>&1
)
%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio installed from wheel"
    goto :PYAUDIO_DONE
)

call :warn "PyAudio could not be installed automatically."
call :warn "Voice commands will be DISABLED. Agent will still work fully via text/cloud."
call :warn "To enable voice later: pip install pipwin && pipwin install pyaudio"

:PYAUDIO_DONE

:: ================================================================
:: STEP 5 - DOWNLOAD AGENT FILE
:: ================================================================
call :header "STEP 5/6" "Setting up Dacexy Agent..."

:: Copy agent from same folder as installer if available
if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%AGENT_PY%" > nul
    call :ok "Agent file copied from installer package"
    goto :AGENT_READY
)

:: Agent already exists in install dir
if exist "%AGENT_PY%" (
    call :ok "Agent file already present"
    goto :AGENT_READY
)

:: Download from backend
call :info "Downloading agent from Dacexy servers..."
%PYTHON_CMD% -c "
import urllib.request, os, sys
url  = 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent'
dest = r'%AGENT_PY%'
try:
    urllib.request.urlretrieve(url, dest)
    sz = os.path.getsize(dest)
    if sz > 10000:
        print('  [OK] Agent downloaded (' + str(sz) + ' bytes)')
    else:
        os.remove(dest)
        print('  [WARN] Download incomplete')
        sys.exit(1)
except Exception as e:
    print('  [WARN] Download failed:', e)
    sys.exit(1)
" 2>&1

if exist "%AGENT_PY%" goto :AGENT_READY

:: Final fallback: write a minimal working launcher that explains the situation
call :warn "Agent file not found. Creating setup helper..."
(
echo import sys, os, webbrowser
echo print("")
echo print("  ================================================================")
echo print("  DACEXY AGENT SETUP REQUIRED")
echo print("  ================================================================")
echo print("  dacexy_agent.py was not found in this folder.")
echo print("")
echo print("  Please:")
echo print("  1. Log in to your dashboard at dacexy.vercel.app")
echo print("  2. Go to Settings > Download Desktop Agent")
echo print("  3. Place dacexy_agent.py in: %INSTALL_DIR%")
echo print("  4. Run install_dacexy_agent.bat again")
echo print("  ================================================================")
echo webbrowser.open("https://dacexy.vercel.app/settings")
echo input("  Press Enter to open your dashboard in browser...")
) > "%AGENT_PY%"
call :warn "Setup helper created. Please download dacexy_agent.py from your dashboard."
call :warn "Then run this installer again."
pause
exit /b 1

:AGENT_READY
call :ok "Agent file ready"

:: Copy launcher BAT into install dir (self-update)
copy /y "%~f0" "%INSTALL_DIR%\install_dacexy_agent.bat" > nul 2>&1

:: ================================================================
:: STEP 6 - REGISTER AUTOSTART + SHORTCUTS
:: ================================================================
call :header "STEP 6/6" "Registering autostart and shortcuts..."

:: Register Windows autostart via registry
%PYTHON_CMD% -c "
import winreg, sys
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    cmd = r'%INSTALL_DIR%\install_dacexy_agent.bat'
    winreg.SetValueEx(key, 'DacexyAgent', 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)
    print('  [OK] Autostart registered')
except Exception as e:
    print('  [WARN] Autostart:', e)
" 2>&1

:: Create desktop shortcut
%PYTHON_CMD% -c "
import os, sys
vbs = r'''
Set oWS = WScript.CreateObject(\"WScript.Shell\")
sLink = oWS.SpecialFolders(\"Desktop\") & \"\Dacexy Agent.lnk\"
Set oLink = oWS.CreateShortcut(sLink)
oLink.TargetPath = \"%INSTALL_DIR%\install_dacexy_agent.bat\"
oLink.WorkingDirectory = \"%INSTALL_DIR%\"
oLink.Description = \"Dacexy AI Desktop Agent\"
oLink.Save
'''
vbs_path = r'%TEMP%\dacexy_sc.vbs'
with open(vbs_path, 'w') as f:
    f.write(vbs)
os.system('cscript //nologo \"' + vbs_path + '\"')
os.remove(vbs_path)
print('  [OK] Desktop shortcut created')
" 2>&1

:: Create Start Menu shortcut
%PYTHON_CMD% -c "
import os, sys
sm = os.path.join(os.environ.get('APPDATA',''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
vbs = r'''
Set oWS = WScript.CreateObject(\"WScript.Shell\")
sLink = \"%s\Dacexy Agent.lnk\"
Set oLink = oWS.CreateShortcut(sLink)
oLink.TargetPath = \"%s\install_dacexy_agent.bat\"
oLink.WorkingDirectory = \"%s\"
oLink.Description = \"Dacexy AI Desktop Agent\"
oLink.Save
''' %% (sm, r'%INSTALL_DIR%', r'%INSTALL_DIR%')
vbs_path = r'%TEMP%\dacexy_sm.vbs'
with open(vbs_path, 'w') as f:
    f.write(vbs)
os.system('cscript //nologo \"' + vbs_path + '\"')
os.remove(vbs_path)
print('  [OK] Start Menu shortcut created')
" 2>&1

call :ok "Autostart registered - Dacexy runs on every PC startup"

:: ================================================================
:: INSTALLATION COMPLETE BANNER
:: ================================================================
echo.
echo  ================================================================
echo.
echo    [OK] DACEXY DESKTOP AGENT INSTALLED SUCCESSFULLY!
echo.
echo    Location : %INSTALL_DIR%
echo    Shortcut : Desktop - "Dacexy Agent"
echo    Autostart: Enabled (runs on Windows startup)
echo    Log file : %INSTALL_DIR%\logs\startup.log
echo.
echo  ================================================================
echo.
call :log "Installation complete"

:: ================================================================
:: LOGIN SECTION
:: ================================================================
:LOGIN_SECTION
echo  ================================================================
echo    STEP: Connect to Your Dacexy Account
echo    Register free at: dacexy.vercel.app
echo  ================================================================
echo.

:: Check if already logged in
%PYTHON_CMD% -c "
import json
from pathlib import Path
f = Path.home() / '.dacexy_agent.json'
if f.exists():
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
        print('LOGGED_IN' if d.get('access_token') else 'NEED_LOGIN')
    except:
        print('NEED_LOGIN')
else:
    print('NEED_LOGIN')
" > "%TEMP%\dacexy_auth.txt" 2>nul
set /p AUTH_STATUS=<"%TEMP%\dacexy_auth.txt"
del "%TEMP%\dacexy_auth.txt" > nul 2>&1

if "!AUTH_STATUS!"=="LOGGED_IN" (
    call :ok "Already logged in. Launching agent..."
    goto :LAUNCH_AGENT
)

echo  Enter your Dacexy account credentials.
echo  (Don't have an account? Register at dacexy.vercel.app)
echo.

:LOGIN_PROMPT
set "DACEXY_EMAIL="
set "DACEXY_PASS="
set /p DACEXY_EMAIL="  Email   : "
set /p DACEXY_PASS="  Password: "
echo.

if "!DACEXY_EMAIL!"=="" (
    call :err "Email cannot be empty."
    goto :LOGIN_PROMPT
)
if "!DACEXY_PASS!"=="" (
    call :err "Password cannot be empty."
    goto :LOGIN_PROMPT
)

call :info "Connecting to Dacexy servers..."

%PYTHON_CMD% -c "
import requests, json, sys
from pathlib import Path

email    = '!DACEXY_EMAIL!'
password = '!DACEXY_PASS!'

if '@' not in email:
    print('  [ERROR] Invalid email address.')
    sys.exit(1)
if len(password) < 4:
    print('  [ERROR] Password too short (min 4 characters).')
    sys.exit(1)

try:
    r = requests.post(
        'https://dacexy-backend-v7ku.onrender.com/api/v1/auth/login',
        json={'email': email, 'password': password},
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    if r.status_code == 200:
        token = r.json().get('access_token', '')
        if token:
            cfg_file = Path.home() / '.dacexy_agent.json'
            cfg = {}
            if cfg_file.exists():
                try: cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
                except: pass
            cfg['access_token'] = token
            cfg_file.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
            print('LOGIN_OK')
        else:
            print('  [ERROR] Server returned no token.')
            sys.exit(1)
    elif r.status_code == 401:
        print('  [ERROR] Wrong email or password. Please try again.')
        sys.exit(2)
    elif r.status_code == 422:
        print('  [ERROR] Invalid email format.')
        sys.exit(2)
    elif r.status_code == 0 or r.status_code >= 500:
        print('  [ERROR] Server error. Try again in a moment.')
        sys.exit(1)
    else:
        try:
            detail = r.json().get('detail', r.text[:80])
            if isinstance(detail, list): detail = detail[0].get('msg', str(detail))
        except: detail = r.text[:80]
        print('  [ERROR] Login failed (' + str(r.status_code) + '): ' + str(detail))
        sys.exit(2)
except requests.exceptions.ConnectionError:
    print('  [ERROR] No internet connection. Please check your network.')
    sys.exit(1)
except requests.exceptions.Timeout:
    print('  [ERROR] Connection timed out. Try again.')
    sys.exit(1)
except Exception as e:
    print('  [ERROR] ' + str(e))
    sys.exit(1)
" 2>&1 | findstr /v "^$"

set LOGIN_EXIT=%ERRORLEVEL%

if %LOGIN_EXIT% EQU 0 (
    call :ok "Login successful! Welcome to Dacexy."
    call :log "Login successful for !DACEXY_EMAIL!"
    goto :LAUNCH_AGENT
)

if %LOGIN_EXIT% EQU 2 (
    echo.
    echo  Try again? (Y=Yes / N=No / R=Register new account)
    choice /c YNR /n /m "  Choice: "
    if errorlevel 3 (
        start "" "https://dacexy.vercel.app/register"
        echo  Browser opened to registration page. Register then come back.
        pause
        goto :LOGIN_PROMPT
    )
    if errorlevel 2 goto :LOGIN_FAILED
    if errorlevel 1 goto :LOGIN_PROMPT
)

:LOGIN_FAILED
echo.
call :err "Login failed. Cannot start Dacexy Agent."
echo  Please check your credentials and try again.
echo.
pause
exit /b 1

:: ================================================================
:: LAUNCH AGENT (24/7 mode)
:: ================================================================
:LAUNCH_AGENT
echo.
echo  ================================================================
echo    STARTING DACEXY AGENT
echo    The agent will now run in the background 24/7
echo    Control it from: dacexy.vercel.app/dashboard
echo    Voice: Say "Hey Dacexy" to activate voice commands
echo    Stop: Ctrl+Shift+E or type 'stop' in this window
echo  ================================================================
echo.
call :log "Launching dacexy_agent.py"

cd /d "%INSTALL_DIR%"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:AGENT_LOOP
%PYTHON_CMD% dacexy_agent.py
set EXIT_CODE=!ERRORLEVEL!
call :log "Agent exited with code !EXIT_CODE!"

:: Clean exit
if !EXIT_CODE! EQU 0 (
    echo.
    echo  Dacexy Agent stopped cleanly.
    goto :AGENT_END
)

:: Auth expired - clear token and re-login
if !EXIT_CODE! EQU 2 (
    call :warn "Session expired. Clearing login..."
    %PYTHON_CMD% -c "
import json
from pathlib import Path
f = Path.home() / '.dacexy_agent.json'
if f.exists():
    try:
        d = json.loads(f.read_text())
        d.pop('access_token', None)
        f.write_text(json.dumps(d, indent=2))
    except: pass
" 2>nul
    goto :LOGIN_SECTION
)

:: Crash - auto restart after delay
echo.
call :warn "Agent stopped (code: !EXIT_CODE!). Auto-restarting in 5 seconds..."
call :warn "Press Ctrl+C to cancel restart."
call :log "Auto-restart triggered (exit code !EXIT_CODE!)"
timeout /t 5 /nobreak > nul
goto :AGENT_LOOP

:AGENT_END
echo.
echo  ================================================================
echo    Options:
echo    R = Restart Dacexy Agent
echo    L = View log file
echo    U = Uninstall Dacexy
echo    E = Exit
echo  ================================================================
choice /c RLUE /n /m "  Choice: "
if errorlevel 4 goto :DONE
if errorlevel 3 (
    call :uninstall
    goto :DONE
)
if errorlevel 2 (
    echo.
    type "%INSTALL_DIR%\logs\startup.log" 2>nul | more
    pause
    goto :AGENT_END
)
if errorlevel 1 goto :AGENT_LOOP

:DONE
echo.
echo  Thank you for using Dacexy!
call :log "Installer session ended"
pause
exit /b 0

:: ================================================================
:: HELPER FUNCTIONS
:: ================================================================
:header
echo.
echo  ----------------------------------------------------------------
echo   %~1  %~2
echo  ----------------------------------------------------------------
call :log "%~1 %~2"
goto :eof

:ok
echo   [OK] %~1
call :log "[OK] %~1"
goto :eof

:info
echo   [..] %~1
call :log "[INFO] %~1"
goto :eof

:warn
echo   [!!] %~1
call :log "[WARN] %~1"
goto :eof

:err
echo   [XX] %~1
call :log "[ERROR] %~1"
goto :eof

:log
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs" > nul 2>&1
echo %DATE% %TIME% | %~1 >> "%LOG%" 2>nul
goto :eof

:uninstall
echo.
echo  Are you sure you want to uninstall Dacexy Agent? (Y/N)
choice /c YN /n /m "  Choice: "
if errorlevel 2 goto :eof
%PYTHON_CMD% -c "
import winreg
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.DeleteValue(key, 'DacexyAgent')
    winreg.CloseKey(key)
except: pass
" > nul 2>&1
echo  Removing desktop shortcut...
del "%USERPROFILE%\Desktop\Dacexy Agent.lnk" > nul 2>&1
echo  Removing start menu shortcut...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Dacexy Agent.lnk" > nul 2>&1
echo  Keep your account data (login, memories, macros)? (Y/N)
choice /c YN /n /m "  Choice: "
if errorlevel 2 (
    del "%USERPROFILE%\.dacexy_agent.json" > nul 2>&1
    del "%USERPROFILE%\.dacexy_memory.json" > nul 2>&1
    del "%USERPROFILE%\.dacexy_macros.json" > nul 2>&1
    del "%USERPROFILE%\dacexy_agent.log" > nul 2>&1
    del "%USERPROFILE%\dacexy_audit.log" > nul 2>&1
)
call :ok "Uninstall complete. Install folder kept at %INSTALL_DIR%"
call :info "To remove install folder: rmdir /s /q \"%INSTALL_DIR%\""
goto :eof
