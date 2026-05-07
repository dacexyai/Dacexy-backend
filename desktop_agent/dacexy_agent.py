"""
Dacexy Desktop Agent v6.0 - Super Smart AI Agent
"""
import subprocess, sys, os

PACKAGES = ["pyautogui", "pillow", "websockets", "requests", "speechrecognition", "pyttsx3", "numpy", "psutil", "pyperclip"]

print("Checking dependencies...")
for pkg in PACKAGES:
    import_name = pkg.replace("-","_")
    if pkg == "speechrecognition": import_name = "speech_recognition"
    try: __import__(import_name)
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
    except: PYAUDIO_OK = False

import asyncio, base64, io, json, logging, platform
import threading, time, webbrowser, re, winreg
from pathlib import Path

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab
import pyttsx3
import pyperclip

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(Path.home() / "dacexy_agent.log", encoding="utf-8")])
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
        except: pass
    return _tts_engine

def speak(text: str):
    print(f"  Dacexy: {text}")
    try:
        with _tts_lock:
            e = get_tts()
            if e: e.say(text); e.runAndWait()
    except: pass

def setup_autostart():
    try:
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        cmd = f'"{sys.executable}" "{agent_path}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except: pass

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg: dict): CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
def get_token(): return load_config().get("access_token")
def save_token(t): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token(): cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return r.status_code == 200
    except: return False

def login():
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent - Login")
    print("="*52)
    email = input("  Email   : ").strip()
    password = input("  Password: ").strip()
    print()
    try:
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token: save_token(token); print("  Login successful!"); return token
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  Login failed: {d}")
    except Exception as e: print(f"  Error: {e}")
    return None

def take_screenshot():
    try:
        img = ImageGrab.grab()
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

# ─── Permission System ────────────────────────────────────────────────────────

SENSITIVE_ACTIONS = {
    "delete_file": "🗑️ DELETE FILE",
    "format": "⚠️ FORMAT DISK",
    "banking": "🏦 BANKING/FINANCE",
    "password": "🔑 PASSWORD ACCESS",
    "camera": "📷 CAMERA ACCESS",
    "microphone_record": "🎙️ RECORD AUDIO",
    "payment": "💳 PAYMENT",
    "admin": "🔐 ADMIN PRIVILEGES",
    "shutdown": "⚡ SHUTDOWN/RESTART",
    "install_software": "📦 INSTALL SOFTWARE",
    "registry": "🔧 REGISTRY EDIT",
    "send_email": "📧 SEND EMAIL",
    "share_screen": "🖥️ SHARE SCREEN",
}

def needs_permission(task: str) -> tuple[bool, str]:
    """Check if task needs user permission. Returns (needs_permission, reason)."""
    task_lower = task.lower()
    if any(w in task_lower for w in ["delete", "remove", "erase", "wipe"]) and any(w in task_lower for w in ["file", "folder", "document", "data"]):
        return True, SENSITIVE_ACTIONS["delete_file"]
    if any(w in task_lower for w in ["bank", "banking", "hdfc", "sbi", "icici", "paytm", "gpay", "phonepay", "upi", "transfer money", "send money"]):
        return True, SENSITIVE_ACTIONS["banking"]
    if any(w in task_lower for w in ["password", "credentials", "login to", "sign in to"]) and any(w in task_lower for w in ["bank", "finance", "payment"]):
        return True, SENSITIVE_ACTIONS["password"]
    if any(w in task_lower for w in ["pay", "payment", "checkout", "purchase", "buy now", "card number"]):
        return True, SENSITIVE_ACTIONS["payment"]
    if any(w in task_lower for w in ["shutdown", "restart", "reboot", "power off", "turn off computer"]):
        return True, SENSITIVE_ACTIONS["shutdown"]
    if any(w in task_lower for w in ["install", "setup.exe", "installer"]) and any(w in task_lower for w in ["software", "program", "app", ".exe"]):
        return True, SENSITIVE_ACTIONS["install_software"]
    if any(w in task_lower for w in ["format", "format disk", "format drive", "fdisk"]):
        return True, SENSITIVE_ACTIONS["format"]
    if "regedit" in task_lower or "registry" in task_lower:
        return True, SENSITIVE_ACTIONS["registry"]
    return False, ""

def ask_permission(task: str, reason: str) -> bool:
    """Ask user permission via console. Returns True if granted."""
    print("\n" + "⚠️" * 20)
    print(f"\n  PERMISSION REQUIRED: {reason}")
    print(f"\n  Task: {task}")
    print(f"\n  Dacexy wants to perform a sensitive action.")
    speak(f"Permission required. {reason}. Do you want to allow this? Say yes or no.")
    print("\n  Type 'yes' to allow or 'no' to deny: ", end="")
    try:
        response = input().strip().lower()
        granted = response in ['yes', 'y', 'allow', 'ok', 'approve']
        if granted:
            print("  ✅ Permission granted")
            speak("Permission granted. Proceeding.")
        else:
            print("  ❌ Permission denied")
            speak("Permission denied. Task cancelled.")
        return granted
    except:
        return False

# ─── Execute commands ─────────────────────────────────────────────────────────

BLOCKED = ["rm -rf /", "format c:", "del /s /q c:\\", "mkfs", "dd if=/dev/zero"]

def smart_type(text: str):
    try: pyperclip.copy(text); pyautogui.hotkey('ctrl', 'v')
    except: pyautogui.write(text, interval=0.04)

def execute_command(cmd: dict, token=None) -> dict:
    action = cmd.get("action", "").lower()
    try:
        if action == "speak":
            speak(cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "screenshot":
            return {"status": "ok", "screenshot": take_screenshot()}
        elif action == "click":
            pyautogui.click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), button=cmd.get("button", "left"))
            time.sleep(0.2)
            return {"status": "ok"}
        elif action == "double_click":
            pyautogui.doubleClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            time.sleep(0.2)
            return {"status": "ok"}
        elif action == "right_click":
            pyautogui.rightClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}
        elif action == "type":
            smart_type(cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "key":
            pyautogui.press(cmd.get("key", ""))
            return {"status": "ok"}
        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys: pyautogui.hotkey(*keys)
            return {"status": "ok"}
        elif action == "scroll":
            pyautogui.scroll(int(cmd.get("clicks", 3)), x=int(cmd.get("x", 0)), y=int(cmd.get("y", 0)))
            return {"status": "ok"}
        elif action == "move":
            pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=0.3)
            return {"status": "ok"}
        elif action == "open_url":
            webbrowser.open(cmd.get("url", ""))
            time.sleep(2)
            return {"status": "ok"}
        elif action == "open_app":
            app = cmd.get("app", "")
            if platform.system() == "Windows": os.startfile(app)
            else: subprocess.Popen([app])
            time.sleep(1)
            return {"status": "ok"}
        elif action == "run_shell":
            command = cmd.get("command", "")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status": "error", "message": "Blocked for safety"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": r.stdout[:3000]}
        elif action == "wait":
            time.sleep(float(cmd.get("seconds", 1)))
            return {"status": "ok"}
        elif action == "press_enter":
            pyautogui.press("enter")
            return {"status": "ok"}
        elif action == "navigate_url":
            url = cmd.get("url", "")
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.3)
            smart_type(url)
            pyautogui.press("enter")
            time.sleep(2)
            return {"status": "ok"}
        elif action == "new_tab":
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.5)
            return {"status": "ok"}
        elif action == "get_system_info":
            sz = pyautogui.size()
            return {"status": "ok", "os": platform.system(), "screen_width": sz.width, "screen_height": sz.height, "agent_version": "6.0"}
        elif action == "task":
            task_text = cmd.get("task", "") or cmd.get("goal", "")
            if task_text and token:
                execute_full_task(task_text, token)
            return {"status": "ok"}
        else:
            return {"status": "error", "message": f"Unknown: {action}"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status": "error", "message": str(e)}

def execute_action_list(actions: list, token=None):
    for action in actions:
        if not isinstance(action, dict): continue
        log.info(f"Executing: {action.get('action','?')}")
        execute_command(action, token=token)
        time.sleep(0.3)

# ─── Super Smart AI Brain ─────────────────────────────────────────────────────

def get_ai_actions(task: str, token: str, screenshot_b64: str = None) -> str:
    """
    Send task to AI with full context. AI thinks step by step and returns
    executable actions. Never explains — just does.
    """
    sz = pyautogui.size()
    system = platform.system()

    prompt = f"""You are an elite desktop automation AI. You control a {system} computer ({sz.width}x{sz.height} screen).

TASK: "{task}"

YOUR JOB:
- Complete the task FULLY from start to finish
- Return ONLY a JSON array of actions
- NEVER add explanations or text outside the JSON
- Think step by step about what clicks/types are needed
- Always end with a speak action giving the FINAL OUTPUT to user

SCREEN COORDINATES FOR COMMON UI:
- Gmail Compose button: x=100, y=580
- Gmail To field: x=600, y=290  
- Gmail Subject: x=600, y=345
- Gmail Body: x=600, y=450
- Gmail Send: x=190, y=655
- Browser address bar (Ctrl+L then type)
- Center of screen: x={sz.width//2}, y={sz.height//2}

AVAILABLE ACTIONS (return ONLY these in JSON array):
{{"action":"open_url","url":"https://..."}}
{{"action":"navigate_url","url":"https://..."}}
{{"action":"new_tab"}}
{{"action":"click","x":500,"y":400}}
{{"action":"double_click","x":500,"y":400}}
{{"action":"right_click","x":500,"y":400}}
{{"action":"type","text":"hello"}}
{{"action":"key","key":"enter"}}
{{"action":"hotkey","keys":["ctrl","a"]}}
{{"action":"wait","seconds":2}}
{{"action":"scroll","x":500,"y":400,"clicks":3}}
{{"action":"run_shell","command":"start chrome"}}
{{"action":"open_app","app":"notepad"}}
{{"action":"screenshot"}}
{{"action":"speak","text":"Final result here"}}

TASK PATTERNS:

"open youtube":
[{{"action":"open_url","url":"https://youtube.com"}},{{"action":"speak","text":"YouTube is now open"}}]

"search youtube for [query]":
[{{"action":"open_url","url":"https://youtube.com/results?search_query=[query]"}},{{"action":"wait","seconds":3}},{{"action":"click","x":{sz.width//2},"y":350}},{{"action":"speak","text":"Playing [query] on YouTube"}}]

"send email on gmail to X@gmail.com subject Y body Z":
[{{"action":"open_url","url":"https://mail.google.com"}},{{"action":"wait","seconds":4}},{{"action":"click","x":100,"y":580}},{{"action":"wait","seconds":1}},{{"action":"click","x":600,"y":290}},{{"action":"type","text":"X@gmail.com"}},{{"action":"key","key":"tab"}},{{"action":"type","text":"Y"}},{{"action":"click","x":600,"y":450}},{{"action":"type","text":"Z"}},{{"action":"click","x":190,"y":655}},{{"action":"speak","text":"Email sent to X successfully"}}]

"search google for X":
[{{"action":"open_url","url":"https://google.com/search?q=X"}},{{"action":"speak","text":"Here are Google results for X"}}]

"open notepad and write X":
[{{"action":"open_app","app":"notepad"}},{{"action":"wait","seconds":1}},{{"action":"type","text":"X"}},{{"action":"speak","text":"Written in Notepad"}}]

"take screenshot":
[{{"action":"screenshot"}},{{"action":"speak","text":"Screenshot taken"}}]

"open whatsapp":
[{{"action":"open_url","url":"https://web.whatsapp.com"}},{{"action":"speak","text":"WhatsApp Web is open"}}]

"what is the time" or "what time is it":
[{{"action":"run_shell","command":"echo %time%"}},{{"action":"speak","text":"Checking system time for you"}}]

Now complete this task and return ONLY JSON array: "{task}" """

    try:
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
            log.info(f"AI raw: {content[:300]}")
            match = re.search(r'\[[\s\S]*?\]', content)
            if match:
                try:
                    actions = json.loads(match.group(0))
                    if isinstance(actions, list) and len(actions) > 0:
                        non_speak = [a for a in actions if a.get("action") != "speak"]
                        if non_speak:
                            return json.dumps(actions)
                except: pass
        return force_direct_action(task)
    except Exception as e:
        log.error(f"AI error: {e}")
        return force_direct_action(task)

def force_direct_action(command: str) -> str:
    """Instant execution for common commands without needing AI."""
    cmd = command.lower().strip()

    if "youtube" in cmd:
        query = re.sub(r'open|youtube|play|search|for|on|in|chrome|browser|new tab', '', cmd).strip()
        url = f"https://youtube.com/results?search_query={query.replace(' ','+')}" if query else "https://youtube.com"
        return json.dumps([{"action":"open_url","url":url},{"action":"wait","seconds":3},{"action":"speak","text":f"YouTube opened{' and searched for '+query if query else ''}"}])

    if ("email" in cmd or "gmail" in cmd) and ("send" in cmd or "compose" in cmd or "write" in cmd):
        email_match = re.search(r'[\w.\-+]+@[\w.\-]+\.\w+', command)
        to_email = email_match.group(0) if email_match else ""
        subj_match = re.search(r'subject[:\s]+([^,]+?)(?:\s+body|\s+saying|\s+with body|$)', command, re.I)
        body_match = re.search(r'(?:body|saying|content)[:\s]+(.+?)(?:send|$)', command, re.I)
        subject = subj_match.group(1).strip() if subj_match else "Hello"
        body = body_match.group(1).strip() if body_match else "Hi, I hope you are doing well."
        actions = [{"action":"open_url","url":"https://mail.google.com"},{"action":"wait","seconds":4}]
        if to_email:
            actions += [
                {"action":"click","x":100,"y":580},{"action":"wait","seconds":1},
                {"action":"click","x":600,"y":290},{"action":"type","text":to_email},
                {"action":"key","key":"tab"},{"action":"type","text":subject},
                {"action":"click","x":600,"y":450},{"action":"type","text":body},
                {"action":"click","x":190,"y":655},
                {"action":"speak","text":f"Email sent to {to_email} with subject '{subject}'"}
            ]
        else:
            actions += [{"action":"click","x":100,"y":580},{"action":"speak","text":"Gmail compose window opened"}]
        return json.dumps(actions)

    if "whatsapp" in cmd:
        return json.dumps([{"action":"open_url","url":"https://web.whatsapp.com"},{"action":"speak","text":"WhatsApp Web opened"}])

    if "instagram" in cmd:
        return json.dumps([{"action":"open_url","url":"https://instagram.com"},{"action":"speak","text":"Instagram opened"}])

    if "twitter" in cmd or " x.com" in cmd:
        return json.dumps([{"action":"open_url","url":"https://x.com"},{"action":"speak","text":"Twitter opened"}])

    if "facebook" in cmd:
        return json.dumps([{"action":"open_url","url":"https://facebook.com"},{"action":"speak","text":"Facebook opened"}])

    if "google" in cmd and ("search" in cmd or "find" in cmd):
        query = re.sub(r'search|google|for|on|find|in', '', cmd).strip()
        return json.dumps([{"action":"open_url","url":f"https://google.com/search?q={query.replace(' ','+')}"},{"action":"speak","text":f"Google results for {query}"}])

    if "chrome" in cmd and ("open" in cmd or "start" in cmd or "launch" in cmd):
        return json.dumps([{"action":"run_shell","command":"start chrome"},{"action":"speak","text":"Chrome opened"}])

    if "notepad" in cmd:
        text_match = re.search(r'(?:write|type|say|note)[:\s]+(.+)', command, re.I)
        actions = [{"action":"open_app","app":"notepad"},{"action":"wait","seconds":1}]
        if text_match: actions.append({"action":"type","text":text_match.group(1)})
        actions.append({"action":"speak","text":"Notepad opened"})
        return json.dumps(actions)

    if "calculator" in cmd or " calc" in cmd:
        return json.dumps([{"action":"open_app","app":"calc"},{"action":"speak","text":"Calculator opened"}])

    if "screenshot" in cmd or "screen shot" in cmd:
        return json.dumps([{"action":"screenshot"},{"action":"speak","text":"Screenshot taken"}])

    if "volume up" in cmd or "louder" in cmd:
        return json.dumps([{"action":"key","key":"volumeup"},{"action":"speak","text":"Volume increased"}])

    if "volume down" in cmd or "quieter" in cmd:
        return json.dumps([{"action":"key","key":"volumedown"},{"action":"speak","text":"Volume decreased"}])

    if "mute" in cmd:
        return json.dumps([{"action":"key","key":"volumemute"},{"action":"speak","text":"Muted"}])

    if "time" in cmd or "what time" in cmd:
        import datetime
        now = datetime.datetime.now().strftime("%I:%M %p")
        return json.dumps([{"action":"speak","text":f"The current time is {now}"}])

    if "date" in cmd or "today" in cmd:
        import datetime
        today = datetime.datetime.now().strftime("%B %d, %Y")
        return json.dumps([{"action":"speak","text":f"Today is {today}"}])

    if "lock" in cmd and "screen" in cmd:
        return json.dumps([{"action":"hotkey","keys":["win","l"]},{"action":"speak","text":"Screen locked"}])

    if "minimize" in cmd and "all" in cmd:
        return json.dumps([{"action":"hotkey","keys":["win","d"]},{"action":"speak","text":"All windows minimized"}])

    if "close" in cmd and ("window" in cmd or "tab" in cmd):
        return json.dumps([{"action":"hotkey","keys":["alt","f4"]},{"action":"speak","text":"Window closed"}])

    # Default: Google search
    query = command.replace(" ", "+")
    return json.dumps([{"action":"open_url","url":f"https://google.com/search?q={query}"},{"action":"speak","text":f"Searching for {command}"}])

def execute_full_task(task: str, token: str):
    """Main task executor — checks permission, gets AI plan, executes, gives output."""
    log.info(f"Task: {task}")

    # Check if permission needed
    needs_perm, reason = needs_permission(task)
    if needs_perm:
        granted = ask_permission(task, reason)
        if not granted:
            speak(f"Task cancelled. You did not grant permission for {reason}.")
            return

    speak("On it!")

    # Take screenshot for context
    ss = take_screenshot()

    # Get AI action plan
    actions_json = get_ai_actions(task, token, ss)

    try:
        actions = json.loads(actions_json)
        if isinstance(actions, list) and len(actions) > 0:
            log.info(f"Executing {len(actions)} actions")
            execute_action_list(actions, token=token)
        else:
            speak("I could not plan that task. Please try rephrasing.")
    except Exception as e:
        log.error(f"Execute error: {e}")
        speak("Something went wrong. Please try again.")

# ─── Voice Agent ──────────────────────────────────────────────────────────────

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
            print("  No microphone — using TEXT mode.")

    def listen_continuous(self):
        if not self.microphone: return
        print(f'\n  Always listening for "{WAKE_WORD.title()}"...\n')
        while self.running:
            if self.is_processing: time.sleep(0.1); continue
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=8)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    if WAKE_WORD in text:
                        command = text.replace(WAKE_WORD, "").strip()
                        if len(command) > 2:
                            self.is_processing = True
                            threading.Thread(target=self._run_task, args=(command,), daemon=True).start()
                        else:
                            speak("Yes?")
                            self._listen_next()
                except sr.UnknownValueError: pass
            except sr.WaitTimeoutError: pass
            except Exception: time.sleep(0.5)

    def _listen_next(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            print(f"  You said: {text}")
            self.is_processing = True
            threading.Thread(target=self._run_task, args=(text,), daemon=True).start()
        except: speak("I did not hear anything.")

    def _run_task(self, command: str):
        try:
            execute_full_task(command, self.token)
        finally:
            self.is_processing = False

    def text_input_loop(self):
        print("\n  Commands: type anything and press Enter")
        print("  Examples: open youtube | send email to x@gmail.com | search google for weather\n")
        while self.running:
            try:
                command = input("  > ").strip()
                if not command: continue
                if command.lower() in ['quit', 'exit']: self.running = False; break
                threading.Thread(target=self._run_task, args=(command,), daemon=True).start()
            except (EOFError, KeyboardInterrupt): break

    def run(self):
        self.running = True
        if self.microphone:
            threading.Thread(target=self.listen_continuous, daemon=True).start()
        self.text_input_loop()

    def stop(self): self.running = False

# ─── WebSocket Remote ─────────────────────────────────────────────────────────

async def agent_loop(token: str):
    retry_delay = 5
    while True:
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(BACKEND_WS, ping_interval=20, ping_timeout=30, open_timeout=30) as ws:
                await ws.send(json.dumps({"token": token}))
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)

                if data.get("type") == "error":
                    msg = data.get("message", "")
                    print(f"\n  Auth failed: {msg}")
                    if "expired" in msg.lower() or "invalid" in msg.lower():
                        clear_token(); return
                    await asyncio.sleep(retry_delay); continue

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
                            await ws.send(json.dumps({"type": "pong"})); continue

                        if mtype == "task":
                            task_text = cmd.get("task", "") or cmd.get("goal", "")
                            log.info(f"Remote task: {task_text}")

                            def run_remote_task():
                                execute_full_task(task_text, token)

                            t = threading.Thread(target=run_remote_task, daemon=True)
                            t.start(); t.join(timeout=120)
                            await ws.send(json.dumps({"type": "task_result", "status": "completed", "task": task_text}))
                            continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action", "unknown")
                            log.info(f"Remote: {action}")
                            if action not in ["screenshot", "get_system_info", "get_screen_size"]:
                                ss = take_screenshot()
                                if ss: await ws.send(json.dumps({"type": "screenshot_before", "data": ss}))
                            result = execute_command(cmd, token=token)
                            await ws.send(json.dumps({"type": "result", "action": action, "data": result}))
                            await asyncio.sleep(0.5)
                            ss = take_screenshot()
                            if ss: await ws.send(json.dumps({"type": "screenshot_after", "data": ss}))

                    except json.JSONDecodeError: pass
                    except Exception as e: log.error(f"Loop error: {e}")

        except websockets.exceptions.ConnectionClosed: log.warning("Connection closed")
        except Exception as e: log.error(f"Connection error: {e}")

        log.info(f"Reconnecting in {retry_delay}s...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent v6.0")
    print("   Super Smart — Always On")
    print("="*52 + "\n")

    setup_autostart()

    token = get_token()
    if token:
        print("  Checking session...")
        if not check_token_valid(token):
            print("  Session expired. Please login again.")
            clear_token(); token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            remaining = 2 - attempt
            if remaining > 0: print(f"  {remaining} attempts remaining.\n")
        if not token:
            input("  Press Enter to exit..."); return

    print(f"\n  Logged in!")
    print(f"  Starting super smart agent...\n")

    voice = VoiceAgent(token)
    voice_thread = threading.Thread(target=voice.run, daemon=True)
    voice_thread.start()

    speak("Dacexy v6 is active. I am ready to do anything on your computer.")

    try:
        asyncio.run(agent_loop(token))
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        voice.stop()

if __name__ == "__main__":
    main()
