#!/bin/bash
echo ""
echo "============================================"
echo "  Dacexy Desktop Agent - Mac/Linux Installer"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python3 || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        sudo apt-get install -y python3 python3-pip
    fi
fi

echo "Installing dependencies..."
pip3 install pyautogui pillow websockets requests -q

echo "Downloading Dacexy Agent..."
curl -o ~/dacexy_agent.py https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py

# Create launcher
cat > ~/Desktop/DacexyAgent.sh << 'EOF'
#!/bin/bash
python3 ~/dacexy_agent.py
EOF
chmod +x ~/Desktop/DacexyAgent.sh

# Mac app bundle
if [[ "$OSTYPE" == "darwin"* ]]; then
    mkdir -p ~/Desktop/DacexyAgent.app/Contents/MacOS
    cat > ~/Desktop/DacexyAgent.app/Contents/MacOS/DacexyAgent << 'EOF'
#!/bin/bash
python3 ~/dacexy_agent.py
EOF
    chmod +x ~/Desktop/DacexyAgent.app/Contents/MacOS/DacexyAgent
    cat > ~/Desktop/DacexyAgent.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>DacexyAgent</string>
<key>CFBundleName</key><string>Dacexy Agent</string>
</dict></plist>
EOF
fi

echo ""
echo "============================================"
echo "  Installation Complete!"
echo "  Double-click DacexyAgent on your desktop"
echo "============================================"
echo ""
