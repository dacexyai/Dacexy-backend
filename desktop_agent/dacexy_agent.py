

#!/usr/bin/env python3
"""
Dacexy Desktop Agent
Connects to your Dacexy account and lets AI control your computer.
"""

import json
import os
import sys
import time
import threading
import subprocess
import platform
import requests
import pyautogui
import keyboard
from PIL import ImageGrab

SYSTEM = platform.system()
CONFIG_FILE = "config.json"
SERVER_URL = "https://dacexy-backend-v7ku.onrender.com"
WAKE_WORD = "hey dacexy"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("Config not found. Please run installer first.")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def take_screenshot():
    img = ImageGrab.grab()
    img.save("screenshot.png")
    return "screenshot.png"

def execute_command(command: str, token: str) -> str:
    cmd = command.lower().strip()
    try:
        # Open applications
        if "open chrome" in cmd or "open browser" in cmd:
            if SYSTEM == "Windows":
                subprocess.Popen(["start", "chrome"], shell=True)
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", "-a", "Google Chrome"])
            return "Chrome opened successfully"

        elif "open youtube" in cmd:
            import webbrowser
            webbrowser.open("https://www.youtube.com")
            return "YouTube opened in browser"

        elif "open whatsapp" in cmd:
            import webbrowser
            webbrowser.open("https://web.whatsapp.com")
            return "WhatsApp Web opened in browser"

        elif "open excel" in cmd or "open spreadsheet" in cmd:
            if SYSTEM == "Windows":
                subprocess.Popen(["start", "excel"], shell=True)
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", "-a", "Microsoft Excel"])
            return "Excel opened"

        elif "open notepad" in cmd or "open text editor" in cmd:
            if SYSTEM == "Windows":
                subprocess.Popen(["notepad"])
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", "-a", "TextEdit"])
            return "Text editor opened"

        elif "take screenshot" in cmd or "screenshot" in cmd:
            path = take_screenshot()
            return f"Screenshot saved as {path}"

        elif "type " in cmd:
            text = command[command.lower().index("type ") + 5:]
            pyautogui.typewrite(text, interval=0.05)
            return f"Typed: {text}"

        elif "click" in cmd:
            pyautogui.click()
            return "Clicked"

        elif "scroll down" in cmd:
            pyautogui.scroll(-3)
            return "Scrolled down"

        elif "scroll up" in cmd:
            pyautogui.scroll(3)
            return "Scrolled up"

        elif "press enter" in cmd:
            pyautogui.press("enter")
            return "Pressed Enter"

        elif "press escape" in cmd or "press esc" in cmd:
            pyautogui.press("escape")
            return "Pressed Escape"

        elif "copy" in cmd:
            pyautogui.hotkey("ctrl", "c")
            return "Copied to clipboard"

        elif "paste" in cmd:
            pyautogui.hotkey("ctrl", "v")
            return "Pasted from clipboard"

        elif "search for " in cmd or "google " in cmd:
            query = cmd.replace("search for ", "").replace("google ", "")
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Searching Google for: {query}"

        else:
            # Send to AI for interpretation
            response = requests.post(
                f"{SERVER_URL}/api/v1/ai/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messages": [
                        {"role": "system", "content": "You are a desktop automation assistant. The user wants to perform a computer action. Describe exactly what pyautogui commands to use, or say CANNOT_DO if it's not possible."},
                        {"role": "user", "content": command}
                    ],
                    "stream": False
                },
                timeout=30
            )
            if response.ok:
                return response.json().get("content", "Command processed")
            return f"Unknown command: {command}"

    except Exception as e:
        return f"Error executing command: {str(e)}"

def listen_for_voice(token: str):
    try:
        import speech_recognition as sr
        import pyttsx3

        recognizer = sr.Recognizer()
        tts = pyttsx3.init()

        def speak(text):
            tts.say(text)
            tts.runAndWait()

        print("Voice mode active. Say 'Hey Dacexy' to give a command.")
        speak("Dacexy agent is ready. Say Hey Dacexy to give me a command.")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            while True:
                try:
                    print("Listening...")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"Heard: {text}")

                    if WAKE_WORD in text:
                        command = text.replace(WAKE_WORD, "").strip()
                        if command:
                            print(f"Command: {command}")
                            speak("Got it, working on it.")
                            result = execute_command(command, token)
                            print(f"Result: {result}")
                            speak(result[:100])
                        else:
                            speak("Yes? What would you like me to do?")
                            audio2 = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                            command = recognizer.recognize_google(audio2)
                            result = execute_command(command, token)
                            speak(result[:100])

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    print(f"Voice error: {e}")
                    time.sleep(1)

    except ImportError:
        print("Voice libraries not available. Running in text mode only.")

def poll_commands(token: str):
    print("Polling for commands from server...")
    while True:
        try:
            response = requests.get(
                f"{SERVER_URL}/api/v1/agent/desktop/commands",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if response.ok:
                data = response.json()
                commands = data.get("commands", [])
                for cmd in commands:
                    print(f"Executing: {cmd['command']}")
                    result = execute_command(cmd["command"], token)
                    requests.post(
                        f"{SERVER_URL}/api/v1/agent/desktop/result",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"command_id": cmd["id"], "result": result}
                    )
        except Exception as e:
            pass
        time.sleep(3)

def main():
    print("=" * 40)
    print("   DACEXY DESKTOP AGENT v1.0")
    print("=" * 40)

    config = load_config()
    token = config.get("token")

    if not token:
        print("No token found in config. Please run installer.")
        sys.exit(1)

    print(f"Connected to: {SERVER_URL}")
    print("Agent is running. Press Ctrl+C to stop.")
    print("")
    print("You can:")
    print("- Say 'Hey Dacexy' for voice commands")
    print("- Commands will also be received from the chat")
    print("")

    # Start voice in background thread
    voice_thread = threading.Thread(target=listen_for_voice, args=(token,), daemon=True)
    voice_thread.start()

    # Start polling for commands from server
    try:
        poll_commands(token)
    except KeyboardInterrupt:
        print("\nDacexy Agent stopped.")

if __name__ == "__main__":
    main()
