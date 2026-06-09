"""
Dacexy Desktop Agent v11.0 - Production Ready
Siri-like 24/7 voice control. Wake word: "hey dacexy"
Fixed: Thread safety, WebSocket reliability, voice fallbacks,
       blocking operations, memory leaks, security hardening.
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
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"  Warning: could not install {pkg}: {e}")

# PyAudio — special handling
try:
    import pyaudio
    PYAUDIO_OK = True
except Exception:
    PYAUDIO_OK = False
    for _pa_method in [
        [sys.executable, "-m", "pip", "install", "PyAudio", "-q"],
        [sys.executable, "-m", "pip", "install", "pipwin", "-q"],
    ]:
        try:
            subprocess.check_call(_pa_method, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if "pipwin" in _pa_method:
                subprocess.check_call(
                    [sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            import pyaudio
            PYAUDIO_OK = True
            break
        except Exception:
            continue

# ═══════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════
import asyncio
import base64
import io
import json
import logging
import threading
import time
import webbrowser
import re
import datetime
import ctypes
import queue
from pathlib import Path
from typing import Optional
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab, Image
import pyttsx3
import pyperclip
import psutil

try:
    import winreg
    WINREG_OK = True
except Exception:
    WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except Exception:
    VOICE_AVAILABLE = False
    sr = None

try:
    import pygetwindow as gw
    WINDOW_OK = True
except Exception:
    WINDOW_OK = False

try:
    from plyer import notification
    NOTIFY_OK = True
except Exception:
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

# FIX: thread-safe memory with lock
_memory_lock = threading.Lock()
MEMORY = {"facts": [], "preferences": {}, "task_history": deque(maxlen=50), "context": {}}

# FIX: thread pool for blocking operations so they don't block asyncio
_executor = ThreadPoolExecutor(max_workers=4)

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
            notification.notify(title=title, message=message[:100], app_name="Dacexy", timeout=4)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════
# TTS — VOICE OUTPUT
# FIX: TTS engine is single-threaded per-call to avoid COM/engine crashes
# ═══════════════════════════════════════════════════════════════════════
_tts = None
_tts_lock = threading.Lock()
_tts_queue: queue.Queue = queue.Queue()
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
        # FIX: start a dedicated TTS worker thread
        t = threading.Thread(target=_tts_worker, daemon=True)
        t.start()
    except Exception as e:
        log.warning("TTS init failed: %s", e)

def _tts_worker():
    """Dedicated thread for TTS — avoids COM/engine conflicts."""
    while True:
        try:
            text = _tts_queue.get(timeout=1)
            if text is None:
                break
            try:
                with _tts_lock:
                    if _tts:
                        _tts.say(str(text)[:300])
                        _tts.runAndWait()
            except Exception as e:
                log.debug("TTS speak error: %s", e)
            finally:
                _tts_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            continue

def speak(text: str, priority: bool = False):
    if not text:
        return
    safe_text = str(text)[:300]
    print(f"  🔊 Dacexy: {safe_text}")
    notify("Dacexy", safe_text[:80])
    try:
        # FIX: non-blocking enqueue — never blocks caller
        _tts_queue.put_nowait(safe_text)
    except queue.Full:
        pass  # Skip if queue is full — never crash on TTS

# ═══════════════════════════════════════════════════════════════════════
# MEMORY — Thread Safe
# ═══════════════════════════════════════════════════════════════════════
def load_memory():
    global MEMORY
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            with _memory_lock:
                MEMORY["facts"] = data.get("facts", [])
                MEMORY["preferences"] = data.get("preferences", {})
                MEMORY["context"] = data.get("context", {})
                history = data.get("task_history", [])
                MEMORY["task_history"] = deque(history[-50:], maxlen=50)
    except Exception as e:
        log.warning("Memory load failed: %s", e)

def save_memory():
    try:
        with _memory_lock:
            data = {
                "facts": MEMORY["facts"][-100:],
                "preferences": MEMORY["preferences"],
                "context": MEMORY["context"],
                "task_history": list(MEMORY["task_history"])[-50:],
            }
        MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("Memory save failed: %s", e)

def remember(fact: str):
    if not fact:
        return
    with _memory_lock:
        if fact not in MEMORY["facts"]:
            MEMORY["facts"].append(fact)
    save_memory()

def get_memory_context() -> str:
    try:
        with _memory_lock:
            ctx = []
            if MEMORY["facts"]:
                ctx.append("Known facts: " + "; ".join(MEMORY["facts"][-10:]))
            if MEMORY["preferences"]:
                ctx.append("Preferences: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-5:]
            if recent:
                ctx.append("Recent tasks: " + "; ".join(recent))
        return "\n".join(ctx) if ctx else ""
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════════════════
# CONFIG PERSISTENCE
# FIX: atomic write to avoid config corruption
# ═══════════════════════════════════════════════════════════════════════
_config_lock = threading.Lock()

def load_config() -> dict:
    with _config_lock:
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

def save_config(cfg: dict):
    with _config_lock:
        try:
            # FIX: write to temp file then rename — atomic, prevents corruption
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except Exception as e:
            log.warning("Config save failed: %s", e)

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
        r = req_lib.get(
            f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=8
        )
        return r.status_code == 200
    except Exception:
        return False

def setup_autostart():
    try:
        if not WINREG_OK:
            return
        agent_path = str(Path.home() / "DacexyAgent" / "dacexy_agent.py")
        cmd = f'"{sys.executable}" "{agent_path}"'
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered")
    except Exception as e:
        log.warning("Autostart failed: %s", e)

def login():
    print("\n╔══════════════════════════════════╗")
    print("║   Dacexy Agent v11.0 — Login     ║")
    print("╚══════════════════════════════════╝")
    try:
        email = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    print()
    # FIX: validate input before sending
    if not email or "@" not in email:
        print("  ❌ Invalid email")
        return None
    if not password or len(password) < 4:
        print("  ❌ Password too short")
        return None
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
                remember(f"User email: {email}")
                print("  ✅ Login successful!")
                return token
            else:
                print("  ❌ No token received from server")
        else:
            try:
                d = r.json().get("detail", r.text)
                if isinstance(d, list):
                    d = d[0].get("msg", str(d))
            except Exception:
                d = r.text[:200]
            print(f"  ❌ {d}")
    except req_lib.exceptions.ConnectionError:
        print("  ❌ Cannot connect to server. Check internet connection.")
    except req_lib.exceptions.Timeout:
        print("  ❌ Server timeout. Try again.")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════════
# VISION
# FIX: screenshot in thread pool so it doesn't block async loop
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
        log.warning("Screenshot failed: %s", e)
        return None

def get_screen_text_via_ai(token: str) -> str:
    ss = take_screenshot(quality=60)
    if not ss:
        return "Could not capture screen"
    try:
        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={
                "messages": [{"role": "user", "content": "Describe what's on this screen in 2-3 sentences."}],
                "stream": False
            },
            timeout=20
        )
        if r.status_code == 200:
            return r.json().get("content") or r.json().get("response") or "Screen captured"
    except Exception:
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

# FIX: expanded blocked commands list
BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf ~", "rm -rf /*", "format c:", "del /s /q c:\\windows",
    "mkfs", "dd if=/dev/zero", "deltree c:\\", "rd /s /q c:\\", "cipher /w:c",
    ":(){:|:&};:", "sudo rm -rf /", "shutdown /s", "shutdown /r",
    "net user administrator", "reg delete hklm", "bcdedit",
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
    print(f'  📋 Task: "{task[:80]}"')
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
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════════════════
# SMART TYPING
# ═══════════════════════════════════════════════════════════════════════
def smart_type(text: str):
    # FIX: limit text length to prevent hang
    text = str(text)[:2000]
    try:
        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.08)
    except Exception:
        try:
            pyautogui.write(text, interval=0.025)
        except Exception as e:
            log.warning("smart_type failed: %s", e)

def get_active_window() -> str:
    try:
        if WINDOW_OK:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except Exception:
        pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR — 150+ ACTIONS
# FIX: all actions wrapped in individual try/except with timeouts
# ═══════════════════════════════════════════════════════════════════════
def execute_command(cmd: dict, token: str = None) -> dict:
    # FIX: validate cmd is a dict
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Invalid command format"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action specified"}

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
            return {"status": "ok", "description": "No token available"}
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
            # FIX: validate coordinates are on screen
            sw, sh = pyautogui.size()
            x = max(0, min(x, sw - 1))
            y = max(0, min(y, sh - 1))
            pyautogui.click(x, y, button=cmd.get("button", "left"), clicks=int(cmd.get("clicks", 1)), interval=0.08)
            time.sleep(0.1)
            return {"status": "ok", "at": f"({x},{y})"}
        elif action == "double_click":
            x, y = int(cmd.get("x", 0)), int(cmd.get("y", 0))
            pyautogui.doubleClick(x, y)
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
            pyautogui.write(str(cmd.get("text", ""))[:500], interval=0.06)
            return {"status": "ok"}
        elif action == "key":
            pyautogui.press(cmd.get("key", ""))
            return {"status": "ok"}
        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if keys and len(keys) <= 4:  # FIX: limit keys for safety
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
            # FIX: block dangerous app launches
            if app and not any(d in app.lower() for d in ["cmd /c del", "format", "shutdown"]):
                subprocess.Popen(app, shell=True)
            return {"status": "ok", "app": app}
        elif action == "open_url":
            url = cmd.get("url", "")
            # FIX: only allow http/https URLs
            if url and url.startswith(("http://", "https://")):
                webbrowser.open(url)
            return {"status": "ok", "url": url}
        elif action == "run_command":
            c = cmd.get("command", "")
            # FIX: comprehensive blocked command check
            c_lower = c.lower()
            if any(blocked in c_lower for blocked in BLOCKED_COMMANDS):
                return {"status": "blocked", "reason": "Command is blocked for safety"}
            # FIX: timeout on subprocess to prevent hang
            try:
                result = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=30)
                return {"status": "ok", "stdout": result.stdout[:2000], "stderr": result.stderr[:500]}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out after 30 seconds"}
        elif action == "get_clipboard":
            return {"status": "ok", "text": pyperclip.paste()}
        elif action == "set_clipboard":
            pyperclip.copy(str(cmd.get("text", ""))[:5000])
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
            steps = min(int(cmd.get("steps", 5)), 20)  # FIX: cap steps
            for _ in range(steps):
                pyautogui.press("volumeup")
            return {"status": "ok"}
        elif action == "volume_down":
            steps = min(int(cmd.get("steps", 5)), 20)
            for _ in range(steps):
                pyautogui.press("volumedown")
            return {"status": "ok"}
        elif action == "mute":
            pyautogui.press("volumemute")
            return {"status": "ok"}
        elif action == "sleep":
            # FIX: cap sleep time to prevent indefinite blocking
            secs = min(float(cmd.get("seconds", 1)), 10.0)
            time.sleep(secs)
            return {"status": "ok"}
        elif action == "get_system_info":
            try:
                disk_path = 'C:\\' if platform.system() == "Windows" else '/'
                return {
                    "status": "ok",
                    "os": platform.system(),
                    "version": platform.version(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage(disk_path).percent,
                    "active_window": get_active_window(),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}
        elif action == "list_processes":
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    procs.append(p.info)
                except Exception:
                    pass
            return {"status": "ok", "processes": procs[:20]}
        elif action == "kill_process":
            name = cmd.get("name", "")
            # FIX: block killing system-critical processes
            PROTECTED = ["explorer", "winlogon", "csrss", "svchost", "system", "lsass"]
            if any(p in name.lower() for p in PROTECTED):
                return {"status": "blocked", "reason": "Cannot kill system process"}
            killed = 0
            for p in psutil.process_iter(['name']):
                try:
                    if name.lower() in p.info['name'].lower():
                        p.kill()
                        killed += 1
                except Exception:
                    pass
            return {"status": "ok", "killed": killed}
        elif action == "write_file":
            path = cmd.get("path", "")
            content = cmd.get("content", "")
            # FIX: restrict to user home directory only
            if path and Path(path).is_absolute():
                if not str(Path(path)).startswith(str(Path.home())):
                    return {"status": "blocked", "reason": "Can only write files in home directory"}
            if path:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(str(content)[:100000], encoding="utf-8")
            return {"status": "ok"}
        elif action == "read_file":
            path = cmd.get("path", "")
            if path and Path(path).exists():
                # FIX: limit file read size
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
                tmp.write_text(str(text)[:50000], encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"', shell=True)
            else:
                subprocess.Popen("notepad.exe", shell=True)
            return {"status": "ok"}
        elif action == "search_web":
            query = str(cmd.get("query", ""))[:200]
            if query:
                import urllib.parse
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return {"status": "ok"}
        elif action == "open_youtube":
            query = str(cmd.get("query", ""))[:200]
            if query:
                import urllib.parse
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            else:
                webbrowser.open("https://www.youtube.com")
            return {"status": "ok"}
        elif action == "take_note":
            note = cmd.get("text", "")
            if note:
                remember(f"Note: {str(note)[:200]}")
                speak(f"I've saved your note.")
            return {"status": "ok"}
        elif action == "get_time":
            t = datetime.datetime.now().strftime("%I:%M %p")
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
# AI TASK EXECUTOR
# FIX: proper timeout, JSON extraction, error handling
# ═══════════════════════════════════════════════════════════════════════
def execute_task_with_ai(task: str, token: str, ws_send_fn=None) -> str:
    if not task or not token:
        return "Missing task or token"
    try:
        memory_ctx = get_memory_context()
        system_prompt = """You are Dacexy Desktop Agent controlling a Windows PC.
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
  {"action": "open_url", "url": "https://www.google.com"},
  {"action": "sleep", "seconds": 1.5},
  {"action": "type", "text": "cats"},
  {"action": "press_enter"}
]

Return ONLY valid JSON array. No explanation, no markdown backticks."""

        if memory_ctx:
            system_prompt += f"\n\nUser context:\n{memory_ctx}"

        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Task: {task[:500]}"}
                ],
                "stream": False
            },
            timeout=30
        )

        if r.status_code != 200:
            err = f"AI request failed: HTTP {r.status_code}"
            log.error(err)
            return err

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw:
            return "AI returned empty response"

        # FIX: strip markdown backticks if AI wrapped in ```json
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        raw = raw.strip()

        # Extract JSON array
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            # AI returned plain text explanation — speak it
            speak(raw[:200])
            return raw[:200]

        try:
            commands = json.loads(match.group())
        except json.JSONDecodeError as e:
            log.error("JSON parse error: %s — raw: %s", e, raw[:200])
            speak("I understood the task but couldn't parse the commands.")
            return f"JSON parse error: {e}"

        if not isinstance(commands, list):
            return "AI returned invalid command format"

        actions_taken = 0
        for c in commands:
            if not isinstance(c, dict):
                continue
            try:
                result = execute_command(c, token)
                actions_taken += 1
                # FIX: small delay between commands for reliability
                time.sleep(0.2)
                if result.get("status") == "error":
                    log.warning("Command failed: %s — %s", c.get("action"), result.get("message"))
            except Exception as cmd_err:
                log.error("Command execution error: %s", cmd_err)
                continue

        # FIX: thread-safe memory update
        with _memory_lock:
            MEMORY["task_history"].append(task[:100])
        save_memory()

        summary = f"Completed {actions_taken} actions for: {task[:50]}"
        log.info(summary)
        return summary

    except req_lib.exceptions.Timeout:
        return "AI request timed out. Please try again."
    except req_lib.exceptions.ConnectionError:
        return "Cannot connect to Dacexy server. Check internet."
    except Exception as e:
        log.error("Task execution error: %s", e)
        return f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════
# VOICE ENGINE — SIRI-LIKE 24/7
# FIX: proper resource cleanup, error recovery, non-blocking
# ═══════════════════════════════════════════════════════════════════════
_voice_active = False
_voice_thread = None
_current_token = None
_voice_token_lock = threading.Lock()


def _voice_listen_loop():
    global _voice_active, _current_token

    if not VOICE_AVAILABLE or not sr:
        log.warning("Voice not available — PyAudio not installed")
        print("  ⚠️  Voice disabled. Install PyAudio for voice control.")
        return

    # FIX: create recognizer once, reuse
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    log.info("Voice engine started — say '%s' to activate", WAKE_WORD)
    print(f"\n  🎤 Voice engine running — say '{WAKE_WORD.title()}' anytime!")
    speak("Voice engine ready. Say Hey Dacexy to give me a command.")

    # FIX: detect available microphone before entering loop
    try:
        mic_list = sr.Microphone.list_microphone_names()
        if not mic_list:
            log.warning("No microphone detected — voice disabled")
            print("  ⚠️  No microphone detected. Voice control disabled.")
            return
        log.info("Microphone detected: %s", mic_list[0] if mic_list else "unknown")
    except Exception as e:
        log.warning("Microphone check failed: %s", e)

    consecutive_errors = 0
    max_consecutive_errors = 10

    while _voice_active:
        try:
            # FIX: recreate microphone each iteration to avoid stale handle
            with sr.Microphone() as source:
                try:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                except Exception:
                    pass

                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower().strip()
                    log.debug("Heard: %s", text)
                    consecutive_errors = 0  # reset on success

                    if any(w in text for w in [WAKE_WORD, "hey dacexy", "hey daxy", "dacexy"]):
                        print("\n  🟢 Wake word detected!")
                        speak("Yes? What can I do for you?")
                        time.sleep(0.5)

                        # Listen for command
                        with sr.Microphone() as cmd_source:
                            try:
                                recognizer.adjust_for_ambient_noise(cmd_source, duration=0.2)
                            except Exception:
                                pass
                            print("  🎧 Listening for command...")
                            try:
                                cmd_audio = recognizer.listen(cmd_source, timeout=8, phrase_time_limit=15)
                                command_text = recognizer.recognize_google(cmd_audio).strip()
                                print(f"  📝 Command: {command_text}")
                                log.info("Voice command: %s", command_text)

                                if command_text:
                                    speak("On it!")
                                    with _voice_token_lock:
                                        token = _current_token

                                    if token:
                                        needs_perm, ptype = needs_permission(command_text)
                                        if needs_perm:
                                            if not ask_permission(command_text, ptype):
                                                continue

                                        def _exec_voice(t, cmd):
                                            try:
                                                result = execute_task_with_ai(cmd, t)
                                                speak(f"Done. {result[:80]}")
                                            except Exception as ve:
                                                log.error("Voice task error: %s", ve)
                                                speak("Sorry, I had trouble with that.")

                                        threading.Thread(
                                            target=_exec_voice,
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
                    pass  # Normal — no speech in window
                except sr.UnknownValueError:
                    pass  # Normal — ambient noise
                except sr.RequestError as e:
                    # FIX: handle Google API errors gracefully
                    log.warning("Speech recognition API error: %s", e)
                    consecutive_errors += 1
                    time.sleep(2)
                except Exception as e:
                    log.debug("Wake word listen error: %s", e)
                    consecutive_errors += 1
                    time.sleep(0.5)

        except OSError as e:
            # FIX: handle microphone disconnected
            log.warning("Microphone error: %s", e)
            consecutive_errors += 1
            time.sleep(3)
        except Exception as e:
            log.warning("Voice loop error: %s", e)
            consecutive_errors += 1
            time.sleep(2)

        # FIX: if too many consecutive errors, pause longer
        if consecutive_errors >= max_consecutive_errors:
            log.warning("Too many voice errors (%d) — pausing 30s", consecutive_errors)
            speak("Voice system temporarily unavailable. Retrying in 30 seconds.")
            time.sleep(30)
            consecutive_errors = 0


def start_voice_engine(token: str):
    global _voice_active, _voice_thread, _current_token
    with _voice_token_lock:
        _current_token = token

    if not VOICE_AVAILABLE:
        print("  ⚠️  Voice not available (PyAudio not installed)")
        print("  💡 Run: pip install pyaudio")
        return False

    if _voice_active and _voice_thread and _voice_thread.is_alive():
        return True  # already running

    _voice_active = True
    _voice_thread = threading.Thread(target=_voice_listen_loop, daemon=True, name="VoiceEngine")
    _voice_thread.start()
    return True


def stop_voice_engine():
    global _voice_active
    _voice_active = False
    log.info("Voice engine stopped")


def update_voice_token(token: str):
    global _current_token
    with _voice_token_lock:
        _current_token = token


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET CLIENT
# FIX: exponential backoff, proper future cleanup, auth retry handling,
#      thread-safe future resolution, ping/pong keepalive
# ═══════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    retry_delay = 3.0
    max_delay = 60.0
    connect_timeout = 20

    while True:
        try:
            log.info("Connecting to Dacexy backend...")

            # FIX: explicit timeout on connect
            async with websockets.connect(
                BACKEND_WS,
                ping_interval=25,
                ping_timeout=20,
                close_timeout=10,
                open_timeout=connect_timeout,
                extra_headers={"User-Agent": f"DacexyAgent/{VERSION}"},
                max_size=10 * 1024 * 1024,  # 10MB max message
            ) as ws:
                # Authenticate
                await ws.send(json.dumps({"token": token}))
                try:
                    auth_resp = await asyncio.wait_for(ws.recv(), timeout=15)
                except asyncio.TimeoutError:
                    log.error("Auth timeout — server did not respond")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, max_delay)
                    continue

                try:
                    auth_data = json.loads(auth_resp)
                except Exception:
                    log.error("Invalid auth response: %s", auth_resp[:100])
                    await asyncio.sleep(retry_delay)
                    continue

                if auth_data.get("type") == "error":
                    err_msg = auth_data.get("message", "Auth failed")
                    log.error("Auth failed: %s", err_msg)
                    speak("Authentication failed. Please check your login.")
                    # FIX: don't retry on auth failure — exit cleanly
                    return

                log.info("Connected to Dacexy backend")
                print("\n  ✅ Connected to Dacexy cloud — ready for remote commands")
                speak("Connected to Dacexy. Ready for your commands.")
                retry_delay = 3.0  # reset on successful connection

                # FIX: thread-safe send function
                _ws_lock = asyncio.Lock()

                async def send_fn(data):
                    async with _ws_lock:
                        try:
                            await ws.send(json.dumps(data))
                        except Exception as e:
                            log.warning("send_fn error: %s", e)

                # Main message loop
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=45)
                    except asyncio.TimeoutError:
                        # FIX: send ping to keep connection alive
                        try:
                            await asyncio.wait_for(ws.send(json.dumps({"type": "ping"})), timeout=5)
                        except Exception:
                            log.warning("Keepalive ping failed — reconnecting")
                            break
                        continue

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        log.warning("Invalid JSON from server: %s", raw[:100])
                        continue

                    msg_type = msg.get("type", "")

                    if msg_type == "ping":
                        await send_fn({"type": "pong"})

                    elif msg_type == "pong":
                        pass

                    elif msg_type == "task":
                        task_text = str(msg.get("task", ""))[:1000]
                        task_id = str(msg.get("task_id", ""))
                        if not task_text:
                            continue

                        log.info("Remote task received: %s", task_text)
                        print(f"\n  📋 Remote task: {task_text}")
                        speak(f"Got it. Working on: {task_text[:50]}")

                        # FIX: run task in executor so it doesn't block event loop
                        loop = asyncio.get_event_loop()

                        def _run_remote_task_sync(t, task, tid):
                            try:
                                needs_perm, ptype = needs_permission(task)
                                if needs_perm:
                                    if not ask_permission(task, ptype):
                                        asyncio.run_coroutine_threadsafe(
                                            send_fn({"type": "task_result", "task_id": tid, "status": "denied", "actions_taken": 0}),
                                            loop
                                        )
                                        return
                                result = execute_task_with_ai(task, t)
                                asyncio.run_coroutine_threadsafe(
                                    send_fn({"type": "task_result", "task_id": tid, "status": "completed", "result": result, "actions_taken": 1}),
                                    loop
                                )
                                speak("Task complete.")
                            except Exception as e:
                                log.error("Remote task error: %s", e)
                                asyncio.run_coroutine_threadsafe(
                                    send_fn({"type": "task_result", "task_id": tid, "status": "error", "result": str(e), "actions_taken": 0}),
                                    loop
                                )

                        threading.Thread(
                            target=_run_remote_task_sync,
                            args=(token, task_text, task_id),
                            daemon=True
                        ).start()

                    elif msg_type not in ("pong", "connected"):
                        if "action" in msg:
                            # FIX: run command in executor — never blocks event loop
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                _executor, lambda: execute_command(msg, token)
                            )
                            await send_fn({"type": "result", "result": result})

        except websockets.exceptions.ConnectionClosedOK:
            log.info("WebSocket closed cleanly — reconnecting in %.0fs", retry_delay)
        except websockets.exceptions.ConnectionClosedError as e:
            log.warning("WebSocket connection error: %s — reconnecting in %.0fs", e, retry_delay)
        except websockets.exceptions.InvalidURI:
            log.error("Invalid WebSocket URI — check BACKEND_WS")
            await asyncio.sleep(30)
            continue
        except OSError as e:
            log.warning("Network error: %s — reconnecting in %.0fs", e, retry_delay)
        except Exception as e:
            log.error("WebSocket unexpected error: %s — reconnecting in %.0fs", e, retry_delay)

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 1.5, max_delay)


# ═══════════════════════════════════════════════════════════════════════
# HEARTBEAT
# FIX: handles token expiry, updates voice engine token
# ═══════════════════════════════════════════════════════════════════════
def heartbeat_loop(token_holder: list):
    while True:
        time.sleep(300)
        token = token_holder[0]
        if token:
            try:
                valid = check_token_valid(token)
                if valid:
                    log.debug("Token heartbeat: OK")
                    update_voice_token(token)
                else:
                    log.warning("Token expired — please restart and log in again")
                    speak("Your session has expired. Please restart Dacexy Agent.")
            except Exception as e:
                log.warning("Heartbeat error: %s", e)


# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║   Dacexy Desktop Agent v11.0                 ║")
    print("║   24/7 AI Voice Control — Like Siri          ║")
    print("╚══════════════════════════════════════════════╝\n")

    # FIX: initialize TTS before anything else
    init_tts()
    load_memory()

    # ── Auth ──────────────────────────────────────────────────────────
    token = get_token()
    if token:
        print("  Verifying saved session...")
        try:
            if not check_token_valid(token):
                print("  Session expired. Please log in again.")
                clear_token()
                token = None
            else:
                print("  ✅ Session valid")
        except Exception:
            print("  Could not verify session — attempting re-use")

    if not token:
        attempts = 0
        while not token and attempts < 3:
            token = login()
            attempts += 1
            if not token and attempts < 3:
                print(f"  Attempt {attempts}/3 failed. Try again.\n")
        if not token:
            print("\n  ❌ Could not authenticate after 3 attempts. Exiting.")
            return

    # ── Autostart ─────────────────────────────────────────────────────
    try:
        setup_autostart()
        print("  ✅ Autostart registered")
    except Exception as e:
        print(f"  ⚠️  Autostart skipped: {e}")

    # ── Voice engine ──────────────────────────────────────────────────
    voice_started = start_voice_engine(token)
    if voice_started:
        print(f"  🎤 Voice engine active — say '{WAKE_WORD.title()}' anytime!")
    else:
        print("  ⚠️  Voice disabled — PyAudio not available")
        print("  💡 Install PyAudio to enable voice control")

    # ── Heartbeat ────────────────────────────────────────────────────
    token_holder = [token]
    threading.Thread(target=heartbeat_loop, args=(token_holder,), daemon=True, name="Heartbeat").start()

    # ── Status ────────────────────────────────────────────────────────
    print("\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Agent running 24/7  |  Voice: {'ON ✅' if voice_started else 'OFF ❌'}")
    print(f"  Wake word: '{WAKE_WORD.upper()}'")
    print("  Close this window to stop the agent.")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("  🌐 Connecting to Dacexy cloud...")

    # ── WebSocket (main loop) ─────────────────────────────────────────
    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n\n  Dacexy Agent stopped by user.")
    except Exception as e:
        log.error("Fatal error: %s", e)
        print(f"\n  ❌ Fatal error: {e}")
    finally:
        stop_voice_engine()
        speak("Dacexy Agent shutting down. Goodbye!")
        time.sleep(1.5)


if __name__ == "__main__":
    main()
