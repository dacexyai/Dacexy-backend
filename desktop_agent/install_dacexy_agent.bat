@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v15.0 ENTERPRISE
color 0A

chcp 65001 > nul 2>&1

if not exist "%USERPROFILE%\DacexyAgent" (
    mkdir "%USERPROFILE%\DacexyAgent"
)
if not exist "%USERPROFILE%\DacexyAgent\logs" (
    mkdir "%USERPROFILE%\DacexyAgent\logs"
)
cd /d "%USERPROFILE%\DacexyAgent"

echo.
echo  ============================================================
echo    DACEXY Desktop Agent v15.0 ENTERPRISE
echo    Starting...
echo  ============================================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH.
    echo  Please install Python 3.9+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] %PYVER%

echo  [INFO] Checking pip...
python -m pip install --upgrade pip -q --no-warn-script-location > nul 2>&1

echo  [INFO] Checking websockets...
python -m pip install --upgrade websockets -q --no-warn-script-location > nul 2>&1
python -c "import websockets; print('  [OK] websockets', websockets.__version__)" 2>nul

echo  [INFO] Verifying core packages...
python -c "import requests" > nul 2>&1
if errorlevel 1 (
    echo  [INFO] Installing requests...
    python -m pip install requests -q --no-warn-script-location > nul 2>&1
)

python -c "import psutil" > nul 2>&1
if errorlevel 1 (
    echo  [INFO] Installing psutil...
    python -m pip install psutil -q --no-warn-script-location > nul 2>&1
)

python -c "import pyautogui" > nul 2>&1
if errorlevel 1 (
    echo  [INFO] Installing pyautogui...
    python -m pip install pyautogui -q --no-warn-script-location > nul 2>&1
)

echo  [OK] Core packages ready

if exist "patch.py" (
    echo  [INFO] Applying patch...
    python patch.py > nul 2>&1
)

if exist "dacexy_agent_new.py" (
    echo  [INFO] Applying agent update...
    copy /y "dacexy_agent_new.py" "dacexy_agent.py" > nul
    del "dacexy_agent_new.py" > nul 2>&1
    echo  [OK] Agent updated
)

:: ============================================================
:: DOWNLOAD AGENT IF MISSING
:: ============================================================
if not exist "dacexy_agent.py" (
    echo.
    echo  [INFO] Agent file not found. Downloading from server...
    python -c "
import urllib.request, sys, os
url = 'https://dacexy-backend-v7ku.onrender.com/api/v1/agent/download/windows-agent'
dest = os.path.join(os.path.expanduser('~'), 'DacexyAgent', 'dacexy_agent.py')
try:
    urllib.request.urlretrieve(url, dest)
    print('  [OK] Agent downloaded successfully.')
except Exception as e:
    print('  [WARN] Auto-download failed:', e)
    print('  [INFO] Will try to create minimal agent...')
" 2>&1
)

:: If still missing after download attempt, show clear error and keep window open
if not exist "dacexy_agent.py" (
    echo.
    echo  ============================================================
    echo  [ERROR] dacexy_agent.py not found in:
    echo  %USERPROFILE%\DacexyAgent\
    echo.
    echo  Please place dacexy_agent.py in that folder and
    echo  run this installer again.
    echo  ============================================================
    echo.
    pause
    exit /b 1
)

:: ============================================================
:: LOGIN CHECK
:: ============================================================
python -c "
import json, pathlib, sys
f = pathlib.Path.home() / '.dacexy_agent.json'
if f.exists():
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
        if d.get('access_token'):
            print('LOGGED_IN')
        else:
            print('NEED_LOGIN')
    except:
        print('NEED_LOGIN')
else:
    print('NEED_LOGIN')
" > "%TEMP%\dacexy_check.txt" 2>nul

set /p LOGIN_STATUS=<"%TEMP%\dacexy_check.txt"
del "%TEMP%\dacexy_check.txt" > nul 2>&1

if "!LOGIN_STATUS!"=="NEED_LOGIN" (
    echo.
    echo  ============================================================
    echo    First time setup - Please login to your Dacexy account
    echo    Register free at: dacexy.vercel.app
    echo  ============================================================
    echo.

    set /p DACEXY_EMAIL="  Email   : "
    set /p DACEXY_PASS="  Password: "
    echo.
    echo  [INFO] Logging in...

    python -c "
import requests, json, sys
from pathlib import Path

email    = r'!DACEXY_EMAIL!'
password = r'!DACEXY_PASS!'

if not email or '@' not in email:
    print('  [ERROR] Invalid email address.')
    sys.exit(1)
if not password or len(password) < 4:
    print('  [ERROR] Password too short.')
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
            print('  [OK] Login successful! Welcome to Dacexy.')
        else:
            print('  [ERROR] No token received. Check credentials.')
            sys.exit(1)
    elif r.status_code == 401:
        print('  [ERROR] Wrong email or password.')
        sys.exit(1)
    elif r.status_code == 422:
        print('  [ERROR] Invalid credentials format.')
        sys.exit(1)
    else:
        try:
            detail = r.json().get('detail', r.text[:100])
            if isinstance(detail, list):
                detail = detail[0].get('msg', str(detail))
        except:
            detail = r.text[:100]
        print(f'  [ERROR] Login failed ({r.status_code}): {detail}')
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print('  [ERROR] Cannot connect. Check internet connection.')
    sys.exit(1)
except requests.exceptions.Timeout:
    print('  [ERROR] Server timeout. Try again.')
    sys.exit(1)
except Exception as e:
    print(f'  [ERROR] {e}')
    sys.exit(1)
"

    if errorlevel 1 (
        echo.
        echo  Login failed. Press any key to exit.
        pause > nul
        exit /b 1
    )
    echo.
)

:: ============================================================
:: LAUNCH AGENT
:: ============================================================
echo  [INFO] Starting Dacexy Agent...
echo  [INFO] Log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo.

:LAUNCH
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo  Dacexy Agent exited cleanly.
    goto END
)

if %EXIT_CODE% EQU 2 (
    echo.
    echo  [WARN] Session expired. Clearing token and re-logging in...
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
"
    goto LAUNCH
)

:RESTART_PROMPT
echo.
echo  ============================================================
echo  Dacexy Agent stopped (exit code: %EXIT_CODE%)
echo  Log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo  ============================================================
echo.
echo  R = Restart agent
echo  L = View log
echo  E = Exit
echo.
choice /c RLE /n /m "  Choice: "

if errorlevel 3 goto END
if errorlevel 2 (
    type "%USERPROFILE%\DacexyAgent\logs\startup.log" 2>nul | more
    goto RESTART_PROMPT
)
if errorlevel 1 goto LAUNCH

:END
echo.
echo  Thank you for using Dacexy!
pause
ENDOFFILE
echo "Done"
