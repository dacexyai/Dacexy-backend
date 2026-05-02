"""
Dacexy Desktop Agent v5.0 - Full Computer Control
"""
import subprocess, sys, os

PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil", "pyperclip"
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
from PIL import ImageGrab, Image
import pyttsx3
import pyperclip

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except ImportError:
    VOICE_AVAILABLE = False

pyautogui.FAILSAFE = False
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

def setup_autostart():
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
        log.info("Auto-start enabled")
    except Exception as e:
        log.warning(f"Auto-start failed: {e}")

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
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"}, timeout=10)
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
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                save_token(token)
                print("  Login successful!")
                return token
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  Login failed: {d}")
    except Exception as e:
        print(f"  Error: {e}")
    return None

def take_screenshot() -> str:
    try:
        img = ImageGrab.grab()
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return None

def find_on_screen(text: str):
    """Find text position on screen using screenshot + AI vision."""
    try:
        import pyautogui
        location = pyautogui.locateOnScreen
        return None
    except:
        return None

def wait_and_click(x: int, y: int, wait: float = 0.5):
    time.sleep(wait)
    pyautogui.click(x, y)

def smart_type(text: str):
    """Type text reliably using clipboard."""
    try:
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
    except:
        pyautogui.write(text, interval=0.05)

BLOCKED = ["rm -rf /", "format c:", "del /s /q c:\\"]

def execute_command(cmd: dict, token=None) -> dict:
    action = cmd.get("action", "").lower()
    try:
        if action == "speak":
            text = cmd.get("text", "")
            speak(text)
            return {"status": "ok"}

        elif action == "screenshot":
            ss = take_screenshot()
            return {"status": "ok", "screenshot": ss}

        elif action == "click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.click(x, y, button=cmd.get("button", "left"))
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "double_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.doubleClick(x, y)
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "right_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.rightClick(x, y)
            return {"status": "ok"}

        elif action == "type":
            text = cmd.get("text", "")
            smart_type(text)
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
            pyautogui.moveTo(x, y, duration=0.3)
            return {"status": "ok"}

        elif action == "open_url":
            url = cmd.get("url", "")
            webbrowser.open(url)
            time.sleep(2)
            return {"status": "ok", "opened": url}

        elif action == "open_app":
            app = cmd.get("app", "")
            if platform.system() == "Windows":
                os.startfile(app)
            else:
                subprocess.Popen([app])
            time.sleep(1)
            return {"status": "ok"}

        elif action == "run_shell":
            command = cmd.get("command", "")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status": "error", "message": "Blocked"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": r.stdout[:3000]}

        elif action == "wait":
            seconds = float(cmd.get("seconds", 1))
            time.sleep(seconds)
            return {"status": "ok"}

        elif action == "press_enter":
            pyautogui.press("enter")
            return {"status": "ok"}

        elif action == "select_all":
            pyautogui.hotkey("ctrl", "a")
            return {"status": "ok"}

        elif action == "copy":
            pyautogui.hotkey("ctrl", "c")
            return {"status": "ok"}

        elif action == "paste":
            pyautogui.hotkey("ctrl", "v")
            return {"status": "ok"}

        elif action == "new_tab":
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.5)
            return {"status": "ok"}

        elif action == "close_tab":
            pyautogui.hotkey("ctrl", "w")
            return {"status": "ok"}

        elif action == "navigate_url":
            url = cmd.get("url", "")
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.3)
            smart_type(url)
            pyautogui.press("enter")
            time.sleep(2)
            return {"status": "ok"}

        elif action == "get_screen_size":
            sz = pyautogui.size()
            return {"status": "ok", "width": sz.width, "height": sz.height}

        elif action == "get_system_info":
            sz = pyautogui.size()
            return {"status": "ok", "os": platform.system(),
                    "screen_width": sz.width, "screen_height": sz.height,
                    "agent_version": "5.0"}

        elif action == "task":
            task_text = cmd.get("task", "") or cmd.get("goal", "")
            if task_text and token:
                execute_full_task(task_text, token)
                return {"status": "ok"}
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
        result = execute_command(action, token=token)
        log.info(f"Result: {result.get('status','?')}")
        time.sleep(0.4)

def execute_full_task(task: str, token: str):
    """
    Execute a full multi-step task with vision feedback.
    Takes screenshot after each step so AI can see current state.
    """
    speak("Working on it, give me a moment...")
    log.info(f"Full task: {task}")

    sz = pyautogui.size()
    screen_w, screen_h = sz.width, sz.height

    # Take initial screenshot
    ss = take_screenshot()

    prompt = f"""You are an expert Windows desktop automation AI with full computer control.

TASK: "{task}"

Screen size: {screen_w}x{screen_h}
Current screenshot is attached (base64 encoded).

You must complete this task FULLY from start to finish.
Think step by step about what needs to happen.

For example, if asked to "send an email on Gmail":
1. Open Gmail in browser
2. Wait for it to load
3. Click Compose button (usually bottom left, around x=100, y=600)
4. Fill To field
5. Fill Subject
6. Fill body
7. Click Send

IMPORTANT RULES:
- Use EXACT pixel coordinates based on the {screen_w}x{screen_h} screen
- For Gmail Compose button: approximately x=100, y=580
- For Gmail To field: approximately x=600, y=300
- For Gmail Subject: approximately x=600, y=350  
- For Gmail Body: approximately x=600, y=450
- For Gmail Send button: approximately x=200, y=650
- Always wait between steps for pages to load
- Use navigate_url to go to URLs in already open browser
- Use open_url to open new browser window

Return ONLY a JSON array. Available actions:
{{"action":"open_url","url":"https://..."}}
{{"action":"navigate_url","url":"https://..."}}
{{"action":"new_tab"}}
{{"action":"click","x":500,"y":400}}
{{"action":"double_click","x":500,"y":400}}
{{"action":"right_click","x":500,"y":400}}
{{"action":"type","text":"hello world"}}
{{"action":"key","key":"enter"}}
{{"action":"hotkey","keys":["ctrl","a"]}}
{{"action":"wait","seconds":2}}
{{"action":"press_enter"}}
{{"action":"scroll","x":500,"y":400,"clicks":3}}
{{"action":"run_shell","command":"start chrome"}}
{{"action":"open_app","app":"notepad"}}
{{"action":"screenshot"}}
{{"action":"speak","text":"Done!"}}

TASK EXAMPLES:

"open gmail and send email to test@gmail.com subject hello body hi there":
[
  {{"action":"open_url","url":"https://mail.google.com"}},
  {{"action":"wait","seconds":3}},
  {{"action":"click","x":100,"y":580}},
  {{"action":"wait","seconds":1}},
  {{"action":"click","x":600,"y":290}},
  {{"action":"type","text":"test@gmail.com"}},
  {{"action":"key","key":"tab"}},
  {{"action":"type","text":"hello"}},
  {{"action":"click","x":600,"y":450}},
  {{"action":"type","text":"hi there"}},
  {{"action":"click","x":200,"y":650}},
  {{"action":"speak","text":"Email sent successfully"}}
]

"search youtube for lofi music and play first video":
[
  {{"action":"open_url","url":"https://www.youtube.com/results?search_query=lofi+music"}},
  {{"action":"wait","seconds":3}},
  {{"action":"click","x":640,"y":350}},
  {{"action":"speak","text":"Playing lofi music on YouTube"}}
]

"open notepad and write a poem about nature":
[
  {{"action":"open_app","app":"notepad"}},
  {{"action":"wait","seconds":1}},
  {{"action":"type","text":"Nature's Beauty\\n\\nThe trees sway gently in the breeze,\\nFlowers bloom with morning ease,\\nRivers flow through valleys wide,\\nNature's wonders never hide."}},
  {{"action":"speak","text":"Written a poem about nature in Notepad"}}
]

Now complete this task: "{task}"
Return ONLY the JSON array:"""

    try:
        # Send to AI with screenshot for vision
        messages = [{"role": "user", "content": prompt}]
        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"messages": messages, "stream": False},
            timeout=45
        )

        if r.status_code == 200:
            data = r.json()
            content = data.get("content") or data.get("response") or data.get("text") or ""
            log.info(f"AI response: {content[:200]}")

            # Extract JSON array
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                arr_str = match.group(0)
                try:
                    actions = json.loads(arr_str)
                    if isinstance(actions, list) and len(actions) > 0:
                        non_speak = [a for a in actions if a.get("action") != "speak"]
                        if non_speak:
                            log.info(f"Executing {len(actions)} actions")
                            execute_action_list(actions, token=token)
                            return
                except json.JSONDecodeError:
                    pass

        # AI failed — use direct action
        log.warning("AI did not return valid actions, using direct execution")
        direct = force_direct_action(task)
        actions = json.loads(direct)
        execute_action_list(actions, token=token)

    except Exception as e:
        log.error(f"Full task error: {e}")
        speak("I encountered an error. Please try again.")

def force_direct_action(command: str) -> str:
    """Direct execution for common commands."""
    cmd = command.lower()

    # Email tasks
    if "gmail" in cmd or ("email" in cmd and "send" in cmd):
        # Extract email address if present
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', command)
        to_email = email_match.group(0) if email_match else ""

        # Extract subject
        subject = "Hello"
        if "subject" in cmd:
            subj_match = re.search(r'subject[:\s]+([^,\.]+)', cmd, re.IGNORECASE)
            if subj_match: subject = subj_match.group(1).strip()

        # Extract body
        body = "Hi, I hope this message finds you well."
        if "body" in cmd or "write" in cmd or "say" in cmd:
            body_match = re.search(r'(?:body|write|say)[:\s]+(.+?)(?:send|$)', cmd, re.IGNORECASE)
            if body_match: body = body_match.group(1).strip()

        actions = [
            {"action": "open_url", "url": "https://mail.google.com"},
            {"action": "wait", "seconds": 3},
            {"action": "speak", "text": "Gmail opened, looking for compose button"}
        ]

        if to_email:
            actions += [
                {"action": "click", "x": 100, "y": 580},
                {"action": "wait", "seconds": 1},
                {"action": "click", "x": 600, "y": 290},
                {"action": "type", "text": to_email},
                {"action": "key", "key": "tab"},
                {"action": "type", "text": subject},
                {"action": "click", "x": 600, "y": 450},
                {"action": "type", "text": body},
                {"action": "click", "x": 200, "y": 650},
                {"action": "speak", "text": f"Email sent to {to_email}"}
            ]
        else:
            actions += [
                {"action": "click", "x": 100, "y": 580},
                {"action": "speak", "text": "Compose window opened. Please fill in the details."}
            ]
        return json.dumps(actions)

    # YouTube
    if "youtube" in cmd:
        query = re.sub(r'open|youtube|play|search|on|in|chrome|browser', '', cmd).strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = "https://www.youtube.com"
        return json.dumps([
            {"action": "open_url", "url": url},
            {"action": "wait", "seconds": 3},
            {"action": "speak", "text": f"Opened YouTube{' and searched for ' + query if query else ''}"}
        ])

    # Google search
    if "search" in cmd or "google" in cmd:
        query = re.sub(r'search|google|for|on|in', '', cmd).strip()
        return json.dumps([
            {"action": "open_url", "url": f"https://www.google.com/search?q={query.replace(' ', '+')}"},
            {"action": "speak", "text": f"Searched Google for {query}"}
        ])

    # WhatsApp web
    if "whatsapp" in cmd:
        return json.dumps([
            {"action": "open_url", "url": "https://web.whatsapp.com"},
            {"action": "wait", "seconds": 3},
            {"action": "speak", "text": "WhatsApp Web opened"}
        ])

    # Instagram
    if "instagram" in cmd:
        return json.dumps([
            {"action": "open_url", "url": "https://www.instagram.com"},
            {"action": "speak", "text": "Instagram opened"}
        ])

    # Twitter/X
    if "twitter" in cmd or " x " in cmd:
        return json.dumps([
            {"action": "open_url", "url": "https://www.x.com"},
            {"action": "speak", "text": "Twitter opened"}
        ])

    # Chrome
    if "chrome" in cmd:
        return json.dumps([
            {"action": "run_shell", "command": "start chrome"},
            {"action": "speak", "text": "Opening Chrome"}
        ])

    # Notepad
    if "notepad" in cmd:
        text_match = re.search(r'(?:write|type|say)[:\s]+(.+)', cmd, re.IGNORECASE)
        actions = [{"action": "open_app", "app": "notepad"}, {"action": "wait", "seconds": 1}]
        if text_match:
            actions.append({"action": "type", "text": text_match.group(1)})
        actions.append({"action": "speak", "text": "Opened Notepad"})
        return json.dumps(actions)

    # Calculator
    if "calculator" in cmd or "calc" in cmd:
        return json.dumps([
            {"action": "open_app", "app": "calc"},
            {"action": "speak", "text": "Opening Calculator"}
        ])

    # Screenshot
    if "screenshot" in cmd:
        return json.dumps([
            {"action": "screenshot"},
            {"action": "speak", "text": "Screenshot taken"}
        ])

    # Volume controls
    if "volume up" in cmd or "louder" in cmd:
        return json.dumps([{"action": "key", "key": "volumeup"}, {"action": "speak", "text": "Volume up"}])
    if "volume down" in cmd or "quieter" in cmd:
        return json.dumps([{"action": "key", "key": "volumedown"}, {"action": "speak", "text": "Volume down"}])
    if "mute" in cmd:
        return json.dumps([{"action": "key", "key": "volumemute"}, {"action": "speak", "text": "Muted"}])

    # Default Google search
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
        self.is_processing = False

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

    def listen_continuous(self):
        if not self.microphone: return
        print(f'\n  Always listening for "{WAKE_WORD.title()}"...\n')
        while self.running:
            if self.is_processing:
                time.sleep(0.1)
                continue
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=8)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    log.info(f"Heard: {text}")
                    if WAKE_WORD in text:
                        command = text.replace(WAKE_WORD, "").strip()
                        if len(command) > 2:
                            self.is_processing = True
                            self.process_command(command)
                            self.is_processing = False
                        else:
                            speak("Yes? What would you like me to do?")
                            self.listen_next_command()
                except sr.UnknownValueError:
                    pass
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                time.sleep(0.5)

    def listen_next_command(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("  Listening for command...")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            print(f"  You said: {text}")
            self.is_processing = True
            self.process_command(text)
            self.is_processing = False
        except sr.WaitTimeoutError:
            speak("I did not hear anything.")
        except sr.UnknownValueError:
            speak("Could not understand, please try again.")
        except Exception as e:
            log.error(f"Listen error: {e}")

    def process_command(self, command: str):
        speak("On it!")
        log.info(f"Processing: {command}")
        execute_full_task(command, self.token)

    def text_input_loop(self):
        print("\n  Type commands and press Enter:")
        print("  Examples:")
        print("    open youtube and search lofi music")
        print("    send email on gmail to xyz@gmail.com subject hello body hi there")
        print("    open notepad and write a poem")
        print("    search google for weather today\n")
        while self.running:
            try:
                command = input("  > ").strip()
                if not command: continue
                if command.lower() in ['quit', 'exit']:
                    self.running = False
                    break
                threading.Thread(target=self.process_command, args=(command,), daemon=True).start()
            except (EOFError, KeyboardInterrupt):
                break

    def run(self):
        self.running = True
        if self.microphone:
            voice_thread = threading.Thread(target=self.listen_continuous, daemon=True)
            voice_thread.start()
        self.text_input_loop()

    def stop(self):
        self.running = False


async def agent_loop(token: str):
    retry_delay = 5
    while True:
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(
                BACKEND_WS, ping_interval=20, ping_timeout=30, open_timeout=30
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
                            log.info(f"Remote task: {task_text}")

                            def run_task():
                                execute_full_task(task_text, token)

                            task_thread = threading.Thread(target=run_task, daemon=True)
                            task_thread.start()
                            task_thread.join(timeout=120)

                            await ws.send(json.dumps({
                                "type": "task_result",
                                "status": "completed",
                                "task": task_text
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
    print("   Dacexy Desktop Agent v5.0")
    print("   Full Computer Control - Always On")
    print("="*52 + "\n")

    setup_autostart()

    token = get_token()
    if token:
        print("  Checking session...")
        if not check_token_valid(token):
            print("  Session expired. Please login again.")
            clear_token()
            token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            remaining = 2 - attempt
            if remaining > 0:
                print(f"  {remaining} attempts remaining.\n")
        if not token:
            input("  Press Enter to exit...")
            return

    print(f"\n  Logged in!")
    print(f"  Starting full computer control...\n")
    print(f'  Say "Hey Dacexy [command]" OR type commands below\n')

    voice = VoiceAgent(token)
    voice_thread = threading.Thread(target=voice.run, daemon=True)
    voice_thread.start()

    speak("Dacexy v5 is active! I can now do anything on your computer.")

    try:
        asyncio.run(agent_loop(token))
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        voice.stop()


if __name__ == "__main__":
    main()
