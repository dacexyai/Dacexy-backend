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

:: ── One-time websockets compatibility fix ─────────────────────
:: Checks if the fix has already been applied; if not, runs it.
python -c "open('dacexy_agent.py').read().index('_ws_kw')" >nul 2>&1
if errorlevel 1 (
    if exist apply_fix.py (
        echo  [SETUP] Applying WebSocket compatibility fix...
        python apply_fix.py
        if errorlevel 1 (
            echo  [WARN] Auto-fix failed - continuing anyway.
        ) else (
            echo  [OK] Fix applied successfully.
        )
        echo.
    )
)

:: ── Ensure websockets is up to date ───────────────────────────
:: Upgrade silently so extra_headers / additional_headers is stable
python -m pip install --upgrade websockets -q --no-warn-script-location
python -c "import websockets; print('  [OK] websockets', websockets.__version__)"
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
