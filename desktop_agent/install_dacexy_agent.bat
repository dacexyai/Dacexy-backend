@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul 2>&1
title Dacexy Desktop Agent - Installer

:: ================================================================
::  DACEXY DESKTOP AGENT v15.0 - WORLD'S BEST DESKTOP AI AGENT
::  Self-contained Windows Installer
:: ================================================================

:: ----------------------------------------------------------------
:: FIX: Keep window open on ANY unexpected exit
:: ----------------------------------------------------------------
if "%~1"=="__CHILD__" goto :MAIN_ENTRY
cmd /k "%~f0" __CHILD__
exit /b

:MAIN_ENTRY

set "INSTALL_DIR=%USERPROFILE%\DacexyAgent"
set "LOG=%INSTALL_DIR%\logs\install.log"
set "AGENT_PY=%INSTALL_DIR%\dacexy_agent.py"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
set "BACKEND=https://dacexy-backend-v7ku.onrender.com/api/v1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHON_CMD="

:: ================================================================
:: STEP 0 - CREATE FOLDERS
:: ================================================================
if not exist "%INSTALL_DIR%"         mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs"    mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\data"    mkdir "%INSTALL_DIR%\data"
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

:: Try python command
python --version > nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    call :ok "Python found: !PYVER!"
    set "PYTHON_CMD=python"
    goto :PYTHON_OK
)

:: Try py launcher
py --version > nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('py --version 2^>^&1') do set PYVER=%%i
    call :ok "Python found via py launcher: !PYVER!"
    set "PYTHON_CMD=py"
    goto :PYTHON_OK
)

:: Try common install paths directly
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
) do (
    if exist %%P (
        set "PYTHON_CMD=%%~P"
        call :ok "Python found at %%~P"
        goto :PYTHON_OK
    )
)

:: Python not found - download and install automatically
call :warn "Python not found. Downloading Python 3.11 automatically..."
echo  This may take 2-5 minutes depending on your internet speed.
echo.

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing}" 2>nul

if not exist "%PYTHON_INSTALLER%" (
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
    call :fatal_pause
)

call :info "Installing Python 3.11 silently (this takes ~2 min)..."
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1

:: Refresh PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%b"
set "PATH=%SYSPATH%;%USERPATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

python --version > nul 2>&1
if errorlevel 1 (
    call :err "Python installation failed."
    echo  Please install Python 3.11 manually from https://www.python.org
    echo  Then run this installer again.
    call :fatal_pause
)

del "%PYTHON_INSTALLER%" > nul 2>&1
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
call :ok "Python installed: !PYVER!"
set "PYTHON_CMD=python"

:PYTHON_OK

:: ================================================================
:: STEP 2 - UPGRADE PIP
:: ================================================================
call :header "STEP 2/6" "Upgrading pip..."
%PYTHON_CMD% -m pip install --upgrade pip -q --no-warn-script-location > nul 2>&1
if errorlevel 1 (
    call :warn "pip upgrade failed, continuing with existing pip..."
) else (
    call :ok "pip ready"
)

:: ================================================================
:: STEP 3 - INSTALL ALL REQUIRED PACKAGES
:: ================================================================
call :header "STEP 3/6" "Installing packages (may take 5-10 minutes)..."
echo  Installing core packages...

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
    call :warn "Batch install had issues. Trying individually..."
    for %%p in (pyautogui pillow websockets requests psutil pyperclip keyboard pygetwindow plyer selenium webdriver-manager opencv-python numpy pyttsx3 SpeechRecognition colorama packaging cryptography) do (
        %PYTHON_CMD% -m pip install %%p -q --no-warn-script-location > nul 2>&1
        if errorlevel 1 (
            call :warn "Could not install %%p - will skip"
        ) else (
            call :ok "Installed %%p"
        )
    )
) else (
    call :ok "All core packages installed"
)

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

%PYTHON_CMD% -m pip install PyAudio -q --no-warn-script-location > nul 2>&1
%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio installed via pip"
    goto :PYAUDIO_DONE
)

%PYTHON_CMD% -m pip install pipwin -q --no-warn-script-location > nul 2>&1
%PYTHON_CMD% -m pipwin install pyaudio > nul 2>&1
%PYTHON_CMD% -c "import pyaudio" > nul 2>&1
if not errorlevel 1 (
    call :ok "PyAudio installed via pipwin"
    goto :PYAUDIO_DONE
)

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

call :warn "PyAudio could not be installed - voice disabled. Agent still works fully via text/cloud."
call :warn "To enable voice later: pip install pipwin && pipwin install pyaudio"

:PYAUDIO_DONE

:: ================================================================
:: STEP 5 - LOCATE / DOWNLOAD AGENT FILE
:: ================================================================
call :header "STEP 5/6" "Setting up Dacexy Agent..."

if exist "%~dp0dacexy_agent.py" (
    copy /y "%~dp0dacexy_agent.py" "%AGENT_PY%" > nul
    call :ok "Agent file copied from installer package"
    goto :AGENT_READY
)

if exist "%AGENT_PY%" (
    call :ok "Agent file already present"
    goto :AGENT_READY
)

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

call :err "Agent file (dacexy_agent.py) not found and could not be downloaded."
echo.
echo  Please place dacexy_agent.py in the same folder as this installer:
echo  %~dp0
echo  Then run this installer again.
echo.
echo  Or download from: dacexy.vercel.app/settings
start "" "https://dacexy.vercel.app/settings"
call :fatal_pause

:AGENT_READY
call :ok "Agent file ready"
copy /y "%~f0" "%INSTALL_DIR%\install_dacexy_agent.bat" > nul 2>&1

:: ================================================================
:: STEP 6 - REGISTER AUTOSTART + SHORTCUTS
:: ================================================================
call :header "STEP 6/6" "Registering autostart and shortcuts..."

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

%PYTHON_CMD% -c "
import os
vbs = '''
Set oWS = WScript.CreateObject(\"WScript.Shell\")
sLink = oWS.SpecialFolders(\"Desktop\") & \"\Dacexy Agent.lnk\"
Set oLink = oWS.CreateShortcut(sLink)
oLink.TargetPath = \"%INSTALL_DIR%\install_dacexy_agent.bat\"
oLink.WorkingDirectory = \"%INSTALL_DIR%\"
oLink.Description = \"Dacexy AI Desktop Agent\"
oLink.Save
'''
vbs_path = r'%TEMP%\dacexy_sc.vbs'
open(vbs_path, 'w').write(vbs)
os.system('cscript //nologo \"' + vbs_path + '\"')
os.remove(vbs_path)
print('  [OK] Desktop shortcut created')
" 2>&1

call :ok "Autostart registered - Dacexy runs on every PC startup"

:: ================================================================
:: INSTALLATION COMPLETE
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
echo  (No account? Register at dacexy.vercel.app)
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
    sys.exit(2)
if len(password) < 4:
    print('  [ERROR] Password too short (min 4 characters).')
    sys.exit(2)

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
    elif r.status_code in (401, 403):
        print('  [ERROR] Wrong email or password. Please try again.')
        sys.exit(2)
    elif r.status_code == 422:
        print('  [ERROR] Invalid email format.')
        sys.exit(2)
    elif r.status_code >= 500:
        print('  [ERROR] Server error (' + str(r.status_code) + '). Try again in a moment.')
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
" 2>&1
set LOGIN_EXIT=!ERRORLEVEL!

:: Check if LOGIN_OK was printed
findstr /C:"LOGIN_OK" "%TEMP%\dacexy_login_result.txt" > nul 2>&1

if !LOGIN_EXIT! EQU 0 (
    call :ok "Login successful! Welcome to Dacexy."
    call :log "Login successful for !DACEXY_EMAIL!"
    goto :LAUNCH_AGENT
)

if !LOGIN_EXIT! EQU 2 (
    echo.
    echo  Try again? (Y=Yes / N=No / R=Register new account)
    choice /c YNR /n /m "  Choice: "
    if errorlevel 3 (
        start "" "https://dacexy.vercel.app/register"
        echo  Browser opened to registration page. Register then come back.
        pause
        goto :LOGIN_PROMPT
    )
    if errorlevel 2 (
        call :err "Login cancelled. Exiting."
        call :fatal_pause
    )
    if errorlevel 1 goto :LOGIN_PROMPT
)

echo.
echo  Login failed (network or server issue). Try again? (Y/N)
choice /c YN /n /m "  Choice: "
if errorlevel 2 (
    call :err "Login failed. Cannot start Dacexy Agent."
    call :fatal_pause
)
goto :LOGIN_PROMPT

:: ================================================================
:: LAUNCH AGENT (24/7 mode)
:: ================================================================
:LAUNCH_AGENT
echo.
echo  ================================================================
echo    STARTING DACEXY AGENT
echo    Running in background 24/7
echo    Dashboard: dacexy.vercel.app/dashboard
echo    Voice    : Say "Hey Dacexy" to activate
echo    Stop     : Ctrl+Shift+E or type 'stop' in this window
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

if !EXIT_CODE! EQU 0 (
    echo.
    echo  Dacexy Agent stopped cleanly.
    goto :AGENT_END
)

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

echo.
call :warn "Agent stopped (code: !EXIT_CODE!). Auto-restarting in 5 seconds..."
call :warn "Press Ctrl+C to cancel restart."
call :log "Auto-restart triggered (exit code !EXIT_CODE!)"
timeout /t 5 /nobreak > nul
goto :AGENT_LOOP

:AGENT_END
echo.
echo  ================================================================
echo    R = Restart  |  L = View log  |  U = Uninstall  |  E = Exit
echo  ================================================================
choice /c RLUE /n /m "  Choice: "
if errorlevel 4 goto :DONE
if errorlevel 3 ( call :uninstall & goto :DONE )
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

:fatal_pause
echo.
echo  ================================================================
echo   Press any key to exit...
echo  ================================================================
pause > nul
exit /b 1

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
del "%USERPROFILE%\Desktop\Dacexy Agent.lnk" > nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Dacexy Agent.lnk" > nul 2>&1
echo  Keep your account data? (Y/N)
choice /c YN /n /m "  Choice: "
if errorlevel 2 (
    del "%USERPROFILE%\.dacexy_agent.json" > nul 2>&1
    del "%USERPROFILE%\.dacexy_memory.json" > nul 2>&1
    del "%USERPROFILE%\.dacexy_macros.json" > nul 2>&1
    del "%USERPROFILE%\dacexy_agent.log" > nul 2>&1
    del "%USERPROFILE%\dacexy_audit.log" > nul 2>&1
)
call :ok "Uninstall complete."
goto :eof
