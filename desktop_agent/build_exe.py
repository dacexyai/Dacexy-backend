

"""
Run this script to build the Windows .exe installer.
Run on a Windows machine: python build_exe.py
"""
import subprocess
import sys

# Install PyInstaller
subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

# Build the exe
subprocess.run([
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--name", "Dacexy_Agent_Setup",
    "--icon", "NONE",
    "--add-data", "dacexy_agent.py;.",
    "setup_windows.py"
], check=True)

print("\n✅ Build complete!")
print("Your installer is at: dist/Dacexy_Agent_Setup.exe")
print("Share this .exe file with your beta testers.")
