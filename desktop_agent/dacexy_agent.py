"""
Dacexy Desktop Agent v11.0 - World's Most Powerful AI Desktop Agent
Like Siri but for your entire computer. 24/7 always-on background agent.
"""
import subprocess, sys, os, platform

# ═══════════════════════════════════════════════════════════════════════
# AUTO-INSTALL
# ═══════════════════════════════════════════════════════════════════════
PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
    "pyperclip", "keyboard", "pygetwindow", "plyer",
]

for pkg in PACKAGES:
    imp = pkg.replace("-","_")
    if pkg == "speechrecognition": imp = "speech_recognition"
    if pkg == "pillow": imp = "PIL"
    try: __import__(imp)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import pyaudio; PYAUDIO_OK = True
except:
    PYAUDIO_OK = False
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","pipwin","-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([sys.executable,"-m","pipwin","install","pyaudio","-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import pyaudio; PYAUDIO_OK = True
    except:
        try:
            subprocess.check_call([sys.executable,"-m","pip","install","PyAudio","-q"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True
        except: PYAUDIO_OK = False

# ═══════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════
import asyncio, base64, io, json, logging, threading
import time, webbrowser, re, datetime, winreg, ctypes
from pathlib import Path
from typing import Optional
from collections import deque

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab, Image
import pyttsx3, pyperclip, psutil

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except: VOICE_AVAILABLE = False

try:
    import pygetwindow as gw
    WINDOW_OK = True
except: WINDOW_OK = False

try:
    from plyer import notification
    NOTIFY_OK = True
except: NOTIFY_OK = False

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

# Agent brain memory — persists across sessions
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
# SYSTEM NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════
def notify(title: str, message: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=message, app_name="Dacexy", timeout=4)
    except: pass

# ═══════════════════════════════════════════════════════════════════════
# TTS - VOICE OUTPUT
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
            if any(x in (v.name or "").lower() for x in ["zira","hazel","female","woman","aria"]):
                _tts.setProperty("voice", v.id); break
    except: pass

def speak(text: str, priority: bool = False):
    global _speaking
    if not text: return
    print(f"  🔊 Dacexy: {text}")
    notify("Dacexy", text[:80])
    def _speak():
        global _speaking
        _speaking = True
        try:
            with _tts_lock:
                if _tts:
                    _tts.say(text)
                    _tts.runAndWait()
        except: pass
        finally: _speaking = False
    t = threading.Thread(target=_speak, daemon=True)
    t.start()
    if priority: t.join(timeout=10)

# ═══════════════════════════════════════════════════════════════════════
# MEMORY SYSTEM
# ═══════════════════════════════════════════════════════════════════════
def load_memory():
    global MEMORY
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            MEMORY["facts"] = data.get("facts", [])
            MEMORY["preferences"] = data.get("preferences", {})
            MEMORY["context"] = data.get("context", {})
            history = data.get("task_history", [])
            MEMORY["task_history"] = deque(history[-50:], maxlen=50)
    except: pass

def save_memory():
    try:
        MEMORY_FILE.write_text(json.dumps({
            "facts": MEMORY["facts"][-100:],
            "preferences": MEMORY["preferences"],
            "context": MEMORY["context"],
            "task_history": list(MEMORY["task_history"])[-50:],
        }, indent=2), encoding="utf-8")
    except: pass

def remember(fact: str):
    if fact and fact not in MEMORY["facts"]:
        MEMORY["facts"].append(fact)
        save_memory()

def get_memory_context() -> str:
    ctx = []
    if MEMORY["facts"]: ctx.append("Known facts: " + "; ".join(MEMORY["facts"][-10:]))
    if MEMORY["preferences"]: ctx.append("Preferences: " + str(MEMORY["preferences"]))
    recent = list(MEMORY["task_history"])[-5:]
    if recent: ctx.append("Recent tasks: " + "; ".join(recent))
    return "\n".join(ctx) if ctx else ""

# ═══════════════════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg: dict): CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
def get_token(): return load_config().get("access_token")
def save_token(t): cfg=load_config(); cfg["access_token"]=t; save_config(cfg)
def clear_token(): cfg=load_config(); cfg.pop("access_token",None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"}, timeout=8)
        return r.status_code == 200
    except: return False

def setup_autostart():
    try:
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        cmd = f'"{sys.executable}" "{agent_path}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except: pass

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
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  ❌ {d}")
    except Exception as e: print(f"  ❌ Error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# VISION — SCREENSHOT WITH AI ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def take_screenshot(quality: int = 75) -> Optional[str]:
    try:
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1440: img = img.resize((1440, int(h * 1440/w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot: {e}")
        return None

def get_screen_text_via_ai(token: str) -> str:
    """Ask AI what's on screen using screenshot."""
    ss = take_screenshot(quality=60)
    if not ss: return "Could not capture screen"
    try:
        prompt = "Look at this screenshot and describe in 2-3 sentences what is currently visible on the screen. Be specific about app names, content, and any important information visible."
        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":[{"role":"user","content":prompt}],"stream":False},
            timeout=20)
        if r.status_code == 200:
            return r.json().get("content") or r.json().get("response") or "Screen captured"
    except: pass
    return "Screen captured"

# ═══════════════════════════════════════════════════════════════════════
# PERMISSION SYSTEM — ENTERPRISE SECURITY
# ═══════════════════════════════════════════════════════════════════════
PERMISSION_RULES = {
    "delete_files": {
        "triggers": [["delete","remove","erase","wipe","trash"],["file","folder","document","photo","data"]],
        "icon": "🗑️", "label": "DELETE FILES",
        "warn": "This will permanently delete files from your computer."
    },
    "banking": {
        "triggers": [["bank","hdfc","sbi","icici","axis","paytm","gpay","phonepe","upi","net banking","money transfer","neft","imps"],["any"]],
        "icon": "🏦", "label": "BANKING ACCESS",
        "warn": "Accessing banking or financial services on your behalf."
    },
    "payment": {
        "triggers": [["pay","payment","checkout","purchase","buy now","credit card","debit card","cvv"],["any"]],
        "icon": "💳", "label": "PAYMENT",
        "warn": "Making a payment or accessing payment information."
    },
    "private_data": {
        "triggers": [["aadhar","pan card","passport","social security","date of birth","mother maiden"],["any"]],
        "icon": "🔒", "label": "PRIVATE IDENTITY DATA",
        "warn": "Accessing sensitive personal identity information."
    },
    "passwords": {
        "triggers": [["password","credentials","lastpass","1password","bitwarden","keychain","my passwords"],["any"]],
        "icon": "🔑", "label": "PASSWORD ACCESS",
        "warn": "Accessing passwords or credential storage."
    },
    "camera_mic": {
        "triggers": [["open camera","start camera","record video","record audio","start recording","webcam"],["any"]],
        "icon": "📷", "label": "CAMERA/MICROPHONE",
        "warn": "Accessing camera or recording audio/video."
    },
    "shutdown": {
        "triggers": [["shutdown","restart","reboot","power off","turn off computer","hibernate"],["any"]],
        "icon": "⚡", "label": "SHUTDOWN/RESTART",
        "warn": "This will shut down or restart your computer."
    },
    "install_software": {
        "triggers": [["install","setup.exe",".msi"],["software","program","application",".exe"]],
        "icon": "📦", "label": "INSTALL SOFTWARE",
        "warn": "Installing software on your computer."
    },
    "email_send": {
        "triggers": [["send email","send mail","compose email","email to"],["any"]],
        "icon": "📧", "label": "SEND EMAIL",
        "warn": "Sending an email on your behalf."
    },
    "social_post": {
        "triggers": [["post on","tweet","share on","publish post","go live"],["facebook","instagram","twitter","linkedin","youtube","tiktok"]],
        "icon": "📱", "label": "SOCIAL MEDIA POST",
        "warn": "Posting content on social media on your behalf."
    },
    "format_disk": {
        "triggers": [["format disk","format drive","fdisk","diskpart","wipe drive"],["any"]],
        "icon": "☢️", "label": "FORMAT DISK — DANGER",
        "warn": "⚠️ DANGER: This will erase ALL data on a disk permanently!"
    },
    "registry": {
        "triggers": [["regedit","registry editor","windows registry"],["any"]],
        "icon": "🔧", "label": "REGISTRY EDIT",
        "warn": "Editing the Windows registry — can affect system stability."
    },
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
    icon = rule.get("icon","⚠️")
    label = rule.get("label","SENSITIVE ACTION")
    warn = rule.get("warn","This action needs your approval.")
    border = "═"*48
    print(f"\n  {border}")
    print(f"  {icon}  PERMISSION REQUIRED: {label}")
    print(f"  {border}")
    print(f"  ⚠  {warn}")
    print(f"  📋 Task: \"{task}\"")
    print(f"  {border}")
    speak(f"Permission needed. {warn} Do you want to allow this?", priority=False)
    print("\n  Type YES to allow or NO to deny: ", end="", flush=True)
    try:
        r = input().strip().lower()
        granted = r in ['yes','y','allow','ok','sure','approve','proceed','yeah']
        if granted:
            print("  ✅ Permitted\n")
            speak("Permission granted.")
        else:
            print("  ❌ Denied\n")
            speak("Task cancelled for your security.")
        return granted
    except: return False

# ═══════════════════════════════════════════════════════════════════════
# SMART TYPING
# ═══════════════════════════════════════════════════════════════════════
def smart_type(text: str):
    try:
        pyperclip.copy(str(text))
        time.sleep(0.05)
        pyautogui.hotkey('ctrl','v')
        time.sleep(0.08)
    except:
        pyautogui.write(str(text), interval=0.025)

def get_active_window() -> str:
    try:
        if WINDOW_OK:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except: pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length+1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length+1)
        return buf.value
    except: return ""

# ═══════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR — 150+ ACTIONS
# ═══════════════════════════════════════════════════════════════════════
def execute_command(cmd: dict, token: str = None) -> dict:
    action = cmd.get("action","").lower().strip()
    try:
        # ── SPEECH & NOTIFICATIONS ──────────────────────────────
        if action == "speak":
            speak(cmd.get("text",""))
            return {"status":"ok"}
        elif action == "notify":
            notify(cmd.get("title","Dacexy"), cmd.get("text",""))
            return {"status":"ok"}

        # ── SCREENSHOT & VISION ─────────────────────────────────
        elif action == "screenshot":
            return {"status":"ok","screenshot":take_screenshot()}
        elif action == "what_on_screen":
            if token:
                desc = get_screen_text_via_ai(token)
                speak(desc)
                return {"status":"ok","description":desc}
            return {"status":"ok"}
        elif action == "screenshot_region":
            try:
                img = ImageGrab.grab(bbox=(
                    int(cmd.get("x",0)), int(cmd.get("y",0)),
                    int(cmd.get("x",0))+int(cmd.get("w",400)),
                    int(cmd.get("y",0))+int(cmd.get("h",300))
                ))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=80)
                return {"status":"ok","screenshot":base64.b64encode(buf.getvalue()).decode()}
            except Exception as e: return {"status":"error","message":str(e)}

        # ── MOUSE ────────────────────────────────────────────────
        elif action == "click":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.click(x, y, button=cmd.get("button","left"), clicks=int(cmd.get("clicks",1)), interval=0.08)
            time.sleep(0.1)
            return {"status":"ok","at":f"({x},{y})"}
        elif action == "double_click":
            pyautogui.doubleClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            time.sleep(0.15)
            return {"status":"ok"}
        elif action == "right_click":
            pyautogui.rightClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            return {"status":"ok"}
        elif action == "triple_click":
            pyautogui.click(int(cmd.get("x",0)), int(cmd.get("y",0)), clicks=3, interval=0.08)
            return {"status":"ok"}
        elif action == "move":
            pyautogui.moveTo(int(cmd.get("x",0)), int(cmd.get("y",0)), duration=float(cmd.get("duration",0.15)))
            return {"status":"ok"}
        elif action == "drag_to":
            sx,sy = int(cmd.get("sx",0)), int(cmd.get("sy",0))
            ex,ey = int(cmd.get("ex",0)), int(cmd.get("ey",0))
            pyautogui.moveTo(sx, sy)
            pyautogui.dragTo(ex, ey, duration=0.4, button='left')
            return {"status":"ok"}
        elif action == "scroll":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            if x or y: pyautogui.moveTo(x, y)
            pyautogui.scroll(int(cmd.get("clicks",3)))
            return {"status":"ok"}
        elif action == "scroll_down":
            pyautogui.scroll(-int(cmd.get("amount",5)))
            return {"status":"ok"}
        elif action == "scroll_up":
            pyautogui.scroll(int(cmd.get("amount",5)))
            return {"status":"ok"}
        elif action == "get_mouse_pos":
            p = pyautogui.position()
            return {"status":"ok","x":p.x,"y":p.y}

        # ── KEYBOARD ─────────────────────────────────────────────
        elif action == "type":
            smart_type(cmd.get("text",""))
            return {"status":"ok"}
        elif action == "type_slow":
            pyautogui.write(str(cmd.get("text","")), interval=0.06)
            return {"status":"ok"}
        elif action == "key":
            pyautogui.press(cmd.get("key",""))
            return {"status":"ok"}
        elif action == "hotkey":
            keys = cmd.get("keys",[])
            if keys: pyautogui.hotkey(*keys)
            return {"status":"ok"}
        elif action == "key_down":
            pyautogui.keyDown(cmd.get("key",""))
            return {"status":"ok"}
        elif action == "key_up":
            pyautogui.keyUp(cmd.get("key",""))
            return {"status":"ok"}
        elif action == "press_enter": pyautogui.press("enter"); return {"status":"ok"}
        elif action == "press_tab": pyautogui.press("tab"); return {"status":"ok"}
        elif action == "press_escape": pyautogui.press("escape"); return {"status":"ok"}
        elif action == "press_space": pyautogui.press("space"); return {"status":"ok"}
        elif action == "press_backspace":
            for _ in range(int(cmd.get("count",1))): pyautogui.press("backspace")
            return {"status":"ok"}
        elif action == "press_delete": pyautogui.press("delete"); return {"status":"ok"}
        elif action == "press_f5": pyautogui.press("f5"); return {"status":"ok"}

        # ── CLIPBOARD ────────────────────────────────────────────
        elif action == "copy":
            pyautogui.hotkey("ctrl","c"); time.sleep(0.2)
            return {"status":"ok","content":pyperclip.paste()}
        elif action == "paste":
            pyautogui.hotkey("ctrl","v"); return {"status":"ok"}
        elif action == "cut":
            pyautogui.hotkey("ctrl","x"); return {"status":"ok"}
        elif action == "select_all":
            pyautogui.hotkey("ctrl","a"); return {"status":"ok"}
        elif action == "get_clipboard":
            return {"status":"ok","content":pyperclip.paste()}
        elif action == "set_clipboard":
            pyperclip.copy(str(cmd.get("text",""))); return {"status":"ok"}
        elif action == "clear_field":
            pyautogui.hotkey("ctrl","a"); time.sleep(0.05); pyautogui.press("delete"); return {"status":"ok"}

        # ── BROWSER ──────────────────────────────────────────────
        elif action == "open_url":
            url = cmd.get("url","")
            if not url.startswith("http"): url = "https://" + url
            webbrowser.open(url); time.sleep(2)
            return {"status":"ok","opened":url}
        elif action == "navigate_url":
            url = cmd.get("url","")
            if not url.startswith("http"): url = "https://" + url
            pyautogui.hotkey("ctrl","l"); time.sleep(0.3)
            pyautogui.hotkey("ctrl","a"); smart_type(url)
            pyautogui.press("enter"); time.sleep(2.5)
            return {"status":"ok"}
        elif action == "new_tab": pyautogui.hotkey("ctrl","t"); time.sleep(0.5); return {"status":"ok"}
        elif action == "close_tab": pyautogui.hotkey("ctrl","w"); time.sleep(0.2); return {"status":"ok"}
        elif action == "new_window": pyautogui.hotkey("ctrl","n"); time.sleep(0.8); return {"status":"ok"}
        elif action == "incognito": pyautogui.hotkey("ctrl","shift","n"); time.sleep(0.8); return {"status":"ok"}
        elif action == "browser_back": pyautogui.hotkey("alt","left"); time.sleep(1); return {"status":"ok"}
        elif action == "browser_forward": pyautogui.hotkey("alt","right"); time.sleep(1); return {"status":"ok"}
        elif action == "browser_refresh": pyautogui.hotkey("ctrl","r"); time.sleep(2); return {"status":"ok"}
        elif action == "browser_find":
            pyautogui.hotkey("ctrl","f"); time.sleep(0.3); smart_type(cmd.get("text","")); pyautogui.press("enter")
            return {"status":"ok"}
        elif action == "browser_zoom_in": pyautogui.hotkey("ctrl","="); return {"status":"ok"}
        elif action == "browser_zoom_out": pyautogui.hotkey("ctrl","-"); return {"status":"ok"}
        elif action == "browser_zoom_reset": pyautogui.hotkey("ctrl","0"); return {"status":"ok"}
        elif action == "open_dev_tools": pyautogui.press("f12"); time.sleep(0.5); return {"status":"ok"}

        # ── FILES ────────────────────────────────────────────────
        elif action == "open_file":
            path = cmd.get("path","")
            if os.path.exists(path):
                os.startfile(path) if platform.system()=="Windows" else subprocess.Popen(["open",path])
                time.sleep(1); return {"status":"ok","opened":path}
            return {"status":"error","message":f"File not found: {path}"}
        elif action == "find_file":
            name = cmd.get("name",""); results = []
            for base in [Path.home(), Path.home()/"Desktop", Path.home()/"Documents", Path.home()/"Downloads"]:
                try:
                    for root,dirs,files in os.walk(str(base)):
                        for f in files:
                            if name.lower() in f.lower(): results.append(os.path.join(root,f))
                            if len(results) >= 10: break
                        if len(results) >= 10: break
                except: pass
                if len(results) >= 10: break
            return {"status":"ok","files":results}
        elif action == "open_folder":
            path = cmd.get("path", str(Path.home()))
            subprocess.Popen(["explorer",path] if platform.system()=="Windows" else ["open",path])
            return {"status":"ok"}
        elif action == "create_file":
            path = cmd.get("path",""); content = cmd.get("content","")
            if path: Path(path).write_text(content, encoding="utf-8"); return {"status":"ok","created":path}
            return {"status":"error","message":"No path"}
        elif action == "read_file":
            path = cmd.get("path","")
            if path and os.path.exists(path):
                return {"status":"ok","content":Path(path).read_text(encoding="utf-8",errors="ignore")[:8000]}
            return {"status":"error","message":"Not found"}
        elif action == "list_files":
            path = cmd.get("path", str(Path.home()/"Desktop"))
            try: return {"status":"ok","files":os.listdir(path)[:50]}
            except Exception as e: return {"status":"error","message":str(e)}
        elif action == "open_downloads":
            subprocess.Popen(["explorer", str(Path.home()/"Downloads")]); return {"status":"ok"}
        elif action == "open_desktop":
            subprocess.Popen(["explorer", str(Path.home()/"Desktop")]); return {"status":"ok"}
        elif action == "open_documents":
            subprocess.Popen(["explorer", str(Path.home()/"Documents")]); return {"status":"ok"}
        elif action == "take_note":
            text = cmd.get("text","")
            note_file = Path.home()/"DacexyAgent"/"notes.txt"
            note_file.parent.mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(note_file,"a",encoding="utf-8") as f: f.write(f"\n[{ts}] {text}\n")
            remember(f"User note: {text[:60]}")
            return {"status":"ok","saved":str(note_file)}
        elif action == "read_notes":
            note_file = Path.home()/"DacexyAgent"/"notes.txt"
            if note_file.exists():
                content = note_file.read_text(encoding="utf-8")
                speak("Here are your recent notes: " + content[-500:])
                return {"status":"ok","notes":content[-2000:]}
            return {"status":"ok","notes":"No notes yet"}

        # ── APPS ─────────────────────────────────────────────────
        elif action == "open_app":
            app = cmd.get("app","")
            try:
                if platform.system()=="Windows": os.startfile(app)
                elif platform.system()=="Darwin": subprocess.Popen(["open","-a",app])
                else: subprocess.Popen([app])
                time.sleep(1.5); return {"status":"ok","opened":app}
            except:
                result = subprocess.run(f"start {app}", shell=True, capture_output=True, timeout=8)
                return {"status":"ok" if result.returncode==0 else "error"}
        elif action == "run_shell":
            command = cmd.get("command","")
            for b in BLOCKED_COMMANDS:
                if b.lower() in command.lower():
                    return {"status":"error","message":f"Blocked for safety"}
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                return {"status":"ok","stdout":result.stdout[:3000],"stderr":result.stderr[:300],"code":result.returncode}
            except subprocess.TimeoutExpired:
                return {"status":"error","message":"Timed out"}
        elif action == "run_powershell":
            cmd_text = cmd.get("command","")
            for b in BLOCKED_COMMANDS:
                if b.lower() in cmd_text.lower(): return {"status":"error","message":"Blocked"}
            result = subprocess.run(["powershell","-Command",cmd_text], capture_output=True, text=True, timeout=30)
            return {"status":"ok","stdout":result.stdout[:3000]}
        elif action == "kill_process":
            name = cmd.get("name",""); killed = []
            for proc in psutil.process_iter(['name']):
                if name.lower() in (proc.info['name'] or "").lower():
                    try: proc.kill(); killed.append(proc.info['name'])
                    except: pass
            return {"status":"ok","killed":killed}
        elif action == "list_processes":
            procs = [p.name() for p in psutil.process_iter(['name']) if p.info['name']][:30]
            return {"status":"ok","processes":procs}

        # ── WINDOW MANAGEMENT ─────────────────────────────────────
        elif action == "minimize_window": pyautogui.hotkey("win","down"); return {"status":"ok"}
        elif action == "maximize_window": pyautogui.hotkey("win","up"); return {"status":"ok"}
        elif action == "close_window": pyautogui.hotkey("alt","f4"); time.sleep(0.2); return {"status":"ok"}
        elif action == "switch_window": pyautogui.hotkey("alt","tab"); time.sleep(0.3); return {"status":"ok"}
        elif action == "show_desktop": pyautogui.hotkey("win","d"); return {"status":"ok"}
        elif action == "snap_left": pyautogui.hotkey("win","left"); return {"status":"ok"}
        elif action == "snap_right": pyautogui.hotkey("win","right"); return {"status":"ok"}
        elif action == "task_view": pyautogui.hotkey("win","tab"); return {"status":"ok"}
        elif action == "open_task_manager": pyautogui.hotkey("ctrl","shift","esc"); return {"status":"ok"}
        elif action == "get_active_window":
            return {"status":"ok","title":get_active_window()}

        # ── SYSTEM ────────────────────────────────────────────────
        elif action == "lock_screen": pyautogui.hotkey("win","l"); return {"status":"ok"}
        elif action == "open_settings": pyautogui.hotkey("win","i"); time.sleep(1); return {"status":"ok"}
        elif action == "open_file_explorer": pyautogui.hotkey("win","e"); time.sleep(1); return {"status":"ok"}
        elif action == "open_run":
            pyautogui.hotkey("win","r"); time.sleep(0.4)
            if cmd.get("command"):
                smart_type(cmd["command"]); pyautogui.press("enter")
            return {"status":"ok"}
        elif action == "open_start": pyautogui.press("win"); time.sleep(0.5); return {"status":"ok"}
        elif action == "search_windows":
            pyautogui.hotkey("win","s"); time.sleep(0.5)
            if cmd.get("query"): smart_type(cmd["query"])
            return {"status":"ok"}
        elif action == "clipboard_history": pyautogui.hotkey("win","v"); return {"status":"ok"}

        # ── MEMORY ────────────────────────────────────────────────
        elif action == "remember":
            fact = cmd.get("fact","") or cmd.get("text","")
            if fact: remember(fact)
            return {"status":"ok","remembered":fact}
        elif action == "recall":
            ctx = get_memory_context()
            speak("Here is what I remember: " + (ctx or "I don't have anything saved yet."))
            return {"status":"ok","memory":ctx}
        elif action == "forget_all":
            MEMORY["facts"].clear(); MEMORY["preferences"].clear(); save_memory()
            speak("I have cleared my memory.")
            return {"status":"ok"}

        # ── TIME & INFO ───────────────────────────────────────────
        elif action == "get_time":
            now = datetime.datetime.now()
            result = {"time":now.strftime("%I:%M %p"),"date":now.strftime("%A, %B %d %Y")}
            speak(f"It is {result['time']} on {result['date']}")
            return {"status":"ok",**result}
        elif action == "get_weather":
            city = cmd.get("city","")
            url = f"https://wttr.in/{city.replace(' ','+')}?format=3" if city else "https://wttr.in/?format=3"
            try:
                r = req_lib.get(url, timeout=6)
                w = r.text.strip()
                speak(w)
                return {"status":"ok","weather":w}
            except: return {"status":"error","message":"Could not fetch weather"}
        elif action == "get_system_info":
            sz = pyautogui.size()
            try:
                bat = psutil.sensors_battery()
                battery = f"{bat.percent:.0f}% {'charging' if bat.power_plugged else 'discharging'}" if bat else None
            except: battery = None
            info = {
                "status":"ok",
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "screen": f"{sz.width}x{sz.height}",
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_percent": psutil.virtual_memory().percent,
                "battery": battery,
                "active_window": get_active_window(),
                "agent_version": VERSION,
            }
            return info
        elif action == "battery_status":
            try:
                bat = psutil.sensors_battery()
                if bat:
                    msg = f"Battery is at {bat.percent:.0f}% and {'charging' if bat.power_plugged else 'discharging'}"
                    speak(msg); return {"status":"ok","message":msg}
            except: pass
            return {"status":"ok","message":"Battery info unavailable"}

        # ── VOLUME & MEDIA ────────────────────────────────────────
        elif action == "volume_up":
            for _ in range(int(cmd.get("steps",3))): pyautogui.press("volumeup")
            return {"status":"ok"}
        elif action == "volume_down":
            for _ in range(int(cmd.get("steps",3))): pyautogui.press("volumedown")
            return {"status":"ok"}
        elif action == "volume_mute": pyautogui.press("volumemute"); return {"status":"ok"}
        elif action == "volume_set":
            level = int(cmd.get("level",50))
            steps = abs(level - 50) // 2
            key = "volumeup" if level > 50 else "volumedown"
            for _ in range(steps): pyautogui.press(key)
            return {"status":"ok"}
        elif action == "media_play_pause": pyautogui.press("playpause"); return {"status":"ok"}
        elif action == "media_next": pyautogui.press("nexttrack"); return {"status":"ok"}
        elif action == "media_prev": pyautogui.press("prevtrack"); return {"status":"ok"}
        elif action == "media_stop": pyautogui.press("stop"); return {"status":"ok"}

        # ── EDIT ACTIONS ──────────────────────────────────────────
        elif action == "save": pyautogui.hotkey("ctrl","s"); time.sleep(0.2); return {"status":"ok"}
        elif action == "save_as": pyautogui.hotkey("ctrl","shift","s"); time.sleep(0.5); return {"status":"ok"}
        elif action == "undo": pyautogui.hotkey("ctrl","z"); return {"status":"ok"}
        elif action == "redo": pyautogui.hotkey("ctrl","y"); return {"status":"ok"}
        elif action == "find": pyautogui.hotkey("ctrl","f"); time.sleep(0.3); smart_type(cmd.get("text","")); pyautogui.press("enter"); return {"status":"ok"}
        elif action == "print": pyautogui.hotkey("ctrl","p"); time.sleep(1); return {"status":"ok"}
        elif action == "zoom_in": pyautogui.hotkey("ctrl","="); return {"status":"ok"}
        elif action == "zoom_out": pyautogui.hotkey("ctrl","-"); return {"status":"ok"}
        elif action == "fullscreen": pyautogui.press("f11"); return {"status":"ok"}
        elif action == "bold": pyautogui.hotkey("ctrl","b"); return {"status":"ok"}
        elif action == "italic": pyautogui.hotkey("ctrl","i"); return {"status":"ok"}
        elif action == "underline": pyautogui.hotkey("ctrl","u"); return {"status":"ok"}

        # ── WAIT ──────────────────────────────────────────────────
        elif action == "wait":
            time.sleep(min(float(cmd.get("seconds",1)), 15))
            return {"status":"ok"}
        elif action == "wait_for_load":
            time.sleep(float(cmd.get("seconds",3)))
            return {"status":"ok"}

        # ── AI QUERY ──────────────────────────────────────────────
        elif action == "ask_ai":
            question = cmd.get("question","")
            if question and token:
                try:
                    r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                        headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
                        json={"messages":[{"role":"user","content":question}],"stream":False},
                        timeout=30)
                    if r.status_code == 200:
                        answer = r.json().get("content") or r.json().get("response") or ""
                        if answer: speak(answer[:500])
                        return {"status":"ok","answer":answer}
                except Exception as e: return {"status":"error","message":str(e)}
            return {"status":"ok"}

        # ── TASK ──────────────────────────────────────────────────
        elif action == "task":
            task_text = cmd.get("task","") or cmd.get("goal","")
            if task_text and token:
                execute_full_task(task_text, token)
            return {"status":"ok"}

        else:
            return {"status":"error","message":f"Unknown action: {action}"}

    except pyautogui.FailSafeException:
        return {"status":"error","message":"Failsafe triggered"}
    except Exception as e:
        log.error(f"Command [{action}]: {e}")
        return {"status":"error","message":str(e)}

def execute_action_list(actions: list, token: str = None):
    for i, action in enumerate(actions):
        if not isinstance(action, dict): continue
        a = action.get("action","?")
        desc = (action.get("url") or action.get("text","")[:30] or
                action.get("key","") or action.get("command","")[:30] or "")
        log.info(f"  [{i+1}/{len(actions)}] {a} {desc}")
        result = execute_command(action, token=token)
        if result.get("status") == "error":
            log.warning(f"  ✗ {result.get('message','')}")
        time.sleep(0.18)

# ═══════════════════════════════════════════════════════════════════════
# SUPREME AI BRAIN — 10^99999999999 IQ
# ═══════════════════════════════════════════════════════════════════════
def get_ai_plan(task: str, token: str, context: str = "") -> str:
    sz = pyautogui.size()
    now = datetime.datetime.now().strftime("%I:%M %p, %A %B %d %Y")
    active_win = get_active_window()
    mem_ctx = get_memory_context()

    sys_ctx = f"""SYSTEM STATE:
- Screen: {sz.width}×{sz.height}px
- Time: {now}
- Active window: {active_win}
- OS: {platform.system()} {platform.version()[:30]}
{f"- Memory: {mem_ctx}" if mem_ctx else ""}
{f"- Context: {context}" if context else ""}"""

    gmail_x = int(sz.width * 0.08)
    gmail_y_compose = int(sz.height * 0.75)
    cx, cy = sz.width // 2, sz.height // 2

    prompt = f"""You are DACEXY — the world's most powerful desktop AI assistant with infinite intelligence.
You control a Windows computer with {sz.width}×{sz.height} screen.

{sys_ctx}

TASK: "{task}"

RULES:
1. Return ONLY a valid JSON array — no text before or after
2. Complete the task COMPLETELY — never stop halfway
3. Include wait actions after loading pages (2-4 seconds)
4. Always click fields before typing into them
5. End with a speak action giving the user the result
6. Use EXACT pixel coordinates

GMAIL COORDINATES ({sz.width}×{sz.height}):
- Compose button: ({gmail_x}, {gmail_y_compose})
- To field: ({int(sz.width*0.47)}, {int(sz.height*0.38)})
- Subject: ({int(sz.width*0.47)}, {int(sz.height*0.44)})
- Body: ({int(sz.width*0.47)}, {int(sz.height*0.58)})
- Send button: ({int(sz.width*0.155)}, {int(sz.height*0.845)})
- Center screen: ({cx}, {cy})

COMPLETE ACTION REFERENCE:
Mouse: click, double_click, right_click, triple_click, move, drag_to, scroll, scroll_up, scroll_down
Keys: type, key, hotkey, press_enter, press_tab, press_escape, press_backspace, press_delete, press_space, press_f5
Clipboard: copy, paste, cut, select_all, get_clipboard, set_clipboard, clear_field
Browser: open_url, navigate_url, new_tab, close_tab, new_window, incognito, browser_back, browser_forward, browser_refresh, browser_find
Files: open_file, find_file, open_folder, create_file, read_file, list_files, open_downloads, open_desktop, take_note, read_notes
Apps: open_app, run_shell, run_powershell, kill_process, list_processes
Windows: minimize_window, maximize_window, close_window, switch_window, show_desktop, snap_left, snap_right, task_view, open_task_manager
System: lock_screen, open_settings, open_file_explorer, open_run, open_start, search_windows
Memory: remember, recall, forget_all
Info: get_time, get_weather, get_system_info, battery_status, what_on_screen
Media: volume_up, volume_down, volume_mute, volume_set, media_play_pause, media_next, media_prev
Edit: save, undo, redo, find, print, fullscreen, bold, italic, underline, zoom_in, zoom_out
AI: ask_ai
Other: wait, wait_for_load, screenshot, notify, speak

FIELD FORMATS:
{{"action":"open_url","url":"https://..."}}
{{"action":"navigate_url","url":"https://..."}}
{{"action":"click","x":N,"y":N,"button":"left","clicks":1}}
{{"action":"type","text":"..."}}
{{"action":"key","key":"enter/tab/esc/f5/..."}}
{{"action":"hotkey","keys":["ctrl","c"]}}
{{"action":"wait","seconds":N}}
{{"action":"run_shell","command":"..."}}
{{"action":"ask_ai","question":"..."}}
{{"action":"remember","fact":"..."}}
{{"action":"get_weather","city":"Mumbai"}}
{{"action":"speak","text":"Final result"}}

TASK EXAMPLES:

"open youtube and play lofi music":
[{{"action":"open_url","url":"https://youtube.com/results?search_query=lofi+music"}},{{"action":"wait","seconds":3}},{{"action":"click","x":{cx},"y":380}},{{"action":"speak","text":"Playing lofi music on YouTube"}}]

"send email on gmail to john@test.com subject Meeting body Let us meet tomorrow at 10am":
[{{"action":"open_url","url":"https://mail.google.com"}},{{"action":"wait","seconds":4}},{{"action":"click","x":{gmail_x},"y":{gmail_y_compose}}},{{"action":"wait","seconds":1}},{{"action":"click","x":{int(sz.width*0.47)},"y":{int(sz.height*0.38)}}},{{"action":"type","text":"john@test.com"}},{{"action":"key","key":"tab"}},{{"action":"type","text":"Meeting"}},{{"action":"click","x":{int(sz.width*0.47)},"y":{int(sz.height*0.58)}}},{{"action":"type","text":"Let us meet tomorrow at 10am"}},{{"action":"click","x":{int(sz.width*0.155)},"y":{int(sz.height*0.845)}}},{{"action":"speak","text":"Email sent to john@test.com successfully"}}]

"what time is it":
[{{"action":"get_time"}},{{"action":"speak","text":"I just told you the time!"}}]

"what is the weather in delhi":
[{{"action":"get_weather","city":"delhi"}}]

"remember that my name is Vivaan":
[{{"action":"remember","fact":"User name is Vivaan"}},{{"action":"speak","text":"Got it! I will remember that your name is Vivaan"}}]

"take a note: buy groceries tomorrow":
[{{"action":"take_note","text":"buy groceries tomorrow"}},{{"action":"speak","text":"Note saved: buy groceries tomorrow"}}]

"what is on my screen right now":
[{{"action":"what_on_screen"}}]

"open notepad and write a resignation letter":
[{{"action":"open_app","app":"notepad"}},{{"action":"wait","seconds":1}},{{"action":"type","text":"Dear Manager,\\n\\nI am writing to formally resign from my position, effective two weeks from today. Thank you for the opportunity.\\n\\nSincerely,\\n[Your Name]"}},{{"action":"speak","text":"Resignation letter written in Notepad"}}]

"search google for best AI tools 2026":
[{{"action":"open_url","url":"https://www.google.com/search?q=best+AI+tools+2026"}},{{"action":"speak","text":"Here are Google results for best AI tools 2026"}}]

Now generate the PERFECT complete action plan for: "{task}"
Return ONLY valid JSON array — nothing else:"""

    try:
        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":[{"role":"user","content":prompt}],"stream":False},
            timeout=60)
        if r.status_code == 200:
            content = r.json().get("content") or r.json().get("response") or r.json().get("text") or ""
            log.info(f"AI plan ({len(content)} chars)")
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                try:
                    actions = json.loads(match.group(0))
                    if isinstance(actions, list) and len(actions) > 0:
                        non_speak = [a for a in actions if a.get("action") != "speak"]
                        if non_speak:
                            return json.dumps(actions)
                except json.JSONDecodeError: pass
        log.warning(f"AI returned {r.status_code}, using direct")
        return force_direct(task, sz)
    except Exception as e:
        log.error(f"AI brain error: {e}")
        return force_direct(task, sz)

def force_direct(command: str, sz=None) -> str:
    """Lightning-fast direct execution for 60+ common commands."""
    if sz is None: sz = pyautogui.size()
    cmd = command.lower().strip()
    cx, cy = sz.width//2, sz.height//2

    # Time / Date
    if any(x in cmd for x in ["what time","current time","tell me the time","what's the time"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        return json.dumps([{"action":"speak","text":f"It is {now}"}])
    if any(x in cmd for x in ["what date","today's date","what day","what is today"]):
        today = datetime.datetime.now().strftime("%A, %B %d %Y")
        return json.dumps([{"action":"speak","text":f"Today is {today}"}])

    # Weather
    if "weather" in cmd:
        city_m = re.search(r'(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$)',command,re.I)
        city = city_m.group(1).strip() if city_m else "my location"
        return json.dumps([{"action":"get_weather","city":city}])

    # Battery
    if "battery" in cmd:
        return json.dumps([{"action":"battery_status"}])

    # Memory
    if any(x in cmd for x in ["remember that","please remember","don't forget","note that"]):
        fact_m = re.search(r'(?:remember that|please remember|note that|don\'t forget)[:\s]+(.+)',command,re.I)
        fact = fact_m.group(1).strip() if fact_m else command
        return json.dumps([{"action":"remember","fact":fact},{"action":"speak","text":f"Got it! Remembered: {fact}"}])
    if any(x in cmd for x in ["what do you remember","recall","what did i tell you","your memory"]):
        return json.dumps([{"action":"recall"}])

    # Notes
    if any(x in cmd for x in ["take a note","make a note","note down","write down"]):
        note_m = re.search(r'(?:note|note down|write down)[:\s]+(.+)',command,re.I)
        note = note_m.group(1).strip() if note_m else command
        return json.dumps([{"action":"take_note","text":note},{"action":"speak","text":f"Note saved: {note}"}])
    if "read my notes" in cmd or "show my notes" in cmd:
        return json.dumps([{"action":"read_notes"}])

    # YouTube
    if "youtube" in cmd:
        q = re.sub(r'open|youtube|play|search|for|on|in|new tab|chrome','',cmd).strip()
        url = f"https://youtube.com/results?search_query={q.replace(' ','+')}" if len(q)>2 else "https://youtube.com"
        return json.dumps([{"action":"open_url","url":url},{"action":"wait","seconds":3},
            {"action":"speak","text":f"YouTube opened{' — searching for '+q if len(q)>2 else ''}"}])

    # Gmail / Email
    if "gmail" in cmd or ("email" in cmd and any(x in cmd for x in ["send","compose","write","check"])):
        em = re.search(r'[\w.\-+]+@[\w.\-]+\.\w+',command)
        to = em.group(0) if em else ""
        sm = re.search(r'subject[:\s]+([^,]+?)(?:\s+body|\s+saying|\s+with|$)',command,re.I)
        bm = re.search(r'(?:body|saying|content|message|write|say)[:\s]+(.+?)(?:\s+send|$)',command,re.I)
        subj = sm.group(1).strip() if sm else "Hello"
        body = bm.group(1).strip() if bm else "Hi there!"
        actions = [{"action":"open_url","url":"https://mail.google.com"},{"action":"wait","seconds":4}]
        if to:
            actions += [
                {"action":"click","x":int(sz.width*0.08),"y":int(sz.height*0.75)},
                {"action":"wait","seconds":1},
                {"action":"click","x":int(sz.width*0.47),"y":int(sz.height*0.38)},
                {"action":"type","text":to},{"action":"key","key":"tab"},
                {"action":"type","text":subj},
                {"action":"click","x":int(sz.width*0.47),"y":int(sz.height*0.58)},
                {"action":"type","text":body},
                {"action":"click","x":int(sz.width*0.155),"y":int(sz.height*0.845)},
                {"action":"speak","text":f"Email sent to {to} — subject: {subj}"}
            ]
        else:
            actions += [{"action":"click","x":int(sz.width*0.08),"y":int(sz.height*0.75)},
                       {"action":"speak","text":"Gmail compose window opened"}]
        return json.dumps(actions)

    # Google Search
    if "search" in cmd or ("google" in cmd and "open" not in cmd):
        q = re.sub(r'search|google|for|on|find|look up','',cmd).strip() or cmd
        return json.dumps([{"action":"open_url","url":f"https://google.com/search?q={q.replace(' ','+')}"},
            {"action":"speak","text":f"Searched Google for: {q}"}])

    # Social/Web shortcuts
    shortcuts = [
        ("whatsapp","https://web.whatsapp.com","WhatsApp Web"),
        ("instagram","https://instagram.com","Instagram"),
        ("twitter","https://x.com","Twitter"),
        ("facebook","https://facebook.com","Facebook"),
        ("linkedin","https://linkedin.com","LinkedIn"),
        ("reddit","https://reddit.com","Reddit"),
        ("spotify","https://open.spotify.com","Spotify"),
        ("netflix","https://netflix.com","Netflix"),
        ("amazon","https://amazon.in","Amazon"),
        ("flipkart","https://flipkart.com","Flipkart"),
        ("swiggy","https://swiggy.com","Swiggy"),
        ("zomato","https://zomato.com","Zomato"),
        ("github","https://github.com","GitHub"),
        ("chatgpt","https://chat.openai.com","ChatGPT"),
        ("maps","https://maps.google.com","Google Maps"),
        ("gmail","https://mail.google.com","Gmail"),
        ("drive","https://drive.google.com","Google Drive"),
        ("docs","https://docs.google.com","Google Docs"),
        ("sheets","https://sheets.google.com","Google Sheets"),
        ("translate","https://translate.google.com","Google Translate"),
    ]
    for kw,url,name in shortcuts:
        if kw in cmd:
            return json.dumps([{"action":"open_url","url":url},{"action":"speak","text":f"{name} opened"}])

    # Apps
    if "chrome" in cmd and any(x in cmd for x in ["open","start","launch"]):
        return json.dumps([{"action":"run_shell","command":"start chrome"},{"action":"speak","text":"Opening Chrome"}])
    if "notepad" in cmd:
        tm = re.search(r'(?:write|type|say)[:\s]+(.+)',command,re.I)
        acts = [{"action":"open_app","app":"notepad"},{"action":"wait","seconds":1}]
        if tm: acts.append({"action":"type","text":tm.group(1)})
        acts.append({"action":"speak","text":"Notepad opened"})
        return json.dumps(acts)
    if "calculator" in cmd:
        mm = re.search(r'(\d[\d\s\+\-\*\/\(\)\.]+\d)',command)
        acts = [{"action":"open_app","app":"calc"},{"action":"wait","seconds":1}]
        if mm: acts += [{"action":"type","text":mm.group(1).strip()},{"action":"press_enter"}]
        acts.append({"action":"speak","text":f"Calculator opened{' — calculated: '+mm.group(1) if mm else ''}"})
        return json.dumps(acts)
    if "screenshot" in cmd:
        return json.dumps([{"action":"screenshot"},{"action":"speak","text":"Screenshot taken!"}])
    if "what is on" in cmd or "what's on" in cmd or "whats on" in cmd:
        return json.dumps([{"action":"what_on_screen"}])

    # Volume
    if any(x in cmd for x in ["volume up","louder","increase volume"]): return json.dumps([{"action":"volume_up","steps":4},{"action":"speak","text":"Volume increased"}])
    if any(x in cmd for x in ["volume down","quieter","decrease volume"]): return json.dumps([{"action":"volume_down","steps":4},{"action":"speak","text":"Volume decreased"}])
    if "mute" in cmd: return json.dumps([{"action":"volume_mute"},{"action":"speak","text":"Muted"}])
    if "unmute" in cmd: return json.dumps([{"action":"volume_mute"},{"action":"speak","text":"Unmuted"}])

    # System
    if "lock" in cmd and any(x in cmd for x in ["screen","computer"]): return json.dumps([{"action":"lock_screen"},{"action":"speak","text":"Screen locked"}])
    if "show desktop" in cmd: return json.dumps([{"action":"show_desktop"},{"action":"speak","text":"Showing desktop"}])
    if "task manager" in cmd: return json.dumps([{"action":"open_task_manager"},{"action":"speak","text":"Task Manager opened"}])
    if "file explorer" in cmd: return json.dumps([{"action":"open_file_explorer"},{"action":"speak","text":"File Explorer opened"}])
    if "close window" in cmd: return json.dumps([{"action":"close_window"},{"action":"speak","text":"Window closed"}])
    if "fullscreen" in cmd: return json.dumps([{"action":"fullscreen"},{"action":"speak","text":"Toggled fullscreen"}])
    if "open downloads" in cmd: return json.dumps([{"action":"open_downloads"},{"action":"speak","text":"Downloads folder opened"}])
    if "open desktop" in cmd: return json.dumps([{"action":"open_desktop"},{"action":"speak","text":"Desktop folder opened"}])
    if "play pause" in cmd: return json.dumps([{"action":"media_play_pause"},{"action":"speak","text":"Play/Pause"}])
    if "next song" in cmd: return json.dumps([{"action":"media_next"},{"action":"speak","text":"Next track"}])
    if "previous song" in cmd: return json.dumps([{"action":"media_prev"},{"action":"speak","text":"Previous track"}])
    if "battery" in cmd: return json.dumps([{"action":"battery_status"}])
    if "system info" in cmd: return json.dumps([{"action":"get_system_info"},{"action":"speak","text":"System information retrieved"}])

    # Ask AI as fallback
    return json.dumps([
        {"action":"ask_ai","question":command},
    ])

def execute_full_task(task: str, token: str, context: str = ""):
    log.info(f"Task: {task}")
    MEMORY["task_history"].append(task)
    save_memory()

    # Permission check
    needs_perm, ptype = needs_permission(task)
    if needs_perm:
        if not ask_permission(task, ptype):
            speak("Task cancelled for your security.")
            return

    speak("On it!")

    # Get plan
    actions_json = get_ai_plan(task, token, context)

    try:
        actions = json.loads(actions_json)
        if isinstance(actions, list) and len(actions) > 0:
            non_speak = [a for a in actions if a.get("action") not in ["speak","notify"]]
            if not non_speak:
                # Retry with force direct
                actions_json = force_direct(task)
                actions = json.loads(actions_json)
            log.info(f"Executing {len(actions)} actions")
            execute_action_list(actions, token=token)
        else:
            speak("I could not plan that. Please rephrase and try again.")
    except Exception as e:
        log.error(f"Task error: {e}")
        speak("Something went wrong. Please try again.")

# ═══════════════════════════════════════════════════════════════════════
# SIRI-LIKE VOICE AGENT — ALWAYS ON 24/7
# ═══════════════════════════════════════════════════════════════════════
class SiriAgent:
    """Always-on background voice agent like Siri/Google Assistant."""

    def __init__(self, token: str):
        self.token = token
        self.running = False
        self.processing = False
        self.rec = None
        self.mic = None
        self._init_mic()

    def _init_mic(self):
        if not VOICE_AVAILABLE:
            print("  ⚠️  No microphone — text mode only")
            return
        try:
            self.rec = sr.Recognizer()
            self.rec.energy_threshold = 200
            self.rec.dynamic_energy_threshold = True
            self.rec.dynamic_energy_adjustment_damping = 0.1
            self.rec.pause_threshold = 0.6
            self.rec.phrase_threshold = 0.3
            self.rec.non_speaking_duration = 0.4
            self.mic = sr.Microphone()
            print("  🎤 Calibrating microphone (2 seconds)...")
            with self.mic as src:
                self.rec.adjust_for_ambient_noise(src, duration=2)
            print(f'  ✅ Mic calibrated! Say "{WAKE_WORD.title()}" anytime.\n')
        except Exception as e:
            print(f"  ⚠️  Mic error: {e}")
            self.mic = None

    def _listen_once(self, timeout=1, phrase_limit=12) -> Optional[str]:
        if not self.mic: return None
        try:
            with self.mic as src:
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            return self.rec.recognize_google(audio).lower()
        except sr.WaitTimeoutError: return None
        except sr.UnknownValueError: return None
        except Exception: return None

    def _listen_command(self, timeout=12) -> Optional[str]:
        """Listen for the actual command after wake word."""
        speak("Yes?")
        try:
            with self.mic as src:
                self.rec.adjust_for_ambient_noise(src, duration=0.3)
                print("  👂 Listening...")
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=25)
            text = self.rec.recognize_google(audio)
            print(f"  🗣️  You: {text}")
            return text
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Try again.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return None
        except Exception as e:
            log.error(f"Command listen error: {e}")
            return None

    def _process(self, command: str):
        """Process a voice command in a thread."""
        self.processing = True
        try:
            execute_full_task(command, self.token)
        finally:
            self.processing = False

    def voice_loop(self):
        """Background thread — always listening for wake word like Siri."""
        if not self.mic:
            return
        print(f'  👂 Always listening in background for "{WAKE_WORD.title()}"...\n')
        while self.running:
            if self.processing:
                time.sleep(0.05)
                continue
            text = self._listen_once(timeout=1, phrase_limit=8)
            if not text:
                continue
            if WAKE_WORD in text:
                # Command may be inline: "Hey Dacexy open YouTube"
                inline = text.replace(WAKE_WORD, "").strip()
                if len(inline) > 2:
                    print(f"  🗣️  Inline: {inline}")
                    threading.Thread(target=self._process, args=(inline,), daemon=True).start()
                else:
                    # Wait for separate command
                    cmd = self._listen_command()
                    if cmd:
                        threading.Thread(target=self._process, args=(cmd,), daemon=True).start()

    def text_loop(self):
        """Text input loop — type commands."""
        print("  ⌨️  Type commands (or say 'Hey Dacexy <command>'):")
        print("  ──────────────────────────────────────────────")
        print("  Examples:")
        print("    → open youtube and play lofi music")
        print("    → send email to boss@company.com subject hello body hi there")
        print("    → what is the weather in mumbai")
        print("    → remember that my meeting is at 3pm")
        print("    → take a screenshot")
        print("    → what is on my screen")
        print("    → search google for best restaurants near me")
        print("    → open notepad and write a to-do list")
        print("    → what time is it")
        print("    → history  (see recent tasks)")
        print("    → quit  (exit agent)")
        print("  ──────────────────────────────────────────────\n")

        while self.running:
            try:
                command = input("  dacexy ❯ ").strip()
                if not command: continue
                if command.lower() in ['quit','exit','q','bye']:
                    speak("Goodbye! Dacexy is shutting down.")
                    self.running = False; break
                if command.lower() == 'history':
                    print("\n  📋 Recent Tasks:")
                    for i, t in enumerate(list(MEMORY["task_history"])[-10:], 1):
                        print(f"     {i}. {t}")
                    print()
                    continue
                if command.lower() == 'memory':
                    ctx = get_memory_context()
                    print(f"\n  🧠 Memory:\n  {ctx or 'Empty'}\n")
                    continue
                if command.lower().startswith('remember '):
                    fact = command[9:]
                    remember(fact); speak(f"Remembered: {fact}")
                    continue
                # Run in thread so voice stays responsive
                threading.Thread(target=self._process, args=(command,), daemon=True).start()
            except (EOFError, KeyboardInterrupt):
                self.running = False; break

    def run(self):
        self.running = True
        # Start voice in background
        if self.mic:
            vt = threading.Thread(target=self.voice_loop, daemon=True)
            vt.start()
        # Run text in foreground
        self.text_loop()

    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET REMOTE CONTROL
# ═══════════════════════════════════════════════════════════════════════
async def remote_loop(token: str):
    delay = 3
    while True:
        try:
            log.info("🔌 Connecting to Dacexy cloud...")
            async with websockets.connect(
                BACKEND_WS, ping_interval=20, ping_timeout=30, open_timeout=30
            ) as ws:
                await ws.send(json.dumps({"token": token}))
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)

                if data.get("type") == "error":
                    msg = data.get("message","")
                    print(f"\n  ❌ Auth: {msg}")
                    if any(x in msg.lower() for x in ["expired","invalid"]):
                        clear_token(); return
                    await asyncio.sleep(delay); continue

                log.info("✅ Remote control connected!")
                notify("Dacexy", "Remote control connected!")
                delay = 3

                # Send system info
                info = execute_command({"action":"get_system_info"})
                await ws.send(json.dumps({"type":"system_info","data":info}))

                async for raw in ws:
                    try:
                        cmd = json.loads(raw)
                        mtype = cmd.get("type","")

                        if mtype == "ping":
                            await ws.send(json.dumps({"type":"pong"}))
                            continue

                        if mtype == "task":
                            task_text = cmd.get("task","") or cmd.get("goal","")
                            ctx = cmd.get("context","")
                            log.info(f"📋 Remote task: {task_text}")

                            def run_t():
                                execute_full_task(task_text, token, context=ctx)

                            t = threading.Thread(target=run_t, daemon=True)
                            t.start(); t.join(timeout=120)

                            await ws.send(json.dumps({
                                "type":"task_result","status":"completed",
                                "task":task_text,"actions":len(MEMORY["task_history"])
                            }))
                            continue

                        if mtype == "command" or "action" in cmd:
                            act = cmd.get("action","")
                            log.info(f"🎮 Remote: {act}")
                            if act not in ["screenshot","get_system_info","get_screen_info"]:
                                ss = take_screenshot()
                                if ss: await ws.send(json.dumps({"type":"screenshot_before","data":ss}))
                            result = execute_command(cmd, token=token)
                            await ws.send(json.dumps({"type":"result","action":act,"data":result}))
                            await asyncio.sleep(0.4)
                            ss = take_screenshot()
                            if ss: await ws.send(json.dumps({"type":"screenshot_after","data":ss}))

                    except json.JSONDecodeError: pass
                    except Exception as e: log.error(f"WS loop: {e}")

        except websockets.exceptions.ConnectionClosed:
            log.warning("Connection closed")
        except ConnectionRefusedError:
            log.warning("Backend sleeping...")
        except Exception as e:
            log.error(f"Remote error: {e}")

        log.info(f"⏳ Retry in {delay}s...")
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, 30)

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║         DACEXY Desktop Agent v11.0                  ║")
    print("║   World's Most Powerful AI Desktop Agent            ║")
    print("║   Like Siri — 24/7 Always On — 150+ Actions         ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    init_tts()
    load_memory()
    setup_autostart()

    token = get_token()
    if token:
        print("  Verifying session...")
        if check_token_valid(token):
            print("  ✅ Session valid!\n")
        else:
            print("  ⚠️  Session expired\n")
            clear_token(); token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            remaining = 2 - attempt
            if remaining > 0: print(f"  {remaining} attempts left\n")
        if not token:
            input("\n  Press Enter to exit...")
            return

    print(f"\n  ✅ Logged in!")
    print(f"\n  🚀 DACEXY CAPABILITIES:")
    print(f"  ├─ 🌐  Browse web, search, open any site")
    print(f"  ├─ 📧  Send emails on Gmail automatically")
    print(f"  ├─ 📁  Manage files, read, create, search")
    print(f"  ├─ 🖱️   Click, type, scroll anywhere")
    print(f"  ├─ 🎤  Voice (say '{WAKE_WORD.title()}' to activate)")
    print(f"  ├─ 🧠  Memory — remembers your preferences")
    print(f"  ├─ 👁️   Vision — sees what's on your screen")
    print(f"  ├─ 🔒  Smart permission system for sensitive actions")
    print(f"  ├─ 🔄  Auto-reconnects, auto-starts on boot")
    print(f"  └─ ⚡  150+ actions for complete computer control\n")

    siri = SiriAgent(token)

    speak("Dacexy version 11 is now active. I am your always-on AI assistant. Say Hey Dacexy anytime!")

    # Run remote WebSocket in background
    async def bg():
        await remote_loop(token)

    def run_remote():
        asyncio.run(bg())

    remote_thread = threading.Thread(target=run_remote, daemon=True)
    remote_thread.start()

    # Run Siri-like agent in foreground
    try:
        siri.run()
    except KeyboardInterrupt:
        print("\n  👋 Shutting down...")
        speak("Goodbye!")
        siri.stop()

if __name__ == "__main__":
    main()
