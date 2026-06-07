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
