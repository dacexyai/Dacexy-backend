#!/bin/bash
echo ""
echo "============================================"
echo "  Dacexy Desktop Agent v3.0 - Mac Installer"
echo "  Voice + AI Computer Control"
echo "============================================"
echo ""

# Install Homebrew if needed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python if needed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    brew install python3
fi

# Install PortAudio for PyAudio (microphone support)
echo "Installing PortAudio for microphone support..."
brew install portaudio

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip -q
pip3 install pyautogui pillow websockets requests pyttsx3 SpeechRecognition numpy pystray -q
pip3 install pyaudio -q

# Download agent
echo "Downloading Dacexy Agent..."
curl -o ~/dacexy_agent.py "https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py"

# Grant microphone and accessibility permissions
echo ""
echo "IMPORTANT: Grant these permissions when prompted:"
echo "  1. Microphone access (for voice control)"
echo "  2. Accessibility access (for mouse/keyboard control)"
echo "  Go to: System Preferences > Security & Privacy"
echo ""

# Create Mac app
mkdir -p ~/Desktop/DacexyAgent.app/Contents/MacOS
cat > ~/Desktop/DacexyAgent.app/Contents/MacOS/DacexyAgent << 'APPEOF'
#!/bin/bash
cd ~
python3 ~/dacexy_agent.py
APPEOF
chmod +x ~/Desktop/DacexyAgent.app/Contents/MacOS/DacexyAgent

cat > ~/Desktop/DacexyAgent.app/Contents/Info.plist << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>DacexyAgent</string>
    <key>CFBundleIdentifier</key><string>com.dacexy.agent</string>
    <key>CFBundleName</key><string>Dacexy Agent</string>
    <key>CFBundleVersion</key><string>3.0</string>
    <key>NSMicrophoneUsageDescription</key><string>Dacexy Agent needs microphone for voice commands</string>
    <key>NSAppleEventsUsageDescription</key><string>Dacexy Agent needs accessibility for computer control</string>
</dict>
</plist>
PLISTEOF

# Auto-start on login
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.dacexy.agent.plist << LAUNCHEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.dacexy.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>$HOME/dacexy_agent.py</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>
LAUNCHEOF

launchctl load ~/Library/LaunchAgents/com.dacexy.agent.plist 2>/dev/null

echo ""
echo "============================================"
echo "  Installation Complete!"
echo ""
echo "  Double-click DacexyAgent on your Desktop"
echo "  Auto-starts when Mac boots"
echo ""
echo '  Say "Hey Dacexy" for voice commands'
echo "============================================"
echo ""
read -p "Launch Dacexy Agent now? (y/n): " LAUNCH
if [ "$LAUNCH" = "y" ]; then
    python3 ~/dacexy_agent.py &
fi
