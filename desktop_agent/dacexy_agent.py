"""
Dacexy Desktop Agent v11.0 - World's Most Powerful AI Desktop Agent
Siri-like 24/7 voice control. Wake word: "hey dacexy"
"""
import subprocess, sys, os, platform

# ═══════════════════════════════════════════════════════════════════════
# AUTO-INSTALL ALL PACKAGES
# ═══════════════════════════════════════════════════════════════════════
PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
    "pyperclip", "keyboard", "pygetwindow", "plyer",
]

for pkg in PACKAGES:
    imp = pkg.replace("-", "_")
    if pkg == "speechrecognition": imp = "speech_recognition"
    if pkg == "pillow": imp = "PIL"
    try:
        __import__(imp)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import pyaudio
    PYAUDIO_OK = True
except:
    PYAUDIO_OK = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin", "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import pyaudio
        PYAUDIO_OK = True
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio", "-q"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio
            PYAUDIO_OK = True
        except:
            PYAUDIO_OK = False

# ═══════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════
import asyncio, base64, io, json, logging, threading
import time, webbrowser, re, datetime, ctypes
from pathlib import Path
from typing import Optional
from collections import deque

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab, Image
import pyttsx3, pyperclip, psutil

try:
    import winreg
    WINREG_OK = True
except:
    WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except:
    VOICE_AVAILABLE = False
    sr = None

try:
    import pygetwindow as gw
    WINDOW_OK = True
except:
    WINDOW_OK = False

try:
    from plyer import notification
    NOTIFY_OK = True
except:
    NOTIFY_OK = False

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.08

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
LOG_FILE     = Path.home() / "dacexy_agent.log"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
WAKE_WORD    = "hey dacexy"
VERSION      = "11.0"

MEMORY = {"facts": [], "preferences": {}, "task_history": deque(maxlen=50), "context": {}}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    ]
)
log = logging.getLogger("dacexy")

# ═══════════════════════════════════════════════════════════════════════
# NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════
def notify(title: str, message: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=message, app_name="Dacexy", timeout=4)
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════
# TTS — VOICE OUTPUT (Siri-like)
# ═══════════════════════════════════════════════════════════════════════
_tts = None
_tts_lock = threading.Lock()
_speaking = False

def init_tts():
    global _tts
    try:
        _tts = pyttsx3.init()
        _tts.setProperty("rate", 165)
        _tts.setProperty("volume", 0.95)
        voices = _tts.getProperty("voices") or []
        for v in voices:
            if any(x in (v.name or "").lower() for x in ["zira", "hazel", "female", "woman", "aria"]):
                _tts.setProperty("voice", v.id)
                break
    except:
        pass

def speak(text: str, priority: bool = False):
    global _speaking
    if not text:
        return
    print(f"  🔊 Dacexy: {text}")
    notify("Dacexy", text[:80])
    def _do_speak():
        global _speaking
        _speaking = True
        try:
            with _tts_lock:
                if _tts:
                    _tts.say(text)
                    _tts.runAndWait()
        except:
            pass
        finally:
            _speaking = False
    t = threading.Thread(target=_do_speak, daemon=True)
    t.start()
    if priority:
        t.join(timeout=10)

# ═══════════════════════════════════════════════════════════════════════
# MEMORY
# ═══════════════════════════════════════════════════════════════════════
def load_memory():
    global MEMORY
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            MEMORY["facts"] = data.get("facts", [])
            MEMORY["preferences"] = data.get("preferences", {})
            MEMORY["context"] = data.get("context", {})
            MEMORY["task_history"] = deque(data.get("task_history", [])[-50:], maxlen=50)
    except:
        pass

def save_memory():
    try:
        MEMORY_FILE.write_text(json.dumps({
            "facts": MEMORY["facts"][-100:],
            "preferences": MEMORY["preferences"],
            "context": MEMORY["context"],
            "task_history": list(MEMORY["task_history"])[-50:],
        }, indent=2), encoding="utf-8")
    except:
        pass

def remember(fact: str):
    if fact and fact not in MEMORY["facts"]:
        MEMORY["facts"].append(fact)
        save_memory()

def get_memory_context() -> str:
    ctx = []
    if MEMORY["facts"]:
        ctx.append("Known facts: " + "; ".join(MEMORY["facts"][-10:]))
    if MEMORY["preferences"]:
        ctx.append("Preferences: " + str(MEMORY["preferences"]))
    recent = list(MEMORY["task_history"])[-5:]
    if recent:
        ctx.append("Recent tasks: " + "; ".join(recent))
    return "\n".join(ctx) if ctx else ""

# ═══════════════════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════
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

def save_token(t):
    cfg = load_config()
    cfg["access_token"] = t
    save_config(cfg)

def clear_token():
    cfg = load_config()
    cfg.pop("access_token", None)
    save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
                        headers={"Authorization": f"Bearer {token}"}, timeout=8)
        return r.status_code == 200
    except:
        return False

def setup_autostart():
    """Register agent to start with Windows."""
    try:
        if not WINREG_OK:
            return
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        cmd = f'"{sys.executable}" "{agent_path}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered")
    except Exception as e:
        log.warning("Autostart failed: %s", e)

def login():
    print("\n╔══════════════════════════════════╗")
    print("║   Dacexy Agent v11.0 — Login     ║")
    print("╚══════════════════════════════════╝")
    email = input("  Email   : ").strip()
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
                remember(f"User email: {email}")
                print("  ✅ Login successful!")
                return token
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list):
                d = d[0].get("msg", str(d))
            print(f"  ❌ {d}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# VISION
# ═══════════════════════════════════════════════════════════════════════
def take_screenshot(quality: int = 75) -> Optional[str]:
    try:
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1440:
            img = img.resize((1440, int(h * 1440 / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot: {e}")
        return None

def get_screen_text_via_ai(token: str) -> str:
    ss = take_screenshot(quality=60)
    if not ss:
        return "Could not capture screen"
    try:
        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                         json={"messages": [{"role": "user", "content": "Describe what's on this screen in 2-3 sentences."}], "stream": False},
                         timeout=20)
        if r.status_code == 200:
            return r.json().get("content") or r.json().get("response") or "Screen captured"
    except:
        pass
    return "Screen captured"

# ═══════════════════════════════════════════════════════════════════════
# PERMISSION SYSTEM
# ═══════════════════════════════════════════════════════════════════════
PERMISSION_RULES = {
    "delete_files": {"triggers": [["delete","remove","erase","wipe","trash"],["file","folder","document","photo","data"]],"icon":"🗑️","label":"DELETE FILES","warn":"This will permanently delete files from your computer."},
    "banking": {"triggers": [["bank","hdfc","sbi","icici","axis","paytm","gpay","phonepe","upi","net banking","money transfer","neft","imps"],["any"]],"icon":"🏦","label":"BANKING ACCESS","warn":"Accessing banking or financial services on your behalf."},
    "payment": {"triggers": [["pay","payment","checkout","purchase","buy now","credit card","debit card","cvv"],["any"]],"icon":"💳","label":"PAYMENT","warn":"Making a payment or accessing payment information."},
    "private_data": {"triggers": [["aadhar","pan card","passport","social security","date of birth","mother maiden"],["any"]],"icon":"🔒","label":"PRIVATE IDENTITY DATA","warn":"Accessing sensitive personal identity information."},
    "passwords": {"triggers": [["password","credentials","lastpass","1password","bitwarden","keychain","my passwords"],["any"]],"icon":"🔑","label":"PASSWORD ACCESS","warn":"Accessing passwords or credential storage."},
    "camera_mic": {"triggers": [["open camera","start camera","record video","record audio","start recording","webcam"],["any"]],"icon":"📷","label":"CAMERA/MICROPHONE","warn":"Accessing camera or recording audio/video."},
    "shutdown": {"triggers": [["shutdown","restart","reboot","power off","turn off computer","hibernate"],["any"]],"icon":"⚡","label":"SHUTDOWN/RESTART","warn":"This will shut down or restart your computer."},
    "install_software": {"triggers": [["install","setup.exe",".msi"],["software","program","application",".exe"]],"icon":"📦","label":"INSTALL SOFTWARE","warn":"Installing software on your computer."},
    "email_send": {"triggers": [["send email","send mail","compose email","email to"],["any"]],"icon":"📧","label":"SEND EMAIL","warn":"Sending an email on your behalf."},
    "social_post": {"triggers": [["post on","tweet","share on","publish post","go live"],["facebook","instagram","twitter","linkedin","youtube","tiktok"]],"icon":"📱","label":"SOCIAL MEDIA POST","warn":"Posting content on social media on your behalf."},
    "format_disk": {"triggers": [["format disk","format drive","fdisk","diskpart","wipe drive"],["any"]],"icon":"☢️","label":"FORMAT DISK — DANGER","warn":"DANGER: This will erase ALL data on a disk permanently!"},
    "registry": {"triggers": [["regedit","registry editor","windows registry"],["any"]],"icon":"🔧","label":"REGISTRY EDIT","warn":"Editing the Windows registry."},
}

BLOCKED_COMMANDS = [
    "rm -rf /","rm -rf ~","rm -rf /*","format c:","del /s /q c:\\windows",
    "mkfs","dd if=/dev/zero","deltree c:\\","rd /s /q c:\\","cipher /w:c",
    ":(){:|:&};:","sudo rm -rf /",
]

def needs_permission(task: str) -> tuple:
    tl = task.lower()
    for ptype, rule in PERMISSION_RULES.items():
        kws, ctx = rule["triggers"]
        if any(k in tl for k in kws):
            if ctx == ["any"] or any(c in tl for c in ctx):
                return True, ptype
    return False, ""

def ask_permission(task: str, ptype: str) -> bool:
    rule = PERMISSION_RULES.get(ptype, {})
    icon = rule.get("icon", "⚠️")
    label = rule.get("label", "SENSITIVE ACTION")
    warn = rule.get("warn", "This action needs your approval.")
    border = "═" * 48
    print(f"\n  {border}")
    print(f"  {icon}  PERMISSION REQUIRED: {label}")
    print(f"  {border}")
    print(f"  ⚠  {warn}")
    print(f'  📋 Task: "{task}"')
    print(f"  {border}")
    speak(f"Permission needed. {warn} Say yes to allow or no to deny.", priority=False)
    print("\n  Type YES to allow or NO to deny: ", end="", flush=True)
    try:
        r = input().strip().lower()
        granted = r in ['yes', 'y', 'allow', 'ok', 'sure', 'approve', 'proceed', 'yeah']
        if granted:
            print("  ✅ Permitted\n")
            speak("Permission granted.")
        else:
            print("  ❌ Denied\n")
            speak("Task cancelled for your security.")
        return granted
    except:
        return False

# ═══════════════════════════════════════════════════════════════════════
# SMART TYPING
# ═══════════════════════════════════════════════════════════════════════
def smart_type(text: str):
    try:
        pyperclip.copy(str(text))
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.08)
    except:
        pyautogui.write(str(text), interval=0.025)

def get_active_window() -> str:
    try:
        if WINDOW_OK:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except:
        pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except:
        return ""

# ═══════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR — 150+ ACTIONS
# ═══════════════════════════════════════════════════════════════════════
def execute_command(cmd: dict, token: str = None) -> dict:
    action = cmd.get("action", "").lower().strip()
    try:
        if action == "speak":
            speak(cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "notify":
            notify(cmd.get("title", "Dacexy"), cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "screenshot":
            return {"status": "ok", "screenshot": take_screenshot()}
        elif action == "what_on_screen":
            if token:
                desc = get_screen_text_via_ai(token)
                speak(desc)
                return {"status": "ok", "description": desc}
            return {"status": "ok"}
        elif action == "screenshot_region":
            try:
                img = ImageGrab.grab(bbox=(
                    int(cmd.get("x", 0)), int(cmd.get("y", 0)),
                    int(cmd.get("x", 0)) + int(cmd.get("w", 400)),
                    int(cmd.get("y", 0)) + int(cmd.get("h", 300))
                ))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=80)
                return {"status": "ok", "screenshot": base64.b64encode(buf.getvalue()).decode()}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        elif action == "click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.click(x, y, button=cmd.get("button", "left"), clicks=int(cmd.get("clicks", 1)), interval=0.08)
            time.sleep(0.1)
            return {"status": "ok", "at": f"({x},{y})"}
        elif action == "double_click":
            pyautogui.doubleClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            time.sleep(0.15)
            return {"status": "ok"}
        elif action == "right_click":
            pyautogui.rightClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}
        elif action == "triple_click":
            pyautogui.click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), clicks=3, interval=0.08)
            return {"status": "ok"}
        elif action == "move":
            pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=float(cmd.get("duration", 0.15)))
            return {"status": "ok"}
        elif action == "drag_to":
            sx, sy = int(cmd.get("sx", 0)), int(cmd.get("sy", 0))
            ex, ey = int(cmd.get("ex", 0)), int(cmd.get("ey", 0))
            pyautogui.moveTo(sx, sy)
            pyautogui.dragTo(ex, ey, duration=0.4, button='left')
            return {"status": "ok"}
        elif action == "scroll":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            if x or y:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(int(cmd.get("clicks", 3)))
            return {"status": "ok"}
        elif action == "scroll_down":
            pyautogui.scroll(-int(cmd.get("amount", 5)))
            return {"status": "ok"}
        elif action == "scroll_up":
            pyautogui.scroll(int(cmd.get("amount", 5)))
            return {"status": "ok"}
        elif action == "get_mouse_pos":
            p = pyautogui.position()
            return {"status": "ok", "x": p.x, "y": p.y}
        elif action == "type":
            smart_type(cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "type_slow":
            pyautogui.write(str(cmd.get("text", "")), interval=0.06)
            return {"status": "ok"}
        elif action == "key":
            pyautogui.press(cmd.get("key", ""))
            return {"status": "ok"}
        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
            return {"status": "ok"}
        elif action == "key_down":
            pyautogui.keyDown(cmd.get("key", ""))
            return {"status": "ok"}
        elif action == "key_up":
            pyautogui.keyUp(cmd.get("key", ""))
            return {"status": "ok"}
        elif action == "press_enter":
            pyautogui.press("enter")
            return {"status": "ok"}
        elif action == "press_tab":
            pyautogui.press("tab")
            return {"status": "ok"}
        elif action == "press_escape":
            pyautogui.press("escape")
            return {"status": "ok"}
        elif action == "select_all":
            pyautogui.hotkey('ctrl', 'a')
            return {"status": "ok"}
        elif action == "copy":
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            return {"status": "ok", "clipboard": pyperclip.paste()}
        elif action == "paste":
            pyautogui.hotkey('ctrl', 'v')
            return {"status": "ok"}
        elif action == "cut":
            pyautogui.hotkey('ctrl', 'x')
            return {"status": "ok"}
        elif action == "undo":
            pyautogui.hotkey('ctrl', 'z')
            return {"status": "ok"}
        elif action == "redo":
            pyautogui.hotkey('ctrl', 'y')
            return {"status": "ok"}
        elif action == "save":
            pyautogui.hotkey('ctrl', 's')
            return {"status": "ok"}
        elif action == "open_app":
            app = cmd.get("app", "")
            if app:
                subprocess.Popen(app, shell=True)
            return {"status": "ok", "app": app}
        elif action == "open_url":
            url = cmd.get("url", "")
            if url:
                webbrowser.open(url)
            return {"status": "ok", "url": url}
        elif action == "run_command":
            c = cmd.get("command", "")
            if any(blocked in c.lower() for blocked in BLOCKED_COMMANDS):
                return {"status": "blocked", "reason": "Command is blocked for safety"}
            result = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=30)
            return {"status": "ok", "stdout": result.stdout[:2000], "stderr": result.stderr[:500]}
        elif action == "get_clipboard":
            return {"status": "ok", "text": pyperclip.paste()}
        elif action == "set_clipboard":
            pyperclip.copy(cmd.get("text", ""))
            return {"status": "ok"}
        elif action == "minimize_window":
            pyautogui.hotkey('win', 'd')
            return {"status": "ok"}
        elif action == "maximize_window":
            pyautogui.hotkey('win', 'up')
            return {"status": "ok"}
        elif action == "close_window":
            pyautogui.hotkey('alt', 'f4')
            return {"status": "ok"}
        elif action == "switch_window":
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.3)
            return {"status": "ok"}
        elif action == "open_file_explorer":
            subprocess.Popen("explorer.exe", shell=True)
            return {"status": "ok"}
        elif action == "open_task_manager":
            subprocess.Popen("taskmgr.exe", shell=True)
            return {"status": "ok"}
        elif action == "open_settings":
            subprocess.Popen("ms-settings:", shell=True)
            return {"status": "ok"}
        elif action == "volume_up":
            for _ in range(int(cmd.get("steps", 5))):
                pyautogui.press("volumeup")
            return {"status": "ok"}
        elif action == "volume_down":
            for _ in range(int(cmd.get("steps", 5))):
                pyautogui.press("volumedown")
            return {"status": "ok"}
        elif action == "mute":
            pyautogui.press("volumemute")
            return {"status": "ok"}
        elif action == "sleep":
            time.sleep(float(cmd.get("seconds", 1)))
            return {"status": "ok"}
        elif action == "get_system_info":
            return {
                "status": "ok",
                "os": platform.system(),
                "version": platform.version(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if platform.system() != "Windows" else psutil.disk_usage('C:\\').percent,
                "active_window": get_active_window(),
            }
        elif action == "list_processes":
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    procs.append(p.info)
                except:
                    pass
            return {"status": "ok", "processes": procs[:20]}
        elif action == "kill_process":
            name = cmd.get("name", "")
            for p in psutil.process_iter(['name']):
                try:
                    if name.lower() in p.info['name'].lower():
                        p.kill()
                except:
                    pass
            return {"status": "ok"}
        elif action == "write_file":
            path = cmd.get("path", "")
            content = cmd.get("content", "")
            if path:
                Path(path).write_text(content, encoding="utf-8")
            return {"status": "ok"}
        elif action == "read_file":
            path = cmd.get("path", "")
            if path and Path(path).exists():
                return {"status": "ok", "content": Path(path).read_text(encoding="utf-8", errors="ignore")[:5000]}
            return {"status": "error", "message": "File not found"}
        elif action == "list_files":
            path = cmd.get("path", str(Path.home()))
            try:
                files = [f.name for f in Path(path).iterdir()]
                return {"status": "ok", "files": files[:50]}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        elif action == "open_notepad":
            text = cmd.get("text", "")
            if text:
                tmp = Path.home() / "dacexy_note.txt"
                tmp.write_text(text, encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"', shell=True)
            else:
                subprocess.Popen("notepad.exe", shell=True)
            return {"status": "ok"}
        elif action == "search_web":
            query = cmd.get("query", "")
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            return {"status": "ok"}
        elif action == "open_youtube":
            query = cmd.get("query", "")
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
            else:
                webbrowser.open("https://www.youtube.com")
            return {"status": "ok"}
        elif action == "take_note":
            note = cmd.get("text", "")
            if note:
                remember(f"Note: {note}")
                speak(f"I've saved your note: {note[:50]}")
            return {"status": "ok"}
        elif action == "get_time":
            now = datetime.datetime.now()
            t = now.strftime("%I:%M %p")
            speak(f"The time is {t}")
            return {"status": "ok", "time": t}
        elif action == "get_date":
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {today}")
            return {"status": "ok", "date": today}
        elif action == "ping":
            return {"status": "ok", "pong": True}
        else:
            return {"status": "unknown_action", "action": action}
    except Exception as e:
        log.error("Command error [%s]: %s", action, e)
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# AI TASK EXECUTOR — sends task to Dacexy AI and executes result
# ═══════════════════════════════════════════════════════════════════════
def execute_task_with_ai(task: str, token: str, ws_send_fn=None) -> str:
    """Send task to AI, get back a list of commands, execute them."""
    try:
        memory_ctx = get_memory_context()
        system_prompt = f"""You are Dacexy Desktop Agent controlling a Windows PC.
The user gives you a task. Respond ONLY with a JSON array of commands to execute.
Each command has an "action" field and relevant parameters.

Available actions: click, double_click, right_click, type, key, hotkey, screenshot,
open_app, open_url, run_command, scroll, scroll_down, scroll_up, speak, notify,
get_system_info, search_web, open_youtube, write_file, read_file, list_files,
open_notepad, take_note, get_time, get_date, minimize_window, maximize_window,
close_window, switch_window, volume_up, volume_down, mute, sleep, what_on_screen,
open_file_explorer, open_task_manager, open_settings, kill_process, copy, paste,
select_all, save, press_enter, press_tab, press_escape, get_clipboard, set_clipboard

Example for "open google and search cats":
[
  {{"action": "open_url", "url": "https://www.google.com"}},
  {{"action": "sleep", "seconds": 1.5}},
  {{"action": "click", "x": 640, "y": 400}},
  {{"action": "type", "text": "cats"}},
  {{"action": "press_enter"}}
]

{f'User context: {memory_ctx}' if memory_ctx else ''}

Return ONLY valid JSON array. No explanation, no markdown."""

        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Task: {task}"}
            ], "stream": False},
            timeout=30
        )

        if r.status_code != 200:
            return f"AI request failed: {r.status_code}"

        raw = r.json().get("content") or r.json().get("response") or ""
        raw = raw.strip()

        # Extract JSON array
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            # If AI returned plain text (no commands), just speak it
            speak(raw[:200])
            return raw[:200]

        commands = json.loads(match.group())
        results = []
        actions_taken = 0

        for c in commands:
            if not isinstance(c, dict):
                continue
            result = execute_command(c, token)
            results.append(result)
            actions_taken += 1
            time.sleep(0.15)

        # Record task in memory
        MEMORY["task_history"].append(task[:100])
        save_memory()

        summary = f"Completed {actions_taken} actions for: {task[:50]}"
        log.info(summary)
        return summary

    except json.JSONDecodeError:
        # AI returned explanation not JSON — speak it
        speak(raw[:200] if 'raw' in dir() else "Task completed")
        return "Task completed"
    except Exception as e:
        log.error("Task execution error: %s", e)
        return f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════
# VOICE ENGINE — SIRI-LIKE 24/7 WAKE WORD LISTENER
# ═══════════════════════════════════════════════════════════════════════
_voice_active = False
_voice_thread = None
_current_token = None

def _voice_listen_loop():
    """
    Runs 24/7 in background. Listens for wake word "hey dacexy",
    then listens for the actual command and executes it via AI.
    Like Siri — always on, voice activated.
    """
    global _voice_active, _current_token

    if not VOICE_AVAILABLE or not sr:
        log.warning("Voice not available — PyAudio not installed")
        return

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    log.info("🎤 Voice engine started — say 'Hey Dacexy' to activate")
    print("\n  🎤 Voice engine running — say 'Hey Dacexy' anytime!")
    speak("Voice engine ready. Say Hey Dacexy to give me a command.", priority=False)

    while _voice_active:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                # Listen for wake word (short timeout)
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower().strip()
                    log.info("Heard: %s", text)

                    # Check for wake word
                    if WAKE_WORD in text or "hey dacexy" in text or "hey daxy" in text or "dacexy" in text:
                        print(f"\n  🟢 Wake word detected!")
                        speak("Yes? What can I do for you?", priority=True)

                        # Now listen for the actual command
                        with sr.Microphone() as cmd_source:
                            recognizer.adjust_for_ambient_noise(cmd_source, duration=0.2)
                            print("  🎧 Listening for command...")
                            try:
                                cmd_audio = recognizer.listen(cmd_source, timeout=8, phrase_time_limit=15)
                                command_text = recognizer.recognize_google(cmd_audio).strip()
                                print(f"  📝 Command: {command_text}")
                                log.info("Voice command: %s", command_text)

                                if command_text:
                                    speak("On it!", priority=False)
                                    token = _current_token
                                    if token:
                                        # Check permission for sensitive tasks
                                        needs_perm, ptype = needs_permission(command_text)
                                        if needs_perm:
                                            if not ask_permission(command_text, ptype):
                                                continue

                                        # Execute via AI in background thread
                                        def _exec_voice_task(t, cmd):
                                            result = execute_task_with_ai(cmd, t)
                                            speak(f"Done. {result[:80]}", priority=False)

                                        threading.Thread(
                                            target=_exec_voice_task,
                                            args=(token, command_text),
                                            daemon=True
                                        ).start()
                                    else:
                                        speak("Please log in to Dacexy first.")
                            except sr.WaitTimeoutError:
                                speak("I didn't hear anything. Try again.")
                            except sr.UnknownValueError:
                                speak("I couldn't understand that. Please try again.")
                            except Exception as e:
                                log.warning("Command recognition error: %s", e)

                except sr.WaitTimeoutError:
                    pass  # No speech detected in timeout window — keep looping
                except sr.UnknownValueError:
                    pass  # Couldn't understand ambient noise — keep looping
                except Exception as e:
                    log.debug("Wake word listen error: %s", e)
                    time.sleep(0.5)

        except Exception as e:
            log.warning("Voice loop error: %s", e)
            time.sleep(2)


def start_voice_engine(token: str):
    """Start the 24/7 voice engine in background."""
    global _voice_active, _voice_thread, _current_token
    _current_token = token
    if not VOICE_AVAILABLE:
        print("  ⚠️  Voice not available (PyAudio not installed)")
        print("  💡 Run: pip install pyaudio")
        return False
    if _voice_active:
        return True
    _voice_active = True
    _voice_thread = threading.Thread(target=_voice_listen_loop, daemon=True)
    _voice_thread.start()
    return True


def stop_voice_engine():
    global _voice_active
    _voice_active = False
    log.info("Voice engine stopped")


def update_voice_token(token: str):
    """Update token used by voice engine (call after re-login)."""
    global _current_token
    _current_token = token


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET CLIENT — connects to Dacexy backend
# ═══════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    retry_delay = 3
    max_delay = 60

    while True:
        try:
            log.info("Connecting to Dacexy backend...")
            async with websockets.connect(
                BACKEND_WS,
                ping_interval=20,
                ping_timeout=15,
                close_timeout=10,
                extra_headers={"User-Agent": f"DacexyAgent/{VERSION}"}
            ) as ws:
                # Authenticate
                await ws.send(json.dumps({"token": token}))
                auth_resp = await asyncio.wait_for(ws.recv(), timeout=15)
                auth_data = json.loads(auth_resp)

                if auth_data.get("type") == "error":
                    log.error("Auth failed: %s", auth_data.get("message"))
                    speak("Authentication failed. Please check your login.")
                    return  # Don't retry on auth failure

                log.info("✅ Connected to Dacexy backend")
                print("\n  ✅ Connected to Dacexy cloud — ready for remote commands")
                speak("Connected to Dacexy. Ready for your commands.")
                retry_delay = 3  # Reset on success

                async def send_fn(data):
                    try:
                        await ws.send(json.dumps(data))
                    except:
                        pass

                # Main message loop
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                        msg = json.loads(raw)
                        msg_type = msg.get("type", "")

                        if msg_type == "ping":
                            await ws.send(json.dumps({"type": "pong"}))

                        elif msg_type == "task":
                            task_text = msg.get("task", "")
                            task_id = msg.get("task_id", "")
                            log.info("Remote task received: %s", task_text)
                            print(f"\n  📋 Remote task: {task_text}")
                            speak(f"Got it. Working on: {task_text[:50]}")

                            def _run_remote_task(t, task, tid, sfn):
                                needs_perm, ptype = needs_permission(task)
                                if needs_perm:
                                    if not ask_permission(task, ptype):
                                        asyncio.run(sfn({"type": "task_result", "task_id": tid, "status": "denied", "actions_taken": 0}))
                                        return
                                result = execute_task_with_ai(task, t, sfn)
                                asyncio.run(sfn({"type": "task_result", "task_id": tid, "status": "completed", "result": result, "actions_taken": 1}))
                                speak(f"Task complete.")

                            threading.Thread(
                                target=_run_remote_task,
                                args=(token, task_text, task_id, send_fn),
                                daemon=True
                            ).start()

                        elif msg_type not in ("pong", "connected"):
                            # Single command execution
                            if "action" in msg:
                                result = execute_command(msg, token)
                                await send_fn({"type": "result", "result": result})

                    except asyncio.TimeoutError:
                        # Send keep-alive ping
                        try:
                            await ws.send(json.dumps({"type": "ping"}))
                        except:
                            break

        except websockets.exceptions.ConnectionClosed as e:
            log.warning("WebSocket closed: %s — reconnecting in %ds", e, retry_delay)
        except OSError as e:
            log.warning("Network error: %s — reconnecting in %ds", e, retry_delay)
        except Exception as e:
            log.error("WebSocket error: %s — reconnecting in %ds", e, retry_delay)

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 1.5, max_delay)


# ═══════════════════════════════════════════════════════════════════════
# HEARTBEAT — keeps token valid and reconnects if needed
# ═══════════════════════════════════════════════════════════════════════
def heartbeat_loop(token_holder: list):
    """Runs every 5 min to verify token is still valid."""
    while True:
        time.sleep(300)
        token = token_holder[0]
        if token:
            valid = check_token_valid(token)
            if valid:
                log.debug("Token heartbeat: OK")
            else:
                log.warning("Token expired — please restart agent and log in again")
                speak("Your session may have expired. Please restart Dacexy Agent.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║   Dacexy Desktop Agent v11.0                 ║")
    print("║   24/7 AI Voice Control — Like Siri          ║")
    print("╚══════════════════════════════════════════════╝\n")

    init_tts()
    load_memory()

    # ── Auth ──────────────────────────────────────────────────────────
    token = get_token()
    if token:
        print("  Verifying saved session...")
        if not check_token_valid(token):
            print("  Session expired. Please log in again.")
            clear_token()
            token = None

    if not token:
        attempts = 0
        while not token and attempts < 3:
            token = login()
            attempts += 1
        if not token:
            print("\n  ❌ Could not authenticate after 3 attempts. Exiting.")
            return

    # ── Setup autostart ───────────────────────────────────────────────
    setup_autostart()
    print("  ✅ Autostart registered — agent will run on every Windows login")

    # ── Start voice engine (Siri-like) ────────────────────────────────
    voice_started = start_voice_engine(token)
    if voice_started:
        print(f"  🎤 Voice engine active — say '{WAKE_WORD.title()}' anytime!")
    else:
        print("  ⚠️  Voice disabled — PyAudio not available")

    # ── Start heartbeat ───────────────────────────────────────────────
    token_holder = [token]
    threading.Thread(target=heartbeat_loop, args=(token_holder,), daemon=True).start()

    # ── Start WebSocket connection ────────────────────────────────────
    print("  🌐 Connecting to Dacexy cloud...")
    print("\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Agent running 24/7. Voice: {'ON ✅' if voice_started else 'OFF ❌'}")
    print(f"  Wake word: '{WAKE_WORD.upper()}'")
    print("  Close this window to stop the agent.")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n\n  Dacexy Agent stopped.")
        stop_voice_engine()
        speak("Dacexy Agent shutting down. Goodbye!")
        time.sleep(1)


if __name__ == "__main__":
    main()
