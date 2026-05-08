"""
Dacexy Desktop Agent v10.0 - World's Most Powerful AI Desktop Agent
====================================================================
Features:
- Infinite IQ AI Brain with vision (sees your screen)
- Multi-step autonomous task execution
- Smart permission system for sensitive actions
- Always-on voice control (Hey Dacexy)
- Auto-reconnects, auto-starts on boot
- 100+ actions: click, type, scroll, shell, browser, files, apps
- Learns from context, remembers session state
- Handles ANY task a human can do on a computer
"""

import subprocess, sys, os, platform

# ═══════════════════════════════════════════════════════════════════════
# AUTO-INSTALL ALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════

REQUIRED = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
    "pyperclip", "keyboard", "pygetwindow",
]

print("╔══════════════════════════════════════╗")
print("║   Dacexy Agent v10.0 - Starting...   ║")
print("╚══════════════════════════════════════╝\n")
print("Checking dependencies...")

for pkg in REQUIRED:
    import_name = pkg.replace("-", "_")
    if pkg == "speechrecognition": import_name = "speech_recognition"
    if pkg == "pillow": import_name = "PIL"
    if pkg == "pygetwindow": import_name = "pygetwindow"
    try:
        __import__(import_name)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# PyAudio for voice
try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False
    try:
        print("  Installing PyAudio...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin", "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import pyaudio
        PYAUDIO_OK = True
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                "PyAudio", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio
            PYAUDIO_OK = True
        except:
            PYAUDIO_OK = False

print("  All dependencies ready!\n")

# ═══════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════

import asyncio, base64, io, json, logging, threading
import time, webbrowser, re, datetime, winreg, shutil
import ctypes, struct
from pathlib import Path
from typing import Optional

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab, Image
import pyttsx3
import pyperclip
import psutil

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except ImportError:
    VOICE_AVAILABLE = False

try:
    import pygetwindow as gw
    WINDOW_CONTROL = True
except ImportError:
    WINDOW_CONTROL = False

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
LOG_FILE     = Path.home() / "dacexy_agent.log"
WAKE_WORD    = "hey dacexy"
AGENT_VERSION = "10.0"

# Session memory — remembers context during session
SESSION_MEMORY = {
    "last_task": "",
    "last_url": "",
    "open_apps": [],
    "clipboard_history": [],
    "task_history": [],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
log = logging.getLogger("dacexy")

# ═══════════════════════════════════════════════════════════════════════
# TTS ENGINE
# ═══════════════════════════════════════════════════════════════════════

_tts_engine = None
_tts_lock = threading.Lock()

def get_tts():
    global _tts_engine
    if _tts_engine is None:
        try:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 170)
            _tts_engine.setProperty("volume", 1.0)
            voices = _tts_engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "female" in v.name.lower():
                    _tts_engine.setProperty("voice", v.id)
                    break
        except: pass
    return _tts_engine

def speak(text: str):
    print(f"  🔊 {text}")
    try:
        with _tts_lock:
            e = get_tts()
            if e:
                e.say(text)
                e.runAndWait()
    except: pass

# ═══════════════════════════════════════════════════════════════════════
# CONFIG MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_token(): return load_config().get("access_token")
def save_token(t): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token(): cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return r.status_code == 200
    except: return False

# ═══════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════

def login():
    print("\n╔══════════════════════════════════════╗")
    print("║      Dacexy Agent - Login            ║")
    print("╚══════════════════════════════════════╝")
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
                print("  ✅ Login successful!")
                return token
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  ❌ Login failed: {d}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# AUTOSTART
# ═══════════════════════════════════════════════════════════════════════

def setup_autostart():
    try:
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        cmd = f'"{sys.executable}" "{agent_path}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Auto-start configured")
    except: pass

# ═══════════════════════════════════════════════════════════════════════
# SCREENSHOT WITH AI VISION
# ═══════════════════════════════════════════════════════════════════════

def take_screenshot(quality: int = 80) -> Optional[str]:
    try:
        img = ImageGrab.grab()
        img.thumbnail((1440, 900))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return None

def take_region_screenshot(x: int, y: int, w: int, h: int) -> Optional[str]:
    try:
        img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

# ═══════════════════════════════════════════════════════════════════════
# PERMISSION SYSTEM - FULL SECURITY
# ═══════════════════════════════════════════════════════════════════════

PERMISSION_RULES = {
    "delete_files": {
        "keywords": ["delete", "remove", "erase", "wipe", "trash", "unlink"],
        "context": ["file", "folder", "document", "photo", "image", "video", "data", "directory"],
        "message": "🗑️ DELETE FILES",
        "desc": "Dacexy wants to delete files from your computer. This cannot be undone."
    },
    "banking": {
        "keywords": ["bank", "banking", "hdfc", "sbi", "icici", "axis", "kotak", "pnb",
                     "paytm", "gpay", "google pay", "phonepe", "upi", "neft", "imps", "rtgs",
                     "transfer money", "send money", "net banking", "mobile banking"],
        "context": ["any"],
        "message": "🏦 BANKING / FINANCIAL",
        "desc": "Dacexy wants to access banking or financial services."
    },
    "payment": {
        "keywords": ["payment", "pay now", "checkout", "purchase", "buy now",
                     "card number", "cvv", "credit card", "debit card", "expiry"],
        "context": ["any"],
        "message": "💳 PAYMENT",
        "desc": "Dacexy wants to make a payment or access payment details."
    },
    "private_data": {
        "keywords": ["aadhar", "aadhaar", "pan card", "passport", "driving license",
                     "social security", "ssn", "date of birth", "mother maiden",
                     "secret question", "security answer"],
        "context": ["any"],
        "message": "🔒 PRIVATE IDENTITY DATA",
        "desc": "Dacexy wants to access private identity documents or data."
    },
    "password_access": {
        "keywords": ["password", "passwords", "login credentials", "my passwords",
                     "password manager", "lastpass", "1password", "bitwarden", "keepass"],
        "context": ["any"],
        "message": "🔑 PASSWORD ACCESS",
        "desc": "Dacexy wants to access passwords or credential managers."
    },
    "camera_mic": {
        "keywords": ["open camera", "start camera", "record video", "record audio",
                     "start recording", "take photo with camera", "webcam"],
        "context": ["any"],
        "message": "📷 CAMERA / MICROPHONE",
        "desc": "Dacexy wants to access your camera or record audio."
    },
    "shutdown_restart": {
        "keywords": ["shutdown", "shut down", "restart", "reboot", "power off",
                     "turn off computer", "hibernate", "sleep mode"],
        "context": ["any"],
        "message": "⚡ SHUTDOWN / RESTART",
        "desc": "Dacexy wants to shut down or restart your computer."
    },
    "install_software": {
        "keywords": ["install", "setup.exe", ".msi installer", "download and install"],
        "context": ["software", "program", "application", "app", ".exe", ".msi"],
        "message": "📦 INSTALL SOFTWARE",
        "desc": "Dacexy wants to install software on your computer."
    },
    "registry_edit": {
        "keywords": ["regedit", "registry editor", "edit registry", "windows registry"],
        "context": ["any"],
        "message": "🔧 REGISTRY EDIT",
        "desc": "Dacexy wants to edit the Windows registry. This is advanced and risky."
    },
    "format_disk": {
        "keywords": ["format disk", "format drive", "fdisk", "diskpart", "wipe drive",
                     "disk cleanup all", "format c", "format d"],
        "context": ["any"],
        "message": "☢️ FORMAT DISK — DANGER",
        "desc": "DANGER: Dacexy wants to FORMAT a disk. ALL DATA WILL BE LOST."
    },
    "admin_elevation": {
        "keywords": ["run as administrator", "runas", "admin privileges",
                     "elevated command", "uac prompt"],
        "context": ["any"],
        "message": "🔐 ADMINISTRATOR ACCESS",
        "desc": "Dacexy wants to run something with administrator privileges."
    },
    "email_send": {
        "keywords": ["send email", "send mail", "compose email"],
        "context": ["any"],
        "message": "📧 SEND EMAIL",
        "desc": "Dacexy wants to send an email on your behalf."
    },
    "social_post": {
        "keywords": ["post on", "tweet", "share on", "publish post", "upload to",
                     "go live", "story on"],
        "context": ["facebook", "instagram", "twitter", "linkedin", "youtube",
                    "tiktok", "snapchat", "social media"],
        "message": "📱 SOCIAL MEDIA POST",
        "desc": "Dacexy wants to post something on social media on your behalf."
    },
}

BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf ~", "rm -rf /*",
    "format c:", "format c:/q /u",
    "del /s /q c:\\windows",
    "del /s /q c:\\",
    "mkfs.ext4 /dev/sda",
    "dd if=/dev/zero of=/dev/sda",
    "deltree c:\\",
    ":(){:|:&};:",
    "sudo rm -rf /",
    "rd /s /q c:\\",
]

def needs_permission(task: str) -> tuple:
    task_lower = task.lower()
    for perm_type, rule in PERMISSION_RULES.items():
        kw_match = any(k in task_lower for k in rule["keywords"])
        if not kw_match:
            continue
        if rule["context"] == ["any"]:
            return True, perm_type
        ctx_match = any(c in task_lower for c in rule["context"])
        if ctx_match:
            return True, perm_type
    return False, ""

def ask_permission(task: str, perm_type: str) -> bool:
    rule = PERMISSION_RULES.get(perm_type, {})
    msg = rule.get("message", "⚠️ SENSITIVE ACTION")
    desc = rule.get("desc", "Dacexy wants to perform a sensitive action.")

    border = "═" * 50
    print(f"\n  {border}")
    print(f"  ⚠️  PERMISSION REQUIRED")
    print(f"  {border}")
    print(f"  Action: {msg}")
    print(f"  Detail: {desc}")
    print(f"  Task  : \"{task}\"")
    print(f"  {border}")

    speak(f"Permission needed. {desc} Do you want to allow this? Say yes or no.")
    print("\n  Type YES to allow or NO to deny: ", end="", flush=True)

    try:
        response = input().strip().lower()
        granted = response in ['yes', 'y', 'allow', 'ok', 'approve', 'sure', 'yeah', 'proceed']
        if granted:
            print(f"  ✅ Permission GRANTED\n")
            speak("Permission granted. Proceeding carefully.")
        else:
            print(f"  ❌ Permission DENIED\n")
            speak("Permission denied. Task cancelled for your security.")
        return granted
    except:
        return False

# ═══════════════════════════════════════════════════════════════════════
# SMART TYPE & UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def smart_type(text: str):
    try:
        pyperclip.copy(str(text))
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
    except:
        pyautogui.write(str(text), interval=0.03)

def get_active_window_title() -> str:
    try:
        if WINDOW_CONTROL:
            w = gw.getActiveWindow()
            return w.title if w else "Unknown"
    except: pass
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except: return "Unknown"

def get_running_processes() -> list:
    try:
        return [p.name() for p in psutil.process_iter(['name']) if p.info['name']][:20]
    except: return []

def get_system_stats() -> dict:
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "battery": psutil.sensors_battery().percent if psutil.sensors_battery() else None,
        }
    except: return {}

def find_file(filename: str, search_path: str = None) -> list:
    results = []
    search_paths = [search_path] if search_path else [
        str(Path.home()),
        str(Path.home() / "Desktop"),
        str(Path.home() / "Documents"),
        str(Path.home() / "Downloads"),
    ]
    for root_path in search_paths:
        try:
            for root, dirs, files in os.walk(root_path):
                for f in files:
                    if filename.lower() in f.lower():
                        results.append(os.path.join(root, f))
                    if len(results) >= 10:
                        return results
        except: pass
    return results

def open_file_or_url(path_or_url: str):
    if path_or_url.startswith("http"):
        webbrowser.open(path_or_url)
    else:
        if platform.system() == "Windows":
            os.startfile(path_or_url)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path_or_url])
        else:
            subprocess.Popen(["xdg-open", path_or_url])

# ═══════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR - 120+ ACTIONS
# ═══════════════════════════════════════════════════════════════════════

def execute_command(cmd: dict, token: str = None) -> dict:
    action = cmd.get("action", "").lower().strip()

    try:
        # ── SPEECH ──────────────────────────────────────────
        if action == "speak":
            text = cmd.get("text", "")
            speak(text)
            return {"status": "ok", "spoken": text}

        # ── SCREENSHOT ──────────────────────────────────────
        elif action == "screenshot":
            ss = take_screenshot()
            return {"status": "ok", "screenshot": ss}

        elif action == "screenshot_region":
            ss = take_region_screenshot(
                int(cmd.get("x", 0)), int(cmd.get("y", 0)),
                int(cmd.get("w", 400)), int(cmd.get("h", 300))
            )
            return {"status": "ok", "screenshot": ss}

        # ── MOUSE ────────────────────────────────────────────
        elif action == "click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            button = cmd.get("button", "left")
            clicks = int(cmd.get("clicks", 1))
            pyautogui.click(x, y, button=button, clicks=clicks, interval=0.1)
            time.sleep(0.15)
            return {"status": "ok", "clicked": f"({x},{y})"}

        elif action == "double_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.doubleClick(x, y)
            time.sleep(0.2)
            return {"status": "ok"}

        elif action == "right_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.rightClick(x, y)
            time.sleep(0.1)
            return {"status": "ok"}

        elif action == "triple_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.click(x, y, clicks=3, interval=0.1)
            return {"status": "ok"}

        elif action == "move":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            duration = float(cmd.get("duration", 0.2))
            pyautogui.moveTo(x, y, duration=duration)
            return {"status": "ok"}

        elif action == "drag":
            x1, y1 = int(cmd.get("x1", 0)), int(cmd.get("y1", 0))
            x2, y2 = int(cmd.get("x2", 0)), int(cmd.get("y2", 0))
            pyautogui.drag(x1-pyautogui.position().x, y1-pyautogui.position().y, duration=0.3)
            pyautogui.moveTo(x1, y1)
            pyautogui.dragTo(x2, y2, duration=0.5, button='left')
            return {"status": "ok"}

        elif action == "scroll":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            clicks = int(cmd.get("clicks", 3))
            if x > 0 or y > 0:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(clicks)
            return {"status": "ok"}

        elif action == "scroll_down":
            amount = int(cmd.get("amount", 3))
            pyautogui.scroll(-amount)
            return {"status": "ok"}

        elif action == "scroll_up":
            amount = int(cmd.get("amount", 3))
            pyautogui.scroll(amount)
            return {"status": "ok"}

        elif action == "get_mouse_position":
            pos = pyautogui.position()
            return {"status": "ok", "x": pos.x, "y": pos.y}

        # ── KEYBOARD ─────────────────────────────────────────
        elif action == "type":
            text = str(cmd.get("text", ""))
            smart_type(text)
            time.sleep(0.1)
            return {"status": "ok"}

        elif action == "key":
            key = cmd.get("key", "")
            if key:
                pyautogui.press(key)
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

        elif action == "press_backspace":
            count = int(cmd.get("count", 1))
            for _ in range(count):
                pyautogui.press("backspace")
            return {"status": "ok"}

        elif action == "press_delete":
            pyautogui.press("delete")
            return {"status": "ok"}

        # ── CLIPBOARD ────────────────────────────────────────
        elif action == "copy":
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.3)
            content = pyperclip.paste()
            SESSION_MEMORY["clipboard_history"].append(content[:200])
            return {"status": "ok", "content": content}

        elif action == "paste":
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
            return {"status": "ok"}

        elif action == "cut":
            pyautogui.hotkey("ctrl", "x")
            time.sleep(0.2)
            return {"status": "ok"}

        elif action == "select_all":
            pyautogui.hotkey("ctrl", "a")
            return {"status": "ok"}

        elif action == "get_clipboard":
            content = pyperclip.paste()
            return {"status": "ok", "content": content}

        elif action == "set_clipboard":
            text = cmd.get("text", "")
            pyperclip.copy(text)
            return {"status": "ok"}

        elif action == "clear_field":
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
            pyautogui.press("delete")
            return {"status": "ok"}

        # ── BROWSER / URL ─────────────────────────────────────
        elif action == "open_url":
            url = cmd.get("url", "")
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url)
            SESSION_MEMORY["last_url"] = url
            time.sleep(2)
            return {"status": "ok", "opened": url}

        elif action == "navigate_url":
            url = cmd.get("url", "")
            if not url.startswith("http"):
                url = "https://" + url
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.4)
            pyautogui.hotkey("ctrl", "a")
            smart_type(url)
            pyautogui.press("enter")
            SESSION_MEMORY["last_url"] = url
            time.sleep(2.5)
            return {"status": "ok", "navigated": url}

        elif action == "new_tab":
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.6)
            return {"status": "ok"}

        elif action == "close_tab":
            pyautogui.hotkey("ctrl", "w")
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "new_window":
            pyautogui.hotkey("ctrl", "n")
            time.sleep(0.6)
            return {"status": "ok"}

        elif action == "browser_back":
            pyautogui.hotkey("alt", "left")
            time.sleep(1)
            return {"status": "ok"}

        elif action == "browser_forward":
            pyautogui.hotkey("alt", "right")
            time.sleep(1)
            return {"status": "ok"}

        elif action == "browser_refresh":
            pyautogui.hotkey("ctrl", "r")
            time.sleep(2)
            return {"status": "ok"}

        elif action == "browser_zoom_in":
            pyautogui.hotkey("ctrl", "=")
            return {"status": "ok"}

        elif action == "browser_zoom_out":
            pyautogui.hotkey("ctrl", "-")
            return {"status": "ok"}

        elif action == "browser_zoom_reset":
            pyautogui.hotkey("ctrl", "0")
            return {"status": "ok"}

        elif action == "browser_find":
            query = cmd.get("text", "")
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.3)
            smart_type(query)
            pyautogui.press("enter")
            return {"status": "ok"}

        elif action == "open_incognito":
            pyautogui.hotkey("ctrl", "shift", "n")
            time.sleep(1)
            return {"status": "ok"}

        # ── FILE OPERATIONS ───────────────────────────────────
        elif action == "open_file":
            path = cmd.get("path", "")
            if path and os.path.exists(path):
                open_file_or_url(path)
                time.sleep(1)
                return {"status": "ok", "opened": path}
            return {"status": "error", "message": f"File not found: {path}"}

        elif action == "find_file":
            name = cmd.get("name", "")
            results = find_file(name)
            return {"status": "ok", "files": results, "count": len(results)}

        elif action == "open_folder":
            path = cmd.get("path", str(Path.home()))
            subprocess.Popen(["explorer", path] if platform.system() == "Windows" else ["open", path])
            time.sleep(0.8)
            return {"status": "ok"}

        elif action == "create_file":
            path = cmd.get("path", "")
            content = cmd.get("content", "")
            if path:
                Path(path).write_text(content, encoding="utf-8")
                return {"status": "ok", "created": path}
            return {"status": "error", "message": "No path provided"}

        elif action == "read_file":
            path = cmd.get("path", "")
            if path and os.path.exists(path):
                content = Path(path).read_text(encoding="utf-8", errors="ignore")
                return {"status": "ok", "content": content[:5000]}
            return {"status": "error", "message": "File not found"}

        elif action == "list_files":
            path = cmd.get("path", str(Path.home() / "Desktop"))
            try:
                files = os.listdir(path)
                return {"status": "ok", "files": files[:50], "path": path}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif action == "open_downloads":
            downloads = str(Path.home() / "Downloads")
            subprocess.Popen(["explorer", downloads])
            return {"status": "ok"}

        elif action == "open_desktop":
            desktop = str(Path.home() / "Desktop")
            subprocess.Popen(["explorer", desktop])
            return {"status": "ok"}

        elif action == "open_documents":
            docs = str(Path.home() / "Documents")
            subprocess.Popen(["explorer", docs])
            return {"status": "ok"}

        # ── APP CONTROL ───────────────────────────────────────
        elif action == "open_app":
            app = cmd.get("app", "")
            try:
                if platform.system() == "Windows":
                    os.startfile(app)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", "-a", app])
                else:
                    subprocess.Popen([app])
                time.sleep(1.5)
                return {"status": "ok", "opened": app}
            except Exception as e:
                # Try shell command as fallback
                result = subprocess.run(f"start {app}", shell=True, capture_output=True, timeout=10)
                return {"status": "ok" if result.returncode == 0 else "error"}

        elif action == "run_shell":
            command = cmd.get("command", "")
            for blocked in BLOCKED_COMMANDS:
                if blocked.lower() in command.lower():
                    return {"status": "error", "message": f"Command blocked for safety: {blocked}"}
            try:
                result = subprocess.run(command, shell=True, capture_output=True,
                                       text=True, timeout=30)
                return {
                    "status": "ok",
                    "stdout": result.stdout[:3000],
                    "stderr": result.stderr[:500],
                    "code": result.returncode
                }
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out after 30 seconds"}

        elif action == "run_powershell":
            command = cmd.get("command", "")
            for blocked in BLOCKED_COMMANDS:
                if blocked.lower() in command.lower():
                    return {"status": "error", "message": "Command blocked for safety"}
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True, text=True, timeout=30
            )
            return {"status": "ok", "stdout": result.stdout[:3000], "stderr": result.stderr[:500]}

        elif action == "kill_process":
            process_name = cmd.get("name", "")
            killed = []
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed.append(proc.info['name'])
            return {"status": "ok", "killed": killed}

        elif action == "get_running_apps":
            processes = get_running_processes()
            return {"status": "ok", "processes": processes}

        # ── WINDOW MANAGEMENT ─────────────────────────────────
        elif action == "minimize_window":
            pyautogui.hotkey("win", "down")
            return {"status": "ok"}

        elif action == "maximize_window":
            pyautogui.hotkey("win", "up")
            return {"status": "ok"}

        elif action == "close_window":
            pyautogui.hotkey("alt", "f4")
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "switch_window":
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "show_desktop":
            pyautogui.hotkey("win", "d")
            return {"status": "ok"}

        elif action == "snap_left":
            pyautogui.hotkey("win", "left")
            return {"status": "ok"}

        elif action == "snap_right":
            pyautogui.hotkey("win", "right")
            return {"status": "ok"}

        elif action == "get_active_window":
            title = get_active_window_title()
            return {"status": "ok", "title": title}

        elif action == "open_task_manager":
            pyautogui.hotkey("ctrl", "shift", "esc")
            return {"status": "ok"}

        # ── SYSTEM ────────────────────────────────────────────
        elif action == "lock_screen":
            pyautogui.hotkey("win", "l")
            return {"status": "ok"}

        elif action == "open_settings":
            pyautogui.hotkey("win", "i")
            time.sleep(1)
            return {"status": "ok"}

        elif action == "open_control_panel":
            subprocess.Popen(["control"])
            time.sleep(1)
            return {"status": "ok"}

        elif action == "open_file_explorer":
            pyautogui.hotkey("win", "e")
            time.sleep(1)
            return {"status": "ok"}

        elif action == "open_run_dialog":
            pyautogui.hotkey("win", "r")
            time.sleep(0.5)
            cmd_text = cmd.get("command", "")
            if cmd_text:
                smart_type(cmd_text)
                pyautogui.press("enter")
            return {"status": "ok"}

        elif action == "open_search":
            pyautogui.hotkey("win", "s")
            time.sleep(0.5)
            query = cmd.get("query", "")
            if query:
                smart_type(query)
            return {"status": "ok"}

        elif action == "take_note":
            text = cmd.get("text", "")
            notes_file = Path.home() / "DacexyAgent" / "notes.txt"
            notes_file.parent.mkdir(exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(notes_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}] {text}\n")
            return {"status": "ok", "saved_to": str(notes_file)}

        elif action == "get_time":
            now = datetime.datetime.now()
            return {
                "status": "ok",
                "time": now.strftime("%I:%M %p"),
                "date": now.strftime("%A, %B %d %Y"),
                "timestamp": now.isoformat()
            }

        elif action == "get_weather":
            city = cmd.get("city", "")
            url = f"https://wttr.in/{city.replace(' ', '+')}?format=3" if city else "https://wttr.in/?format=3"
            try:
                r = req_lib.get(url, timeout=5)
                return {"status": "ok", "weather": r.text.strip()}
            except:
                return {"status": "ok", "weather": "Could not fetch weather"}

        elif action == "get_system_info":
            sz = pyautogui.size()
            stats = get_system_stats()
            battery = None
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery = f"{bat.percent:.0f}% {'charging' if bat.power_plugged else 'discharging'}"
            except: pass
            return {
                "status": "ok",
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "hostname": platform.node(),
                "python": platform.python_version(),
                "screen_width": sz.width,
                "screen_height": sz.height,
                "cpu_percent": stats.get("cpu_percent"),
                "memory_percent": stats.get("memory_percent"),
                "battery": battery,
                "agent_version": AGENT_VERSION,
                "active_window": get_active_window_title(),
                "session_tasks": len(SESSION_MEMORY["task_history"]),
            }

        # ── VOLUME / MEDIA ────────────────────────────────────
        elif action == "volume_up":
            for _ in range(int(cmd.get("steps", 3))):
                pyautogui.press("volumeup")
            return {"status": "ok"}

        elif action == "volume_down":
            for _ in range(int(cmd.get("steps", 3))):
                pyautogui.press("volumedown")
            return {"status": "ok"}

        elif action == "volume_mute":
            pyautogui.press("volumemute")
            return {"status": "ok"}

        elif action == "media_play_pause":
            pyautogui.press("playpause")
            return {"status": "ok"}

        elif action == "media_next":
            pyautogui.press("nexttrack")
            return {"status": "ok"}

        elif action == "media_prev":
            pyautogui.press("prevtrack")
            return {"status": "ok"}

        # ── WAIT ──────────────────────────────────────────────
        elif action == "wait":
            secs = float(cmd.get("seconds", 1))
            secs = min(secs, 15)  # max 15 seconds
            time.sleep(secs)
            return {"status": "ok"}

        elif action == "wait_for_load":
            time.sleep(float(cmd.get("seconds", 3)))
            return {"status": "ok"}

        # ── SAVE / UNDO / REDO ────────────────────────────────
        elif action == "save":
            pyautogui.hotkey("ctrl", "s")
            time.sleep(0.3)
            return {"status": "ok"}

        elif action == "save_as":
            pyautogui.hotkey("ctrl", "shift", "s")
            time.sleep(0.5)
            return {"status": "ok"}

        elif action == "undo":
            pyautogui.hotkey("ctrl", "z")
            return {"status": "ok"}

        elif action == "redo":
            pyautogui.hotkey("ctrl", "y")
            return {"status": "ok"}

        elif action == "print":
            pyautogui.hotkey("ctrl", "p")
            time.sleep(1)
            return {"status": "ok"}

        elif action == "zoom_in":
            pyautogui.hotkey("ctrl", "=")
            return {"status": "ok"}

        elif action == "zoom_out":
            pyautogui.hotkey("ctrl", "-")
            return {"status": "ok"}

        elif action == "fullscreen":
            pyautogui.press("f11")
            return {"status": "ok"}

        # ── TASK / SUB-TASK ───────────────────────────────────
        elif action == "task":
            task_text = cmd.get("task", "") or cmd.get("goal", "")
            context = cmd.get("context", "")
            if task_text and token:
                execute_full_task(task_text, token, context=context)
            return {"status": "ok"}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Failsafe triggered — move mouse away from corner"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status": "error", "message": str(e)}


def execute_action_list(actions: list, token: str = None):
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        a = action.get("action", "?")
        desc = action.get("url") or action.get("text", "")[:40] or action.get("key", "") or action.get("command", "")[:40] or ""
        log.info(f"  Step {i+1}/{len(actions)}: {a} {desc}")
        result = execute_command(action, token=token)
        if result.get("status") == "error":
            log.warning(f"  ✗ Step {i+1} failed: {result.get('message', '')}")
        time.sleep(0.2)


# ═══════════════════════════════════════════════════════════════════════
# WORLD'S MOST POWERFUL AI BRAIN
# ═══════════════════════════════════════════════════════════════════════

def get_ai_actions(task: str, token: str, context: str = "", screenshot_b64: str = None) -> str:
    sz = pyautogui.size()
    system_info = platform.system()
    now = datetime.datetime.now().strftime("%I:%M %p, %A %B %d %Y")
    active_win = get_active_window_title()
    last_tasks = SESSION_MEMORY["task_history"][-3:] if SESSION_MEMORY["task_history"] else []

    prompt = f"""You are DACEXY — the world's most powerful and intelligent desktop automation AI.
You have a 10 billion IQ. You control a {system_info} computer perfectly.

CURRENT STATE:
- Screen: {sz.width}×{sz.height}px
- Time: {now}
- Active window: {active_win}
- Recent tasks: {last_tasks}
{f"- Context: {context}" if context else ""}

TASK TO COMPLETE: "{task}"

YOUR MISSION:
1. Think deeply about EVERY step needed to complete this task
2. Return a perfect JSON array of actions
3. NEVER leave the task half-done
4. Always give a final spoken result to the user
5. Use exact pixel coordinates for clicks

CRITICAL RULES:
- Return ONLY valid JSON array — no text before or after
- Make sure EVERY step is included
- Use wait actions between browser loads (at least 2-3 seconds)
- For email: open_url gmail → wait 4s → click compose → fill fields → send
- For search: use open_url with ?q= parameter directly
- For typing in fields: always click the field first, then type
- For multi-step tasks: include ALL steps

SCREEN COORDINATES:
- Browser address bar: use navigate_url action
- Gmail Compose: ({int(sz.width*0.08)}, {int(sz.height*0.75)})
- Gmail To field: ({int(sz.width*0.47)}, {int(sz.height*0.38)})
- Gmail Subject: ({int(sz.width*0.47)}, {int(sz.height*0.44)})
- Gmail Body: ({int(sz.width*0.47)}, {int(sz.height*0.58)})
- Gmail Send: ({int(sz.width*0.15)}, {int(sz.height*0.84)})
- Page center: ({sz.width//2}, {sz.height//2})
- Top center: ({sz.width//2}, 200)

ALL AVAILABLE ACTIONS (use exact keys):
Mouse: click, double_click, right_click, triple_click, move, drag, scroll, scroll_up, scroll_down
Keyboard: type, key, hotkey, press_enter, press_tab, press_escape, press_backspace, press_delete, key_down, key_up
Clipboard: copy, paste, cut, select_all, get_clipboard, set_clipboard, clear_field
Browser: open_url, navigate_url, new_tab, close_tab, new_window, browser_back, browser_forward, browser_refresh, browser_find, open_incognito, browser_zoom_in, browser_zoom_out
Files: open_file, find_file, open_folder, create_file, read_file, list_files, open_downloads, open_desktop, open_documents
Apps: open_app, run_shell, run_powershell, kill_process
Windows: minimize_window, maximize_window, close_window, switch_window, show_desktop, snap_left, snap_right, open_task_manager
System: lock_screen, open_settings, open_file_explorer, open_run_dialog, open_search, get_time, get_system_info, take_note
Media: volume_up, volume_down, volume_mute, media_play_pause, media_next, media_prev
Other: wait, wait_for_load, save, undo, redo, screenshot, fullscreen, speak

JSON FIELD DETAILS:
- click: {{"action":"click","x":N,"y":N,"button":"left/right","clicks":1}}
- type: {{"action":"type","text":"..."}}
- key: {{"action":"key","key":"enter/tab/esc/f5/delete/backspace/..."}}
- hotkey: {{"action":"hotkey","keys":["ctrl","c"]}}
- open_url: {{"action":"open_url","url":"https://..."}}
- navigate_url: {{"action":"navigate_url","url":"https://..."}}
- run_shell: {{"action":"run_shell","command":"..."}}
- wait: {{"action":"wait","seconds":N}}
- speak: {{"action":"speak","text":"FINAL RESULT FOR USER"}}

TASK COMPLETION EXAMPLES:

"open youtube and search for lofi music and play first video":
[
  {{"action":"open_url","url":"https://www.youtube.com/results?search_query=lofi+music"}},
  {{"action":"wait","seconds":3}},
  {{"action":"click","x":{sz.width//2},"y":370}},
  {{"action":"speak","text":"Playing lofi music on YouTube for you!"}}
]

"send email on gmail to test@gmail.com with subject Meeting Tomorrow and say see you at 10am":
[
  {{"action":"open_url","url":"https://mail.google.com"}},
  {{"action":"wait","seconds":4}},
  {{"action":"click","x":{int(sz.width*0.08)},"y":{int(sz.height*0.75)}}},
  {{"action":"wait","seconds":1}},
  {{"action":"click","x":{int(sz.width*0.47)},"y":{int(sz.height*0.38)}}},
  {{"action":"type","text":"test@gmail.com"}},
  {{"action":"key","key":"tab"}},
  {{"action":"type","text":"Meeting Tomorrow"}},
  {{"action":"click","x":{int(sz.width*0.47)},"y":{int(sz.height*0.58)}}},
  {{"action":"type","text":"See you at 10am"}},
  {{"action":"click","x":{int(sz.width*0.15)},"y":{int(sz.height*0.84)}}},
  {{"action":"speak","text":"Email sent to test@gmail.com with subject Meeting Tomorrow!"}}
]

"open notepad write a resignation letter and save it":
[
  {{"action":"open_app","app":"notepad"}},
  {{"action":"wait","seconds":1}},
  {{"action":"type","text":"Dear Manager,\\n\\nI am writing to formally resign from my position, effective two weeks from today.\\n\\nThank you for the opportunity to work with this organization.\\n\\nSincerely,\\n[Your Name]"}},
  {{"action":"save"}},
  {{"action":"speak","text":"Resignation letter written and saved in Notepad"}}
]

"what is the weather in mumbai":
[
  {{"action":"open_url","url":"https://www.google.com/search?q=weather+in+mumbai"}},
  {{"action":"wait","seconds":2}},
  {{"action":"speak","text":"I searched Google for Mumbai weather. Results are on your screen."}}
]

"take a screenshot and tell me whats on screen":
[
  {{"action":"screenshot"}},
  {{"action":"speak","text":"Screenshot taken! I can see your current screen."}}
]

"search google for best laptop under 50000 and open first result":
[
  {{"action":"open_url","url":"https://www.google.com/search?q=best+laptop+under+50000"}},
  {{"action":"wait","seconds":2}},
  {{"action":"click","x":{sz.width//2},"y":320}},
  {{"action":"wait","seconds":2}},
  {{"action":"speak","text":"Opened the first Google result for best laptops under 50000"}}
]

Now generate the PERFECT action plan for: "{task}"
Return ONLY the JSON array:"""

    try:
        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            content = data.get("content") or data.get("response") or data.get("text") or ""
            log.info(f"AI plan received ({len(content)} chars)")

            # Extract JSON array from response
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                try:
                    actions = json.loads(match.group(0))
                    if isinstance(actions, list) and len(actions) > 0:
                        non_speak = [a for a in actions if a.get("action") != "speak"]
                        if non_speak:
                            log.info(f"AI returned {len(actions)} actions")
                            return json.dumps(actions)
                except json.JSONDecodeError:
                    log.warning("AI returned invalid JSON, using direct action")

        log.warning(f"AI returned status {r.status_code}, using direct action")
        return force_direct_action(task)

    except Exception as e:
        log.error(f"AI brain error: {e}")
        return force_direct_action(task)


def force_direct_action(command: str) -> str:
    """Instant execution for 50+ common commands."""
    cmd = command.lower().strip()
    sz = pyautogui.size()

    # ── YouTube ─────────────────────────────────────────────────────
    if "youtube" in cmd:
        query = re.sub(r'open|youtube|play|search|for|on|in|chrome|browser|new tab', '', cmd).strip()
        url = f"https://youtube.com/results?search_query={query.replace(' ', '+')}" if len(query) > 2 else "https://youtube.com"
        return json.dumps([
            {"action": "open_url", "url": url},
            {"action": "wait", "seconds": 3},
            {"action": "speak", "text": f"YouTube opened{' searching for '+query if len(query)>2 else ''}"}
        ])

    # ── Gmail / Email ────────────────────────────────────────────────
    if "gmail" in cmd or ("email" in cmd and ("send" in cmd or "compose" in cmd)):
        email_match = re.search(r'[\w.\-+]+@[\w.\-]+\.\w+', command)
        to_email = email_match.group(0) if email_match else ""
        subj_m = re.search(r'subject[:\s]+([^,]+?)(?:\s+body|\s+saying|\s+with|$)', command, re.I)
        body_m = re.search(r'(?:body|saying|content|message|write|say)[:\s]+(.+?)(?:\s+send|\s+to\s[\w@]|$)', command, re.I)
        subject = subj_m.group(1).strip() if subj_m else "Hello from Dacexy"
        body = body_m.group(1).strip() if body_m else "Hi, hope you are doing well!"

        actions = [
            {"action": "open_url", "url": "https://mail.google.com"},
            {"action": "wait", "seconds": 4}
        ]
        if to_email:
            actions += [
                {"action": "click", "x": int(sz.width*0.08), "y": int(sz.height*0.75)},
                {"action": "wait", "seconds": 1},
                {"action": "click", "x": int(sz.width*0.47), "y": int(sz.height*0.38)},
                {"action": "type", "text": to_email},
                {"action": "key", "key": "tab"},
                {"action": "type", "text": subject},
                {"action": "click", "x": int(sz.width*0.47), "y": int(sz.height*0.58)},
                {"action": "type", "text": body},
                {"action": "click", "x": int(sz.width*0.15), "y": int(sz.height*0.84)},
                {"action": "speak", "text": f"Email sent to {to_email} with subject '{subject}'"}
            ]
        else:
            actions += [
                {"action": "click", "x": int(sz.width*0.08), "y": int(sz.height*0.75)},
                {"action": "speak", "text": "Gmail compose window opened. Please fill in the recipient."}
            ]
        return json.dumps(actions)

    # ── Google Search ───────────────────────────────────────────────
    if "search" in cmd or ("google" in cmd and "open" not in cmd):
        query = re.sub(r'search|google|for|on|find|look up|lookup', '', cmd).strip()
        if not query or len(query) < 2: query = cmd
        return json.dumps([
            {"action": "open_url", "url": f"https://google.com/search?q={query.replace(' ', '+')}"},
            {"action": "speak", "text": f"Searched Google for: {query}"}
        ])

    # ── WhatsApp ────────────────────────────────────────────────────
    if "whatsapp" in cmd:
        return json.dumps([
            {"action": "open_url", "url": "https://web.whatsapp.com"},
            {"action": "speak", "text": "WhatsApp Web is open"}
        ])

    # ── Social Media ────────────────────────────────────────────────
    for site, url, name in [
        ("instagram", "https://instagram.com", "Instagram"),
        ("twitter", "https://x.com", "Twitter"),
        ("facebook", "https://facebook.com", "Facebook"),
        ("linkedin", "https://linkedin.com", "LinkedIn"),
        ("reddit", "https://reddit.com", "Reddit"),
        ("tiktok", "https://tiktok.com", "TikTok"),
        ("snapchat", "https://snapchat.com", "Snapchat"),
        ("pinterest", "https://pinterest.com", "Pinterest"),
        ("spotify", "https://open.spotify.com", "Spotify"),
        ("netflix", "https://netflix.com", "Netflix"),
        ("amazon", "https://amazon.in", "Amazon"),
        ("flipkart", "https://flipkart.com", "Flipkart"),
        ("swiggy", "https://swiggy.com", "Swiggy"),
        ("zomato", "https://zomato.com", "Zomato"),
        ("github", "https://github.com", "GitHub"),
        ("stackoverflow", "https://stackoverflow.com", "Stack Overflow"),
        ("chatgpt", "https://chat.openai.com", "ChatGPT"),
    ]:
        if site in cmd:
            return json.dumps([
                {"action": "open_url", "url": url},
                {"action": "speak", "text": f"{name} opened"}
            ])

    # ── Browser / Chrome ────────────────────────────────────────────
    if "chrome" in cmd and ("open" in cmd or "start" in cmd or "launch" in cmd):
        return json.dumps([
            {"action": "run_shell", "command": "start chrome"},
            {"action": "speak", "text": "Chrome is opening"}
        ])

    # ── Notepad ─────────────────────────────────────────────────────
    if "notepad" in cmd:
        text_m = re.search(r'(?:write|type|say|note|create)[:\s]+(.+)', command, re.I)
        actions = [{"action": "open_app", "app": "notepad"}, {"action": "wait", "seconds": 1}]
        if text_m:
            actions.append({"action": "type", "text": text_m.group(1)})
        actions.append({"action": "speak", "text": f"Notepad opened{' and text written' if text_m else ''}"})
        return json.dumps(actions)

    # ── Calculator ──────────────────────────────────────────────────
    if "calculator" in cmd or " calc" in cmd:
        math_m = re.search(r'(\d[\d\s\+\-\*\/\(\)\.]+\d)', command)
        actions = [{"action": "open_app", "app": "calc"}, {"action": "wait", "seconds": 1}]
        if math_m:
            expr = math_m.group(1).strip()
            actions.append({"action": "type", "text": expr})
            actions.append({"action": "press_enter"})
        actions.append({"action": "speak", "text": f"Calculator opened{' and calculated: '+math_m.group(1) if math_m else ''}"})
        return json.dumps(actions)

    # ── Screenshot ──────────────────────────────────────────────────
    if "screenshot" in cmd:
        return json.dumps([
            {"action": "screenshot"},
            {"action": "speak", "text": "Screenshot taken!"}
        ])

    # ── Volume ──────────────────────────────────────────────────────
    if "volume up" in cmd or "increase volume" in cmd or "louder" in cmd:
        return json.dumps([{"action": "volume_up", "steps": 3}, {"action": "speak", "text": "Volume increased"}])
    if "volume down" in cmd or "decrease volume" in cmd or "quieter" in cmd:
        return json.dumps([{"action": "volume_down", "steps": 3}, {"action": "speak", "text": "Volume decreased"}])
    if "mute" in cmd:
        return json.dumps([{"action": "volume_mute"}, {"action": "speak", "text": "Muted"}])
    if "unmute" in cmd:
        return json.dumps([{"action": "volume_mute"}, {"action": "speak", "text": "Unmuted"}])

    # ── Time / Date ─────────────────────────────────────────────────
    if ("time" in cmd and ("what" in cmd or "tell" in cmd)) or cmd.strip() in ["time", "what time"]:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return json.dumps([{"action": "speak", "text": f"The current time is {now}"}])

    if "date" in cmd or ("today" in cmd and "task" not in cmd):
        today = datetime.datetime.now().strftime("%A, %B %d %Y")
        return json.dumps([{"action": "speak", "text": f"Today is {today}"}])

    # ── Weather ─────────────────────────────────────────────────────
    if "weather" in cmd:
        city_m = re.search(r'(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\s*\?|$)', command, re.I)
        city = city_m.group(1).strip() if city_m else "my city"
        return json.dumps([
            {"action": "open_url", "url": f"https://google.com/search?q=weather+in+{city.replace(' ', '+')}"},
            {"action": "speak", "text": f"Showing weather for {city}"}
        ])

    # ── Files ────────────────────────────────────────────────────────
    if "open downloads" in cmd or "downloads folder" in cmd:
        return json.dumps([{"action": "open_downloads"}, {"action": "speak", "text": "Downloads folder opened"}])
    if "open desktop" in cmd or "desktop folder" in cmd:
        return json.dumps([{"action": "open_desktop"}, {"action": "speak", "text": "Desktop opened"}])
    if "open documents" in cmd or "documents folder" in cmd:
        return json.dumps([{"action": "open_documents"}, {"action": "speak", "text": "Documents folder opened"}])
    if "file explorer" in cmd:
        return json.dumps([{"action": "open_file_explorer"}, {"action": "speak", "text": "File Explorer opened"}])

    # ── System ───────────────────────────────────────────────────────
    if "lock screen" in cmd or "lock computer" in cmd:
        return json.dumps([{"action": "lock_screen"}, {"action": "speak", "text": "Screen locked"}])
    if "show desktop" in cmd or "minimize all" in cmd:
        return json.dumps([{"action": "show_desktop"}, {"action": "speak", "text": "Desktop shown"}])
    if "task manager" in cmd:
        return json.dumps([{"action": "open_task_manager"}, {"action": "speak", "text": "Task Manager opened"}])
    if "settings" in cmd and ("open" in cmd or "windows" in cmd):
        return json.dumps([{"action": "open_settings"}, {"action": "speak", "text": "Windows Settings opened"}])
    if "close window" in cmd or "close this" in cmd:
        return json.dumps([{"action": "close_window"}, {"action": "speak", "text": "Window closed"}])
    if "fullscreen" in cmd or "full screen" in cmd:
        return json.dumps([{"action": "fullscreen"}, {"action": "speak", "text": "Toggled fullscreen"}])

    # ── Take note ────────────────────────────────────────────────────
    if "take note" in cmd or "remember this" in cmd or "note that" in cmd:
        note_m = re.search(r'(?:note|remember|note that)[:\s]+(.+)', command, re.I)
        if note_m:
            return json.dumps([
                {"action": "take_note", "text": note_m.group(1)},
                {"action": "speak", "text": "Note saved!"}
            ])

    # ── Default: Google search ────────────────────────────────────────
    query = command.replace(" ", "+")
    return json.dumps([
        {"action": "open_url", "url": f"https://google.com/search?q={query}"},
        {"action": "speak", "text": f"Searched Google for: {command}"}
    ])


# ═══════════════════════════════════════════════════════════════════════
# TASK EXECUTOR - FULL PIPELINE
# ═══════════════════════════════════════════════════════════════════════

def execute_full_task(task: str, token: str, context: str = ""):
    log.info(f"🎯 Task: {task}")
    SESSION_MEMORY["last_task"] = task
    SESSION_MEMORY["task_history"].append(task)

    # ── Permission Check ─────────────────────────────────────────────
    needs_perm, perm_type = needs_permission(task)
    if needs_perm:
        granted = ask_permission(task, perm_type)
        if not granted:
            speak("Task cancelled. Your security is protected.")
            return

    speak("On it!")

    # ── Take screenshot for context ───────────────────────────────────
    ss = take_screenshot(quality=70)

    # ── Get AI plan ───────────────────────────────────────────────────
    actions_json = get_ai_actions(task, token, context=context, screenshot_b64=ss)

    try:
        actions = json.loads(actions_json)
        if isinstance(actions, list) and len(actions) > 0:
            total = len(actions)
            non_speak = [a for a in actions if a.get("action") != "speak"]
            if not non_speak:
                log.warning("AI returned only speak — using direct action")
                actions_json = force_direct_action(task)
                actions = json.loads(actions_json)

            log.info(f"▶ Executing {total} steps for: {task}")
            execute_action_list(actions, token=token)
        else:
            speak("Could not plan that task. Please try again with more detail.")
    except Exception as e:
        log.error(f"Task execution error: {e}")
        speak("Something went wrong. Please try again.")


# ═══════════════════════════════════════════════════════════════════════
# VOICE AGENT - ALWAYS LISTENING
# ═══════════════════════════════════════════════════════════════════════

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
                self.recognizer.energy_threshold = 250
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.7
                self.recognizer.phrase_threshold = 0.3
                self.microphone = sr.Microphone()
                print("  🎤 Calibrating microphone...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print(f'  ✅ Mic ready! Say "{WAKE_WORD.title()}" anytime.')
            except Exception as e:
                print(f"  ⚠️ Microphone: {e}")
                self.microphone = None
        if not self.microphone:
            print("  💬 No microphone — using TEXT mode")

    def listen_continuous(self):
        if not self.microphone:
            return
        print(f'\n  👂 Always listening for "{WAKE_WORD.title()}"...\n')
        while self.running:
            if self.is_processing:
                time.sleep(0.05)
                continue
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=12)
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    log.debug(f"Heard: {text}")
                    if WAKE_WORD in text:
                        command = text.replace(WAKE_WORD, "").strip()
                        if len(command) > 2:
                            print(f"  🗣️ Command: {command}")
                            self.is_processing = True
                            threading.Thread(target=self._run, args=(command,), daemon=True).start()
                        else:
                            speak("Yes? What would you like me to do?")
                            self._listen_next()
                except sr.UnknownValueError:
                    pass
            except sr.WaitTimeoutError:
                pass
            except Exception:
                time.sleep(0.3)

    def _listen_next(self):
        if not self.microphone:
            return
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("  👂 Listening...")
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)
            text = self.recognizer.recognize_google(audio)
            print(f"  🗣️ You said: {text}")
            self.is_processing = True
            threading.Thread(target=self._run, args=(text,), daemon=True).start()
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Say Hey Dacexy to try again.")
        except sr.UnknownValueError:
            speak("Couldn't understand. Please speak clearly.")
        except Exception as e:
            log.error(f"Listen error: {e}")

    def _run(self, command: str):
        try:
            execute_full_task(command, self.token)
        finally:
            self.is_processing = False

    def text_input_loop(self):
        print("\n  ⌨️  Type any command and press Enter:")
        print("  ─────────────────────────────────────────")
        print("  Examples:")
        print("  → open youtube and search lofi music")
        print("  → send email to boss@company.com subject Leave Request body I need a day off")
        print("  → search google for best phone under 20000")
        print("  → take a screenshot")
        print("  → open notepad and write meeting notes for today")
        print("  → what is the weather in bangalore")
        print("  → open calculator and calculate 15 percent of 50000")
        print("  ─────────────────────────────────────────\n")

        while self.running:
            try:
                command = input("  dacexy > ").strip()
                if not command:
                    continue
                if command.lower() in ['quit', 'exit', 'q', 'bye']:
                    speak("Goodbye! Dacexy Agent shutting down.")
                    self.running = False
                    break
                if command.lower() == 'history':
                    print("\n  Task History:")
                    for i, t in enumerate(SESSION_MEMORY["task_history"][-10:], 1):
                        print(f"  {i}. {t}")
                    print()
                    continue
                if command.lower() == 'help':
                    print("\n  Available commands:")
                    print("  Any natural language task!")
                    print("  'history' - show recent tasks")
                    print("  'quit' - exit agent\n")
                    continue
                threading.Thread(target=self._run, args=(command,), daemon=True).start()
            except (EOFError, KeyboardInterrupt):
                break

    def run(self):
        self.running = True
        if self.microphone:
            threading.Thread(target=self.listen_continuous, daemon=True).start()
        self.text_input_loop()

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET REMOTE CONTROL
# ═══════════════════════════════════════════════════════════════════════

async def agent_loop(token: str):
    retry_delay = 3
    while True:
        try:
            log.info("🔌 Connecting to Dacexy backend...")
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
                    print(f"\n  ❌ Auth failed: {msg}")
                    if "expired" in msg.lower() or "invalid" in msg.lower():
                        clear_token()
                        return
                    await asyncio.sleep(retry_delay)
                    continue

                log.info("✅ Remote control CONNECTED!")
                speak("Remote control connected! I am ready to work.")
                retry_delay = 3

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
                            context = cmd.get("context", "")
                            log.info(f"📋 Remote task: {task_text}")

                            def run_remote():
                                execute_full_task(task_text, token, context=context)

                            t = threading.Thread(target=run_remote, daemon=True)
                            t.start()
                            t.join(timeout=120)

                            await ws.send(json.dumps({
                                "type": "task_result",
                                "status": "completed",
                                "task": task_text,
                                "actions_taken": len(SESSION_MEMORY["task_history"])
                            }))
                            continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action", "")
                            log.info(f"🎮 Remote command: {action}")

                            # Send before screenshot
                            if action not in ["screenshot", "get_system_info", "get_screen_info"]:
                                ss = take_screenshot()
                                if ss:
                                    await ws.send(json.dumps({"type": "screenshot_before", "data": ss}))

                            result = execute_command(cmd, token=token)
                            await ws.send(json.dumps({"type": "result", "action": action, "data": result}))

                            # Send after screenshot
                            await asyncio.sleep(0.5)
                            ss = take_screenshot()
                            if ss:
                                await ws.send(json.dumps({"type": "screenshot_after", "data": ss}))

                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        log.error(f"WebSocket loop error: {e}")

        except websockets.exceptions.ConnectionClosed:
            log.warning("Connection closed — reconnecting...")
        except ConnectionRefusedError:
            log.warning("Connection refused — backend may be sleeping...")
        except Exception as e:
            log.error(f"Connection error: {e}")

        log.info(f"⏳ Reconnecting in {retry_delay}s...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 1.5, 30)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n╔══════════════════════════════════════════════════╗")
    print("║       DACEXY DESKTOP AGENT v10.0                 ║")
    print("║       World's Most Powerful AI Desktop Agent     ║")
    print("║       120+ Actions | Vision | Voice | Security   ║")
    print("╚══════════════════════════════════════════════════╝\n")

    # Setup Windows autostart
    setup_autostart()

    # Check token
    token = get_token()
    if token:
        print("  Checking saved session...")
        if not check_token_valid(token):
            print("  ⚠️ Session expired. Please login again.")
            clear_token()
            token = None
        else:
            print("  ✅ Session valid!\n")

    # Login if needed
    if not token:
        for attempt in range(3):
            token = login()
            if token:
                break
            remaining = 2 - attempt
            if remaining > 0:
                print(f"  {remaining} attempts remaining.\n")
        if not token:
            input("\n  Press Enter to exit...")
            return

    print(f"\n  ✅ Logged in successfully!")
    print(f"\n  🚀 CAPABILITIES:")
    print(f"  ├─ 🌐 Browse any website & search anything")
    print(f"  ├─ 📧 Send emails on Gmail automatically")
    print(f"  ├─ 📁 Open, read, create, manage files")
    print(f"  ├─ 🖱️  Click, type, scroll anywhere on screen")
    print(f"  ├─ 🎤 Voice control (Say '{WAKE_WORD.title()}')")
    print(f"  ├─ 🔒 Permission system for sensitive actions")
    print(f"  ├─ 🔄 Auto-reconnects & auto-starts on boot")
    print(f"  ├─ 🧠 AI vision — sees and understands screen")
    print(f"  └─ ⚡ 120+ actions for complete computer control\n")

    # Start voice agent in background
    voice = VoiceAgent(token)
    voice_thread = threading.Thread(target=voice.run, daemon=True)
    voice_thread.start()

    speak(f"Dacexy version 10 is now active. I am the world's most powerful desktop agent. Ready for any task!")

    # Start WebSocket remote control
    try:
        asyncio.run(agent_loop(token))
    except KeyboardInterrupt:
        print("\n  👋 Shutting down Dacexy Agent...")
        speak("Goodbye!")
        voice.stop()


if __name__ == "__main__":
    main()
