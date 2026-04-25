@echo off
title Dacexy Desktop Agent Installer
echo.
echo  ================================
echo   DACEXY Desktop Agent v3.0
echo  ================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please download from https://python.org/downloads
    echo Make sure to check "Add Python to PATH"
    pause
    start https://python.org/downloads
    exit /b 1
)
echo [OK] Python found.

echo.
echo Installing required packages...
pip install websockets pyautogui requests pillow speechrecognition pyaudio psutil --quiet
echo [OK] Packages installed.

echo.
if not exist "%USERPROFILE%\DacexyAgent" mkdir "%USERPROFILE%\DacexyAgent"

echo Downloading agent script...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\DacexyAgent\dacexy_agent.py'"
echo [OK] Agent downloaded.

echo.
echo ================================
echo  Paste your Agent Token below.
echo  Get it from dacexy.vercel.app/settings
echo ================================
echo.
set /p TOKEN="Your token: "
echo %TOKEN%> "%USERPROFILE%\DacexyAgent\token.txt"

echo.
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\cs.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\Desktop\Dacexy Agent.lnk") >> %SCRIPT%
echo oLink.TargetPath = "python" >> %SCRIPT%
echo oLink.Arguments = "%USERPROFILE%\DacexyAgent\dacexy_agent.py" >> %SCRIPT%
echo oLink.WorkingDirectory = "%USERPROFILE%\DacexyAgent" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ================================
echo  Done! Launching agent now...
echo ================================
echo.
cd "%USERPROFILE%\DacexyAgent"
python dacexy_agent.py
pause
