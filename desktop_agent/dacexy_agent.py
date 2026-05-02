"""
Dacexy Desktop Agent v4.0 - Always On, Voice + Remote Control
"""
import subprocess, sys, os

PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
]

print("Checking dependencies...")
for pkg in PACKAGES:
    import_name = pkg.replace("-","_")
    if pkg == "speechrecognition": import_name = "speech_recognition"
    try:
        __import__(import_name)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False
    print("  Installing PyAudio...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin", "-q"])
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"])
        import pyaudio
        PYAUDIO_OK = True
    except:
        PYAUDIO_OK = False

import asyncio, base64, io, json, logging, platform
import threading, time, webbrowser, re, winreg
from pathlib import Path

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab
import pyttsx3

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except ImportError:
    VOICE_AVAILABLE = False

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
WAKE_WORD    = "hey dacexy"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / "dacexy_agent.log", encoding="utf-8")
    ]
)
log = logging.getLogger("dacexy")

_tts_engine = None
_tts_lock = threading.Lock()

def get_tts():
    global _tts_engine
    if _tts_engine is None:
        try:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 175)
            _tts_engine.setProperty("volume", 0.9)
        except Exception as e:
            log.warning(f"TTS init failed: {e}")
    return _tts_engine

def speak(text: str):
    print(f"  Dacexy: {text}")
    try:
        with _tts_lock:
            engine = get_tts()
            if engine:
                engine.say(text)
                engine.runAndWait()
    except Exception as e:
        log.warning(f"TTS failed: {e}")

def setup_autostart():
    """Add agent to Windows startup so it runs automatically on boot."""
    try:
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        python_path = sys.executable
        cmd = f'"{python_path}" "{agent_path}"'
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("  Auto-start enabled — Dacexy will start automatically on Windows boot!")
    except Exception as e:
        log.warning(f"Auto-start setup failed: {e}")

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_token():
    return load_config().get("access_token")

def save_token(token: str):
    cfg = load_config()
    cfg["access_token"] = token
    save_config(cfg)

def clear_token():
    cfg = load_config()
    cfg.pop("access_token", None)
    save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(
            f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        return r.status_code == 200
    except:
        return False

def login():
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent - Login")
    print("="*52)
    email    = input("  Email   : ").strip()
    password = input("  Password: ").strip()
    print()
    try:
        r = req_lib.post(
            f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                save_token(token)
                print("  Login successful!")
                return token
            print("  No token received.")
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  Login failed: {d}")
    except req_lib.exceptions.ConnectionError:
        print("  Cannot connect. Check internet.")
    except Exception as e:
        print(f"  Error: {e}")
    return None

def take_screenshot():
    try:
        img = ImageGrab.grab()
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return None

def get_screen_center():
    sz = pyautogui.size()
    return sz.width // 2, sz.height // 2

BLOCKED = ["rm -rf /", "format c:", "del /s /q c:\\"]

def execute_command(cmd: dict, token=None) -> dict:
    action = cmd.get("action", "").lower()
    try:
        if action == "speak":
            text = cmd.get("text", "")
            speak(text)
            return {"status": "ok", "spoken": text}

        elif action == "screenshot":
            return {"status": "ok", "screenshot": take_screenshot()}

        elif action == "click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.click(x, y, button=cmd.get("button", "left"))
            return {"status": "ok"}

        elif action == "double_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.doubleClick(x, y)
            return {"status": "ok"}

        elif action == "right_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.rightClick(x, y)
            return {"status": "ok"}

        elif action == "type":
            text = cmd.get("text", "")
            pyautogui.write(text, interval=0.05)
            return {"status": "ok"}

        elif action == "key":
            pyautogui.press(cmd.get("key", ""))
            return {"status": "ok"}

        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys: pyautogui.hotkey(*keys)
            return {"status": "ok"}

        elif action == "scroll":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.scroll(int(cmd.get("clicks", 3)), x=x, y=y)
            return {"status": "ok"}

        elif action == "move":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.moveTo(x, y, duration=float(cmd.get("duration", 0.3)))
            return {"status": "ok"}

        elif action == "open_url":
            url = cmd.get("url", "")
            webbrowser.open(url)
            time.sleep(1)
            return {"status": "ok", "opened": url}

        elif action == "open_app":
            app = cmd.get("app", "")
            os.startfile(app) if platform.system() == "Windows" else subprocess.Popen([app])
            time.sleep(1)
            return {"status": "ok", "opened": app}

        elif action == "run_shell":
            command = cmd.get("command", "")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status": "error", "message": f"Blocked"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": r.stdout[:3000], "stderr": r.stderr[:500]}

        elif action == "get_screen_size":
            sz = pyautogui.size()
            return {"status": "ok", "width": sz.width, "height": sz.height}

        elif action == "get_system_info":
            sz = pyautogui.size()
            return {"status": "ok", "os": platform.system(), "os_version": platform.version(),
                    "machine": platform.machine(), "hostname": platform.node(),
                    "screen_width": sz.width, "screen_height": sz.height, "agent_version": "4.0"}

        elif action == "task":
            task_text = cmd.get("task", "") or cmd.get("goal", "")
            if task_text and token:
                actions_json = get_ai_actions(task_text, token)
                try:
                    actions = json.loads(actions_json)
                    if isinstance(actions, list):
                        execute_action_list(actions, token=token)
                        return {"status": "ok", "actions_taken": len(actions)}
                except:
                    pass
            return {"status": "ok"}

        else:
            return {"status": "error", "message": f"Unknown: {action}"}

    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Failsafe"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status": "error", "message": str(e)}

def execute_action_list(actions: list, token=None):
    for action in actions:
        if not isinstance(action, dict): continue
        log.info(f"Executing: {action.get('action','?')}")
        execute_command(action, token=token)
        time.sleep(0.4)

def get_ai_actions(command: str, token: str) -> str:
    """Get AI planned actions for a command — returns JSON array."""
    try:
        sz = pyautogui.size()
        system = platform.system()

        # Build very specific prompt so AI returns real actions not just speak
        prompt = f"""You are a Windows desktop automation AI. The user wants: "{command}"

OS: {system}, Screen: {sz.width}x{sz.height}

IMPORTANT RULES:
1. You MUST return ONLY a valid JSON array of actions
2. NEVER return just a speak action — always do the actual task
3. For opening websites: use open_url action
4. For opening apps: use open_app action  
5. For typing: use type action
6. Always end with a speak action confirming what you did

AVAILABLE ACTIONS:
- {{"action":"open_url","url":"https://..."}} — opens URL in browser
- {{"action":"open_app","app":"notepad"}} — opens application
- {{"action":"run_shell","command":"start chrome"}} — runs shell command
- {{"action":"click","x":500,"y":400}} — clicks at position
- {{"action":"double_click","x":500,"y":400}} — double clicks
- {{"action":"type","text":"hello"}} — types text
- {{"action":"key","key":"enter"}} — presses key
- {{"action":"hotkey","keys":["ctrl","t"]}} — keyboard shortcut
- {{"action":"screenshot"}} — takes screenshot
- {{"action":"speak","text":"..."}} — says something out loud

EXAMPLES:
User: "open youtube in chrome"
Response: [{{"action":"open_url","url":"https://www.youtube.com"}},{{"action":"speak","text":"Opened YouTube for you"}}]

User: "open notepad and type hello world"
Response: [{{"action":"open_app","app":"notepad"}},{{"action":"key","key":"enter"}},{{"action":"type","text":"hello world"}},{{"action":"speak","text":"Opened Notepad and typed hello world"}}]

User: "take a screenshot"
Response: [{{"action":"screenshot"}},{{"action":"speak","text":"Screenshot taken"}}]

User: "open chrome"
Response: [{{"action":"run_shell","command":"start chrome"}},{{"action":"speak","text":"Opening Chrome"}}]

User: "search google for weather today"
Response: [{{"action":"open_url","url":"https://www.google.com/search?q=weather+today"}},{{"action":"speak","text":"Searching Google for weather today"}}]

Now respond to: "{command}"
Return ONLY the JSON array, nothing else."""

        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            content = data.get("content") or data.get("response") or data.get("text") or ""
            # Extract JSON array from response
            match = re.search(r'\[.*?\]', content, re.DOTALL)
            if match:
                arr = match.group(0)
                # Validate it's real actions not just speak
                parsed = json.loads(arr)
                if isinstance(parsed, list) and len(parsed) > 0:
                    # If only speak action, try to do the task directly
                    non_speak = [a for a in parsed if a.get("action") != "speak"]
                    if not non_speak:
                        # AI returned only speak — force direct action
                        return force_direct_action(command)
                    return arr

        return force_direct_action(command)

    except Exception as e:
        log.error(f"AI error: {e}")
        return force_direct_action(command)

def force_direct_action(command: str) -> str:
    """Execute common commands directly without AI when AI fails."""
    cmd_lower = command.lower()

    # YouTube
    if "youtube" in cmd_lower:
        return json.dumps([
            {"action": "open_url", "url": "https://www.youtube.com"},
            {"action": "speak", "text": "Opened YouTube"}
        ])
    # Google search
    if "search" in cmd_lower and "google" in cmd_lower:
        query = cmd_lower.replace("search", "").replace("google", "").replace("for", "").strip()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return json.dumps([
            {"action": "open_url", "url": url},
            {"action": "speak", "text": f"Searched Google for {query}"}
        ])
    # Chrome
    if "chrome" in cmd_lower and ("open" in cmd_lower or "start" in cmd_lower):
        return json.dumps([
            {"action": "run_shell", "command": "start chrome"},
            {"action": "speak", "text": "Opening Chrome"}
        ])
    # Notepad
    if "notepad" in cmd_lower:
        return json.dumps([
            {"action": "open_app", "app": "notepad"},
            {"action": "speak", "text": "Opening Notepad"}
        ])
    # Calculator
    if "calculator" in cmd_lower or "calc" in cmd_lower:
        return json.dumps([
            {"action": "open_app", "app": "calc"},
            {"action": "speak", "text": "Opening Calculator"}
        ])
    # Screenshot
    if "screenshot" in cmd_lower or "screen" in cmd_lower:
        return json.dumps([
            {"action": "screenshot"},
            {"action": "speak", "text": "Screenshot taken"}
        ])
    # Volume
    if "volume up" in cmd_lower:
        return json.dumps([
            {"action": "key", "key": "volumeup"},
            {"action": "speak", "text": "Volume increased"}
        ])
    if "volume down" in cmd_lower:
        return json.dumps([
            {"action": "key", "key": "volumedown"},
            {"action": "speak", "text": "Volume decreased"}
        ])
    # Mute
    if "mute" in cmd_lower:
        return json.dumps([
            {"action": "key", "key": "volumemute"},
            {"action": "speak", "text": "Muted"}
        ])
    # Any URL
    if "open" in cmd_lower and "." in cmd_lower:
        words = cmd_lower.split()
        for w in words:
            if "." in w and len(w) > 4:
                url = w if w.startswith("http") else f"https://{w}"
                return json.dumps([
                    {"action": "open_url", "url": url},
                    {"action": "speak", "text": f"Opened {w}"}
                ])
    # Default — open Google search
    query = command.replace(" ", "+")
    return json.dumps([
        {"action": "open_url", "url": f"https://www.google.com/search?q={query}"},
        {"action": "speak", "text": f"Searching for {command}"}
    ])


class VoiceAgent:
    def __init__(self, token: str):
        self.token = token
        self.running = False
        self.recognizer = None
        self.microphone = None

        if VOICE_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.microphone = sr.Microphone()
                print("  Calibrating microphone...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print(f'  Microphone ready! Say "{WAKE_WORD.title()}" anytime.')
            except Exception as e:
                print(f"  Microphone error: {e}")
                self.microphone = None
        else:
            print("  Voice unavailable — using TEXT mode.")
            print("  Just type commands below and press Enter!\n")

    def listen_continuous(self):
        """Always listening for wake word."""
        if not self.microphone: return
        while self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    log.debug(f"Heard: {text}")
                    if WAKE_WORD in text:
                        print(f"\n  Wake word detected!")
                        # Remove wake word to get command
                        command = text.replace(WAKE_WORD, "").strip()
                        if len(command) > 2:
                            # Command was said with wake word
                            self.process_command(command)
                        else:
                            # Wait for command
                            speak("Yes?")
                            self.listen_for_command()
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                time.sleep(0.5)

    def listen_for_command(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("  Listening...")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            print(f"  You said: {text}")
            self.process_command(text)
        except sr.WaitTimeoutError:
            speak("I did not hear anything.")
        except sr.UnknownValueError:
            speak("Could not understand, please try again.")
        except Exception as e:
            log.error(f"Listen error: {e}")

    def process_command(self, command: str):
        speak("On it!")
        print(f"  Executing: {command}")
        actions_json = get_ai_actions(command, self.token)
        try:
            actions = json.loads(actions_json)
            if isinstance(actions, list):
                execute_action_list(actions, token=self.token)
        except Exception as e:
            log.error(f"Execute error: {e}")
            speak("Something went wrong.")

    def text_input_loop(self):
        print("\n  Type commands and press Enter:")
        print("  Example: open youtube, search weather, open notepad\n")
        while self.running:
            try:
                command = input("  > ").strip()
                if not command: continue
                if command.lower() in ['quit', 'exit']: break
                self.process_command(command)
            except (EOFError, KeyboardInterrupt):
                break

    def run(self):
        self.running = True
        if self.microphone:
            # Start always-listening in background
            voice_thread = threading.Thread(target=self.listen_continuous, daemon=True)
            voice_thread.start()
        # Always run text input too
        self.text_input_loop()

    def stop(self):
        self.running = False


async def agent_loop(token: str):
    retry_delay = 5
    while True:
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(
                BACKEND_WS,
                ping_interval=20,
                ping_timeout=30,
                open_timeout=30
            ) as ws:
                await ws.send(json.dumps({"token": token}))
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)

                if data.get("type") == "error":
                    msg = data.get("message", "")
                    print(f"\n  Auth failed: {msg}")
                    if "expired" in msg.lower() or "invalid" in msg.lower():
                        clear_token()
                        return
                    await asyncio.sleep(retry_delay)
                    continue

                log.info("Remote control connected!")
                retry_delay = 5
                info = execute_command({"action": "get_system_info"})
                await ws.send(json.dumps({"type": "system_info", "data": info}))

                async for raw in ws:
                    try:
                        cmd = json.loads(raw)
                        mtype = cmd.get("type", "")

                        if mtype == "ping":
                            await ws.send(json.dumps({"type": "pong"}))
                            continue

                        if mtype == "task":
                            task_text = cmd.get("task", "") or cmd.get("goal", "")
                            log.info(f"Task: {task_text}")
                            speak(f"On it!")
                            actions_json = get_ai_actions(task_text, token)
                            try:
                                actions = json.loads(actions_json)
                                execute_action_list(actions, token=token)
                                await ws.send(json.dumps({
                                    "type": "task_result",
                                    "status": "completed",
                                    "actions_taken": len(actions),
                                    "task": task_text
                                }))
                            except Exception as e:
                                await ws.send(json.dumps({
                                    "type": "task_result",
                                    "status": "failed",
                                    "error": str(e)
                                }))
                            continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action", "unknown")
                            log.info(f"Remote: {action}")
                            if action not in ["screenshot", "get_system_info", "get_screen_size"]:
                                ss = take_screenshot()
                                if ss:
                                    await ws.send(json.dumps({"type": "screenshot_before", "data": ss}))
                            result = execute_command(cmd, token=token)
                            await ws.send(json.dumps({"type": "result", "action": action, "data": result}))
                            if action not in ["get_system_info", "get_screen_size"]:
                                await asyncio.sleep(0.5)
                                ss = take_screenshot()
                                if ss:
                                    await ws.send(json.dumps({"type": "screenshot_after", "data": ss}))

                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        log.error(f"Loop error: {e}")

        except websockets.exceptions.ConnectionClosed:
            log.warning("Connection closed")
        except Exception as e:
            log.error(f"Connection error: {e}")

        log.info(f"Reconnecting in {retry_delay}s...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)


def main():
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent v4.0")
    print("   Always On - Voice + Remote Control")
    print("="*52 + "\n")

    # Setup Windows autostart
    setup_autostart()

    token = get_token()
    if token:
        print("  Checking session...")
        if not check_token_valid(token):
            print("  Session expired. Please login again.")
            clear_token()
            token = None

    if not token:
        print("  Login to Dacexy\n")
        for attempt in range(3):
            token = login()
            if token: break
            remaining = 2 - attempt
            if remaining > 0:
                print(f"  {remaining} attempts remaining.\n")
        if not token:
            input("  Press Enter to exit...")
            return

    print(f"\n  Logged in successfully!")
    print(f"  Dacexy is now ALWAYS ON.")
    print(f'  Say "Hey Dacexy open YouTube" anytime!\n')

    voice = VoiceAgent(token)
    voice_thread = threading.Thread(target=voice.run, daemon=True)
    voice_thread.start()

    speak("Dacexy is now active and always listening!")

    try:
        asyncio.run(agent_loop(token))
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        voice.stop()


if __name__ == "__main__":
    main()
