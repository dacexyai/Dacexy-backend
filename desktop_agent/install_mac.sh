

#!/bin/bash
echo "===================================="
echo "   Dacexy Desktop Agent Installer"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python not found. Installing Python 3.11..."
    curl -o python_installer.pkg https://www.python.org/ftp/python/3.11.0/python-3.11.0-macos11.pkg
    sudo installer -pkg python_installer.pkg -target /
    rm python_installer.pkg
    echo "Python installed successfully."
fi

echo ""
echo "Installing Dacexy Agent dependencies..."
pip3 install requests pyautogui pillow websockets SpeechRecognition pyttsx3 keyboard mouse psutil > /dev/null 2>&1
echo "Dependencies installed."

echo ""
echo "Downloading Dacexy Agent..."
curl -o dacexy_agent.py https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py

echo ""
read -p "Enter your Dacexy Agent Token (from Settings page): " TOKEN

echo "{\"token\": \"$TOKEN\", \"server\": \"https://dacexy-backend-v7ku.onrender.com\"}" > config.json

echo ""
echo "Starting Dacexy Agent..."
echo "Say 'Hey Dacexy' to activate voice commands."
echo ""
python3 dacexy_agent.py
