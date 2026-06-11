"""
DACEXY DESKTOP AGENT v25.0 - FULLY FIXED
==========================================
FIXES vs v24:
  1. AI planner REMOVED - replaced with smart local_parse that handles 200+ patterns
     (AI planner was slow, unreliable, and returned wrong action names)
  2. local_parse order fixed: leads/whatsapp/social checked BEFORE google-search
     ("find leads" was routing to google search instead of lead finder)
  3. configure_email now calls configure_smtp_interactive() directly (was opening browser)
  4. WebSocket connect_kw fixed for ALL websockets versions (no more open_timeout error)
  5. local_parse expanded to handle every common command without needing AI
  6. All action names in exec_cmd verified against local_parse output
  7. token update thread-safe throughout
"""
from __future__ import annotations
import subprocess, sys, os, platform

# ── Windows event-loop policy (must be first) ──────────────────────────────
if platform.system() == "Windows":
    import asyncio as _ae
    if hasattr(_ae, "WindowsSelectorEventLoopPolicy"):
        _ae.set_event_loop_policy(_ae.WindowsSelectorEventLoopPolicy())

# ── UTF-8 stdout/stderr on Windows ─────────────────────────────────────────
if platform.system() == "Windows":
    import io as _io
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                       errors="replace", line_buffering=True)
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                       errors="replace", line_buffering=True)
    except Exception:
        pass


# ── Auto-install missing packages ──────────────────────────────────────────
def _pip(*pkgs):
    try:
        subprocess.call([sys.executable, "-m", "pip", "install", *pkgs, "-q",
                         "--no-warn-script-location"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        timeout=180)
    except Exception:
        pass

print("  [BOOT] Checking packages...")
_REQUIRED = [
    ("pyautogui",        "pyautogui"),
    ("pillow",           "PIL"),
    ("websockets",       "websockets"),
    ("requests",         "requests"),
    ("pyttsx3",          "pyttsx3"),
    ("numpy",            "numpy"),
    ("psutil",           "psutil"),
    ("pyperclip",        "pyperclip"),
    ("pygetwindow",      "pygetwindow"),
    ("plyer",            "plyer"),
    ("speechrecognition","speech_recognition"),
    ("beautifulsoup4",   "bs4"),
    ("keyboard",         "keyboard"),
    ("schedule",         "schedule"),
]
for _pkg, _imp in _REQUIRED:
    try:
        __import__(_imp)
    except ImportError:
        print(f"  [BOOT] Installing {_pkg}...")
        _pip(_pkg)

# Selenium
try:
    from selenium import webdriver as _sw
except ImportError:
    _pip("selenium", "webdriver-manager")

# PyAudio (voice)
PYAUDIO_OK = False
try:
    import pyaudio; PYAUDIO_OK = True
except ImportError:
    _pip("PyAudio")
    try:
        import pyaudio; PYAUDIO_OK = True
    except ImportError:
        try:
            _pip("pipwin")
            subprocess.call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            import pyaudio; PYAUDIO_OK = True
        except Exception:
            pass

# OpenCV + pytesseract (optional vision)
CV2_OK = False
try:
    import cv2; CV2_OK = True
except ImportError:
    pass

OCR_OK = False
try:
    import pytesseract; OCR_OK = True
except ImportError:
    pass

print("  [BOOT] Packages ready.\n")

# ── Standard library imports ────────────────────────────────────────────────
import asyncio, base64, csv, ctypes, datetime, io, json, logging
import queue, random, re, shutil, smtplib, socket, string, threading
import time, urllib.parse, webbrowser, zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ── Third-party imports (graceful fallback) ─────────────────────────────────
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0.04
except Exception:
    pyautogui = None

try:
    import requests as req_lib
except Exception:
    req_lib = None

try:
    import websockets
except Exception:
    websockets = None

try:
    from PIL import ImageGrab, Image, ImageDraw, ImageFont
except Exception:
    ImageGrab = Image = ImageDraw = ImageFont = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import pyperclip
except Exception:
    pyperclip = None

try:
    import psutil
except Exception:
    psutil = None

try:
    import winreg; WINREG_OK = True
except Exception:
    WINREG_OK = False

try:
    import speech_recognition as sr; VOICE_OK = PYAUDIO_OK
except Exception:
    sr = None; VOICE_OK = False

try:
    import pygetwindow as gw; WINDOW_OK = True
except Exception:
    gw = None; WINDOW_OK = False

try:
    from plyer import notification; NOTIFY_OK = True
except Exception:
    NOTIFY_OK = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except Exception:
    SELENIUM_OK = False; webdriver = None

try:
    from bs4 import BeautifulSoup; BS4_OK = True
except Exception:
    BeautifulSoup = None; BS4_OK = False

try:
    import keyboard as kb_lib; KB_OK = True
except Exception:
    kb_lib = None; KB_OK = False

# ── Constants ────────────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR  / "logs" / "agent.log"
SS_DIR       = AGENT_DIR  / "screenshots"
DATA_DIR     = AGENT_DIR  / "data"
VERSION      = "25.0"

for _d in [AGENT_DIR, AGENT_DIR/"logs", DATA_DIR, SS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── SMTP presets ─────────────────────────────────────────────────────────────
SMTP_PRESETS: Dict[str, Dict] = {
    "gmail.com":      {"host": "smtp.gmail.com",       "port": 587},
    "googlemail.com": {"host": "smtp.gmail.com",       "port": 587},
    "outlook.com":    {"host": "smtp.office365.com",   "port": 587},
    "hotmail.com":    {"host": "smtp.office365.com",   "port": 587},
    "live.com":       {"host": "smtp.office365.com",   "port": 587},
    "yahoo.com":      {"host": "smtp.mail.yahoo.com",  "port": 587},
    "yahoo.in":       {"host": "smtp.mail.yahoo.com",  "port": 587},
    "icloud.com":     {"host": "smtp.mail.me.com",     "port": 587},
    "zoho.com":       {"host": "smtp.zoho.com",        "port": 587},
}

# ── Wake words ────────────────────────────────────────────────────────────────
WAKE_WORDS = [
    "dacexy", "hey dacexy", "okay dacexy", "ok dacexy",
    "jarvis", "hey jarvis",
    "computer", "hey computer",
    "assistant", "hey assistant",
]

# ── Site map ─────────────────────────────────────────────────────────────────
SITES: Dict[str, str] = {
    "youtube":        "https://www.youtube.com",
    "google":         "https://www.google.com",
    "gmail":          "https://mail.google.com",
    "facebook":       "https://www.facebook.com",
    "instagram":      "https://www.instagram.com",
    "twitter":        "https://x.com",
    "x":              "https://x.com",
    "linkedin":       "https://www.linkedin.com",
    "whatsapp":       "https://web.whatsapp.com",
    "whatsapp web":   "https://web.whatsapp.com",
    "github":         "https://github.com",
    "amazon":         "https://www.amazon.in",
    "flipkart":       "https://www.flipkart.com",
    "netflix":        "https://www.netflix.com",
    "spotify":        "https://open.spotify.com",
    "maps":           "https://maps.google.com",
    "google maps":    "https://maps.google.com",
    "wikipedia":      "https://www.wikipedia.org",
    "reddit":         "https://www.reddit.com",
    "stackoverflow":  "https://stackoverflow.com",
    "chatgpt":        "https://chat.openai.com",
    "dacexy":         "https://dacexy.vercel.app",
    "notion":         "https://notion.so",
    "canva":          "https://www.canva.com",
    "drive":          "https://drive.google.com",
    "google drive":   "https://drive.google.com",
    "trello":         "https://trello.com",
    "slack":          "https://app.slack.com",
    "zoom":           "https://zoom.us",
    "meet":           "https://meet.google.com",
    "google meet":    "https://meet.google.com",
    "teams":          "https://teams.microsoft.com",
    "discord":        "https://discord.com/app",
    "docs":           "https://docs.google.com",
    "sheets":         "https://sheets.google.com",
    "slides":         "https://slides.google.com",
    "calendar":       "https://calendar.google.com",
    "photos":         "https://photos.google.com",
    "translate":      "https://translate.google.com",
    "pinterest":      "https://www.pinterest.com",
    "tiktok":         "https://www.tiktok.com",
    "twitch":         "https://www.twitch.tv",
    "fiverr":         "https://www.fiverr.com",
    "upwork":         "https://www.upwork.com",
    "medium":         "https://medium.com",
    "quora":          "https://www.quora.com",
    "paypal":         "https://www.paypal.com",
    "razorpay":       "https://razorpay.com",
    "telegram web":   "https://web.telegram.org",
    "news":           "https://news.google.com",
    "claude":         "https://claude.ai",
    "anthropic":      "https://anthropic.com",
    "perplexity":     "https://perplexity.ai",
    "gemini":         "https://gemini.google.com",
    "openai":         "https://openai.com",
}

# ── App map (Windows executables) ────────────────────────────────────────────
APPS: Dict[str, str] = {
    "chrome":              "chrome.exe",
    "google chrome":       "chrome.exe",
    "edge":                "msedge.exe",
    "microsoft edge":      "msedge.exe",
    "firefox":             "firefox.exe",
    "brave":               "brave.exe",
    "notepad":             "notepad.exe",
    "notepad++":           r"C:\Program Files\Notepad++\notepad++.exe",
    "calculator":          "calc.exe",
    "calc":                "calc.exe",
    "paint":               "mspaint.exe",
    "explorer":            "explorer.exe",
    "file explorer":       "explorer.exe",
    "task manager":        "taskmgr.exe",
    "cmd":                 "cmd.exe",
    "command prompt":      "cmd.exe",
    "terminal":            "cmd.exe",
    "powershell":          "powershell.exe",
    "word":                "winword.exe",
    "excel":               "excel.exe",
    "powerpoint":          "powerpnt.exe",
    "outlook":             "outlook.exe",
    "vlc":                 "vlc.exe",
    "zoom":                "zoom.exe",
    "discord":             "discord.exe",
    "spotify":             "spotify.exe",
    "vscode":              "code.exe",
    "visual studio code":  "code.exe",
    "vs code":             "code.exe",
    "telegram":            "telegram.exe",
    "snipping tool":       "SnippingTool.exe",
    "control panel":       "control.exe",
    "settings":            "ms-settings:",
    "regedit":             "regedit.exe",
    "device manager":      "devmgmt.msc",
    "disk management":     "diskmgmt.msc",
    "event viewer":        "eventvwr.msc",
    "services":            "services.msc",
    "winrar":              "winrar.exe",
    "7zip":                "7zFM.exe",
    "obs":                 "obs64.exe",
    "steam":               "steam.exe",
    "gimp":                "gimp-2.10.exe",
    "photoshop":           "photoshop.exe",
    "audacity":            "audacity.exe",
    "skype":               "skype.exe",
    "teams":               "teams.exe",
    "anydesk":             "anydesk.exe",
    "teamviewer":          "teamviewer.exe",
}

# ── Safety blocklist ─────────────────────────────────────────────────────────
BLOCKED = [
    "rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
    "rd /s /q c:\\", "reg delete hklm", "dd if=/dev/zero",
    "rmdir /s /q c:\\", "deltree", ":(){ :|:& };:",
    "shutdown /s", "shutdown -s",
]

# ── Global state ─────────────────────────────────────────────────────────────
_mem_lock    = threading.Lock()
_cfg_lock    = threading.Lock()
_executor    = ThreadPoolExecutor(max_workers=20)
_running     = True
_tts_q: queue.Queue = queue.Queue(maxsize=20)
_tts_engine  = None
_tts_lock    = threading.Lock()
_voice_on    = False
_cur_token   = None
_tok_lock    = threading.Lock()
_smtp_cfg:   Dict = {}
_sched_jobs: List = []
_convo:      deque = deque(maxlen=30)
_selenium_driver = None
_sel_lock    = threading.Lock()

MEMORY: Dict = {
    "facts":        [],
    "preferences":  {},
    "task_history": deque(maxlen=1000),
    "context":      {},
    "contacts":     {},
    "skills":       [],
}

# ── Logging ───────────────────────────────────────────────────────────────────
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
        ]
    )
except Exception:
    logging.basicConfig(level=logging.INFO)

log      = logging.getLogger("dacexy")
audit    = logging.getLogger("dacexy.audit")
plan_log = logging.getLogger("dacexy.planner")

log.info("Dacexy Agent v%s starting", VERSION)

# =============================================================================
# TTS
# =============================================================================
def _tts_worker():
    while _running:
        try:
            text = _tts_q.get(timeout=1)
            if text is None:
                break
            try:
                with _tts_lock:
                    if _tts_engine:
                        _tts_engine.say(str(text)[:400])
                        _tts_engine.runAndWait()
            except Exception:
                pass
            finally:
                try: _tts_q.task_done()
                except Exception: pass
        except queue.Empty:
            continue
        except Exception:
            continue


def init_tts():
    global _tts_engine
    if not pyttsx3:
        return
    try:
        eng = pyttsx3.init()
        eng.setProperty("rate",   165)
        eng.setProperty("volume", 0.92)
        try:
            voices = eng.getProperty("voices") or []
            for v in voices:
                n = (v.name or "").lower()
                if any(x in n for x in ["david", "mark", "zira", "hazel"]):
                    eng.setProperty("voice", v.id)
                    break
        except Exception:
            pass
        _tts_engine = eng
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS initialized OK")
    except Exception as e:
        log.warning("TTS init failed: %s", e)


def speak(text: str):
    if not text:
        return
    s = str(text)[:400]
    try:
        print(f"\n  [Dacexy] {s}")
        sys.stdout.flush()
    except Exception:
        pass
    log.info("SPEAK: %s", s)
    try:
        _tts_q.put_nowait(s)
    except queue.Full:
        pass


# =============================================================================
# NOTIFICATION
# =============================================================================
def _notify(title: str, msg: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=str(msg)[:100],
                                app_name="Dacexy", timeout=4)
    except Exception:
        pass


# =============================================================================
# CONFIG / TOKEN
# =============================================================================
def load_config() -> dict:
    with _cfg_lock:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}


def save_config(cfg: dict):
    with _cfg_lock:
        try:
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except Exception as e:
            log.warning("save_config: %s", e)


def get_token()       -> Optional[str]: return load_config().get("access_token")
def save_token(t: str): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token():       cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)


def check_token_valid(token: str) -> bool:
    if not req_lib:
        return False
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
                        headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# =============================================================================
# AUTOSTART
# =============================================================================
def setup_autostart():
    try:
        if not WINREG_OK:
            return
        launcher = str(AGENT_DIR / "start_dacexy.bat")
        cmd = (f'"{launcher}"' if os.path.exists(launcher)
               else f'"{sys.executable}" "{Path(__file__).resolve()}"')
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered: %s", cmd)
    except Exception as e:
        log.warning("Autostart: %s", e)


# =============================================================================
# LOGIN
# =============================================================================
def login() -> Optional[str]:
    print("\n" + "="*55)
    print("  DACEXY AGENT v25.0 - Login")
    print("="*55)
    print("  Register at: dacexy.vercel.app\n")
    try:
        email    = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not email or "@" not in email:
        print("  [ERROR] Invalid email"); return None
    if not password or len(password) < 4:
        print("  [ERROR] Password too short"); return None
    if not req_lib:
        print("  [ERROR] requests not installed"); return None
    print("  Connecting...")
    for kw in [{"data": {"username": email, "password": password}},
               {"json": {"email": email, "password": password}}]:
        try:
            r = req_lib.post(f"{BACKEND_HTTP}/auth/login", timeout=30, **kw)
            if r.status_code == 200:
                t = (r.json().get("access_token") or "").strip()
                if t:
                    save_token(t)
                    with _mem_lock:
                        if f"email:{email}" not in MEMORY["facts"]:
                            MEMORY["facts"].append(f"email:{email}")
                    print("  [OK] Login successful!")
                    audit.info("ACTION=LOGIN | %s | RESULT=SUCCESS", email)
                    return t
        except Exception:
            pass
    print("  [ERROR] Login failed. Check credentials at dacexy.vercel.app")
    return None


# =============================================================================
# MEMORY
# =============================================================================
def load_memory():
    global _smtp_cfg, _sched_jobs
    try:
        if MEMORY_FILE.exists():
            d = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            with _mem_lock:
                MEMORY["facts"]        = d.get("facts", [])
                MEMORY["preferences"]  = d.get("preferences", {})
                MEMORY["context"]      = d.get("context", {})
                MEMORY["contacts"]     = d.get("contacts", {})
                MEMORY["skills"]       = d.get("skills", [])
                MEMORY["task_history"] = deque(d.get("task_history", [])[-1000:], maxlen=1000)
            _smtp_cfg   = d.get("smtp_config", {})
            _sched_jobs = d.get("sched_jobs", [])
            log.info("Memory loaded: %d facts, %d contacts, %d skills",
                     len(MEMORY["facts"]), len(MEMORY["contacts"]), len(MEMORY["skills"]))
    except Exception as e:
        log.warning("load_memory: %s", e)


def save_memory():
    try:
        with _mem_lock:
            d = {
                "facts":        MEMORY["facts"][-1000:],
                "preferences":  MEMORY["preferences"],
                "context":      MEMORY["context"],
                "contacts":     MEMORY["contacts"],
                "skills":       MEMORY["skills"],
                "task_history": list(MEMORY["task_history"])[-200:],
                "smtp_config":  _smtp_cfg,
                "sched_jobs":   _sched_jobs[-50:],
            }
        tmp = MEMORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        tmp.replace(MEMORY_FILE)
    except Exception as e:
        log.warning("save_memory: %s", e)


def remember(fact: str):
    if not fact:
        return
    with _mem_lock:
        if fact not in MEMORY["facts"]:
            MEMORY["facts"].append(fact)
    save_memory()


def get_mem_ctx() -> str:
    try:
        with _mem_lock:
            parts = []
            if MEMORY["facts"]:
                parts.append("Facts: " + "; ".join(MEMORY["facts"][-10:]))
            if MEMORY["preferences"]:
                parts.append("Prefs: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-8:]
            if recent:
                parts.append("Recent tasks: " + "; ".join(recent))
            contacts = list(MEMORY["contacts"].keys())[:8]
            if contacts:
                parts.append("Contacts: " + ", ".join(contacts))
        conv = list(_convo)[-6:]
        if conv:
            parts.append("Conversation: " + " | ".join(conv))
        return "\n".join(parts)
    except Exception:
        return ""


# =============================================================================
# SCREENSHOT
# =============================================================================
def take_screenshot(save=True, quality=82) -> Optional[str]:
    try:
        if not ImageGrab:
            return None
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1920:
            img = img.resize((1920, int(h * 1920 / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        if save:
            fn = SS_DIR / f"ss_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            fn.write_bytes(base64.b64decode(b64))
            log.info("Screenshot saved: %s", fn)
        return b64
    except Exception as e:
        log.warning("screenshot: %s", e)
        return None


# =============================================================================
# TYPING
# =============================================================================
def smart_type(text: str):
    if not text:
        return
    text = str(text)[:50000]
    try:
        if pyperclip:
            pyperclip.copy(text)
            time.sleep(0.08)
            if pyautogui:
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.15)
            return
        if pyautogui:
            chunk = 500
            for i in range(0, len(text), chunk):
                pyautogui.write(text[i:i+chunk], interval=0.012)
    except Exception as e:
        log.warning("smart_type: %s", e)


# =============================================================================
# WINDOW HELPERS
# =============================================================================
def get_active_win() -> str:
    try:
        if WINDOW_OK and gw:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except Exception:
        pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ln   = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf  = ctypes.create_unicode_buffer(ln + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, ln + 1)
        return buf.value
    except Exception:
        return ""


def list_windows() -> List[str]:
    try:
        if WINDOW_OK and gw:
            return [w.title for w in gw.getAllWindows() if w.title.strip()]
    except Exception:
        pass
    return []


# =============================================================================
# SMART OPEN
# =============================================================================
def smart_open(target: str) -> dict:
    if not target:
        return {"status": "error", "message": "Nothing to open"}

    t  = str(target).strip()
    tl = t.lower()

    for pfx in ["open ", "launch ", "start ", "go to ", "navigate to ",
                "show ", "visit ", "browse ", "run ", "start up ", "load "]:
        if tl.startswith(pfx):
            tl = tl[len(pfx):].strip()
            t  = t[len(pfx):].strip()

    # 1. Exact site match
    if tl in SITES:
        url = SITES[tl]
        webbrowser.open(url)
        speak(f"Opening {tl}")
        log.info("OPEN site: %s -> %s", tl, url)
        return {"status": "ok", "opened": url, "type": "website"}

    # 2. Partial site match
    for site, url in SITES.items():
        if site in tl:
            webbrowser.open(url)
            speak(f"Opening {site}")
            log.info("OPEN site (partial): %s -> %s", site, url)
            return {"status": "ok", "opened": url, "type": "website"}

    # 3. Exact app match
    if tl in APPS:
        exe = APPS[tl]
        try:
            subprocess.Popen(exe, shell=True)
            speak(f"Opening {tl}")
            log.info("OPEN app: %s -> %s", tl, exe)
            return {"status": "ok", "opened": exe, "type": "app"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # 4. Partial app match
    for app, exe in APPS.items():
        if app in tl:
            try:
                subprocess.Popen(exe, shell=True)
                speak(f"Opening {app}")
                log.info("OPEN app (partial): %s -> %s", app, exe)
                return {"status": "ok", "opened": exe, "type": "app"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    # 5. Raw URL
    if tl.startswith(("http://", "https://")):
        webbrowser.open(t)
        speak(f"Opening {t[:60]}")
        return {"status": "ok", "opened": t, "type": "url"}

    # 6. Looks like a domain
    if re.match(r"^[a-z0-9\-]+\.[a-z]{2,}$", tl) and " " not in tl:
        url = "https://" + tl
        webbrowser.open(url)
        speak(f"Opening {tl}")
        return {"status": "ok", "opened": url, "type": "url"}

    # 7. File path
    p = Path(t)
    if p.exists():
        try:
            os.startfile(str(p))
            speak(f"Opening {p.name}")
            return {"status": "ok", "opened": str(p), "type": "file"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # 8. Try as shell command (short names)
    if len(t.split()) <= 4:
        try:
            subprocess.Popen(t, shell=True)
            speak(f"Running {t[:40]}")
            return {"status": "ok", "opened": t, "type": "command"}
        except Exception:
            pass

    return {"status": "error", "message": f"Could not find or open: {target[:80]}"}


# =============================================================================
# EMAIL
# =============================================================================
def configure_smtp_interactive() -> dict:
    global _smtp_cfg
    print("\n  Email Setup")
    print("  For Gmail use an App Password: myaccount.google.com/apppasswords\n")
    try:
        em = input("  Your email address    : ").strip()
        if not em or "@" not in em:
            return {"status": "error", "message": "Invalid email"}
        pw = input("  Password/App Password : ").strip().replace(" ", "")
        if not pw:
            return {"status": "error", "message": "No password"}
        domain = em.split("@")[-1].lower()
        preset = SMTP_PRESETS.get(domain, {"host": f"smtp.{domain}", "port": 587})
        print(f"\n  Testing {preset['host']}:{preset['port']}...")
        try:
            with smtplib.SMTP(preset["host"], preset["port"], timeout=15) as s:
                s.ehlo(); s.starttls(); s.ehlo(); s.login(em, pw)
            print("  [OK] Connection successful!")
        except smtplib.SMTPAuthenticationError:
            print("  [ERROR] Wrong password or App Password required.")
            return {"status": "error", "message": "Auth failed"}
        except Exception as te:
            print(f"  [WARN] {te} - saving anyway.")
        _smtp_cfg = {"email": em, "password": pw,
                     "host": preset["host"], "port": preset["port"]}
        save_memory()
        speak(f"Email configured as {em}.")
        return {"status": "ok", "email": em}
    except (EOFError, KeyboardInterrupt):
        return {"status": "cancelled"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _build_email_msg(from_: str, to_: str, subject: str, body: str,
                     att: Optional[str] = None) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"]    = from_
    msg["To"]      = to_
    msg["Subject"] = subject
    msg["X-Mailer"] = f"Dacexy Agent v{VERSION}"
    plain = body.replace("<br>", "\n").replace("<br/>", "\n")
    html  = "<html><body>" + body.replace("\n", "<br>") + "</body></html>"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))
    if att and os.path.exists(str(att)):
        with open(str(att), "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f"attachment; filename={os.path.basename(str(att))}")
        msg.attach(part)
    return msg


def send_email_real(to: str, subject: str, body: str, att=None) -> dict:
    em = _smtp_cfg.get("email", "")
    pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host",  "smtp.gmail.com")
    pt = int(_smtp_cfg.get("port", 587))

    if not em or not pw:
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(str(body)[:2000])}")
        webbrowser.open(url)
        speak(f"Gmail opened for {to}. Say 'configure email' to enable auto-send.")
        return {"status": "ok", "action": "browser_compose",
                "note": "SMTP not configured - opened in browser"}

    try:
        msg = _build_email_msg(em, to, subject, body, att)
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        speak(f"Email sent to {to}!")
        log.info("Email sent to %s", to)
        return {"status": "ok", "sent_to": to}
    except smtplib.SMTPAuthenticationError:
        speak("Email auth failed. Check your App Password.")
        return {"status": "error", "message": "SMTP auth failed"}
    except Exception as e:
        log.warning("Email send failed: %s - opening browser fallback", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(str(body)[:2000])}")
        webbrowser.open(url)
        return {"status": "ok", "action": "browser_fallback", "note": str(e)}


def send_bulk_email(contacts: list, subject: str, body_tmpl: str,
                    delay: float = 1.5) -> dict:
    em = _smtp_cfg.get("email", "")
    pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host",  "smtp.gmail.com")
    pt = int(_smtp_cfg.get("port", 587))

    if not em or not pw:
        return {"status": "error",
                "message": "Email not configured. Say 'configure email' first."}
    if not contacts:
        return {"status": "error", "message": "No contacts provided."}

    speak(f"Starting bulk email to {len(contacts)} contacts.")
    sent = 0; failed = 0
    delay = max(0.5, float(delay))

    try:
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            for c in contacts:
                try:
                    to_e = (c.get("email") or c.get("Email") or "").strip()
                    if not to_e or "@" not in to_e:
                        failed += 1; continue
                    name    = (c.get("name") or c.get("Name") or
                               to_e.split("@")[0].replace(".", " ").title())
                    company = c.get("company") or c.get("Company") or ""
                    body = (body_tmpl
                            .replace("{name}",    name)
                            .replace("{Name}",    name)
                            .replace("{email}",   to_e)
                            .replace("{company}", company)
                            .replace("{NAME}",    name.upper()))
                    subj = (subject
                            .replace("{name}",    name)
                            .replace("{company}", company))
                    msg = _build_email_msg(em, to_e, subj, body)
                    srv.sendmail(em, [to_e], msg.as_string())
                    sent += 1
                    log.info("Bulk email sent: %s (%d/%d)", to_e, sent, len(contacts))
                    if sent % 10 == 0:
                        speak(f"{sent} emails sent.")
                    time.sleep(delay)
                except smtplib.SMTPServerDisconnected:
                    try:
                        srv.connect(ht, pt)
                        srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
                    except Exception:
                        failed += len(contacts) - sent - failed
                        break
                except Exception as e2:
                    failed += 1
                    log.warning("Bulk fail %s: %s", c.get("email", "?"), e2)
    except Exception as e:
        return {"status": "error", "message": f"SMTP connection failed: {e}"}

    summary = f"Bulk email complete: {sent} sent, {failed} failed of {len(contacts)}"
    speak(summary)
    log.info(summary)
    return {"status": "ok", "sent": sent, "failed": failed, "total": len(contacts)}


def load_csv_contacts(path: str) -> list:
    contacts = []
    try:
        p = Path(path)
        if not p.exists():
            p2 = Path.home() / "Desktop" / p.name
            if p2.exists():
                p = p2
            else:
                return []
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = (row.get("email") or row.get("Email") or
                      row.get("EMAIL") or "").strip()
                if em and "@" in em:
                    contacts.append({
                        "email":   em,
                        "name":    (row.get("name") or row.get("Name") or
                                    em.split("@")[0].replace(".", " ").title()).strip(),
                        "company": (row.get("company") or row.get("Company") or "").strip(),
                    })
    except Exception as e:
        log.warning("load_csv: %s", e)
    return contacts


# =============================================================================
# WEB HELPERS
# =============================================================================
_HDRS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 Chrome/124.0 Safari/537.36")}


def web_research(query: str) -> str:
    if not req_lib:
        return "Web research unavailable (requests not installed)."
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        r   = req_lib.get(url, headers=_HDRS, timeout=15)
        if BS4_OK and r.status_code == 200:
            soup  = BeautifulSoup(r.text, "html.parser")
            snips = []
            for tag in soup.find_all(["div", "span"],
                    class_=lambda c: c and any(
                        x in c for x in ["BNeawe", "VwiC3b", "MUxGbd", "hgKElc", "yDYNvb"])):
                t = tag.get_text(" ", strip=True)
                if len(t) > 60:
                    snips.append(t)
            result = " ".join(snips[:12])[:6000]
        else:
            text   = re.sub(r"<[^>]+>", " ", r.text)
            result = re.sub(r"\s+", " ", text)[:3000]
        return result if result.strip() else "No results found."
    except Exception as e:
        return f"Research error: {e}"


def find_leads_web(product: str, niche: str = "", max_leads: int = 50) -> list:
    if not req_lib:
        return []
    leads     = []
    email_re  = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b')
    skip      = {"example.com", "test.com", "sentry.io", "w3.org", "schema.org",
                 "wix.com", "wordpress.com", "jquery.com", "google.com",
                 "cloudflare.com", "github.com", "npmjs.com"}
    speak(f"Searching leads for {product}. Takes ~60 seconds.")

    queries = [
        f"{niche} {product} contact email",
        f"{product} company director email",
        f"buy {product} business email contact",
        f'"{product}" "@gmail.com" OR "@yahoo.com" contact',
    ]
    for q in queries:
        if len(leads) >= max_leads:
            break
        try:
            r    = req_lib.get(f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20",
                               headers=_HDRS, timeout=15)
            text = BeautifulSoup(r.text, "html.parser").get_text() if BS4_OK else r.text
            for em in email_re.findall(text):
                domain = em.split("@")[-1].lower()
                if domain in skip:
                    continue
                if any(l["email"].lower() == em.lower() for l in leads):
                    continue
                leads.append({
                    "email":   em,
                    "name":    em.split("@")[0].replace(".", " ").title(),
                    "company": domain.split(".")[0].title(),
                })
                if len(leads) >= max_leads:
                    break
            time.sleep(2)
        except Exception as e:
            log.warning("lead search: %s", e)

    try:
        lf = DATA_DIR / "leads.csv"
        with open(lf, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["email", "name", "company"])
            w.writeheader(); w.writerows(leads)
        log.info("Leads saved: %s (%d)", lf, len(leads))
    except Exception:
        pass

    speak(f"Found {len(leads)} leads.")
    return leads


# =============================================================================
# WHATSAPP
# =============================================================================
def wa_send(phone: str, msg: str) -> dict:
    ph = re.sub(r"[^0-9+]", "", str(phone))
    if not ph.startswith("+"):
        ph = "+91" + ph
    url = f"https://wa.me/{ph.lstrip('+')}?text={urllib.parse.quote(str(msg))}"
    webbrowser.open(url)
    speak(f"WhatsApp opened for {phone}. Click Send to confirm.")
    return {"status": "ok", "note": "WhatsApp Web opened - click Send"}


# =============================================================================
# SELENIUM HELPERS
# =============================================================================
def _get_driver(headless: bool = False):
    global _selenium_driver
    with _sel_lock:
        try:
            if _selenium_driver:
                _selenium_driver.current_url
                return _selenium_driver
        except Exception:
            _selenium_driver = None

        if not SELENIUM_OK:
            return None
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        try:
            svc = ChromeService(ChromeDriverManager().install())
            drv = webdriver.Chrome(service=svc, options=opts)
            drv.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _selenium_driver = drv
            return drv
        except Exception as e:
            log.warning("Selenium driver init: %s", e)
            return None


def selenium_open(url: str, wait_for_css: str = None, timeout: int = 15) -> dict:
    drv = _get_driver()
    if not drv:
        webbrowser.open(url)
        return {"status": "ok", "note": "opened in default browser (Selenium unavailable)"}
    try:
        drv.get(url)
        if wait_for_css:
            WebDriverWait(drv, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_css)))
        return {"status": "ok", "url": drv.current_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def selenium_fill(selector: str, value: str,
                  by: str = "css", submit: bool = False) -> dict:
    drv = _get_driver()
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    try:
        by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH,
                  "id": By.ID, "name": By.NAME, "class": By.CLASS_NAME}
        el = WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.clear()
        el.send_keys(value)
        if submit:
            el.send_keys(Keys.RETURN)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def selenium_click(selector: str, by: str = "css") -> dict:
    drv = _get_driver()
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    try:
        by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH,
                  "id": By.ID, "name": By.NAME, "class": By.CLASS_NAME}
        el = WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.click()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# SOCIAL MEDIA AUTOMATION (Selenium)
# =============================================================================
def post_twitter(username: str, password: str, text: str) -> dict:
    speak("Logging into Twitter / X...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://x.com")
        return {"status": "ok", "note": "Twitter opened - Selenium unavailable"}
    try:
        drv.get("https://x.com/login")
        time.sleep(3)
        u = WebDriverWait(drv, 15).until(
            EC.presence_of_element_located((By.NAME, "text")))
        u.send_keys(username); u.send_keys(Keys.RETURN)
        time.sleep(2)
        p = WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.NAME, "password")))
        p.send_keys(password); p.send_keys(Keys.RETURN)
        time.sleep(3)
        btn = WebDriverWait(drv, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                '[data-testid="SideNav_NewTweet_Button"]')))
        btn.click()
        time.sleep(1)
        box = WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                '[data-testid="tweetTextarea_0"]')))
        box.send_keys(text)
        time.sleep(0.5)
        post = WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                '[data-testid="tweetButton"]')))
        post.click()
        time.sleep(2)
        speak("Tweet posted successfully!")
        return {"status": "ok", "platform": "twitter"}
    except Exception as e:
        speak("Twitter post failed.")
        return {"status": "error", "message": str(e)}


def post_linkedin(username: str, password: str, text: str) -> dict:
    speak("Logging into LinkedIn...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://www.linkedin.com")
        return {"status": "ok", "note": "LinkedIn opened - Selenium unavailable"}
    try:
        drv.get("https://www.linkedin.com/login")
        time.sleep(2)
        WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        drv.find_element(By.ID, "password").send_keys(password)
        drv.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        time.sleep(3)
        start = WebDriverWait(drv, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                ".share-box-feed-entry__trigger")))
        start.click()
        time.sleep(1)
        box = WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor")))
        box.click(); box.send_keys(text)
        time.sleep(0.5)
        WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                ".share-actions__primary-action"))).click()
        time.sleep(2)
        speak("LinkedIn post published!")
        return {"status": "ok", "platform": "linkedin"}
    except Exception as e:
        speak("LinkedIn post failed.")
        return {"status": "error", "message": str(e)}


def post_instagram(username: str, password: str,
                   caption: str = "", image_path: str = "") -> dict:
    speak("Opening Instagram...")
    webbrowser.open("https://www.instagram.com")
    speak("Instagram opened. Automated posting requires desktop app or Meta API.")
    return {"status": "ok", "note": "Instagram opened in browser"}


def post_facebook(username: str, password: str, text: str,
                  page_id: str = "") -> dict:
    speak("Logging into Facebook...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://www.facebook.com")
        return {"status": "ok", "note": "Facebook opened - Selenium unavailable"}
    try:
        drv.get("https://www.facebook.com/login")
        time.sleep(2)
        WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.ID, "email"))).send_keys(username)
        drv.find_element(By.ID, "pass").send_keys(password)
        drv.find_element(By.NAME, "login").click()
        time.sleep(4)
        box = WebDriverWait(drv, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                '[aria-label="What\'s on your mind?"]')))
        box.click()
        time.sleep(1)
        editor = WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                '[contenteditable="true"]')))
        editor.send_keys(text)
        time.sleep(0.5)
        WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                '[aria-label="Post"]'))).click()
        time.sleep(2)
        speak("Facebook post published!")
        return {"status": "ok", "platform": "facebook"}
    except Exception as e:
        speak("Facebook post failed.")
        return {"status": "error", "message": str(e)}


def youtube_search_and_play(query: str) -> dict:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    speak(f"Searching YouTube for {query}")
    return {"status": "ok", "url": url}


# =============================================================================
# LOCAL NLP PARSER — handles 200+ patterns, NO AI NEEDED
# CRITICAL: ORDER MATTERS. Specific checks come before general ones.
# =============================================================================
def local_parse(task: str) -> list:
    t  = task.strip()
    tl = t.lower()

    # ── 1. CONFIGURE EMAIL (must be first to not be caught by open/email) ────
    if re.search(r"(?:configure|setup|set up|enable|add)\s+(?:email|smtp|mail)", tl):
        return [{"action": "configure_email"}]

    # ── 2. LEADS (before google search — "find leads" would hit google search) ─
    if re.search(r"(?:find|get|search|generate)\s+(?:leads|customers|clients|prospects)", tl):
        m_prod = re.search(r"for\s+(?:my\s+)?(.+?)(?:\s+and\b|\s+then\b|\s+to\b|\s*$)", tl)
        prod   = m_prod.group(1).strip() if m_prod else "product"
        return [{"action":  "find_leads_and_email",
                 "product": prod, "niche": "",
                 "subject": f"Quick question about {prod}",
                 "body":    f"Hi {{name}},\n\nI think {prod} could really help you.\n"
                             "Would you be open to a 5-minute call?\n\nBest regards"}]

    # ── 3. BULK EMAIL (before regular email) ─────────────────────────────────
    if re.search(r"bulk\s+email|mass\s+email|email\s+all|email\s+campaign|email\s+blast", tl):
        csv_m = re.search(r"(?:from|using|with|file)\s+(.+?\.csv)", tl)
        return [{"action":   "bulk_email",
                 "csv_path": csv_m.group(1) if csv_m else "",
                 "subject":  "Hello from Dacexy",
                 "body":     "Hi {name},\n\nHope this message finds you well!\n\nBest regards"}]

    # ── 4. SEND EMAIL ─────────────────────────────────────────────────────────
    m = re.search(
        r"(?:send|compose|write|draft)\s+(?:an?\s+)?(?:email|mail|message)\s+to\s+"
        r"([^\s,]+@[^\s,]+)"
        r"(?:\s+(?:saying|about|with\s+subject|subject|re|regarding)\s+(.+?))?$",
        tl)
    if m:
        subj = (m.group(2) or "Hello from Dacexy").strip()
        return [{"action":  "send_email",
                 "to":      m.group(1).strip(),
                 "subject": subj,
                 "body":    subj}]

    # ── 5. WHATSAPP (before open, so "open whatsapp" still works below) ───────
    m = re.search(
        r"(?:send|message|whatsapp)\s+(.+?)"
        r"\s+(?:on\s+whatsapp\s+)?(?:saying|message|with|that)\s+(.+)$", tl)
    if m:
        return [{"action":  "whatsapp",
                 "phone":   m.group(1).strip(),
                 "message": m.group(2).strip()}]

    # ── 6. SOCIAL MEDIA POSTS (before open) ───────────────────────────────────
    m_tw = re.search(r"(?:post|tweet|publish|share)\s+(?:on\s+(?:twitter|x)\s+)?(.+?)(?:\s+on\s+(?:twitter|x))?$", tl)
    if re.search(r"\b(?:twitter|tweet)\b", tl) and m_tw:
        txt = m_tw.group(1).strip()
        for rm in ["twitter","tweet","post on","publish on","share on"]:
            txt = txt.replace(rm, "").strip()
        if txt and len(txt) > 2:
            return [{"action": "twitter_post", "username": "", "password": "", "text": txt},
                    {"action": "speak", "text": "Opening Twitter to post."}]

    m_li = re.search(r"(?:post|publish|share)\s+(?:on\s+linkedin\s+)?(.+?)(?:\s+on\s+linkedin)?$", tl)
    if re.search(r"\blinkedin\b", tl) and m_li:
        txt = m_li.group(1).strip()
        for rm in ["linkedin","post on","publish on","share on"]:
            txt = txt.replace(rm, "").strip()
        if txt and len(txt) > 2:
            return [{"action": "linkedin_post", "username": "", "password": "", "text": txt},
                    {"action": "speak", "text": "Opening LinkedIn to post."}]

    if re.search(r"\bfacebook\b", tl) and re.search(r"\b(?:post|publish|share)\b", tl):
        m_fb = re.search(r"(?:post|publish|share)\s+(?:on\s+facebook\s+)?(.+?)(?:\s+on\s+facebook)?$", tl)
        if m_fb:
            txt = m_fb.group(1).strip()
            if txt and len(txt) > 2:
                return [{"action": "facebook_post", "username": "", "password": "", "text": txt}]

    # ── 7. YOUTUBE SEARCH (before open) ──────────────────────────────────────
    m = re.search(r"(?:search|play|find|watch|look up)\s+(.+?)\s+(?:on|in)\s+youtube", tl)
    if m:
        return [{"action": "open_youtube", "query": m.group(1).strip()}]

    if re.search(r"\byoutube\b", tl) and re.search(r"\b(?:search|play|watch|find)\b", tl):
        q = re.sub(r"\b(youtube|search|play|watch|find|open|on|in|for|me)\b", "", tl).strip()
        if q and len(q) > 2:
            return [{"action": "open_youtube", "query": q}]

    # ── 8. OPEN / LAUNCH / START ──────────────────────────────────────────────
    m = re.match(r"(?:open|launch|start|go to|navigate to|visit|browse|load|show)\s+(.+)", tl)
    if m:
        tgt = m.group(1).strip()
        return [{"action": "open",  "target": tgt},
                {"action": "speak", "text":   f"Opening {tgt}"}]

    # ── 9. GOOGLE SEARCH (after leads/social/youtube already checked) ─────────
    m = re.search(r"(?:google|search\s+for|look\s+up|search|find)\s+(.+?)(?:\s+on\s+google)?$", tl)
    if m and "youtube" not in tl and "email" not in tl:
        q = m.group(1).strip()
        if q and len(q) > 1:
            return [{"action": "search_web", "query": q}]

    # ── 10. SCREENSHOT ────────────────────────────────────────────────────────
    if re.search(r"screenshot|screen\s+shot|capture\s+screen|take\s+screenshot", tl):
        return [{"action": "screenshot"},
                {"action": "speak", "text": "Screenshot taken."}]

    # ── 11. TIME / DATE ───────────────────────────────────────────────────────
    if re.search(r"what(?:'s| is)\s+the\s+time|time\s+is\s+it|what\s+time|tell\s+me\s+the\s+time|current\s+time", tl):
        return [{"action": "get_time"}]
    if re.search(r"what(?:'s| is)\s+(?:today|the\s+date)|date\s+is\s+it|what\s+date|today'?s?\s+date|current\s+date", tl):
        return [{"action": "get_date"}]

    # ── 12. SYSTEM INFO ───────────────────────────────────────────────────────
    if re.search(r"system\s+info|cpu\s+usage|ram\s+usage|disk\s+space|memory\s+usage|hardware\s+info|check\s+system|how\s+much\s+(?:ram|memory|cpu|disk)", tl):
        return [{"action": "get_system_info"}]

    # ── 13. VOLUME ────────────────────────────────────────────────────────────
    if re.search(r"volume\s*up|increase\s+volume|louder|turn\s+(?:up|volume\s+up)", tl):
        return [{"action": "volume_up", "steps": 5}]
    if re.search(r"volume\s*down|lower\s+volume|quieter|turn\s+(?:down|volume\s+down)|decrease\s+volume", tl):
        return [{"action": "volume_down", "steps": 5}]
    if re.search(r"\bmute\b|\bsilence\b|\bunmute\b", tl):
        return [{"action": "mute"}]

    # ── 14. WINDOW MANAGEMENT ─────────────────────────────────────────────────
    if re.search(r"minimiz|minimis", tl):
        return [{"action": "minimize_window"}]
    if re.search(r"maximiz|maximis|full.?screen", tl):
        return [{"action": "maximize_window"}]
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app|program|application)", tl):
        return [{"action": "close_window"}]
    if re.search(r"show\s+desktop|win\s*\+\s*d", tl):
        return [{"action": "show_desktop"}]
    if re.search(r"(?:alt|switch)\s+tab|next\s+window|switch\s+window", tl):
        return [{"action": "switch_window"}]

    # ── 15. TYPING ────────────────────────────────────────────────────────────
    m = re.match(r"(?:type|write|enter|input)\s+(.+)", tl)
    if m:
        return [{"action": "type", "text": m.group(1).strip()}]

    # ── 16. SCROLL ────────────────────────────────────────────────────────────
    if re.search(r"scroll\s+down|page\s+down|scroll\s+(?:the\s+)?(?:page|window)\s+down", tl):
        return [{"action": "scroll_down", "amount": 5}]
    if re.search(r"scroll\s+up|page\s+up|scroll\s+(?:the\s+)?(?:page|window)\s+up", tl):
        return [{"action": "scroll_up", "amount": 5}]

    # ── 17. KEYBOARD SHORTCUTS ────────────────────────────────────────────────
    if re.search(r"\b(?:press|hit)\s+enter\b|submit\s+form|confirm\s+dialog", tl):
        return [{"action": "key", "key": "enter"}]
    if re.search(r"\b(?:press|hit)\s+escape\b|press\s+esc\b", tl):
        return [{"action": "key", "key": "escape"}]
    if re.search(r"\b(?:press|hit)\s+tab\b", tl):
        return [{"action": "key", "key": "tab"}]
    if re.search(r"copy\s+(?:it|that|all|text|this)", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "c"]}]
    if re.search(r"paste\s+(?:it|that|here|text)", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "v"]}]
    if re.search(r"select\s+all", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "a"]}]
    if re.search(r"undo\s+(?:that|last|it)", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "z"]}]
    if re.search(r"save\s+(?:the\s+)?(?:file|document|this)", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "s"]}]
    if re.search(r"(?:refresh|reload)\s+(?:the\s+)?(?:page|browser|tab)", tl):
        return [{"action": "key", "key": "f5"}]
    if re.search(r"new\s+tab\b", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "t"]}]
    if re.search(r"close\s+tab\b", tl):
        return [{"action": "hotkey", "keys": ["ctrl", "w"]}]

    # ── 18. MEDIA CONTROLS ────────────────────────────────────────────────────
    if re.search(r"(?:play|pause|toggle)\s+(?:music|media|song|video|playback)", tl):
        return [{"action": "media_play_pause"}]
    if re.search(r"next\s+(?:song|track|music)", tl):
        return [{"action": "media_next"}]
    if re.search(r"(?:previous|prev|back)\s+(?:song|track|music)", tl):
        return [{"action": "media_prev"}]

    # ── 19. REMEMBER ──────────────────────────────────────────────────────────
    m = re.match(r"remember\s+(?:that\s+)?(.+)", tl)
    if m:
        return [{"action": "remember", "fact": m.group(1)},
                {"action": "speak",    "text": "Got it, I'll remember that."}]

    # ── 20. SPEAK / SAY ───────────────────────────────────────────────────────
    m = re.match(r"(?:say|speak|tell\s+me|announce|read\s+aloud)\s+(.+)", tl)
    if m:
        return [{"action": "speak", "text": m.group(1)}]

    # ── 21. WEB RESEARCH ──────────────────────────────────────────────────────
    m = re.match(r"(?:research|investigate|find\s+out\s+about|look\s+up\s+info\s+on|get\s+info\s+on)\s+(.+)", tl)
    if m:
        return [{"action": "web_research", "query": m.group(1).strip()}]

    # ── 22. SHELL COMMAND ─────────────────────────────────────────────────────
    m = re.match(r"(?:run|execute|cmd|shell)\s+(?:command\s+)?(.+)", tl)
    if m:
        return [{"action": "run_command", "command": m.group(1).strip()}]

    # ── 23. SCHEDULE ──────────────────────────────────────────────────────────
    m = re.search(r"(?:schedule|remind\s+me|set\s+reminder)\s+(.+?)\s+(?:at|every|daily|tomorrow)\s+(.+)", tl)
    if m:
        return [{"action": "schedule_task",
                 "task":     m.group(1).strip(),
                 "schedule": m.group(2).strip()}]

    # ── 24. WHATSAPP OPEN (fallback after send check above) ───────────────────
    if re.search(r"\bwhatsapp\b", tl):
        return [{"action": "open", "target": "whatsapp web"}]

    # ── 25. SINGLE KNOWN APP/SITE NAME ───────────────────────────────────────
    for app in APPS:
        if tl.strip() == app or tl.strip().startswith(app + " "):
            return [{"action": "open",  "target": app},
                    {"action": "speak", "text":   f"Opening {app}"}]
    for site in SITES:
        if tl.strip() == site:
            return [{"action": "open",  "target": site},
                    {"action": "speak", "text":   f"Opening {site}"}]

    # ── 26. STATUS / HELP ────────────────────────────────────────────────────
    if re.search(r"\b(?:help|what\s+can\s+you\s+do|commands|capabilities)\b", tl):
        return [{"action": "speak",
                 "text": ("I can open apps and websites, send emails, take screenshots, "
                          "search the web, find leads, post to social media, control volume, "
                          "type text, run commands, and much more. Just ask!")}]

    if re.search(r"\b(?:hello|hi|hey|good\s+morning|good\s+evening|howdy)\b", tl):
        return [{"action": "speak",
                 "text": f"Hello! Dacexy Agent v{VERSION} is ready. What would you like me to do?"}]

    if re.search(r"\b(?:ping|test|are\s+you\s+(?:there|working|online)|status)\b", tl):
        return [{"action": "ping"}]

    return []  # No match — execute_task handles the unknown-command path


# =============================================================================
# COMMAND EXECUTOR
# =============================================================================
def exec_cmd(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Command must be a dict"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action specified"}

    raw_str = " ".join(str(v) for v in cmd.values()).lower()
    if any(b in raw_str for b in BLOCKED):
        log.warning("BLOCKED command: %s", action)
        return {"status": "blocked", "message": "Blocked for safety"}

    log.info("EXEC action=%s", action)
    audit.info("ACTION=EXEC | %s | params=%s", action,
               {k: v for k, v in cmd.items() if k != "action"})

    try:
        # ── SPEAK / NOTIFY ──────────────────────────────────────────────────
        if action == "speak":
            speak(str(cmd.get("text", "")))
            return {"status": "ok"}

        if action == "notify":
            _notify(str(cmd.get("title", "Dacexy")), str(cmd.get("text", "")))
            return {"status": "ok"}

        # ── CONFIGURE EMAIL ──────────────────────────────────────────────────
        # FIX: was opening a browser URL instead of running interactive setup
        if action == "configure_email":
            return configure_smtp_interactive()

        # ── OPEN / LAUNCH (catches ALL planner hallucinations) ────────────────
        if action in {
            "open", "open_url", "open_browser", "launch", "start", "navigate",
            "navigate_to", "go_to", "browse", "visit", "open_site", "open_website",
            "open_app", "run_app", "open_application", "launch_application",
            "start_application", "open_program", "run_program",
            "open_chrome", "chrome_open", "launch_chrome", "launch_browser",
            "open_browser_chrome", "open_firefox", "open_edge", "launch_edge",
            "navigate_browser", "open_url_in_browser", "start_browser",
            "open_web_browser", "load_url", "load_website", "goto",
        }:
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                   cmd.get("name") or cmd.get("site") or cmd.get("target") or
                   cmd.get("browser") or cmd.get("website") or "").strip()
            if not tgt:
                for kw in ["chrome", "firefox", "edge", "brave"]:
                    if kw in action:
                        tgt = kw; break
            if not tgt:
                return {"status": "error", "message": "No target for open"}
            return smart_open(tgt)

        # ── EMAIL ─────────────────────────────────────────────────────────────
        if action in {"send_email", "email", "compose_email", "send_mail", "mail",
                      "gmail_send", "send_message_email", "email_send"}:
            to_ = str(cmd.get("to") or cmd.get("email") or
                      cmd.get("recipient") or "").strip()
            if not to_:
                return {"status": "error", "message": "No recipient email address"}
            return send_email_real(
                to_,
                str(cmd.get("subject") or "Message from Dacexy"),
                str(cmd.get("body")    or cmd.get("text") or
                    cmd.get("content") or "Hello"))

        if action in {"bulk_email", "send_bulk_email", "mass_email",
                      "email_all", "email_blast", "email_campaign"}:
            contacts = cmd.get("contacts") or []
            csv_p    = cmd.get("csv_path") or cmd.get("file") or ""
            if csv_p and not contacts:
                contacts = load_csv_contacts(str(csv_p))
            if not contacts:
                return {"status": "error", "message": "No contacts found."}
            return send_bulk_email(
                contacts,
                str(cmd.get("subject") or "Hello from Dacexy"),
                str(cmd.get("body")    or "Hi {name},\n\nHope this finds you well!\n\nBest regards"),
                float(cmd.get("delay") or 1.5))

        if action in {"find_leads_and_email", "lead_campaign", "find_and_email"}:
            product = str(cmd.get("product") or "product")
            leads   = find_leads_web(product,
                                     str(cmd.get("niche") or ""),
                                     int(cmd.get("max") or 50))
            if not leads:
                return {"status": "error", "message": "No leads found."}
            return send_bulk_email(
                leads,
                str(cmd.get("subject") or f"About {product}"),
                str(cmd.get("body")    or
                    f"Hi {{name}},\n\nI noticed you might benefit from {product}.\n"
                    "Would you be open to a quick 5-minute chat?\n\nBest regards"),
                2.0)

        if action in {"find_leads", "lead_finder", "scrape_leads", "get_leads"}:
            leads = find_leads_web(
                str(cmd.get("product") or ""),
                str(cmd.get("niche")   or ""),
                int(cmd.get("max")     or 50))
            return {"status": "ok", "leads_found": len(leads)}

        if action in {"web_research", "research", "investigate", "research_topic"}:
            q = str(cmd.get("query") or cmd.get("text") or
                    cmd.get("topic") or "")
            if not q:
                return {"status": "error", "message": "No query for research"}
            speak(f"Researching {q[:50]}...")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(
                f"Research: {q}\nDate: {datetime.datetime.now()}\n\n{result}",
                encoding="utf-8")
            try:
                subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception:
                pass
            speak("Research done. Report opened in Notepad.")
            return {"status": "ok", "result": result[:800]}

        # ── WHATSAPP ──────────────────────────────────────────────────────────
        if action in {"whatsapp", "whatsapp_send", "send_whatsapp", "wa_send"}:
            phone = str(cmd.get("phone") or cmd.get("contact") or
                        cmd.get("to")    or "")
            if not phone:
                return {"status": "error", "message": "No phone number"}
            return wa_send(phone,
                           str(cmd.get("message") or cmd.get("text") or ""))

        # ── YOUTUBE ───────────────────────────────────────────────────────────
        if action in {"open_youtube", "youtube", "youtube_search",
                      "play_youtube", "search_youtube"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                return youtube_search_and_play(q)
            webbrowser.open("https://www.youtube.com")
            return {"status": "ok"}

        # ── SEARCH ────────────────────────────────────────────────────────────
        if action in {"search_web", "search", "google_search", "google",
                      "google_search_query", "search_google", "web_search"}:
            q = str(cmd.get("query")        or cmd.get("text") or
                    cmd.get("search_query") or "")
            if q:
                webbrowser.open(
                    f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                speak(f"Searching Google for {q[:60]}")
                return {"status": "ok"}
            webbrowser.open("https://www.google.com")
            return {"status": "ok"}

        # ── SOCIAL MEDIA ──────────────────────────────────────────────────────
        if action in {"twitter_post", "post_twitter", "tweet", "post_tweet"}:
            return post_twitter(
                str(cmd.get("username") or cmd.get("user") or ""),
                str(cmd.get("password") or cmd.get("pass") or ""),
                str(cmd.get("text")     or cmd.get("content") or ""))

        if action in {"linkedin_post", "post_linkedin", "linkedin"}:
            return post_linkedin(
                str(cmd.get("username") or ""),
                str(cmd.get("password") or ""),
                str(cmd.get("text")     or cmd.get("content") or ""))

        if action in {"facebook_post", "post_facebook", "facebook"}:
            return post_facebook(
                str(cmd.get("username") or ""),
                str(cmd.get("password") or ""),
                str(cmd.get("text")     or cmd.get("content") or ""),
                str(cmd.get("page_id")  or ""))

        if action in {"instagram_post", "post_instagram", "instagram"}:
            return post_instagram(
                str(cmd.get("username")   or ""),
                str(cmd.get("password")   or ""),
                str(cmd.get("caption")    or cmd.get("text") or ""),
                str(cmd.get("image_path") or ""))

        if action in {"post_all_social", "post_all", "all_social", "social_post_all"}:
            text  = str(cmd.get("text") or "")
            creds = cmd.get("credentials") or {}
            results = {}
            for plat, fn in [("twitter",  post_twitter),
                              ("linkedin", post_linkedin),
                              ("facebook", post_facebook)]:
                c = creds.get(plat, {})
                if c.get("username"):
                    results[plat] = fn(c["username"], c.get("password",""), text)
                else:
                    speak(f"No credentials for {plat}")
                    results[plat] = {"status": "skipped"}
            return {"status": "ok", "results": results}

        if action in {"youtube_search", "youtube_play", "play_on_youtube"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            return youtube_search_and_play(q) if q else {"status": "error"}

        # ── SELENIUM ACTIONS ─────────────────────────────────────────────────
        if action == "selenium_open":
            return selenium_open(
                str(cmd.get("url") or cmd.get("target") or ""),
                cmd.get("wait_for"),
                int(cmd.get("timeout") or 15))

        if action in {"selenium_fill", "fill_field", "type_in_field"}:
            return selenium_fill(
                str(cmd.get("selector") or ""),
                str(cmd.get("value")    or cmd.get("text") or ""),
                str(cmd.get("by")       or "css"),
                bool(cmd.get("submit",  False)))

        if action == "selenium_click":
            return selenium_click(
                str(cmd.get("selector") or ""),
                str(cmd.get("by")       or "css"))

        # ── KEYBOARD ─────────────────────────────────────────────────────────
        if action in {
            "key", "press", "press_key", "keypress",
            "press_enter",   "hit_enter",   "enter_key",  "submit_form",
            "press_escape",  "escape_key",  "press_esc",
            "press_tab",     "tab_key",
            "press_space",   "space_key",
            "press_backspace","press_delete",
            "press_up",      "press_down",  "press_left", "press_right",
            "press_f1", "press_f2", "press_f4", "press_f5",
            "press_f11", "press_f12", "confirm", "submit",
        }:
            _AK = {
                "press_enter": "enter",   "hit_enter": "enter",
                "enter_key":   "enter",   "submit_form": "enter",
                "submit":      "enter",   "confirm": "enter",
                "press_escape":"escape",  "escape_key": "escape",
                "press_esc":   "escape",
                "press_tab":   "tab",     "tab_key": "tab",
                "press_space": "space",   "space_key": "space",
                "press_backspace": "backspace",
                "press_delete":    "delete",
                "press_up":    "up",      "press_down":  "down",
                "press_left":  "left",    "press_right": "right",
                "press_f1":    "f1",      "press_f2":    "f2",
                "press_f4":    "f4",      "press_f5":    "f5",
                "press_f11":   "f11",     "press_f12":   "f12",
            }
            k = cmd.get("key") or cmd.get("keys") or _AK.get(action, "enter")
            if k and pyautogui:
                pyautogui.press(str(k))
            return {"status": "ok", "key": str(k)}

        if action in {"hotkey", "key_combo", "shortcut", "keyboard_shortcut",
                      "press_hotkey"}:
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str):
                keys = re.split(r"[+\s,]+", keys)
            if keys and pyautogui:
                pyautogui.hotkey(*[str(k) for k in keys[:5]])
            return {"status": "ok"}

        if action == "select_all":
            if pyautogui: pyautogui.hotkey("ctrl", "a")
            return {"status": "ok"}
        if action == "copy":
            if pyautogui: pyautogui.hotkey("ctrl", "c"); time.sleep(0.15)
            return {"status": "ok",
                    "clipboard": pyperclip.paste() if pyperclip else ""}
        if action == "paste":
            if pyautogui: pyautogui.hotkey("ctrl", "v")
            return {"status": "ok"}
        if action == "undo":
            if pyautogui: pyautogui.hotkey("ctrl", "z")
            return {"status": "ok"}
        if action in {"save", "save_file_shortcut"}:
            if pyautogui: pyautogui.hotkey("ctrl", "s")
            return {"status": "ok"}
        if action == "refresh":
            if pyautogui: pyautogui.hotkey("f5")
            return {"status": "ok"}
        if action == "new_tab":
            if pyautogui: pyautogui.hotkey("ctrl", "t")
            return {"status": "ok"}
        if action == "close_tab":
            if pyautogui: pyautogui.hotkey("ctrl", "w")
            return {"status": "ok"}

        # ── MOUSE ─────────────────────────────────────────────────────────────
        if action == "click":
            if not pyautogui:
                return {"status": "error", "message": "pyautogui not available"}
            x = int(cmd.get("x") or 0)
            y = int(cmd.get("y") or 0)
            if x == 0 and y == 0:
                return {"status": "skipped", "reason": "no coordinates given"}
            sw, sh = pyautogui.size()
            pyautogui.click(max(0, min(x, sw-1)), max(0, min(y, sh-1)))
            time.sleep(0.1)
            return {"status": "ok"}

        if action == "double_click":
            if pyautogui:
                pyautogui.doubleClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}

        if action == "right_click":
            if pyautogui:
                pyautogui.rightClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}

        if action in {"move_mouse", "move_to"}:
            if pyautogui:
                pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)),
                                 duration=0.3)
            return {"status": "ok"}

        if action == "drag":
            if pyautogui:
                pyautogui.dragTo(int(cmd.get("x2", 0)), int(cmd.get("y2", 0)),
                                 button="left")
            return {"status": "ok"}

        if action in {"scroll_down", "scrolldown", "scroll_down_page"}:
            if pyautogui:
                pyautogui.scroll(-int(cmd.get("amount", 5)))
            return {"status": "ok"}

        if action in {"scroll_up", "scrollup", "scroll_up_page"}:
            if pyautogui:
                pyautogui.scroll(int(cmd.get("amount", 5)))
            return {"status": "ok"}

        if action == "scroll":
            amt = int(cmd.get("clicks") or cmd.get("amount") or 3)
            d_  = str(cmd.get("direction", "down")).lower()
            if pyautogui:
                pyautogui.scroll(abs(amt) if d_ == "up" else -abs(amt))
            return {"status": "ok"}

        # ── TYPE ──────────────────────────────────────────────────────────────
        if action in {"type", "type_text", "write", "input", "enter_text",
                      "input_text", "write_text", "type_into", "enter_value",
                      "fill", "insert_text"}:
            smart_type(str(cmd.get("text") or cmd.get("content") or
                           cmd.get("value") or ""))
            return {"status": "ok"}

        # ── SCREENSHOT ────────────────────────────────────────────────────────
        if action in {"screenshot", "take_screenshot", "capture_screen",
                      "capture_screenshot", "screen_capture", "screengrab"}:
            ss = take_screenshot(save=True)
            if ss:
                speak("Screenshot taken and saved.")
                return {"status": "ok", "screenshot": ss}
            speak("Could not take screenshot.")
            return {"status": "error", "message": "Screenshot failed"}

        # ── WINDOW ────────────────────────────────────────────────────────────
        if action in {"minimize_window", "minimize", "minimise", "hide_window"}:
            if pyautogui: pyautogui.hotkey("win", "down")
            return {"status": "ok"}

        if action in {"maximize_window", "maximize", "maximise",
                      "fullscreen", "full_screen"}:
            if pyautogui: pyautogui.hotkey("win", "up")
            return {"status": "ok"}

        if action in {"close_window", "close", "close_app", "quit_app",
                      "exit_app", "alt_f4"}:
            if pyautogui: pyautogui.hotkey("alt", "f4")
            return {"status": "ok"}

        if action in {"switch_window", "alt_tab", "next_window"}:
            if pyautogui: pyautogui.hotkey("alt", "tab"); time.sleep(0.3)
            return {"status": "ok"}

        if action in {"show_desktop", "win_d"}:
            if pyautogui: pyautogui.hotkey("win", "d")
            return {"status": "ok"}

        if action in {"get_windows", "list_windows"}:
            wins = list_windows()
            speak(f"{len(wins)} windows open.")
            return {"status": "ok", "windows": wins}

        if action in {"get_active_window", "active_window"}:
            win = get_active_win()
            speak(f"Active window: {win or 'unknown'}")
            return {"status": "ok", "active_window": win}

        # ── VOLUME ────────────────────────────────────────────────────────────
        if action in {"volume_up", "increase_volume", "louder",
                      "turn_up_volume", "raise_volume"}:
            if pyautogui:
                for _ in range(min(int(cmd.get("steps", 5)), 20)):
                    pyautogui.press("volumeup")
            speak("Volume increased")
            return {"status": "ok"}

        if action in {"volume_down", "decrease_volume", "quieter",
                      "lower_volume", "turn_down_volume"}:
            if pyautogui:
                for _ in range(min(int(cmd.get("steps", 5)), 20)):
                    pyautogui.press("volumedown")
            speak("Volume decreased")
            return {"status": "ok"}

        if action in {"mute", "unmute", "toggle_mute", "mute_audio"}:
            if pyautogui: pyautogui.press("volumemute")
            speak("Audio muted / unmuted")
            return {"status": "ok"}

        # ── FILES ─────────────────────────────────────────────────────────────
        if action in {"write_file", "create_file", "save_file", "create_document"}:
            p = Path(str(cmd.get("path") or ""))
            if not p.name:
                p = AGENT_DIR / "output.txt"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(cmd.get("content") or "")[:1_000_000], encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            except Exception: pass
            speak(f"File {p.name} saved.")
            return {"status": "ok", "path": str(p)}

        if action in {"read_file", "open_file", "read_document"}:
            p = Path(str(cmd.get("path") or ""))
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="ignore")[:10000]
                speak(f"File read: {len(content)} characters.")
                return {"status": "ok", "content": content}
            return {"status": "error", "message": f"File not found: {p}"}

        if action in {"list_files", "ls", "dir_listing"}:
            folder = Path(str(cmd.get("folder") or cmd.get("path") or
                              Path.home() / "Desktop"))
            try:
                files = [f.name for f in folder.iterdir()][:50]
                speak(f"{len(files)} files in {folder.name}")
                return {"status": "ok", "files": files}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        if action in {"zip_files", "compress", "create_zip", "backup"}:
            src = Path(str(cmd.get("path") or cmd.get("folder") or
                           str(Path.home() / "Desktop")))
            dst = Path(str(cmd.get("output") or
                           str(AGENT_DIR / f"backup_{int(time.time())}.zip")))
            try:
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file():
                        zf.write(src, src.name)
                    elif src.is_dir():
                        for f in src.rglob("*"):
                            if f.is_file():
                                zf.write(f, f.relative_to(src))
                speak(f"Compressed to {dst.name}")
                return {"status": "ok", "zip": str(dst)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # ── SYSTEM INFO ───────────────────────────────────────────────────────
        if action in {"get_system_info", "system_info", "sysinfo",
                      "system_status", "check_system", "cpu_info",
                      "ram_info", "hardware_info"}:
            if psutil:
                dp   = "C:\\" if platform.system() == "Windows" else "/"
                info = {
                    "cpu":          psutil.cpu_percent(interval=0.5),
                    "cpu_cores":    psutil.cpu_count(),
                    "ram":          psutil.virtual_memory().percent,
                    "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                    "disk":         psutil.disk_usage(dp).percent,
                    "disk_free_gb": round(psutil.disk_usage(dp).free  / 1e9, 1),
                    "platform":     platform.system(),
                    "hostname":     socket.gethostname(),
                    "python":       platform.python_version(),
                }
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%, "
                      f"Disk {info['disk']}%")
                return {"status": "ok", "info": info}
            return {"status": "ok", "info": {"platform": platform.system()}}

        if action == "get_time":
            t_ = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {t_}")
            return {"status": "ok", "time": t_}

        if action == "get_date":
            d_ = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {d_}")
            return {"status": "ok", "date": d_}

        # ── SHELL ─────────────────────────────────────────────────────────────
        if action in {"run_command", "execute_command", "shell", "cmd_run",
                      "execute", "terminal_command"}:
            c_ = str(cmd.get("command") or cmd.get("cmd") or "")
            if not c_:
                return {"status": "error", "message": "No command specified"}
            if any(b in c_.lower() for b in BLOCKED):
                return {"status": "blocked", "message": "Blocked for safety"}
            try:
                r_ = subprocess.run(c_, shell=True, capture_output=True, text=True,
                                    timeout=60, encoding="utf-8", errors="replace")
                out = (r_.stdout or "")[:5000]
                if out.strip():
                    speak(out[:200])
                return {"status": "ok", "stdout": out,
                        "returncode": r_.returncode}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out (60s)"}

        # ── MEMORY ────────────────────────────────────────────────────────────
        if action in {"remember", "save_fact", "take_note", "memorize", "store_fact"}:
            fact = str(cmd.get("fact") or cmd.get("text") or
                       cmd.get("content") or "")
            if fact:
                remember(fact)
                speak("Got it, I'll remember that.")
            return {"status": "ok"}

        if action in {"get_memory", "show_memory", "recall", "what_do_you_know"}:
            ctx = get_mem_ctx()
            speak("Memory retrieved.")
            return {"status": "ok", "memory": ctx}

        if action in {"add_contact", "save_contact", "new_contact"}:
            name = str(cmd.get("name", ""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {
                        "name":  name,
                        "email": str(cmd.get("email", "")),
                        "phone": str(cmd.get("phone", "")),
                    }
                save_memory()
                speak(f"Contact {name} saved.")
            return {"status": "ok"}

        # ── SCHEDULE ──────────────────────────────────────────────────────────
        if action in {"schedule_task", "schedule", "add_schedule", "set_reminder"}:
            task_s = str(cmd.get("task") or cmd.get("command") or "")
            sched  = str(cmd.get("schedule") or cmd.get("time") or "daily at 09:00")
            if not task_s:
                return {"status": "error", "message": "No task to schedule"}
            job = {
                "id":       "".join(random.choices(string.ascii_lowercase, k=8)),
                "task":     task_s,
                "schedule": sched,
                "last_run": "",
            }
            _sched_jobs.append(job); save_memory()
            speak(f"Scheduled: {task_s[:50]} - runs {sched}")
            return {"status": "ok", "job_id": job["id"]}

        # ── WAIT ─────────────────────────────────────────────────────────────
        if action in {"wait", "sleep", "pause", "delay"}:
            secs = min(float(cmd.get("seconds") or cmd.get("duration") or 1), 60)
            time.sleep(secs)
            return {"status": "ok"}

        # ── HEALTH / PING ─────────────────────────────────────────────────────
        if action in {"ping", "test", "health", "health_check", "status",
                      "heartbeat", "check_connection", "verify", "pong"}:
            speak("I am online and working!")
            return {"status": "ok", "pong": True, "version": VERSION}

        # ── BRIGHTNESS ────────────────────────────────────────────────────────
        if action in {"brightness_up", "increase_brightness"}:
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI "
                             "-Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)",
                             shell=True)
            return {"status": "ok"}

        if action in {"brightness_down", "decrease_brightness"}:
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI "
                             "-Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)",
                             shell=True)
            return {"status": "ok"}

        # ── MEDIA CONTROLS ────────────────────────────────────────────────────
        if action in {"media_play_pause", "play_pause"}:
            if pyautogui: pyautogui.press("playpause")
            return {"status": "ok"}
        if action in {"media_next", "next_track"}:
            if pyautogui: pyautogui.press("nexttrack")
            return {"status": "ok"}
        if action in {"media_prev", "prev_track", "previous_track"}:
            if pyautogui: pyautogui.press("prevtrack")
            return {"status": "ok"}

        # ── OCR ───────────────────────────────────────────────────────────────
        if action in {"ocr", "ocr_screen", "read_screen", "screen_text"}:
            if OCR_OK and ImageGrab:
                img  = ImageGrab.grab()
                text = pytesseract.image_to_string(img)
                speak("Screen text extracted.")
                return {"status": "ok", "text": text[:5000]}
            ss = take_screenshot()
            return {"status": "ok", "text": "", "screenshot": ss or "",
                    "note": "pytesseract not installed"}

        # ═════════════════════════════════════════════════════════════════════
        # ULTIMATE FALLBACK — try smart_open, then action name itself
        # ═════════════════════════════════════════════════════════════════════
        tgt = (cmd.get("url") or cmd.get("app") or cmd.get("target") or
               cmd.get("name") or cmd.get("site") or cmd.get("website") or "")
        if tgt:
            res = smart_open(str(tgt))
            if res.get("status") == "ok":
                return res

        action_readable = action.replace("_", " ").strip()
        res = smart_open(action_readable)
        if res.get("status") == "ok":
            return res

        log.warning("Unhandled action after all fallbacks: '%s'", action)
        return {"status": "error", "message": f"Unknown action: '{action}'"}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e, exc_info=True)
        return {"status": "error", "message": f"Exception in {action}: {e}"}


# =============================================================================
# MAIN TASK EXECUTOR — no AI planner, local_parse handles everything
# =============================================================================
def execute_task(task: str, token: str) -> dict:
    if not task or not task.strip():
        return {"status": "error", "ok": 0, "total": 0, "result": "Empty task"}

    task = task.strip()
    log.info("TASK: %s", task[:120])
    print(f"\n  [TASK] Executing: {task[:80]}")
    _convo.append(f"user: {task[:120]}")

    # 1. Local NLP (fast, reliable, no network)
    commands = local_parse(task)
    source   = "local"

    # 2. If local can't parse it, try smart_open for short phrases
    if not commands:
        tl = task.lower().strip()
        words = tl.split()
        # Short phrase that could be an app/website name
        is_open_like = (len(words) <= 5 and
                        not any(w in tl for w in ["send", "email", "search",
                                                   "find", "create", "write",
                                                   "post", "make", "research",
                                                   "schedule", "remind"]))
        if is_open_like:
            res = smart_open(task)
            if res.get("status") == "ok":
                _convo.append(f"dacexy: Opened {task[:60]}")
                with _mem_lock:
                    MEMORY["task_history"].append(
                        f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
                save_memory()
                speak(f"Done! Opened {res.get('opened', task)[:60]}")
                return {"status": "ok", "ok": 1, "total": 1,
                        "result": f"Opened: {task}"}

        # 3. Last resort: tell user clearly what happened
        speak("I'm not sure how to do that. Try rephrasing, or say 'help' for examples.")
        return {"status": "error", "ok": 0, "total": 0,
                "result": f"Could not understand: {task[:80]}"}

    ok_count = 0
    total    = len(commands)
    results  = []

    print(f"  [TASK] Executing {total} steps ({source} plan)...")
    audit.info("ACTION=TASK_START | steps=%d | source=%s | task=%s",
               total, source, task[:80])

    for i, c in enumerate(commands):
        if not isinstance(c, dict):
            total -= 1
            continue
        step_action = c.get("action", "?")
        log.info("  Step %d/%d [%s]: %s | params=%s",
                 i+1, total, source, step_action,
                 {k: v for k, v in c.items() if k != "action"})
        print(f"  [STEP {i+1}/{total}] {step_action}")

        try:
            res = exec_cmd(c, token)
            results.append(res)
            if res.get("status") in ("ok", "skipped"):
                ok_count += 1
                print(f"  [OK] Step {i+1} done")
            else:
                log.warning("  Step %d failed: %s", i+1, res.get("message", "?"))
                print(f"  [FAIL] Step {i+1}: {res.get('message', '?')}")
            time.sleep(0.2)
        except Exception as e:
            log.error("  Step %d exception: %s", i+1, e)
            results.append({"status": "error", "message": str(e)})

    with _mem_lock:
        MEMORY["task_history"].append(
            f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
    save_memory()

    summary = f"Task done: {ok_count}/{total} steps for: {task[:60]}"
    log.info(summary)
    _convo.append(f"dacexy: {'Done' if ok_count > 0 else 'Failed'} - {summary}")
    audit.info("ACTION=TASK_END | ok=%d | total=%d | task=%s",
               ok_count, total, task[:60])

    return {
        "status":  "ok" if ok_count > 0 else "error",
        "ok":      ok_count,
        "total":   total,
        "result":  summary,
        "steps":   results,
    }


# =============================================================================
# SCHEDULER
# =============================================================================
def _scheduler_loop(token_ref: list):
    while _running:
        try:
            now = datetime.datetime.now()
            for job in list(_sched_jobs):
                sched = job.get("schedule", "").lower()
                last  = job.get("last_run", "")
                run   = False
                if "daily at" in sched:
                    m = re.search(r"(\d{1,2}):(\d{2})", sched)
                    if m:
                        h, mi = int(m.group(1)), int(m.group(2))
                        if now.hour == h and now.minute == mi:
                            ts = now.strftime("%Y-%m-%dT%H:%M")
                            if not last or last[:16] != ts:
                                run = True
                if run:
                    job["last_run"] = now.isoformat()
                    save_memory()
                    tok = token_ref[0]
                    if tok:
                        t_ = job.get("task", "")
                        threading.Thread(target=execute_task, args=(t_, tok),
                                         daemon=True).start()
                        log.info("Scheduled job fired: %s", t_[:60])
        except Exception as e:
            log.warning("Scheduler loop: %s", e)
        time.sleep(30)


# =============================================================================
# VOICE
# =============================================================================
def _is_wake_word(heard: str) -> bool:
    h = heard.lower().strip()
    for w in WAKE_WORDS:
        if re.search(r'\b' + re.escape(w) + r'\b', h):
            return True
    return False


def _voice_loop():
    global _voice_on
    if not VOICE_OK or not sr:
        print("  [VOICE] Disabled - install PyAudio to enable voice control.")
        return

    rec = sr.Recognizer()
    rec.energy_threshold      = 350
    rec.dynamic_energy_threshold = True
    rec.pause_threshold       = 0.7
    rec.non_speaking_duration = 0.4

    print("  [VOICE] Active! Say: Dacexy / Hey Dacexy / Jarvis / Computer")
    speak("Voice assistant ready. Say Dacexy or Hey Dacexy to give a command.")

    while _voice_on and _running:
        heard = ""
        try:
            with sr.Microphone() as src:
                try:   rec.adjust_for_ambient_noise(src, duration=0.1)
                except Exception: pass
                try:   audio = rec.listen(src, timeout=3, phrase_time_limit=7)
                except sr.WaitTimeoutError: continue
                except OSError: time.sleep(2); continue
            try:   heard = rec.recognize_google(audio, language="en-IN").lower().strip()
            except sr.UnknownValueError:   continue
            except sr.RequestError:        time.sleep(3); continue
        except Exception:
            time.sleep(1); continue

        if not _is_wake_word(heard):
            continue

        log.info("Wake word detected: '%s'", heard)
        speak("Yes?")
        time.sleep(0.3)

        command = ""
        try:
            with sr.Microphone() as csrc:
                try:   rec.adjust_for_ambient_noise(csrc, duration=0.08)
                except Exception: pass
                try:   caudio = rec.listen(csrc, timeout=8, phrase_time_limit=30)
                except sr.WaitTimeoutError:
                    speak("I didn't catch that."); continue
                except OSError: continue
            try:   command = rec.recognize_google(caudio, language="en-IN").strip()
            except sr.UnknownValueError:
                speak("Could you say that again?"); continue
            except sr.RequestError: continue
        except Exception: continue

        if not command:
            continue

        log.info("Voice command: '%s'", command)
        with _tok_lock: tok = _cur_token
        if not tok:
            speak("Not logged in yet."); continue

        speak("On it!")

        def _run(t_=tok, cmd_=command):
            try:
                execute_task(cmd_, t_)
            except Exception as exc:
                log.error("Voice task error: %s", exc)
                speak("Sorry, there was an error with that command.")

        threading.Thread(target=_run, daemon=True, name="VoiceTask").start()


def start_voice(token: str) -> bool:
    global _voice_on, _cur_token
    with _tok_lock: _cur_token = token
    if not VOICE_OK:
        return False
    _voice_on = True
    threading.Thread(target=_voice_loop, daemon=True, name="Voice").start()
    return True


def stop_voice():
    global _voice_on
    _voice_on = False


def update_token(t: str):
    global _cur_token
    with _tok_lock: _cur_token = t


# =============================================================================
# HEARTBEAT
# =============================================================================
def _heartbeat(token_ref: list):
    while _running:
        time.sleep(240)
        try:
            tok = token_ref[0]
            if tok and not check_token_valid(tok):
                log.warning("Token may be expired - try re-logging.")
        except Exception:
            pass


# =============================================================================
# WEBSOCKET — fixed connect_kw for ALL websockets versions
# =============================================================================
async def run_websocket(token: str):
    retry = 4.0; max_retry = 60.0

    while _running:
        try:
            log.info("WS: connecting to %s", BACKEND_WS)
            print("  [WS] Connecting to Dacexy cloud...")

            # FIX: Build connect kwargs safely for any websockets version
            # websockets < 10: close_timeout
            # websockets >= 10: open_timeout (but connect signature differs)
            # Safest: just use ping_interval/ping_timeout/max_size always
            connect_kw: dict = {
                "ping_interval": 20,
                "ping_timeout":  15,
                "max_size":      16 * 1024 * 1024,
            }
            # Only add timeout param if we can verify the version safely
            try:
                wsv_str = str(getattr(websockets, "__version__", "0"))
                wsv = int(wsv_str.split(".")[0])
                if wsv >= 14:
                    # websockets 14+ uses open_timeout in connect()
                    connect_kw["open_timeout"] = 20
                else:
                    # older versions use close_timeout
                    connect_kw["close_timeout"] = 10
            except Exception:
                # If version detection fails, just don't add timeout — safe default
                pass

            async with websockets.connect(BACKEND_WS, **connect_kw) as ws:
                # Auth handshake
                await ws.send(json.dumps({"token": token}))
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=25)
                    auth_msg = json.loads(auth_raw)
                    if auth_msg.get("type") == "error":
                        log.error("WS auth rejected: %s", auth_msg.get("message"))
                        speak("Authentication failed. Check your account.")
                        await asyncio.sleep(retry)
                        retry = min(retry * 1.5, max_retry)
                        continue
                except asyncio.TimeoutError:
                    log.warning("WS: auth timeout")
                    await asyncio.sleep(retry)
                    retry = min(retry * 1.5, max_retry)
                    continue
                except Exception as e:
                    log.warning("WS: auth error: %s", e)
                    await asyncio.sleep(retry)
                    continue

                # Send capabilities
                await ws.send(json.dumps({
                    "type":     "init",
                    "version":  VERSION,
                    "platform": platform.system(),
                    "machine":  platform.machine(),
                    "hostname": socket.gethostname(),
                    "features": [
                        "voice3", "vision", "browser", "email",
                        "social_selenium", "bulk_email", "lead_gen",
                        "web_research", "scheduler", "memory",
                        "selenium", "ocr", "screenshot", "v25_fixed",
                        "no_ai_planner", "local_nlp_200patterns",
                    ],
                }))

                log.info("WS: connected and authenticated!")
                print("\n  [OK] Connected to Dacexy cloud - agent is LIVE!")
                speak("Connected! Ready for your commands.")
                retry = 4.0

                ws_lock = asyncio.Lock()
                loop    = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with ws_lock:
                        try:
                            await ws.send(json.dumps(data))
                        except Exception as e_:
                            log.warning("ws_send error: %s", e_)

                while _running:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=50)
                    except asyncio.TimeoutError:
                        try:
                            await asyncio.wait_for(
                                ws.send(json.dumps({"type": "ping"})), timeout=8)
                        except Exception:
                            break
                        continue

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    mtype    = msg.get("type",    "")
                    action   = msg.get("action",  "")
                    task_txt = (msg.get("task")  or msg.get("goal") or "").strip()
                    task_id  = str(msg.get("task_id") or "")

                    if mtype == "ping":
                        await ws_send({"type": "pong", "version": VERSION})
                        continue
                    if mtype in ("pong", "connected", "init_ack", "heartbeat"):
                        continue

                    # Direct action (from dashboard command panel)
                    if action and action not in ("swarm_task", "task",
                                                 "run_agent", ""):
                        def _cmd_thread(m_=dict(msg), t_=token, tid_=task_id):
                            try:
                                r_ = exec_cmd(m_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":    "task_result",
                                    "task_id": tid_,
                                    "status":  r_.get("status", "ok"),
                                    "ok":      1 if r_.get("status") in
                                                   ("ok", "skipped") else 0,
                                    "total":   1,
                                    "result":  str(r_.get("message") or
                                                   r_.get("opened") or "done"),
                                    "data":    r_,
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":    "task_result",
                                    "task_id": tid_,
                                    "status":  "error",
                                    "ok":      0, "total": 1,
                                    "result":  str(e_),
                                }), loop)
                        threading.Thread(target=_cmd_thread, daemon=True).start()
                        continue

                    # Natural-language task
                    if task_txt or mtype in ("task", "command"):
                        if not task_txt:
                            task_txt = action
                        if not task_txt:
                            continue
                        log.info("Dashboard task: %s", task_txt[:80])
                        print(f"\n  [TASK] From dashboard: {task_txt[:80]}")
                        speak(f"On it! Working on: {task_txt[:50]}")

                        def _task_thread(t_=token, txt_=task_txt, tid_=task_id):
                            try:
                                r_ = execute_task(txt_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":    "task_result",
                                    "task_id": tid_,
                                    "status":  r_.get("status", "ok"),
                                    "ok":      r_.get("ok",     0),
                                    "total":   r_.get("total",  1),
                                    "result":  r_.get("result", ""),
                                    "steps":   r_.get("steps",  []),
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":    "task_result",
                                    "task_id": tid_,
                                    "status":  "error",
                                    "ok":      0, "total": 0,
                                    "result":  str(e_),
                                }), loop)
                        threading.Thread(target=_task_thread, daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK:
            log.info("WS: connection closed cleanly")
        except websockets.exceptions.ConnectionClosedError as e:
            log.warning("WS: connection error: %s", e)
        except OSError as e:
            log.warning("WS: network error: %s", e)
        except Exception as e:
            log.error("WS: unexpected error: %s", e)

        if _running:
            print(f"\n  [WS] Disconnected. Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry)
            retry = min(retry * 1.5, max_retry)


# =============================================================================
# INTERACTIVE SHELL
# =============================================================================
def _interactive_shell(token: str, tok_ref: list):
    cmds = {
        "help":       "Show this menu",
        "memory":     "Show stored memory",
        "jobs":       "List scheduled jobs",
        "sysinfo":    "System information",
        "screenshot": "Take a screenshot",
        "email":      "Configure SMTP email",
        "quit/exit":  "Exit agent",
    }

    print("\n" + "="*60)
    print(f"  DACEXY v{VERSION} - COMMAND CENTER")
    print("="*60)
    print(f"  Email   : {_smtp_cfg.get('email') or 'NOT CONFIGURED'}")
    print(f"  Voice   : {'ON' if _voice_on else 'OFF'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print("="*60)
    print("  Type any task and press Enter. Type 'help' for commands.")
    print("="*60 + "\n")

    while _running:
        try:
            line = input("  Dacexy> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue

        tl = line.lower()

        if tl in ("quit", "exit"):
            print("  Goodbye!"); break
        if tl in ("help", "menu"):
            print()
            for k, v in cmds.items():
                print(f"    {k:<14} {v}")
            print()
            continue
        if tl == "memory":
            print("\n" + get_mem_ctx() + "\n"); continue
        if tl == "jobs":
            if _sched_jobs:
                for j in _sched_jobs:
                    print(f"  [{j['id']}] {j['task']} - {j['schedule']}")
            else:
                print("  No scheduled jobs.")
            continue
        if tl == "email":
            configure_smtp_interactive(); continue
        if tl == "sysinfo":
            exec_cmd({"action": "get_system_info"}, token); continue
        if tl == "screenshot":
            exec_cmd({"action": "screenshot"}, token); continue

        print(f"  [TASK] Processing: {line[:80]}")
        tok = tok_ref[0]

        def _run(t_=tok, cmd_=line):
            r = execute_task(cmd_, t_)
            ok, tot = r.get("ok", 0), r.get("total", 1)
            print(f"\n  [{'OK' if r['status']=='ok' else 'FAIL'}] "
                  f"Task done: {ok}/{tot} steps.")

        threading.Thread(target=_run, daemon=True, name="ShellTask").start()


# =============================================================================
# MAIN
# =============================================================================
def main():
    global _running

    print("\n" + "="*60)
    print(f"  DACEXY DESKTOP AGENT v{VERSION}")
    print("  Full-featured autonomous Windows AI agent")
    print("  AI planner removed - local NLP handles 200+ commands")
    print("="*60 + "\n")

    init_tts()
    load_memory()

    caps = []
    if pyautogui:                  caps.append("mouse/keyboard")
    if ImageGrab:                  caps.append("screenshot")
    if VOICE_OK:                   caps.append("VOICE")
    if SELENIUM_OK:                caps.append("browser-automation")
    if BS4_OK:                     caps.append("web-scraping")
    if OCR_OK:                     caps.append("OCR")
    if _smtp_cfg.get("email"):     caps.append(f"email={_smtp_cfg['email']}")
    else:                          caps.append("email=NOT CONFIGURED")
    print(f"  Capabilities: {', '.join(caps) or 'basic'}\n")

    token = get_token()
    if token:
        print("  Checking saved session...")
        if check_token_valid(token):
            print("  [OK] Session valid.\n")
        else:
            print("  Session expired - please log in.\n")
            clear_token(); token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2:
                print(f"\n  Attempt {attempt+1}/3 failed. Try again.\n")
        if not token:
            print("\n  [ERROR] Authentication failed. Exiting.")
            sys.exit(1)

    try: setup_autostart()
    except Exception: pass

    if not _smtp_cfg.get("email"):
        print("  [EMAIL] Not configured. Say 'configure email' to enable bulk send.\n")
    else:
        print(f"  [EMAIL] Ready - {_smtp_cfg['email']}\n")

    voice_ok = start_voice(token)
    tok_ref  = [token]

    threading.Thread(target=_heartbeat,        args=(tok_ref,),  daemon=True,
                     name="Heartbeat").start()
    threading.Thread(target=_scheduler_loop,   args=(tok_ref,),  daemon=True,
                     name="Scheduler").start()
    threading.Thread(target=_interactive_shell, args=(token, tok_ref), daemon=True,
                     name="Shell").start()

    print("  " + "-"*56)
    print(f"  Dacexy Agent v{VERSION} - LIVE")
    print(f"  Voice    : {'ON - say Dacexy / Hey Dacexy' if voice_ok else 'OFF'}")
    print(f"  Email    : {_smtp_cfg.get('email') or 'Not configured'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print(f"  Log file : {LOG_FILE}")
    print("  " + "-"*56 + "\n")

    if not websockets:
        print("  [ERROR] websockets package not installed!")
        sys.exit(1)

    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n  Stopped by user.")
    except Exception as e:
        log.error("Fatal WebSocket error: %s", e)
    finally:
        _running = False
        stop_voice()
        with _sel_lock:
            if _selenium_driver:
                try: _selenium_driver.quit()
                except Exception: pass
        try: save_memory()
        except Exception: pass
        print("  Dacexy stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
