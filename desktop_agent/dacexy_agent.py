"""
Dacexy Desktop Agent v3.0 — Voice + Remote Control
===================================================
Say "Hey Dacexy" to activate voice commands.
Also connects to Dacexy AI for remote control from the web.

HOW TO USE:
1. Double-click this file (python dacexy_agent.py)
2. Login with your Dacexy account
3. Say "Hey Dacexy" and give a command!
4. Or go to dacexy.vercel.app/chat for remote control
"""
import subprocess, sys

# ─── Auto-install all dependencies ───────────────────────────────────────────
PACKAGES = [
    "pyautogui",
    "pillow",
    "websockets",
    "requests",
    "speechrecognition",
    "pyttsx3",
    "pyaudio",
    "numpy",
]

print("Checking dependencies (first run may take a few minutes)...")
for pkg in PACKAGES:
    import_name = pkg.replace("-","_").split("[")[0]
    # special cases
    if pkg == "speechrecognition": import_name = "speech_recognition"
    if pkg == "openai-whisper":    import_name = "whisper"
    try:
        __import__(import_name)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

# ─── Imports ──────────────────────────────────────────────────────────────────
import asyncio, base64, io, json, logging, os, platform
import threading, time, webbrowser, re
from pathlib import Path

import pyautogui
import requests
import websockets
from PIL import ImageGrab

# Speech
import pyttsx3
import speech_recognition as sr

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.3

# ─── Config ───────────────────────────────────────────────────────────────────
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

# ─── Text to Speech ───────────────────────────────────────────────────────────
_tts_engine = None
_tts_lock   = threading.Lock()

def get_tts():
    global _tts_engine
    if _tts_engine is None:
        try:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 175)
            _tts_engine.setProperty("volume", 0.9)
            # Try to set a better voice
            voices = _tts_engine.getProperty("voices")
            for v in voices:
                if "en" in v.id.lower() and "female" in v.name.lower():
                    _tts_engine.setProperty("voice", v.id)
                    break
        except Exception as e:
            log.warning(f"TTS init failed: {e}")
    return _tts_engine

def speak(text: str):
    """Speak text through laptop speakers."""
    print(f"  🔊  Dacexy: {text}")
    try:
        with _tts_lock:
            engine = get_tts()
            if engine:
                engine.say(text)
                engine.runAndWait()
    except Exception as e:
        log.warning(f"TTS speak failed: {e}")

# ─── Config helpers ───────────────────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_token() -> str | None:
    return load_config().get("access_token")

def save_token(token: str):
    cfg = load_config(); cfg["access_token"] = token; save_config(cfg)

def clear_token():
    cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

# ─── Login ────────────────────────────────────────────────────────────────────
def login() -> str | None:
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent — Login")
    print("="*52)
    email    = input("  Email   : ").strip()
    password = input("  Password: ").strip()
    print()
    try:
        r = requests.post(
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
    except requests.exceptions.ConnectionError:
        print("  Cannot connect. Check internet.")
    except Exception as e:
        print(f"  Error: {e}")
    return None

# ─── Screenshot ───────────────────────────────────────────────────────────────
def take_screenshot() -> str | None:
    try:
        img = ImageGrab.grab()
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return None

# ─── AI command processing ────────────────────────────────────────────────────
def process_voice_command_with_ai(command: str, token: str) -> str:
    """Send voice command to Dacexy AI and get back action plan."""
    try:
        system = platform.system()
        sz     = pyautogui.size()
        prompt = f"""You are a desktop automation AI. The user said: "{command}"

Current system: {system}, Screen: {sz.width}x{sz.height}

Respond with a JSON array of actions to execute. Each action has this format:
{{"action": "...", ...params}}

Available actions:
- click: {{"action":"click","x":100,"y":200}}
- double_click: {{"action":"double_click","x":100,"y":200}}
- right_click: {{"action":"right_click","x":100,"y":200}}
- type: {{"action":"type","text":"hello"}}
- key: {{"action":"key","key":"enter"}}
- hotkey: {{"action":"hotkey","keys":["ctrl","c"]}}
- scroll: {{"action":"scroll","x":500,"y":400,"clicks":3}}
- open_url: {{"action":"open_url","url":"https://..."}}
- open_app: {{"action":"open_app","app":"notepad"}}
- run_shell: {{"action":"run_shell","command":"..."}}
- screenshot: {{"action":"screenshot"}}
- speak: {{"action":"speak","text":"..."}} - use this to respond to user

Return ONLY the JSON array. No explanation. Example:
[{{"action":"open_url","url":"https://google.com"}},{{"action":"speak","text":"Opened Google for you"}}]"""

        r = requests.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json={
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            content = data.get("content") or data.get("response") or data.get("text") or ""
            # Extract JSON from response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                return match.group(0)
        return json.dumps([{"action": "speak", "text": f"I understood: {command}, but could not plan the actions. Please try again."}])
    except Exception as e:
        log.error(f"AI processing error: {e}")
        return json.dumps([{"action": "speak", "text": "Sorry, I could not connect to Dacexy AI. Please check your internet."}])

# ─── Command executor ─────────────────────────────────────────────────────────
BLOCKED = ["rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\",
           "shutdown /s", "reboot", "mkfs", "dd if=/dev/zero", "sudo rm -rf"]

def execute_command(cmd: dict, token: str = None) -> dict:
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
            return {"status": "ok", "action": f"clicked ({x},{y})"}

        elif action == "double_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.doubleClick(x, y)
            return {"status": "ok", "action": f"double-clicked ({x},{y})"}

        elif action == "right_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.rightClick(x, y)
            return {"status": "ok", "action": f"right-clicked ({x},{y})"}

        elif action == "type":
            text = cmd.get("text", "")
            pyautogui.typewrite(text, interval=0.04)
            return {"status": "ok", "action": f"typed {len(text)} chars"}

        elif action == "key":
            key = cmd.get("key", "")
            pyautogui.press(key)
            return {"status": "ok", "action": f"pressed {key}"}

        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys: pyautogui.hotkey(*keys)
            return {"status": "ok", "action": f"hotkey {'+'.join(keys)}"}

        elif action == "scroll":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.scroll(int(cmd.get("clicks", 3)), x=x, y=y)
            return {"status": "ok", "action": "scrolled"}

        elif action == "move":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.moveTo(x, y, duration=float(cmd.get("duration", 0.3)))
            return {"status": "ok", "action": f"moved to ({x},{y})"}

        elif action == "open_url":
            url = cmd.get("url", "")
            webbrowser.open(url)
            return {"status": "ok", "action": f"opened {url}"}

        elif action == "open_app":
            app = cmd.get("app", "")
            s = platform.system()
            if s == "Windows":   os.startfile(app)
            elif s == "Darwin":  subprocess.Popen(["open", "-a", app])
            else:                subprocess.Popen([app])
            return {"status": "ok", "action": f"opened {app}"}

        elif action == "run_shell":
            command = cmd.get("command", "")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status": "error", "message": f"Blocked for safety: {b}"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": r.stdout[:3000], "stderr": r.stderr[:500], "code": r.returncode}

        elif action == "get_screen_size":
            sz = pyautogui.size()
            return {"status": "ok", "width": sz.width, "height": sz.height}

        elif action == "get_system_info":
            sz = pyautogui.size()
            return {"status": "ok", "os": platform.system(), "os_version": platform.version(),
                    "machine": platform.machine(), "hostname": platform.node(),
                    "screen_width": sz.width, "screen_height": sz.height, "agent_version": "3.0"}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Failsafe triggered — mouse corner"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status": "error", "message": str(e)}

# ─── Execute action list ──────────────────────────────────────────────────────
def execute_action_list(actions: list, token: str = None):
    """Execute a list of actions returned by AI."""
    for action in actions:
        if not isinstance(action, dict): continue
        log.info(f"▶ {action.get('action','?')}")
        result = execute_command(action, token=token)
        log.info(f"  Result: {result.get('status','?')}")
        time.sleep(0.3)

# ─── Voice recognition ────────────────────────────────────────────────────────
class VoiceAgent:
    def __init__(self, token: str):
        self.token      = token
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running    = False
        self.listening  = False

        # Calibrate microphone
        print("  🎤  Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("  ✅  Microphone ready!")
        except Exception as e:
            print(f"  ⚠   Microphone error: {e}")
            print("  Voice control may not work.")

    def listen_for_wake_word(self) -> bool:
        """Listen for wake word 'Hey Dacexy'."""
        try:
            with self.microphone as source:
                log.debug("Listening for wake word...")
                audio = self.recognizer.listen(
                    source,
                    timeout=1,
                    phrase_time_limit=4
                )
            text = self.recognizer.recognize_google(audio).lower()
            log.debug(f"Heard: {text}")
            return WAKE_WORD in text
        except sr.WaitTimeoutError:
            return False
        except sr.UnknownValueError:
            return False
        except Exception as e:
            log.debug(f"Wake word error: {e}")
            return False

    def listen_for_command(self) -> str | None:
        """Listen for a command after wake word detected."""
        speak("Yes, how can I help?")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("  🎤  Listening for command...")
                audio = self.recognizer.listen(
                    source,
                    timeout=8,
                    phrase_time_limit=15
                )
            text = self.recognizer.recognize_google(audio)
            print(f"  👤  You said: {text}")
            return text
        except sr.WaitTimeoutError:
            speak("I did not hear anything. Please try again.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I could not understand that. Please speak clearly.")
            return None
        except Exception as e:
            log.error(f"Command listening error: {e}")
            return None

    def process_command(self, command: str):
        """Process a voice command through AI and execute actions."""
        speak(f"Got it. Working on: {command[:50]}")

        # Get AI action plan
        actions_json = process_voice_command_with_ai(command, self.token)
        try:
            actions = json.loads(actions_json)
            if isinstance(actions, list):
                execute_action_list(actions, token=self.token)
            else:
                speak("Sorry, I could not plan that action.")
        except json.JSONDecodeError:
            speak("Sorry, something went wrong. Please try again.")

    def run(self):
        """Main voice loop — runs in background thread."""
        self.running = True
        print("\n  🎤  Voice control is ACTIVE!")
        print(f'  Say "{WAKE_WORD.title()}" to give a command\n')

        while self.running:
            try:
                if self.listen_for_wake_word():
                    print(f'\n  🔔  Wake word detected!')
                    command = self.listen_for_command()
                    if command:
                        self.process_command(command)
                    print(f'\n  🎤  Listening again... (say "{WAKE_WORD.title()}")')
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Voice loop error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False

# ─── WebSocket remote control ─────────────────────────────────────────────────
async def agent_loop(token: str):
    retry_delay = 5
    failures    = 0

    while True:
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(
                BACKEND_WS,
                ping_interval=20,
                ping_timeout=30
            ) as ws:
                # Authenticate
                await ws.send(json.dumps({"token": token}))
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)

                if data.get("type") == "error":
                    print(f"\n  ❌  Auth failed: {data.get('message')}")
                    clear_token()
                    return

                log.info("Remote control connected!")
                retry_delay = 5
                failures    = 0

                # Send system info
                info = execute_command({"action": "get_system_info"})
                await ws.send(json.dumps({"type": "system_info", "data": info}))

                async for raw in ws:
                    try:
                        cmd   = json.loads(raw)
                        mtype = cmd.get("type", "")

                        if mtype == "ping":
                            await ws.send(json.dumps({"type": "pong"}))
                            continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action", "unknown")
                            log.info(f"Remote command: {action}")

                            # Screenshot before
                            if action not in ["screenshot", "get_system_info", "get_screen_size"]:
                                ss = take_screenshot()
                                if ss:
                                    await ws.send(json.dumps({"type": "screenshot_before", "data": ss}))

                            result = execute_command(cmd, token=token)
                            await ws.send(json.dumps({"type": "result", "action": action, "data": result}))

                            # Screenshot after
                            if action not in ["get_system_info", "get_screen_size"]:
                                await asyncio.sleep(0.5)
                                ss = take_screenshot()
                                if ss:
                                    await ws.send(json.dumps({"type": "screenshot_after", "data": ss}))

                        elif mtype == "voice_command":
                            # Remote triggered voice command
                            command = cmd.get("command", "")
                            if command:
                                speak(f"Remote command received: {command}")
                                actions_json = process_voice_command_with_ai(command, token)
                                try:
                                    actions = json.loads(actions_json)
                                    execute_action_list(actions, token=token)
                                    await ws.send(json.dumps({"type": "voice_result", "status": "completed", "command": command}))
                                except Exception:
                                    await ws.send(json.dumps({"type": "voice_result", "status": "failed", "command": command}))

                    except json.JSONDecodeError:
                        log.warning("Invalid JSON from server")
                    except Exception as e:
                        log.error(f"Loop error: {e}")
                        await ws.send(json.dumps({"type": "error", "message": str(e)}))

        except websockets.exceptions.ConnectionClosedOK:
            log.info("Remote connection closed normally.")
        except Exception as e:
            log.error(f"Remote connection error: {e}")

        failures  += 1
        wait       = min(retry_delay * (2 ** min(failures, 5)), 120)
        log.info(f"Reconnecting remote in {wait}s...")
        await asyncio.sleep(wait)

# ─── System tray ──────────────────────────────────────────────────────────────
def run_with_tray(token: str, voice_agent: VoiceAgent):
    try:
        import pystray
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (64, 64), "#7c3aed")
        d   = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60], fill="#6d28d9")
        d.text((20, 16), "D", fill="white")

        def open_dacexy(icon, item):
            webbrowser.open("https://dacexy.vercel.app/chat")

        def toggle_voice(icon, item):
            if voice_agent.running:
                voice_agent.stop()
                speak("Voice control paused.")
            else:
                t = threading.Thread(target=voice_agent.run, daemon=True)
                t.start()
                speak("Voice control resumed.")

        def quit_agent(icon, item):
            voice_agent.stop()
            speak("Goodbye!")
            time.sleep(1)
            icon.stop()
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open Dacexy Chat", open_dacexy, default=True),
            pystray.MenuItem("Toggle Voice Control", toggle_voice),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Agent", quit_agent),
        )
        icon = pystray.Icon("Dacexy Agent", img, "Dacexy Agent v3 — Active", menu)

        # Start WebSocket remote in background
        def run_ws():
            asyncio.run(agent_loop(token))
        threading.Thread(target=run_ws, daemon=True).start()

        # Start voice in background
        threading.Thread(target=voice_agent.run, daemon=True).start()

        icon.run()

    except ImportError:
        # No systray — run both in threads
        def run_ws():
            asyncio.run(agent_loop(token))
        threading.Thread(target=run_ws, daemon=True).start()
        voice_agent.run()  # blocking

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*52)
    print("  🤖  Dacexy Desktop Agent v3.0")
    print("  Voice + AI Remote Control")
    print("="*52 + "\n")

    token = get_token()
    if not token:
        print("  First time setup — login to Dacexy\n")
        token = login()
        if not token:
            print("\n  ❌  Login failed.")
            input("  Press Enter to exit...")
            sys.exit(1)
    else:
        print("  ✅  Saved credentials found.")

    print("\n  Starting Dacexy Agent...\n")
    speak("Dacexy Agent starting. I am ready.")

    voice_agent = VoiceAgent(token)

    print("\n" + "="*52)
    print("  ✅  DACEXY AGENT IS ACTIVE")
    print(f'  🎤  Say "{WAKE_WORD.title()}" for voice commands')
    print("  🌐  Remote control: dacexy.vercel.app/chat")
    print("  Press Ctrl+C to stop")
    print("="*52 + "\n")

    try:
        run_with_tray(token, voice_agent)
    except KeyboardInterrupt:
        print("\n\n  👋  Agent stopped.")
        speak("Goodbye!")

if __name__ == "__main__":
    main()
