@echo off
setlocal enabledelayedexpansion
title Dacexy Desktop Agent v14.0
color 0A
cd /d "%USERPROFILE%\DacexyAgent"

echo.
echo  ============================================================
echo    DACEXY Desktop Agent v14.0 ULTIMATE
echo    Starting...
echo  ============================================================
echo.

:: Upgrade websockets silently
python -m pip install --upgrade websockets -q --no-warn-script-location >nul 2>&1
python -c "import websockets; print('  [OK] websockets', websockets.__version__)"

:: Apply fix if needed
if exist fix.py (
    python fix.py >nul 2>&1
)

:: Check if already logged in
python -c "
import json, pathlib
f = pathlib.Path.home() / '.dacexy_agent.json'
if f.exists():
    d = json.loads(f.read_text())
    if d.get('access_token'):
        print('LOGGED_IN')
    else:
        print('NEED_LOGIN')
else:
    print('NEED_LOGIN')
" > %TEMP%\dacexy_check.txt 2>nul

set /p LOGIN_STATUS=<%TEMP%\dacexy_check.txt

if "%LOGIN_STATUS%"=="NEED_LOGIN" (
    echo.
    echo  ============================================================
    echo    First time setup - Please login to your Dacexy account
    echo    Register free at: dacexy.vercel.app
    echo  ============================================================
    echo.
    set /p DACEXY_EMAIL="  Email   : "
    set /p DACEXY_PASS="  Password: "
    echo.
    echo  Logging in...
    python -c "
import requests, json
from pathlib import Path
email = '%DACEXY_EMAIL%'
password = '%DACEXY_PASS%'
try:
    r = requests.post('https://dacexy-backend-v7ku.onrender.com/api/v1/auth/login',
        json={'email': email, 'password': password}, timeout=30)
    if r.status_code == 200:
        token = r.json().get('access_token', '')
        if token:
            cfg_file = Path.home() / '.dacexy_agent.json'
            cfg = {}
            if cfg_file.exists():
                try: cfg = json.loads(cfg_file.read_text())
                except: pass
            cfg['access_token'] = token
            cfg_file.write_text(json.dumps(cfg, indent=2))
            print('  [OK] Login successful! Welcome to Dacexy.')
        else:
            print('  [ERROR] No token received. Check credentials.')
    else:
        try: detail = r.json().get('detail', r.text)
        except: detail = r.text
        print(f'  [ERROR] Login failed: {detail}')
        pause
except Exception as e:
    print(f'  [ERROR] Cannot connect: {e}')
    pause
"
    echo.
)

:LAUNCH
python dacexy_agent.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% EQU 0 (
    echo.
    echo  Dacexy Agent exited cleanly.
    goto END
)

echo.
echo  ============================================================
echo  Dacexy Agent stopped (code: %EXIT_CODE%)
echo  Check log: %USERPROFILE%\DacexyAgent\logs\startup.log
echo  ============================================================
echo.
echo  Press R to restart, any other key to exit.
choice /c RE /n /m "  Choice: "
if errorlevel 2 goto END
if errorlevel 1 goto LAUNCH

:END
echo.
pause
