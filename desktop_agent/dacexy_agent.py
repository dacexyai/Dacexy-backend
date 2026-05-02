"""
Dacexy Desktop Agent v3.1
Fixed: token expiry handling, auth retry, robust reconnect
"""
import subprocess, sys, os

PACKAGES = [
    "pyautogui",
    "pillow",
    "websockets",
    "requests",
    "speechrecognition",
    "pyttsx3",
    "numpy",
    "psutil",
]

print("Checking dependencies...")
for pkg in PACKAGES:
    import_name = pkg.replace("-", "_").split("[")[0]
    if pkg == "speechrecognition":
        import_name = "speech_recognition"
    try:
        __import__(import_name)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

import asyncio, base64, io, json, logging, platform
import threading, time, webbrowser, re
from pathlib import Path

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab
import pyttsx3

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

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

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except:
            pass
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

def verify_token_http(token: str) -> bool:
    """Quick HTTP check to see if the token is still valid before trying WebSocket."""
    try:
        r = req_lib.get(
            f"{BACKEND_HTTP}/agent/desktop/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        return r.status_code == 200
    except Exception as e:
        log.warning(f"Token verify HTTP call failed: {e}")
        # Network error – can't tell, assume token might still be ok
        return True

def login() -> str | None:
    print("\n" + "=" * 52)
    print("   Dacexy Desktop Agent - Login")
    print("=" * 52)
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
            data = r.json()
            token = data.get("access_token", "")
            if token:
                save_token(token)
                print("  Login successful!")
                return token
            print("  No token received from server.")
        else:
            try:
                d = r.json().get("detail", r.text)
            except Exception:
                d = r.text
            if isinstance(d, list):
                d = d[0].get("msg", str(d))
            print(f"  Login failed ({r.status_code}): {d}")
    except req_lib.exceptions.ConnectionError:
        print("  Cannot connect to server. Check your internet.")
    except Exception as e:
        print(f"  Error during login: {e}")
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

BLOCKED = ["rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\", "shutdown /s"]

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
            return {"status": "ok", "action": f"clicked ({x},{y})"}

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
            pyautogui.typewrite(text, interval=0.04)
            return {"status": "ok"}

        elif action == "key":
            pyautogui.press(cmd.get("key", ""))
            return {"status": "ok"}

        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
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
            webbrowser.open(cmd.get("url", ""))
            return {"status": "ok"}

        elif action == "open_app":
            app = cmd.get("app", "")
            s = platform.system()
            if s == "Windows":
                os.startfile(app)
            elif s == "Darwin":
                subprocess.Popen(["open", "-a", app])
            else:
                subprocess.Popen([app])
            return {"status": "ok"}

        elif action == "run_shell":
            command = cmd.get("command", "")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status": "error", "message": f"Blocked: {b}"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": r.stdout[:3000], "stderr": r.stderr[:500]}

        elif action == "get_screen_size":
            sz = pyautogui.size()
            return {"status": "ok", "width": sz.width, "height": sz.height}

        elif action == "get_system_info":
            sz = pyautogui.size()
            return {
                "status": "ok",
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "hostname": platform.node(),
                "screen_width": sz.width,
                "screen_height": sz.height,
                "agent_version": "3.1"
            }

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Failsafe triggered (mouse moved to corner)"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status": "error", "message": str(e)}

def execute_action_list(actions: list, token=None):
    for action in actions:
        if not isinstance(action, dict):
            continue
        log.info(f"Executing: {action.get('action', '?')}")
        execute_command(action, token=token)
        time.sleep(0.3)

def process_ai_command(command: str, token: str) -> list:
    """Send a natural language command to the backend AI and get back a list of actions."""
    try:
        sz = pyautogui.size()
        prompt = (
            f'You are a desktop automation AI. The user wants to: "{command}"\n'
            f'System: {platform.system()}, Screen: {sz.width}x{sz.height}\n\n'
            'Return ONLY a valid JSON array of actions, no explanation, no markdown. Available actions:\n'
            '{"action":"click","x":100,"y":200}\n'
            '{"action":"double_click","x":100,"y":200}\n'
            '{"action":"type","text":"hello"}\n'
            '{"action":"key","key":"enter"}\n'
            '{"action":"hotkey","keys":["ctrl","c"]}\n'
            '{"action":"open_url","url":"https://..."}\n'
            '{"action":"open_app","app":"notepad"}\n'
            '{"action":"run_shell","command":"..."}\n'
            '{"action":"scroll","x":500,"y":400,"clicks":3}\n'
            '{"action":"screenshot"}\n'
            '{"action":"speak","text":"..."}\n\n'
            'Example for "open google": [{"action":"open_url","url":"https://google.com"},{"action":"speak","text":"Opened Google for you"}]'
        )

        endpoints = [
            (f"{BACKEND_HTTP}/agent/ai", {"prompt": prompt}),
            (f"{BACKEND_HTTP}/ai/chat", {"messages": [{"role": "user", "content": prompt}], "stream": False}),
        ]

        for url, payload in endpoints:
            try:
                r = req_lib.post(
                    url,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                    json=payload,
                    timeout=45
                )
                if r.status_code == 200:
                    data = r.json()
                    content = (
                        data.get("content") or
                        data.get("response") or
                        data.get("result") or
                        data.get("text") or
                        (data.get("choices", [{}])[0].get("message", {}).get("content", "") if data.get("choices") else "") or
                        ""
                    )
                    if isinstance(content, list):
                        content = " ".join(
                            block.get("text", "") for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        )
                    match = re.search(r'\[[\s\S]*\]', str(content))
                    if match:
                        actions = json.loads(match.group(0))
                        if isinstance(actions, list) and len(actions) > 0:
                            return actions
            except Exception as e:
                log.warning(f"Endpoint {url} failed: {e}")
                continue

        return _fallback_action(command)

    except Exception as e:
        log.error(f"AI command error: {e}")
        return [{"action": "speak", "text": "Sorry, could not connect to Dacexy AI."}]

def _fallback_action(command: str) -> list:
    cmd_lower = command.lower()
    if "open" in cmd_lower and ("chrome" in cmd_lower or "browser" in cmd_lower):
        return [{"action": "open_app", "app": "chrome"}, {"action": "speak", "text": "Opening Chrome"}]
    if "open" in cmd_lower and "notepad" in cmd_lower:
        return [{"action": "open_app", "app": "notepad"}, {"action": "speak", "text": "Opening Notepad"}]
    if any(x in cmd_lower for x in ["google", "search"]):
        query = cmd_lower.replace("search", "").replace("google", "").strip()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}" if query else "https://google.com"
        return [{"action": "open_url", "url": url}, {"action": "speak", "text": f"Searching for {query}"}]
    if "screenshot" in cmd_lower:
        return [{"action": "screenshot"}, {"action": "speak", "text": "Taking a screenshot"}]
    return [{"action": "speak", "text": f"I heard: {command}. Please try again or be more specific."}]


class VoiceAgent:
    def __init__(self, token: str):
        self.token = token
        self.running = False
        if not SR_AVAILABLE:
            print("  Voice: speech_recognition not available, voice disabled.")
            self.microphone = None
            self.recognizer = None
            return
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
            print("  Calibrating microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("  Microphone ready!")
        except Exception as e:
            print(f"  Microphone error (voice disabled): {e}")
            self.microphone = None

    def listen_for_wake_word(self) -> bool:
        if not self.microphone or not self.recognizer:
            return False
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=4)
            text = self.recognizer.recognize_google(audio).lower()
            return WAKE_WORD in text
        except:
            return False

    def listen_for_command(self):
        speak("Yes, how can I help?")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("  Listening for command...")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            print(f"  You said: {text}")
            return text
        except sr.WaitTimeoutError:
            speak("I did not hear anything.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, could not understand.")
            return None
        except Exception as e:
            log.error(f"Listen error: {e}")
            return None

    def process_command(self, command: str):
        speak("Working on it")
        actions = process_ai_command(command, self.token)
        try:
            if isinstance(actions, list) and len(actions) > 0:
                execute_action_list(actions, token=self.token)
            else:
                speak("Could not plan that action.")
        except Exception as e:
            log.error(f"Execute error: {e}")
            speak("Something went wrong.")

    def run(self):
        self.running = True
        if not self.microphone:
            print("  Voice control unavailable (no microphone).")
            return
        print(f'\n  Voice control ACTIVE! Say "{WAKE_WORD.title()}" to give a command\n')
        while self.running:
            try:
                if self.listen_for_wake_word():
                    print("\n  Wake word detected!")
                    command = self.listen_for_command()
                    if command:
                        self.process_command(command)
                    print("\n  Listening again...")
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Voice loop error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False


# ──────────────────────────────────────────────────────────────────────────────
# FIX: The main auth loop now:
#   1. Verifies token via HTTP before trying WebSocket (catches expiry early)
#   2. On "Authentication failed" from WS, clears token and prompts re-login
#      instead of exiting (infinite loop -> user just re-enters credentials)
#   3. Separates "bad token" (stop & re-login) from "network error" (retry)
# ──────────────────────────────────────────────────────────────────────────────

async def agent_loop(token_holder: list, voice_holder: list):
    """
    token_holder[0] holds the current token so we can refresh it mid-run.
    voice_holder[0] holds the VoiceAgent so we can update its token too.
    """
    retry_delay = 5

    while True:
        token = token_holder[0]

        # ── Pre-flight: check token via HTTP first ──────────────────────────
        print("\n  Checking token validity...")
        if not verify_token_http(token):
            print("\n  Token rejected by server (expired or invalid).")
            clear_token()
            new_token = None
            for attempt in range(3):
                new_token = login()
                if new_token:
                    break
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"  {remaining} attempt(s) remaining.\n")
            if not new_token:
                print("\n  Could not log in. Exiting.")
                return
            token_holder[0] = new_token
            if voice_holder[0]:
                voice_holder[0].token = new_token
            token = new_token
            retry_delay = 5

        # ── WebSocket connection ────────────────────────────────────────────
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(
                BACKEND_WS,
                ping_interval=20,
                ping_timeout=30,
                open_timeout=30
            ) as ws:
                await ws.send(json.dumps({"token": token}))

                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=15)
                except asyncio.TimeoutError:
                    log.warning("Server did not respond to auth in time, retrying...")
                    await asyncio.sleep(retry_delay)
                    continue

                data = json.loads(resp)

                if data.get("type") == "error":
                    msg = data.get("message", "")
                    print(f"\n  Auth failed: {msg}")

                    # ── FIX: bad token -> re-login, don't just exit ─────────
                    if "authentication" in msg.lower() or "invalid token" in msg.lower() or "token" in msg.lower():
                        clear_token()
                        print("  Your session has expired. Please log in again.\n")
                        new_token = None
                        for attempt in range(3):
                            new_token = login()
                            if new_token:
                                break
                            remaining = 2 - attempt
                            if remaining > 0:
                                print(f"  {remaining} attempt(s) remaining.\n")
                        if not new_token:
                            print("\n  Could not log in. Exiting.")
                            return
                        token_holder[0] = new_token
                        if voice_holder[0]:
                            voice_holder[0].token = new_token
                        retry_delay = 5
                        continue   # retry the loop with new token
                    else:
                        # Non-auth error from server, just retry
                        await asyncio.sleep(retry_delay)
                        continue

                # ── Authenticated ───────────────────────────────────────────
                log.info("Remote control connected!")
                speak("Dacexy remote control connected!")
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

                        if mtype in ("task", "voice_command"):
                            command = (
                                cmd.get("command", "") or
                                cmd.get("task", "") or
                                cmd.get("goal", "")
                            )
                            if command:
                                log.info(f"AI task received: {command}")
                                speak("Working on it")
                                actions = process_ai_command(command, token)
                                execute_action_list(actions, token=token)
                                await ws.send(json.dumps({
                                    "type": "task_result",
                                    "status": "completed",
                                    "actions_taken": len(actions),
                                    "actions": actions
                                }))
                            continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action", "unknown")
                            log.info(f"Remote command: {action}")

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
                        log.warning("Invalid JSON from server")
                    except Exception as e:
                        log.error(f"Loop error: {e}")

        except websockets.exceptions.ConnectionClosedError as e:
            log.warning(f"Connection closed: {e}")
        except OSError as e:
            log.error(f"Network error: {e}")
        except Exception as e:
            log.error(f"Connection error: {e}")

        log.info(f"Reconnecting in {retry_delay}s...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)


def main():
    print("\n" + "=" * 52)
    print("   Dacexy Desktop Agent v3.1")
    print("   Voice + AI Remote Control")
    print("=" * 52 + "\n")

    token = get_token()

    if not token:
        print("  First time setup - login to Dacexy\n")
        for attempt in range(3):
            token = login()
            if token:
                break
            remaining = 2 - attempt
            if remaining > 0:
                print(f"  Login failed. {remaining} attempt(s) remaining.\n")
        if not token:
            print("  Could not log in. Press Enter to exit...")
            input()
            return

    print(f"\n  Logged in successfully!")
    print(f"  Starting voice control + remote connection...\n")

    # Use lists so agent_loop can mutate them (token refresh, voice token update)
    token_holder = [token]
    voice = VoiceAgent(token)
    voice_holder = [voice]

    voice_thread = threading.Thread(target=voice.run, daemon=True)
    voice_thread.start()

    speak("Dacexy agent is now active and ready!")

    try:
        asyncio.run(agent_loop(token_holder, voice_holder))
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        voice.stop()


if __name__ == "__main__":
    main()
