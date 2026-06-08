@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v15.0 ENTERPRISE
color 0A

:: ============================================================
:: FIX 1: Force UTF-8 output so no garbled characters
:: ============================================================
chcp 65001 > nul 2>&1

:: ============================================================
:: FIX 2: Always work from DacexyAgent folder
:: ============================================================
if not exist "%USERPROFILE%\DacexyAgent" (
    mkdir "%USERPROFILE%\DacexyAgent"
)
cd /d "%USERPROFILE%\DacexyAgent"

:: ============================================================
:: STARTUP BANNER
:: ============================================================
echo.
echo  ============================================================
echo    DACEXY Desktop Agent v15.0 ENTERPRISE
echo    Starting...
echo  ============================================================
echo.

:: ============================================================
:: FIX 3: Check Python exists before anything else
:: ============================================================
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

:: ============================================================
:: FIX 4: Upgrade pip silently first
:: ============================================================
echo  [INFO] Checking pip...
python -m pip install --upgrade pip -q --no-warn-script-location > nul 2>&1

:: ============================================================
:: FIX 5: Upgrade websockets - show version to confirm alive
:: ============================================================
echo  [INFO] Checking websockets...
python -m pip install --upgrade websockets -q --no-warn-script-location > nul 2>&1
python -c "import websockets; print('  [OK] websockets', websockets.__version__)" 2>nul
if errorlevel 1 (
    echo  [WARN] websockets check failed, will retry on agent start
)

:: ============================================================
:: FIX 6: Install critical packages upfront to avoid
::        long install delays mid-run that look like hangs
:: ============================================================
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

:: ============================================================
:: FIX 7: Apply any patches if patch file exists
:: ============================================================
if exist "patch.py" (
    echo  [INFO] Applying patch...
    python patch.py > nul 2>&1
)

:: ============================================================
:: FIX 8: Copy latest agent if update exists
:: ============================================================
if exist "dacexy_agent_new.py" (
    echo  [INFO] Applying agent update...
    copy /y "dacexy_agent_new.py" "dacexy_agent.py" > nul
    del "dacexy_agent_new.py" > nul 2>&1
    echo  [OK] Agent updated
)

:: ============================================================
:: CHECK: Is agent file present?
:: ============================================================
if not exist "dacexy_agent.py" (
    echo.
    echo  [ERROR] dacexy_agent.py not found in %USERPROFILE%\DacexyAgent
    echo  Please re-download the Dacexy installer package.
    echo.
    pause
    exit /b 1
)

:: ============================================================
:: FIX 9: Login check and handling
:: Uses a temp file to avoid pipe/stdin issues
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
    
    :: FIX: Use SET /P for clean console input (not redirected)
    set /p DACEXY_EMAIL="  Email   : "
    set /p DACEXY_PASS="  Password: "
    echo.
    echo  [INFO] Logging in...
    
    :: Write credentials to temp file to avoid quoting/special char issues
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
:: ALL CHECKS PASSED - LAUNCH AGENT
:: ============================================================
echo  [INFO] Starting Dacexy Agent...
echo  [INFO] Log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo.

:LAUNCH
:: FIX 10: Use explicit UTF-8 env var for Python subprocess
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

:: ============================================================
:: EXIT CODE HANDLING
:: ============================================================
if %EXIT_CODE% EQU 0 (
    echo.
    echo  Dacexy Agent exited cleanly.
    goto END
)

if %EXIT_CODE% EQU 1 (
    echo.
    echo  [WARN] Agent exited with code 1 (possible startup error)
    echo  Check log: %USERPROFILE%\DacexyAgent\logs\startup.log
    goto RESTART_PROMPT
)

if %EXIT_CODE% EQU 2 (
    echo.
    echo  [WARN] Agent exited with code 2 (auth expired)
    echo  Clearing saved session...
    python -c "
import json
from pathlib import Path
f = Path.home() / '.dacexy_agent.json'
if f.exists():
    try:
        d = json.loads(f.read_text())
        d.pop('access_token', None)
        f.write_text(json.dumps(d, indent=2))
        print('  [INFO] Session cleared. Please login again.')
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
    type "%USERPROFILE%\DacexyAgent\logs\startup.log" | more
    goto RESTART_PROMPT
)
if errorlevel 1 goto LAUNCH

:END
echo.
echo  Thank you for using Dacexy!
pause
