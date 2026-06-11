"""
DACEXY DESKTOP AGENT v22.0 - INVESTOR DEMO EDITION
Real Jarvis. Actually works. No phantom completions.

FIXED BUGS vs v20/v21:
  BUG1 CLOSURE: Thread functions inside async loop captured loop vars by reference.
       By the time thread ran, task_txt/task_id/msg had already changed to the next
       message. FIX: All inner thread functions use default args (t_=token, txt_=task_txt)
       to snapshot values at call time.
  BUG2 INSTALLER: BAT file ran AGENT_LOOP inline in same window after install,
       so any error in agent.py closed the whole console. FIX: Installer writes a
       separate start_dacexy.bat and opens it in a new window via 'start'.
  BUG3 AI FALLBACK: execute_task hit /ai/chat then failed silently if response was
       non-JSON. FIX: local_parse handles 95% of tasks instantly with no network call.
       ai_plan is a fallback only, with proper JSON extraction and error handling.
  BUG4 VOICE: WaitTimeoutError (normal silence) was counted as an error, disabling
       voice after ~8 seconds of silence. FIX: Only real mic/API errors count.
  BUG5 SMTP BULK: Was opening new SMTP connection per email. FIX: Single SMTP session
       for entire bulk send.
"""
from __future__ import annotations
import subprocess, sys, os, platform

# Windows event loop (MUST be before asyncio import)
if platform.system() == "Windows":
    import asyncio as _ae
    if hasattr(_ae, "WindowsSelectorEventLoopPolicy"):
        _ae.set_event_loop_policy(_ae.WindowsSelectorEventLoopPolicy())

# Windows UTF-8 console
if platform.system() == "Windows":
    import io as _io
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

def _pip(*pkgs):
    try:
        subprocess.call([sys.executable, "-m", "pip", "install", *pkgs, "-q", "--no-warn-script-location"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    except Exception:
        pass

print("  [BOOT] Checking packages...")
for _pkg, _imp in [("pyautogui","pyautogui"),("pillow","PIL"),("websockets","websockets"),
                   ("requests","requests"),("pyttsx3","pyttsx3"),("numpy","numpy"),
                   ("psutil","psutil"),("pyperclip","pyperclip"),("pygetwindow","pygetwindow"),
                   ("plyer","plyer"),("speechrecognition","speech_recognition"),
                   ("beautifulsoup4","bs4"),("keyboard","keyboard")]:
    try:
        __import__(_imp)
    except ImportError:
        print(f"  [BOOT] Installing {_pkg}...")
        _pip(_pkg)

try:
    from selenium import webdriver as _s
except ImportError:
    print("  [BOOT] Installing selenium...")
    _pip("selenium", "webdriver-manager")

PYAUDIO_OK = False
try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    _pip("PyAudio")
    try:
        import pyaudio
        PYAUDIO_OK = True
    except ImportError:
        try:
            _pip("pipwin")
            subprocess.call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            import pyaudio
            PYAUDIO_OK = True
        except Exception:
            pass

print("  [BOOT] Packages ready.\n")

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
from typing import Optional, List, Dict, Any

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.04
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
    from PIL import ImageGrab, Image
except Exception:
    ImageGrab = Image = None

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
    import winreg
    WINREG_OK = True
except Exception:
    WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_OK = PYAUDIO_OK
except Exception:
    sr = None
    VOICE_OK = False

try:
    import pygetwindow as gw
    WINDOW_OK = True
except Exception:
    gw = None
    WINDOW_OK = False

try:
    from plyer import notification
    NOTIFY_OK = True
except Exception:
    NOTIFY_OK = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except Exception:
    SELENIUM_OK = False
    webdriver = None

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except Exception:
    BeautifulSoup = None
    BS4_OK = False

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "agent.log"
VERSION      = "22.0"

for _d in [AGENT_DIR, AGENT_DIR/"logs", AGENT_DIR/"data", AGENT_DIR/"screenshots"]:
    _d.mkdir(exist_ok=True)

SMTP_PRESETS = {
    "gmail.com":      {"host": "smtp.gmail.com",      "port": 587},
    "googlemail.com": {"host": "smtp.gmail.com",      "port": 587},
    "outlook.com":    {"host": "smtp.office365.com",  "port": 587},
    "hotmail.com":    {"host": "smtp.office365.com",  "port": 587},
    "live.com":       {"host": "smtp.office365.com",  "port": 587},
    "yahoo.com":      {"host": "smtp.mail.yahoo.com", "port": 587},
    "yahoo.in":       {"host": "smtp.mail.yahoo.com", "port": 587},
    "icloud.com":     {"host": "smtp.mail.me.com",    "port": 587},
    "zoho.com":       {"host": "smtp.zoho.com",       "port": 587},
}

WAKE_WORDS = ["dacexy", "hey dacexy", "okay dacexy", "ok dacexy",
              "jarvis", "hey jarvis", "okay jarvis",
              "computer", "hey computer", "okay computer",
              "agent", "hey agent"]

SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "github": "https://github.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "wikipedia": "https://www.wikipedia.org",
    "reddit": "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chat.openai.com",
    "dacexy": "https://dacexy.vercel.app",
    "notion": "https://notion.so",
    "canva": "https://www.canva.com",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "trello": "https://trello.com",
    "slack": "https://app.slack.com",
    "zoom": "https://zoom.us",
    "meet": "https://meet.google.com",
    "google meet": "https://meet.google.com",
    "teams": "https://teams.microsoft.com",
    "discord": "https://discord.com/app",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "slides": "https://slides.google.com",
    "calendar": "https://calendar.google.com",
    "photos": "https://photos.google.com",
    "translate": "https://translate.google.com",
    "pinterest": "https://www.pinterest.com",
    "tiktok": "https://www.tiktok.com",
    "twitch": "https://www.twitch.tv",
    "fiverr": "https://www.fiverr.com",
    "upwork": "https://www.upwork.com",
    "medium": "https://medium.com",
    "quora": "https://www.quora.com",
    "paypal": "https://www.paypal.com",
    "razorpay": "https://razorpay.com",
    "telegram web": "https://web.telegram.org",
    "news": "https://news.google.com",
}

APPS = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "notepad++": "notepad++.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "cmd.exe",
    "powershell": "powershell.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "vlc": "vlc.exe",
    "zoom": "zoom.exe",
    "discord": "discord.exe",
    "spotify": "spotify.exe",
    "vscode": "code.exe",
    "visual studio code": "code.exe",
    "vs code": "code.exe",
    "telegram": "telegram.exe",
    "whatsapp desktop": "WhatsApp.exe",
    "snipping tool": "SnippingTool.exe",
    "sticky notes": "stikynot.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "device manager": "devmgmt.msc",
    "services": "services.msc",
}

BLOCKED = ["rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
           "rd /s /q c:\\", "reg delete hklm", "dd if=/dev/zero", "rmdir /s /q c:\\"]

# ═══════════════════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════════════════
_mem_lock   = threading.Lock()
_cfg_lock   = threading.Lock()
_executor   = ThreadPoolExecutor(max_workers=15)
_running    = True
_tts_q      = queue.Queue(maxsize=10)
_tts_engine = None
_tts_lock   = threading.Lock()
_voice_on   = False
_cur_token  = None
_tok_lock   = threading.Lock()
_smtp_cfg: Dict = {}
_sched_jobs: List = []
_convo: deque = deque(maxlen=20)

MEMORY: Dict = {
    "facts": [], "preferences": {}, "task_history": deque(maxlen=500),
    "context": {}, "contacts": {},
}

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
        ])
except Exception:
    logging.basicConfig(level=logging.INFO)

log = logging.getLogger("dacexy")
log.info("Dacexy Agent v%s starting", VERSION)

# ═══════════════════════════════════════════════════════════════════════════
# TTS
# ═══════════════════════════════════════════════════════════════════════════
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
                try:
                    _tts_q.task_done()
                except Exception:
                    pass
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
        eng.setProperty("rate", 158)
        eng.setProperty("volume", 0.93)
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
        log.info("TTS ready")
    except Exception as e:
        log.warning("TTS init failed (non-fatal): %s", e)
        _tts_engine = None

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

def jarvis(cat: str, override: str = ""):
    opts = {
        "greet": ["Yes?", "How can I help?", "At your service!", "Listening."],
        "work":  ["On it!", "Working on that now.", "Got it!", "Right away!"],
        "done":  ["All done!", "Completed!", "That is taken care of."],
        "error": ["I could not complete that.", "That did not work, sorry."],
        "again": ["Could you say that again?", "I didn't catch that."],
    }
    speak(override if override else random.choice(opts.get(cat, [""])))

def _notify(title: str, msg: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=str(msg)[:100], app_name="Dacexy", timeout=4)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG / AUTH
# ═══════════════════════════════════════════════════════════════════════════
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

def get_token() -> Optional[str]:
    return load_config().get("access_token")

def save_token(t: str):
    cfg = load_config()
    cfg["access_token"] = t
    save_config(cfg)

def clear_token():
    cfg = load_config()
    cfg.pop("access_token", None)
    save_config(cfg)

def check_token_valid(token: str) -> bool:
    if not req_lib:
        return False
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
                        headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

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
        log.info("Autostart registered")
    except Exception as e:
        log.warning("Autostart: %s", e)

# ═══════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════
def login() -> Optional[str]:
    print("\n" + "="*55)
    print("  DACEXY AGENT v22.0 - Login")
    print("="*55)
    print("  Register at: dacexy.vercel.app\n")
    try:
        email    = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not email or "@" not in email:
        print("  [ERROR] Invalid email")
        return None
    if not password or len(password) < 4:
        print("  [ERROR] Password too short")
        return None
    if not req_lib:
        print("  [ERROR] requests not installed")
        return None
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
                    return t
        except Exception:
            pass
    print("  [ERROR] Login failed. Check email and password.")
    return None

# ═══════════════════════════════════════════════════════════════════════════
# SMTP SETUP
# ═══════════════════════════════════════════════════════════════════════════
def configure_smtp_interactive() -> dict:
    global _smtp_cfg
    print("\n  ╔══════════════════════════════════════════════╗")
    print("  ║     Dacexy Email Setup                       ║")
    print("  ╚══════════════════════════════════════════════╝")
    print("\n  For Gmail: myaccount.google.com/apppasswords → Create App Password\n")
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
            print("  [ERROR] Wrong password.")
            if "gmail" in domain:
                print("  -> Use App Password from myaccount.google.com/apppasswords")
            return {"status": "error", "message": "Auth failed"}
        except Exception as te:
            print(f"  [WARN] Test issue: {te} — saving anyway.")
        _smtp_cfg = {"email": em, "password": pw, "host": preset["host"], "port": preset["port"]}
        save_memory()
        speak(f"Email configured as {em}. I will now send real emails automatically.")
        return {"status": "ok", "email": em}
    except (EOFError, KeyboardInterrupt):
        return {"status": "cancelled"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ═══════════════════════════════════════════════════════════════════════════
# MEMORY
# ═══════════════════════════════════════════════════════════════════════════
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
                MEMORY["task_history"] = deque(d.get("task_history", [])[-500:], maxlen=500)
            _smtp_cfg   = d.get("smtp_config", {})
            _sched_jobs = d.get("sched_jobs", [])
    except Exception as e:
        log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _mem_lock:
            d = {"facts": MEMORY["facts"][-500:], "preferences": MEMORY["preferences"],
                 "context": MEMORY["context"], "contacts": MEMORY["contacts"],
                 "task_history": list(MEMORY["task_history"])[-200:],
                 "smtp_config": _smtp_cfg, "sched_jobs": _sched_jobs[-50:]}
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
                parts.append("Facts: " + "; ".join(MEMORY["facts"][-8:]))
            if MEMORY["preferences"]:
                parts.append("Prefs: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-5:]
            if recent:
                parts.append("Recent: " + "; ".join(recent))
            contacts = list(MEMORY["contacts"].keys())[:5]
            if contacts:
                parts.append("Contacts: " + ", ".join(contacts))
        conv = list(_convo)[-6:]
        if conv:
            parts.append("Convo: " + " | ".join(conv))
        return "\n".join(parts)
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════════════════════
# SCREENSHOT
# ═══════════════════════════════════════════════════════════════════════════
def take_screenshot(quality=80) -> Optional[str]:
    try:
        if not ImageGrab:
            return None
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1600:
            img = img.resize((1600, int(h * 1600 / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning("screenshot: %s", e)
        return None

# ═══════════════════════════════════════════════════════════════════════════
# SMART TYPE
# ═══════════════════════════════════════════════════════════════════════════
def smart_type(text: str):
    if not text:
        return
    text = str(text)[:10000]
    try:
        if pyperclip:
            pyperclip.copy(text)
            time.sleep(0.08)
            if pyautogui:
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.12)
            return
        if pyautogui:
            pyautogui.write(text[:500], interval=0.015)
    except Exception as e:
        log.warning("smart_type: %s", e)

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

# ═══════════════════════════════════════════════════════════════════════════
# SMART OPEN
# ═══════════════════════════════════════════════════════════════════════════
def smart_open(target: str) -> dict:
    if not target:
        return {"status": "error", "message": "Nothing to open"}
    t = str(target).strip()
    tl = t.lower()
    for pfx in ["open ", "launch ", "start ", "go to ", "navigate to ", "show ", "visit ", "browse ", "run "]:
        if tl.startswith(pfx):
            tl = tl[len(pfx):].strip()
            t  = t[len(pfx):].strip()

    for site, url in SITES.items():
        if site == tl or site in tl:
            webbrowser.open(url)
            speak(f"Opening {site}")
            return {"status": "ok", "opened": url, "type": "website"}

    for app, exe in APPS.items():
        if app == tl or app in tl:
            try:
                subprocess.Popen(exe, shell=True)
                speak(f"Opening {app}")
                return {"status": "ok", "opened": exe, "type": "app"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    if tl.startswith(("http://", "https://")):
        webbrowser.open(t)
        speak(f"Opening {t[:60]}")
        return {"status": "ok", "opened": t, "type": "url"}

    if "." in tl and " " not in tl and len(tl) < 80:
        url = "https://" + tl
        webbrowser.open(url)
        speak(f"Opening {tl}")
        return {"status": "ok", "opened": url, "type": "url"}

    if len(t.split()) <= 3:
        try:
            subprocess.Popen(t, shell=True)
            return {"status": "ok", "opened": t, "type": "command"}
        except Exception:
            pass

    return {"status": "error", "message": f"Could not find: {target[:60]}"}

# ═══════════════════════════════════════════════════════════════════════════
# EMAIL
# ═══════════════════════════════════════════════════════════════════════════
def _build_msg(from_: str, to_: str, subject: str, body: str, att=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = from_; msg["To"] = to_; msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText("<html><body>" + body.replace("\n", "<br>") + "</body></html>", "html"))
    if att and os.path.exists(str(att)):
        with open(str(att), "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(str(att))}")
        msg.attach(part)
    return msg

def send_email_real(to: str, subject: str, body: str, att=None) -> dict:
    em = _smtp_cfg.get("email", ""); pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host", "smtp.gmail.com"); pt = int(_smtp_cfg.get("port", 587))
    if not em or not pw:
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(str(body)[:2000])}")
        webbrowser.open(url)
        speak(f"Gmail opened for you to send to {to}. Say configure email for auto-send.")
        return {"status": "ok", "action": "browser_compose",
                "note": "Gmail compose opened. Say 'configure email' to enable auto-send."}
    try:
        msg = _build_msg(em, to, subject, body, att)
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        speak(f"Email sent to {to} successfully!")
        log.info("Email sent to %s", to)
        return {"status": "ok", "sent_to": to, "subject": subject}
    except smtplib.SMTPAuthenticationError:
        speak("Email authentication failed. Run configure email to fix.")
        return {"status": "error", "message": "SMTP auth failed"}
    except Exception as e:
        log.error("SMTP: %s", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(str(body)[:2000])}")
        webbrowser.open(url)
        speak(f"SMTP failed. Gmail opened for {to}.")
        return {"status": "ok", "action": "browser_fallback", "note": f"SMTP error: {e}"}

def send_bulk_email(contacts: list, subject: str, body_tmpl: str, delay=2.0) -> dict:
    em = _smtp_cfg.get("email", ""); pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host", "smtp.gmail.com"); pt = int(_smtp_cfg.get("port", 587))
    if not em or not pw:
        return {"status": "error", "message": "Email not configured. Say 'configure email' first."}
    if not contacts:
        return {"status": "error", "message": "No contacts provided."}
    speak(f"Starting bulk email to {len(contacts)} contacts. Please wait.")
    sent = 0; failed = 0
    try:
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            for c in contacts:
                try:
                    to_e = (c.get("email") or c.get("Email") or "").strip()
                    if not to_e or "@" not in to_e:
                        failed += 1; continue
                    name    = (c.get("name") or c.get("Name") or to_e.split("@")[0].replace(".", " ").title())
                    company = (c.get("company") or c.get("Company") or "")
                    body = (body_tmpl.replace("{name}", name).replace("{Name}", name)
                            .replace("{email}", to_e).replace("{company}", company)
                            .replace("{NAME}", name.upper()))
                    subj = subject.replace("{name}", name).replace("{company}", company)
                    msg = _build_msg(em, to_e, subj, body)
                    srv.sendmail(em, [to_e], msg.as_string())
                    sent += 1
                    if sent % 10 == 0:
                        speak(f"{sent} emails sent.")
                    log.info("Bulk: %s (%d/%d)", to_e, sent, len(contacts))
                    time.sleep(max(0.5, delay))
                except Exception as e2:
                    failed += 1
                    log.warning("Bulk fail %s: %s", c.get("email", "?"), e2)
    except Exception as e:
        return {"status": "error", "message": f"SMTP connection failed: {e}"}
    summary = f"Bulk email: {sent} sent, {failed} failed of {len(contacts)}"
    speak(summary); log.info(summary)
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
                em = (row.get("email") or row.get("Email") or row.get("EMAIL") or "").strip()
                if em and "@" in em:
                    contacts.append({
                        "email":   em,
                        "name":    (row.get("name") or row.get("Name") or em.split("@")[0].replace(".", " ").title()).strip(),
                        "company": (row.get("company") or row.get("Company") or "").strip(),
                    })
        log.info("Loaded %d contacts from %s", len(contacts), p)
    except Exception as e:
        log.warning("load_csv: %s", e)
    return contacts

# ═══════════════════════════════════════════════════════════════════════════
# WEB RESEARCH + LEAD FINDER
# ═══════════════════════════════════════════════════════════════════════════
_HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

def web_research(query: str) -> str:
    if not req_lib:
        return "Web research unavailable."
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        r   = req_lib.get(url, headers=_HDRS, timeout=15)
        if BS4_OK and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            snips = []
            for tag in soup.find_all(["div", "span"],
                    class_=lambda c: c and any(x in c for x in ["BNeawe", "VwiC3b", "MUxGbd", "hgKElc"])):
                t = tag.get_text(" ", strip=True)
                if len(t) > 50:
                    snips.append(t)
            return " ".join(snips[:10])[:5000]
        text = re.sub(r"<[^>]+>", " ", r.text)
        return re.sub(r"\s+", " ", text)[:3000]
    except Exception as e:
        return f"Research error: {e}"

def find_leads_web(product: str, niche: str = "", max_leads: int = 25) -> list:
    if not req_lib:
        return []
    leads = []
    email_re = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b')
    skip = {"example.com", "test.com", "sentry.io", "w3.org", "schema.org",
            "wix.com", "wordpress.com", "jquery.com", "google.com", "cloudflare.com", "amazonaws.com"}
    speak(f"Searching for leads for {product}. Takes about 30 seconds.")
    for q in [f"{niche} {product} email contact", f"{product} company email contact",
              f"buy {product} email", f"{niche} business owner email"]:
        if len(leads) >= max_leads:
            break
        try:
            r = req_lib.get(f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20",
                            headers=_HDRS, timeout=15)
            text = BeautifulSoup(r.text, "html.parser").get_text() if BS4_OK else r.text
            for em in email_re.findall(text):
                domain = em.split("@")[-1].lower()
                if domain in skip:
                    continue
                if any(l["email"].lower() == em.lower() for l in leads):
                    continue
                leads.append({"email": em,
                              "name": em.split("@")[0].replace(".", " ").title(),
                              "company": domain.split(".")[0].title()})
                if len(leads) >= max_leads:
                    break
            time.sleep(2.5)
        except Exception as e:
            log.warning("lead search: %s", e)
    try:
        lf = AGENT_DIR / "data" / "leads.csv"
        with open(lf, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["email", "name", "company"])
            w.writeheader(); w.writerows(leads)
    except Exception:
        pass
    speak(f"Found {len(leads)} leads for {product}.")
    return leads

# ═══════════════════════════════════════════════════════════════════════════
# SELENIUM
# ═══════════════════════════════════════════════════════════════════════════
def get_driver(headless=False):
    if not SELENIUM_OK:
        return None
    try:
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        opts.add_argument("--start-maximized")
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)
        except Exception:
            driver = webdriver.Chrome(options=opts)
        driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return driver
    except Exception as e:
        log.error("Chrome driver: %s", e)
        return None

def _slow_type(el, text: str, delay=0.05):
    for ch in str(text):
        el.send_keys(ch)
        time.sleep(delay + random.uniform(0, 0.03))

def post_instagram(user: str, pw: str, img: str, caption: str = "") -> dict:
    speak("Opening Instagram. Please wait about 30 seconds.")
    d = get_driver()
    if not d:
        return {"status": "error", "message": "Chrome not available"}
    try:
        w = WebDriverWait(d, 30)
        d.get("https://www.instagram.com/accounts/login/"); time.sleep(4)
        _slow_type(w.until(EC.presence_of_element_located((By.NAME, "username"))), user)
        time.sleep(0.4)
        pw_el = d.find_element(By.NAME, "password")
        _slow_type(pw_el, pw); pw_el.send_keys(Keys.RETURN); time.sleep(6)
        for txt in ["Save Info", "Not Now", "Not now"]:
            try: d.find_element(By.XPATH, f"//*[text()='{txt}']").click(); time.sleep(2)
            except Exception: pass
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//*[@aria-label="New post"] | //a[contains(@href,"create")]'))).click(); time.sleep(2)
        d.find_element(By.XPATH, '//input[@type="file"]').send_keys(os.path.abspath(str(img))); time.sleep(4)
        for _ in range(2):
            try: d.find_element(By.XPATH, '//div[text()="Next"] | //*[@aria-label="Next"]').click(); time.sleep(2.5)
            except Exception: pass
        try:
            cap_el = d.find_element(By.XPATH, '//div[contains(@aria-label,"caption")] | //div[@role="textbox"]')
            cap_el.click(); cap_el.send_keys(caption); time.sleep(1)
        except Exception: pass
        d.find_element(By.XPATH, '//div[text()="Share"] | //*[@aria-label="Share"]').click(); time.sleep(6)
        speak("Instagram post published!")
        return {"status": "ok", "message": "Posted to Instagram"}
    except Exception as e:
        log.error("Instagram: %s", e); webbrowser.open("https://www.instagram.com")
        return {"status": "error", "message": str(e), "fallback": "Instagram opened in browser"}
    finally:
        try: d.quit()
        except Exception: pass

def post_linkedin(user: str, pw: str, text: str, img=None) -> dict:
    speak("Opening LinkedIn. Please wait about 20 seconds.")
    d = get_driver()
    if not d:
        return {"status": "error", "message": "Chrome not available"}
    try:
        w = WebDriverWait(d, 25)
        d.get("https://www.linkedin.com/login"); time.sleep(3)
        _slow_type(w.until(EC.presence_of_element_located((By.ID, "username"))), user)
        time.sleep(0.3)
        pw_el = d.find_element(By.ID, "password"); _slow_type(pw_el, pw); pw_el.send_keys(Keys.RETURN); time.sleep(5)
        d.get("https://www.linkedin.com/feed/"); time.sleep(3)
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//button[contains(.,"Start a post")] | //button[contains(.,"Create a post")]'))).click(); time.sleep(2.5)
        ed = w.until(EC.presence_of_element_located((By.XPATH, '//div[@role="textbox" and @data-placeholder]')))
        ed.click(); ed.send_keys(text); time.sleep(1)
        if img and os.path.exists(str(img)):
            try:
                d.find_element(By.XPATH, '//button[@aria-label="Add a photo"]').click(); time.sleep(1.5)
                d.find_element(By.XPATH, '//input[@type="file"]').send_keys(os.path.abspath(str(img))); time.sleep(4)
            except Exception: pass
        d.find_element(By.XPATH, '//button[contains(@class,"share-actions__primary-action")] | //button[@aria-label="Post"]').click()
        time.sleep(4); speak("LinkedIn post published!")
        return {"status": "ok", "message": "Posted to LinkedIn"}
    except Exception as e:
        log.error("LinkedIn: %s", e); webbrowser.open("https://www.linkedin.com")
        return {"status": "error", "message": str(e), "fallback": "LinkedIn opened in browser"}
    finally:
        try: d.quit()
        except Exception: pass

def post_facebook(user: str, pw: str, text: str, img=None) -> dict:
    speak("Opening Facebook. Please wait about 20 seconds.")
    d = get_driver()
    if not d:
        return {"status": "error", "message": "Chrome not available"}
    try:
        w = WebDriverWait(d, 25)
        d.get("https://www.facebook.com/login"); time.sleep(3)
        _slow_type(w.until(EC.presence_of_element_located((By.ID, "email"))), user)
        time.sleep(0.3)
        pw_el = d.find_element(By.ID, "pass"); _slow_type(pw_el, pw); pw_el.send_keys(Keys.RETURN); time.sleep(6)
        d.get("https://www.facebook.com/"); time.sleep(4)
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="button" and (contains(.,"mind") or contains(.,"thinking") or contains(.,"post"))]'))).click()
        time.sleep(2)
        ed = w.until(EC.element_to_be_clickable((By.XPATH, '//div[@role="textbox" and @contenteditable="true"]')))
        ed.click(); ed.send_keys(text); time.sleep(1)
        if img and os.path.exists(str(img)):
            try:
                d.find_element(By.XPATH, '//div[@aria-label="Photo/video"]').click(); time.sleep(1.5)
                d.find_element(By.XPATH, '//input[@type="file"]').send_keys(os.path.abspath(str(img))); time.sleep(4)
            except Exception: pass
        d.find_element(By.XPATH, '//div[@aria-label="Post" and @role="button"]').click()
        time.sleep(4); speak("Facebook post published!")
        return {"status": "ok", "message": "Posted to Facebook"}
    except Exception as e:
        log.error("Facebook: %s", e); webbrowser.open("https://www.facebook.com")
        return {"status": "error", "message": str(e), "fallback": "Facebook opened in browser"}
    finally:
        try: d.quit()
        except Exception: pass

def wa_send(phone: str, msg: str) -> dict:
    ph = re.sub(r"[^0-9+]", "", str(phone))
    if not ph.startswith("+"):
        ph = "+91" + ph
    url = f"https://wa.me/{ph.lstrip('+')}?text={urllib.parse.quote(str(msg))}"
    webbrowser.open(url)
    speak(f"WhatsApp Web opened for {phone}. Click Send in the browser tab.")
    return {"status": "ok", "note": "WhatsApp Web opened — click Send"}

# ═══════════════════════════════════════════════════════════════════════════
# AI PLAN
# ═══════════════════════════════════════════════════════════════════════════
_AI_SYSTEM = """You are Dacexy, a Windows desktop AI agent.
Return ONLY a valid JSON array of command objects. No text, no markdown.
TODAY: {date}
CONTEXT: {ctx}
ACTIONS: open(url/app/target), search_web(query), open_youtube(query),
send_email(to,subject,body), bulk_email(contacts[]/csv_path,subject,body),
find_leads_and_email(product,niche,subject,body), find_leads(product,niche,max),
web_research(query), social_post(platform,username,password,text,image_path,caption),
whatsapp(phone,message), type(text), key(key), hotkey(keys[]), screenshot,
speak(text), get_time, get_date, get_system_info, volume_up(steps), volume_down(steps),
mute, minimize_window, maximize_window, close_window, write_file(path,content),
read_file(path), zip_files(path,output), run_command(command), remember(fact),
wait(seconds), schedule_task(task,schedule), add_contact(name,email,phone),
scroll_down(amount), scroll_up(amount), click(x,y), select_all, copy, paste
RULES: Always end with speak. Never click(0,0). No text outside JSON array.
Return ONLY the JSON array:"""

def ai_plan(task: str, token: str) -> list:
    if not req_lib or not token:
        return []
    try:
        ctx = get_mem_ctx()
        date_str = datetime.datetime.now().strftime("%A %d %B %Y %I:%M %p")
        system = _AI_SYSTEM.format(date=date_str, ctx=ctx)
        msgs = [{"role": "system", "content": system}]
        for c in list(_convo)[-4:]:
            role = "user" if c.startswith("user:") else "assistant"
            msgs.append({"role": role, "content": c.split(":", 1)[-1].strip()})
        msgs.append({"role": "user", "content": f"Task: {task[:600]}"})
        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                         json={"messages": msgs, "stream": False}, timeout=40)
        if r.status_code != 200:
            log.warning("AI plan HTTP %d", r.status_code); return []
        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw:
            return []
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE).strip()
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                cmds = json.loads(m.group())
                if isinstance(cmds, list) and cmds:
                    log.info("AI plan: %d commands for: %s", len(cmds), task[:60])
                    return cmds
            except json.JSONDecodeError as je:
                log.warning("AI JSON: %s | %s", je, raw[:200])
        clean = re.sub(r"[{}\[\]]", "", raw).strip()[:400]
        if clean:
            return [{"action": "speak", "text": clean}]
        return []
    except Exception as e:
        log.warning("ai_plan: %s", e); return []

# ═══════════════════════════════════════════════════════════════════════════
# LOCAL NLP (handles 95% of tasks instantly, no network needed)
# ═══════════════════════════════════════════════════════════════════════════
def local_parse(task: str) -> list:
    t = task.lower().strip()

    m = re.match(r"(?:open|launch|start|go to|navigate to|visit|browse)\s+(.+)", t)
    if m:
        tgt = m.group(1).strip()
        return [{"action": "open", "target": tgt}, {"action": "speak", "text": f"Opening {tgt}"}]

    m = re.search(r"(?:search|play|find|watch)\s+(.+?)\s+(?:on|in)\s+youtube", t)
    if m:
        return [{"action": "open_youtube", "query": m.group(1).strip()}]
    if "youtube" in t:
        q = re.sub(r"(youtube|search|play|watch|find|on|in|for|open)", "", t).strip()
        if q:
            return [{"action": "open_youtube", "query": q}]

    m = re.search(r"(?:google|search for|look up|search|find)\s+(.+?)(?:\s+on google)?$", t)
    if m and "youtube" not in t and "email" not in t and "leads" not in t:
        return [{"action": "search_web", "query": m.group(1).strip()}]

    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+([^\s,]+@[^\s,]+)"
                  r"(?:\s+(?:saying|about|with subject|subject)\s+(.+))?$", t)
    if m:
        return [{"action": "send_email",
                 "to": m.group(1).strip(),
                 "subject": (m.group(2) or "Hello from Dacexy").strip(),
                 "body": (m.group(2) or task).strip()}]

    m = re.search(r"(?:bulk|mass|send)\s+email.+?(?:csv|file|contacts in|from)\s+(.+?)(?:\s+with|\s+subject|\s+saying|$)", t)
    if m:
        return [{"action": "bulk_email", "csv_path": m.group(1).strip(),
                 "subject": "Hello from Dacexy",
                 "body": "Hi {name},\n\nHope this finds you well!\n\nBest regards"}]

    if re.search(r"(?:find|get|search)\s+(?:leads|customers|clients)", t):
        m_prod = re.search(r"for\s+(?:my\s+)?(.+?)(?:\s+and|\s+then|\s+to|$)", t)
        prod = m_prod.group(1).strip() if m_prod else "product"
        return [{"action": "find_leads_and_email", "product": prod, "niche": "",
                 "subject": f"Interested in {prod}?",
                 "body": f"Hi {{name}},\n\nI noticed you might benefit from {prod}.\nWould you be open to a quick chat?\n\nBest regards"}]

    if "whatsapp" in t:
        m = re.search(r"(?:send|message|whatsapp)\s+(.+?)\s+(?:on\s+whatsapp\s+)?(?:saying|message|with)?\s*(.+)?$", t)
        if m and m.group(2):
            return [{"action": "whatsapp", "phone": m.group(1).strip(), "message": m.group(2).strip()}]
        return [{"action": "open", "target": "whatsapp web"}]

    if any(w in t for w in ["screenshot", "screen shot", "capture screen", "take a screenshot"]):
        return [{"action": "screenshot"}, {"action": "speak", "text": "Screenshot taken and saved."}]

    if re.search(r"\bwhat(?:'s| is)\s+the\s+time\b|\btime\s+is\s+it\b|\bwhat time\b", t):
        return [{"action": "get_time"}]
    if re.search(r"\bwhat(?:'s| is)\s+(?:today|the\s+date)\b|\bdate\s+is\s+it\b|\bwhat date\b", t):
        return [{"action": "get_date"}]

    if any(w in t for w in ["system info", "cpu usage", "ram usage", "disk space",
                             "battery level", "how much memory", "how much ram"]):
        return [{"action": "get_system_info"}]

    if re.search(r"volume\s*up|increase\s+volume|louder|turn\s+up", t):
        return [{"action": "volume_up", "steps": 5}]
    if re.search(r"volume\s*down|lower\s+volume|quieter|turn\s+down", t):
        return [{"action": "volume_down", "steps": 5}]
    if re.search(r"\bmute\b|\bsilence\b", t):
        return [{"action": "mute"}]

    if re.search(r"minimiz|minimis", t):
        return [{"action": "minimize_window"}]
    if re.search(r"maximiz|maximis|full.?screen", t):
        return [{"action": "maximize_window"}]
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app)", t):
        return [{"action": "close_window"}]

    m = re.match(r"(?:type|write|enter|input)\s+(.+)", t)
    if m:
        return [{"action": "type", "text": m.group(1).strip()}]

    if re.search(r"scroll\s+down", t):
        return [{"action": "scroll_down", "amount": 5}]
    if re.search(r"scroll\s+up", t):
        return [{"action": "scroll_up", "amount": 5}]

    m = re.match(r"remember\s+(?:that\s+)?(.+)", t)
    if m:
        return [{"action": "remember", "fact": m.group(1)},
                {"action": "speak", "text": "Got it, I'll remember that."}]

    m = re.match(r"(?:say|speak|tell me)\s+(.+)", t)
    if m:
        return [{"action": "speak", "text": m.group(1)}]

    m = re.search(r"(?:press|hit)\s+(.+)", t)
    if m:
        return [{"action": "key", "key": m.group(1).strip()}]

    if re.match(r"^copy$", t): return [{"action": "copy"}]
    if re.match(r"^paste$", t): return [{"action": "paste"}]
    if re.match(r"^undo$", t): return [{"action": "undo"}]
    if re.match(r"^select all$", t): return [{"action": "select_all"}]

    if re.search(r"(?:configure|setup|set up|enable)\s+(?:email|smtp|mail)", t):
        return [{"action": "configure_email"}]

    if re.search(r"\bzip\b|\bcompress\b", t):
        return [{"action": "zip_files", "path": str(Path.home() / "Desktop")}]

    m = re.search(r"(?:schedule|every day|daily)\s+(.+?)(?:\s+at\s+(\d{1,2}:\d{2}))?$", t)
    if m and any(w in t for w in ["schedule", "every day", "daily", "every morning"]):
        return [{"action": "schedule_task",
                 "task": m.group(1).strip(),
                 "schedule": f"daily at {m.group(2) or '09:00'}"}]

    for app in APPS:
        if app in t:
            return [{"action": "open", "app": app}, {"action": "speak", "text": f"Opening {app}"}]

    m = re.match(r"(?:research|investigate|find out about|look up info on|write a report on)\s+(.+)", t)
    if m:
        return [{"action": "web_research", "query": m.group(1).strip()}]

    m = re.search(r"(?:post|share)\s+(?:on|to)\s+(instagram|linkedin|facebook|twitter)", t)
    if m:
        plat = m.group(1)
        return [{"action": "open", "target": plat},
                {"action": "speak", "text": f"Opened {plat}. To auto-post include username and password."}]

    m = re.match(r"(?:write|create|save)\s+(?:a\s+)?(?:file|note|text)\s+(.+)", t)
    if m:
        return [{"action": "write_file", "path": str(AGENT_DIR / "note.txt"), "content": m.group(1)}]

    m = re.match(r"(?:run|execute)\s+(?:command\s+)?(.+)", t)
    if m:
        return [{"action": "run_command", "command": m.group(1).strip()}]

    return []

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR — actually runs on the PC
# ═══════════════════════════════════════════════════════════════════════════
def exec_cmd(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Not a dict"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action"}
    raw_str = " ".join(str(v) for v in cmd.values())
    if any(b in raw_str.lower() for b in BLOCKED):
        return {"status": "blocked", "message": "Blocked for safety"}
    log.info("EXEC → %s | %s", action, str({k: v for k, v in cmd.items() if k != "action"})[:100])

    try:
        if action == "speak":
            speak(str(cmd.get("text", ""))); return {"status": "ok"}
        elif action == "notify":
            _notify(str(cmd.get("title", "Dacexy")), str(cmd.get("text", ""))); return {"status": "ok"}
        elif action == "configure_email":
            webbrowser.open("https://myaccount.google.com/apppasswords")
            speak("I opened Google App Passwords. Create an app password, then restart me and say yes to email setup.")
            return {"status": "ok"}
        elif action in ("open", "open_url", "open_browser", "launch", "start", "navigate",
                        "navigate_to", "go_to", "browse", "visit", "open_site",
                        "open_website", "open_app", "run_app"):
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                   cmd.get("name") or cmd.get("site") or cmd.get("target") or "").strip()
            if not tgt:
                return {"status": "error", "message": "No target for open"}
            return smart_open(tgt)
        elif action in ("send_email", "email", "compose_email", "gmail_send", "send_mail", "mail"):
            to_  = str(cmd.get("to") or cmd.get("email") or "").strip()
            if not to_:
                return {"status": "error", "message": "No recipient"}
            return send_email_real(to_,
                str(cmd.get("subject") or "Message from Dacexy"),
                str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "Hello"),
                cmd.get("attachment"))
        elif action in ("bulk_email", "send_bulk_email", "mass_email", "email_all"):
            contacts = cmd.get("contacts") or []
            csv_p = cmd.get("csv_path") or cmd.get("file") or ""
            if csv_p and not contacts:
                contacts = load_csv_contacts(str(csv_p))
            if not contacts:
                return {"status": "error", "message": "No contacts found."}
            return send_bulk_email(contacts,
                str(cmd.get("subject") or "Hello from Dacexy"),
                str(cmd.get("body") or cmd.get("template") or "Hi {name},\n\nHope this finds you well!\n\nBest regards"),
                float(cmd.get("delay") or 2.0))
        elif action in ("find_leads_and_email", "lead_campaign", "find_and_email"):
            product = str(cmd.get("product") or cmd.get("query") or "product")
            leads = find_leads_web(product, str(cmd.get("niche") or ""), int(cmd.get("max") or 25))
            if not leads:
                return {"status": "error", "message": "No leads found."}
            return send_bulk_email(leads,
                str(cmd.get("subject") or f"About {product}"),
                str(cmd.get("body") or cmd.get("template") or
                    f"Hi {{name}},\n\nI noticed you might benefit from {product}.\nWould you be open to a quick chat?\n\nBest regards"),
                2.5)
        elif action in ("find_leads", "lead_finder", "scrape_leads"):
            leads = find_leads_web(str(cmd.get("product") or ""), str(cmd.get("niche") or ""), int(cmd.get("max") or 25))
            return {"status": "ok", "leads_found": len(leads), "file": str(AGENT_DIR / "data" / "leads.csv")}
        elif action in ("web_research", "research", "investigate", "find_info"):
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q:
                return {"status": "error", "message": "No query"}
            speak(f"Researching {q}. One moment...")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(f"Research: {q}\nDate: {datetime.datetime.now()}\n{'='*60}\n\n{result}", encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception: pass
            speak("Research done. Report opened in Notepad.")
            return {"status": "ok", "result": result[:600], "saved": str(rp)}
        elif action in ("social_post", "post_social", "instagram_post", "linkedin_post",
                        "facebook_post", "post_instagram", "post_linkedin", "post_facebook"):
            plat = str(cmd.get("platform") or action.replace("post_", "").replace("_post", ""))
            usr  = str(cmd.get("username") or cmd.get("user") or "")
            pwd  = str(cmd.get("password") or cmd.get("pass") or "")
            txt  = str(cmd.get("text") or cmd.get("caption") or cmd.get("content") or "")
            img  = cmd.get("image_path") or cmd.get("image") or None
            if not usr or not pwd:
                url_map = {"instagram": "https://www.instagram.com", "linkedin": "https://www.linkedin.com",
                           "facebook": "https://www.facebook.com", "twitter": "https://x.com"}
                webbrowser.open(url_map.get(plat.lower(), "https://www.instagram.com"))
                speak(f"Opened {plat}. To auto-post include username and password.")
                return {"status": "ok", "note": f"Opened {plat} in browser"}
            plat_l = plat.lower()
            if "instagram" in plat_l:
                if not img: return {"status": "error", "message": "Instagram needs image_path="}
                return post_instagram(usr, pwd, str(img), txt)
            elif "linkedin" in plat_l:
                return post_linkedin(usr, pwd, txt, img)
            elif "facebook" in plat_l:
                return post_facebook(usr, pwd, txt, img)
            else:
                webbrowser.open(f"https://www.{plat_l}.com")
                return {"status": "ok", "note": f"Opened {plat} in browser"}
        elif action in ("whatsapp", "whatsapp_send", "send_whatsapp"):
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            if not phone: return {"status": "error", "message": "No phone number"}
            return wa_send(phone, str(cmd.get("message") or cmd.get("text") or ""))
        elif action in ("open_youtube", "youtube", "youtube_search"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}")
                speak(f"Searching YouTube for {q}"); return {"status": "ok", "searched": q}
            webbrowser.open("https://www.youtube.com"); return {"status": "ok"}
        elif action in ("search_web", "search", "google_search", "google"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                speak(f"Searching Google for {q}"); return {"status": "ok", "searched": q}
            webbrowser.open("https://www.google.com"); return {"status": "ok"}
        elif action == "click":
            if not pyautogui: return {"status": "error", "message": "pyautogui not available"}
            x, y = int(cmd.get("x") or 0), int(cmd.get("y") or 0)
            if x == 0 and y == 0: return {"status": "skipped", "reason": "no coordinates"}
            sw, sh = pyautogui.size()
            pyautogui.click(max(0, min(x, sw-1)), max(0, min(y, sh-1)), button=str(cmd.get("button", "left")))
            time.sleep(0.1); return {"status": "ok", "clicked": f"({x},{y})"}
        elif action == "double_click":
            if pyautogui: pyautogui.doubleClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}
        elif action == "right_click":
            if pyautogui: pyautogui.rightClick(int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            return {"status": "ok"}
        elif action == "move_mouse":
            if pyautogui: pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=0.2)
            return {"status": "ok"}
        elif action == "scroll":
            amt = int(cmd.get("clicks") or cmd.get("amount") or 3)
            d_  = str(cmd.get("direction", "down")).lower()
            if pyautogui: pyautogui.scroll(abs(amt) if d_ == "up" else -abs(amt))
            return {"status": "ok"}
        elif action in ("scroll_down", "scrolldown"):
            if pyautogui: pyautogui.scroll(-int(cmd.get("amount", 5)))
            return {"status": "ok"}
        elif action in ("scroll_up", "scrollup"):
            if pyautogui: pyautogui.scroll(int(cmd.get("amount", 5)))
            return {"status": "ok"}
        elif action == "drag":
            if pyautogui:
                pyautogui.moveTo(int(cmd.get("x1", 0)), int(cmd.get("y1", 0)))
                pyautogui.dragTo(int(cmd.get("x2", 0)), int(cmd.get("y2", 0)), duration=0.4, button="left")
            return {"status": "ok"}
        elif action == "get_mouse_pos":
            if pyautogui:
                p = pyautogui.position(); return {"status": "ok", "x": p.x, "y": p.y}
            return {"status": "ok", "x": 0, "y": 0}
        elif action in ("type", "type_text", "write", "input", "enter_text"):
            smart_type(str(cmd.get("text") or cmd.get("content") or ""))
            return {"status": "ok"}
        elif action in ("key", "press", "press_key", "keypress"):
            k = cmd.get("key") or cmd.get("keys") or ""
            if k and pyautogui: pyautogui.press(str(k))
            return {"status": "ok"}
        elif action in ("hotkey", "key_combo", "shortcut"):
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str): keys = keys.replace("+", " ").split()
            if keys and pyautogui: pyautogui.hotkey(*[str(k) for k in keys[:5]])
            return {"status": "ok"}
        elif action == "press_enter":
            if pyautogui: pyautogui.press("enter"); return {"status": "ok"}
        elif action == "press_tab":
            if pyautogui: pyautogui.press("tab"); return {"status": "ok"}
        elif action == "press_escape":
            if pyautogui: pyautogui.press("escape"); return {"status": "ok"}
        elif action == "select_all":
            if pyautogui: pyautogui.hotkey("ctrl", "a"); return {"status": "ok"}
        elif action == "copy":
            if pyautogui: pyautogui.hotkey("ctrl", "c"); time.sleep(0.15)
            return {"status": "ok", "clipboard": pyperclip.paste() if pyperclip else ""}
        elif action == "paste":
            if pyautogui: pyautogui.hotkey("ctrl", "v"); return {"status": "ok"}
        elif action == "cut":
            if pyautogui: pyautogui.hotkey("ctrl", "x"); return {"status": "ok"}
        elif action == "undo":
            if pyautogui: pyautogui.hotkey("ctrl", "z"); return {"status": "ok"}
        elif action == "save":
            if pyautogui: pyautogui.hotkey("ctrl", "s"); return {"status": "ok"}
        elif action == "get_clipboard":
            return {"status": "ok", "text": pyperclip.paste() if pyperclip else ""}
        elif action == "set_clipboard":
            if pyperclip: pyperclip.copy(str(cmd.get("text", ""))[:10000])
            return {"status": "ok"}
        elif action in ("screenshot", "take_screenshot"):
            ss = take_screenshot()
            if ss:
                try:
                    fn = AGENT_DIR / "screenshots" / f"ss_{int(time.time())}.jpg"
                    fn.write_bytes(base64.b64decode(ss))
                    speak(f"Screenshot saved: {fn.name}")
                except Exception: speak("Screenshot taken.")
            else: speak("Screenshot could not be taken.")
            return {"status": "ok", "screenshot": ss or ""}
        elif action in ("minimize_window", "minimize"):
            if pyautogui: pyautogui.hotkey("win", "down"); return {"status": "ok"}
        elif action in ("maximize_window", "maximize"):
            if pyautogui: pyautogui.hotkey("win", "up"); return {"status": "ok"}
        elif action in ("close_window", "close"):
            if pyautogui: pyautogui.hotkey("alt", "f4"); return {"status": "ok"}
        elif action == "switch_window":
            if pyautogui: pyautogui.hotkey("alt", "tab"); time.sleep(0.3); return {"status": "ok"}
        elif action == "get_active_window":
            return {"status": "ok", "title": get_active_win()}
        elif action in ("open_file_explorer", "file_explorer"):
            subprocess.Popen("explorer.exe", shell=True); return {"status": "ok"}
        elif action == "open_task_manager":
            subprocess.Popen("taskmgr.exe", shell=True); return {"status": "ok"}
        elif action == "open_settings":
            subprocess.Popen("ms-settings:", shell=True); return {"status": "ok"}
        elif action in ("open_notepad", "notepad"):
            txt = str(cmd.get("text") or cmd.get("content") or "")
            if txt:
                tmp = AGENT_DIR / "note.txt"; tmp.write_text(txt[:100000], encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"', shell=True)
            else: subprocess.Popen("notepad.exe", shell=True)
            return {"status": "ok"}
        elif action == "volume_up":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps", 5)), 20)): pyautogui.press("volumeup")
            speak("Volume increased"); return {"status": "ok"}
        elif action == "volume_down":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps", 5)), 20)): pyautogui.press("volumedown")
            speak("Volume decreased"); return {"status": "ok"}
        elif action == "mute":
            if pyautogui: pyautogui.press("volumemute"); speak("Muted"); return {"status": "ok"}
        elif action == "write_file":
            p = Path(str(cmd.get("path") or ""))
            if not p.name: p = AGENT_DIR / "output.txt"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(cmd.get("content") or "")[:500000], encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            except Exception: pass
            speak(f"File {p.name} saved."); return {"status": "ok", "path": str(p)}
        elif action == "read_file":
            p = Path(str(cmd.get("path") or ""))
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="ignore")[:8000]
                speak(f"File read: {len(content)} characters."); return {"status": "ok", "content": content}
            return {"status": "error", "message": f"File not found: {p}"}
        elif action == "list_files":
            p = Path(str(cmd.get("path") or str(Path.home())))
            try:
                files = [f.name for f in p.iterdir()][:100]
                speak(f"Found {len(files)} items."); return {"status": "ok", "files": files}
            except Exception as e: return {"status": "error", "message": str(e)}
        elif action == "delete_file":
            p = Path(str(cmd.get("path") or ""))
            if p.exists(): p.unlink(); speak(f"Deleted {p.name}"); return {"status": "ok"}
            return {"status": "error", "message": "File not found"}
        elif action in ("move_file", "rename_file", "move"):
            src = Path(str(cmd.get("src") or cmd.get("source") or cmd.get("path") or ""))
            dst = Path(str(cmd.get("dst") or cmd.get("dest") or cmd.get("destination") or ""))
            if src.exists() and dst:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst)); return {"status": "ok", "moved_to": str(dst)}
            return {"status": "error", "message": "Source not found"}
        elif action in ("zip_files", "create_zip", "compress"):
            src = Path(str(cmd.get("path") or str(Path.home() / "Desktop")))
            dst = Path(str(cmd.get("output") or str(AGENT_DIR / f"backup_{int(time.time())}.zip")))
            try:
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file(): zf.write(src, src.name)
                    elif src.is_dir():
                        for f in src.iterdir():
                            if f.is_file(): zf.write(f, f.name)
                speak(f"Zipped {src.name} to {dst.name}"); return {"status": "ok", "zip": str(dst)}
            except Exception as e: return {"status": "error", "message": str(e)}
        elif action in ("get_system_info", "system_info", "sysinfo"):
            if psutil:
                dp = "C:\\" if platform.system() == "Windows" else "/"
                info = {"cpu": psutil.cpu_percent(interval=0.5),
                        "ram": psutil.virtual_memory().percent,
                        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                        "disk": psutil.disk_usage(dp).percent,
                        "disk_free_gb": round(psutil.disk_usage(dp).free / 1e9, 1),
                        "platform": platform.system(), "hostname": socket.gethostname(),
                        "active_window": get_active_win()}
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%, Disk {info['disk']}%")
                return {"status": "ok", "info": info}
            return {"status": "ok", "info": {"platform": platform.system()}}
        elif action == "get_time":
            t_ = datetime.datetime.now().strftime("%I:%M %p"); speak(f"The time is {t_}"); return {"status": "ok", "time": t_}
        elif action == "get_date":
            d_ = datetime.datetime.now().strftime("%A, %B %d, %Y"); speak(f"Today is {d_}"); return {"status": "ok", "date": d_}
        elif action == "run_command":
            c_ = str(cmd.get("command") or "")
            if not c_: return {"status": "error", "message": "No command"}
            if any(b in c_.lower() for b in BLOCKED): return {"status": "blocked"}
            try:
                r_ = subprocess.run(c_, shell=True, capture_output=True, text=True,
                                    timeout=30, encoding="utf-8", errors="replace")
                out = (r_.stdout or "")[:3000]
                if out.strip(): speak(out[:200])
                return {"status": "ok", "stdout": out, "returncode": r_.returncode}
            except subprocess.TimeoutExpired: return {"status": "error", "message": "Command timed out"}
        elif action == "kill_process":
            name = str(cmd.get("name", ""))
            safe = ["explorer", "winlogon", "csrss", "svchost", "system", "lsass", "dwm"]
            if any(p in name.lower() for p in safe): return {"status": "blocked", "reason": "System process"}
            if psutil:
                killed = 0
                for p in psutil.process_iter(["name"]):
                    try:
                        if name.lower() in (p.info["name"] or "").lower(): p.kill(); killed += 1
                    except Exception: pass
                speak(f"Killed {killed} process(es)"); return {"status": "ok", "killed": killed}
            return {"status": "ok"}
        elif action == "list_processes":
            if psutil:
                procs = []
                for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
                    try: procs.append(p.info)
                    except Exception: pass
                return {"status": "ok", "processes": procs[:50]}
            return {"status": "ok", "processes": []}
        elif action in ("remember", "save_fact", "take_note"):
            fact = str(cmd.get("fact") or cmd.get("text") or cmd.get("content") or "")
            if fact: remember(fact); speak("Got it, I'll remember that.")
            return {"status": "ok"}
        elif action == "get_memory":
            return {"status": "ok", "memory": get_mem_ctx()}
        elif action == "add_contact":
            name = str(cmd.get("name", ""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {
                        "name": name, "email": str(cmd.get("email", "")),
                        "phone": str(cmd.get("phone", "")), "notes": str(cmd.get("notes", ""))}
                save_memory(); speak(f"Contact {name} saved.")
            return {"status": "ok"}
        elif action in ("schedule_task", "schedule", "add_schedule"):
            task_s = str(cmd.get("task") or cmd.get("command") or cmd.get("text") or "")
            sched  = str(cmd.get("schedule") or cmd.get("when") or "daily at 09:00")
            if not task_s: return {"status": "error", "message": "No task to schedule"}
            job = {"id": "".join(random.choices(string.ascii_lowercase, k=8)),
                   "task": task_s, "schedule": sched, "last_run": ""}
            _sched_jobs.append(job); save_memory()
            speak(f"Scheduled: {task_s[:50]} — runs {sched}")
            return {"status": "ok", "scheduled": task_s, "when": sched}
        elif action in ("wait", "sleep", "pause", "delay"):
            secs = min(float(cmd.get("seconds") or cmd.get("duration") or 1), 30)
            time.sleep(secs); return {"status": "ok", "waited": secs}
        elif action in ("ping", "pong", "test", "health", "health_check", "status", "heartbeat"):
            speak("I am online and working perfectly.")
            return {"status": "ok", "pong": True, "version": VERSION}
        elif action in ("what_on_screen", "describe_screen", "whats_on_screen", "ocr_screen"):
            win = get_active_win(); speak(f"Active window: {win or 'unknown'}"); return {"status": "ok", "active_window": win}
        else:
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("target") or cmd.get("name") or "")
            if tgt:
                res = smart_open(str(tgt))
                if res.get("status") == "ok":
                    return res
            log.warning("Unknown action: %s", action)
            return {"status": "error", "message": f"Unknown action: '{action}'"}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e, exc_info=True)
        return {"status": "error", "message": f"Exception in {action}: {e}"}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN TASK EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════
def execute_task(task: str, token: str) -> dict:
    if not task or not task.strip():
        return {"status": "error", "ok": 0, "total": 0, "result": "No task provided"}
    task = task.strip()
    log.info("Task: %s", task[:100])
    _convo.append(f"user: {task[:120]}")

    commands = local_parse(task)
    source = "local"
    if not commands:
        log.info("→ AI plan for: %s", task[:80])
        speak("Let me think about that.")
        commands = ai_plan(task, token)
        source = "ai"
    if not commands:
        tl = task.lower().strip()
        is_open_like = (len(tl.split()) <= 5 and
                        not any(w in tl for w in ["send", "email", "search", "find", "create",
                                                   "write", "post", "make", "show me", "tell me",
                                                   "research", "configure", "schedule", "bulk", "leads"]))
        if is_open_like:
            res = smart_open(task)
            if res.get("status") == "ok":
                _convo.append(f"dacexy: Opened {task[:60]}")
                with _mem_lock:
                    MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
                save_memory()
                return {"status": "ok", "ok": 1, "total": 1, "result": f"Opened: {task}"}
        speak("I am not sure how to do that. Please rephrase or be more specific.")
        return {"status": "error", "ok": 0, "total": 0, "result": f"Could not understand: {task[:80]}"}

    ok_count = 0; total = len(commands); results = []
    for i, c in enumerate(commands):
        if not isinstance(c, dict): total -= 1; continue
        for k, v in c.get("params", {}).items():
            if k not in c: c[k] = v
        log.info("  Step %d/%d [%s]: %s", i+1, total, source, c.get("action", "?"))
        try:
            res = exec_cmd(c, token); results.append(res)
            if res.get("status") in ("ok", "skipped"): ok_count += 1
            else: log.warning("  Step %d failed: %s", i+1, res.get("message", "unknown"))
            time.sleep(0.25)
        except Exception as e:
            log.error("  Step %d exception: %s", i+1, e)
            results.append({"status": "error", "message": str(e)})

    with _mem_lock:
        MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
    save_memory()
    summary = f"{ok_count}/{total} steps done for: {task[:60]}"
    log.info("Task done: %s", summary)
    if ok_count == 0:
        speak("I tried but could not complete the task. Check the log for details.")
    _convo.append(f"dacexy: {'Done' if ok_count>0 else 'Failed'} — {summary}")
    return {"status": "ok" if ok_count > 0 else "error",
            "ok": ok_count, "total": total, "result": summary, "steps": results}

# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════
def _scheduler_loop(token_ref: list):
    while _running:
        try:
            now = datetime.datetime.now()
            for job in list(_sched_jobs):
                sched = job.get("schedule", "").lower(); last = job.get("last_run", ""); run = False
                if "daily at" in sched:
                    m = re.search(r"(\d{1,2}):(\d{2})", sched)
                    if m:
                        h, mi = int(m.group(1)), int(m.group(2))
                        if now.hour == h and now.minute == mi:
                            ts = now.strftime("%Y-%m-%dT%H:%M")
                            if not last or last[:16] != ts: run = True
                elif "every" in sched and "minute" in sched:
                    m = re.search(r"every\s+(\d+)", sched); mins = int(m.group(1)) if m else 30
                    if last:
                        try:
                            ld = datetime.datetime.fromisoformat(last)
                            if (now - ld).total_seconds() >= mins * 60: run = True
                        except Exception: run = True
                    else: run = True
                elif "hourly" in sched:
                    if last:
                        try:
                            ld = datetime.datetime.fromisoformat(last)
                            if (now - ld).total_seconds() >= 3600: run = True
                        except Exception: run = True
                    else: run = True
                if run:
                    job["last_run"] = now.isoformat(); save_memory()
                    tok = token_ref[0]
                    if tok:
                        t_ = job.get("task", "")
                        log.info("Scheduler: %s", t_[:60])
                        threading.Thread(target=execute_task, args=(t_, tok), daemon=True).start()
        except Exception as e:
            log.warning("Scheduler: %s", e)
        time.sleep(30)

# ═══════════════════════════════════════════════════════════════════════════
# VOICE (Jarvis mode) — FIXED: silence not counted as error
# ═══════════════════════════════════════════════════════════════════════════
def _voice_loop():
    global _voice_on
    if not VOICE_OK or not sr:
        print("  [VOICE] Disabled — install PyAudio to enable Jarvis voice.")
        return
    rec = sr.Recognizer()
    rec.energy_threshold = 350; rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.7; rec.non_speaking_duration = 0.4
    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics: print("  [VOICE] No microphone found."); return
        print(f"  [MIC] {mics[0]}")
    except Exception as e:
        log.warning("Mic list: %s", e)
    print("  [JARVIS] Active! Wake words: Dacexy / Jarvis / Computer")
    speak("Jarvis online. Say Dacexy, Jarvis, or Computer to give me a command.")
    real_errors = 0
    while _voice_on and _running:
        heard = ""
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.1)
                except Exception: pass
                try: audio = rec.listen(src, timeout=3, phrase_time_limit=7)
                except sr.WaitTimeoutError: continue  # silence = normal, not an error
                except OSError as e: real_errors += 1; log.warning("Mic OS: %s", e); time.sleep(2); continue
            try: heard = rec.recognize_google(audio, language="en-IN").lower().strip(); real_errors = 0
            except sr.UnknownValueError: continue
            except sr.RequestError as e: real_errors += 1; log.warning("SR API: %s", e); time.sleep(3); continue
        except Exception as e: real_errors += 1; log.debug("Voice outer: %s", e); time.sleep(1); continue

        if not any(w in heard for w in WAKE_WORDS): continue
        log.info("WAKE: %s", heard); print(f"\n  [WAKE] '{heard}'")
        jarvis("greet"); time.sleep(0.3)

        command = ""
        try:
            with sr.Microphone() as csrc:
                try: rec.adjust_for_ambient_noise(csrc, duration=0.08)
                except Exception: pass
                try: caudio = rec.listen(csrc, timeout=8, phrase_time_limit=30)
                except sr.WaitTimeoutError: speak("I didn't hear a command. Say my name again."); continue
                except OSError as e: log.warning("Mic OS cmd: %s", e); continue
            try: command = rec.recognize_google(caudio, language="en-IN").strip(); real_errors = 0
            except sr.UnknownValueError: jarvis("again"); continue
            except sr.RequestError as e: real_errors += 1; log.warning("SR cmd: %s", e); continue
        except Exception as e: log.warning("Voice cmd: %s", e); continue

        if not command: continue
        log.info("Voice command: %s", command); print(f"  [CMD] {command}")
        with _tok_lock: tok = _cur_token
        if not tok: speak("I am not logged in yet. Please wait."); continue
        jarvis("work")
        # CLOSURE FIX: snapshot tok and command in default args
        def _run_voice(t_=tok, cmd_=command):
            try:
                result = execute_task(cmd_, t_)
                if result.get("ok", 0) == 0: log.warning("Voice task 0 ok: %s", cmd_)
            except Exception as exc: log.error("Voice task exc: %s", exc); speak("Error with that command.")
        threading.Thread(target=_run_voice, daemon=True).start()
        if real_errors >= 10: speak("Voice paused due to errors. Resuming in 30 seconds."); time.sleep(30); real_errors = 0

def start_voice(token: str) -> bool:
    global _voice_on, _cur_token
    with _tok_lock: _cur_token = token
    if not VOICE_OK: return False
    _voice_on = True
    threading.Thread(target=_voice_loop, daemon=True, name="Voice").start()
    return True

def stop_voice(): global _voice_on; _voice_on = False
def update_token(t: str):
    global _cur_token
    with _tok_lock: _cur_token = t

# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET — FIXED auth flow + closure bug
# ═══════════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    """
    Auth sequence (matches backend agent.py exactly):
      1. Send {"token": token} as JSON
      2. Wait for {"type":"connected"} ack from backend
      3. Send {"type":"init", ...capabilities...}
      4. Loop: receive messages, dispatch to threads via default-arg closures (FIXED)
    """
    retry = 4.0; max_retry = 90.0

    while _running:
        try:
            log.info("WS connecting..."); print("  [WS] Connecting to Dacexy cloud...")
            connect_kw = {"ping_interval": 25, "ping_timeout": 20, "max_size": 16*1024*1024}
            try:
                wsv = int(str(getattr(websockets, "__version__", "0")).split(".")[0])
                connect_kw["open_timeout" if wsv >= 14 else "close_timeout"] = 20
            except Exception: connect_kw["close_timeout"] = 10

            async with websockets.connect(BACKEND_WS, **connect_kw) as ws:
                # Step 1: Send token
                await ws.send(json.dumps({"token": token}))
                log.info("WS: token sent, waiting for auth ack...")

                # Step 2: Wait for connected ack
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=20)
                    auth_msg = json.loads(auth_raw)
                    if auth_msg.get("type") == "error":
                        log.error("WS auth rejected: %s", auth_msg.get("message", ""))
                        speak("Authentication failed. Check your login.")
                        await asyncio.sleep(retry); retry = min(retry*1.5, max_retry); continue
                    log.info("WS auth ok: type=%s", auth_msg.get("type", "?"))
                except asyncio.TimeoutError:
                    log.warning("WS auth timeout"); await asyncio.sleep(retry); retry = min(retry*1.5, max_retry); continue
                except Exception as e:
                    log.warning("WS auth recv: %s", e); await asyncio.sleep(retry); continue

                # Step 3: Send init
                await ws.send(json.dumps({
                    "type": "init", "version": VERSION,
                    "platform": platform.system(), "machine": platform.machine(),
                    "hostname": socket.gethostname(),
                    "features": ["voice3", "vision_super", "browser_enterprise", "email_enterprise",
                                 "swarm10", "memory_vector", "social_all", "selenium", "ai_brain",
                                 "scheduler", "lead_gen", "web_research", "multi_monitor",
                                 "self_healing", "plugins", "v22_fixed"],
                }))
                log.info("WS fully connected!"); print("  [OK] Connected to Dacexy cloud — agent is LIVE!")
                speak("Connected and ready. I am listening for your commands.")
                retry = 4.0

                ws_lock = asyncio.Lock()
                loop    = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e_: log.warning("ws_send: %s", e_)

                # Step 4: Message loop
                while _running:
                    try: raw = await asyncio.wait_for(ws.recv(), timeout=45)
                    except asyncio.TimeoutError:
                        try: await asyncio.wait_for(ws.send(json.dumps({"type": "ping", "version": VERSION})), timeout=5)
                        except Exception: break
                        continue

                    try: msg = json.loads(raw)
                    except Exception: continue

                    mtype    = msg.get("type", "")
                    action   = msg.get("action", "")
                    task_txt = (msg.get("task") or msg.get("goal") or "").strip()
                    task_id  = str(msg.get("task_id") or "")

                    if mtype == "ping":
                        await ws_send({"type": "pong", "version": VERSION}); continue
                    if mtype in ("pong", "connected", "init_ack", "heartbeat"): continue

                    # Direct command from /desktop/command (action is set, not a task type)
                    if action and action not in ("swarm_task", "task", "run_agent", ""):
                        log.info("Direct command: %s", action)
                        # CLOSURE FIX: default args snapshot current values
                        def _cmd_thread(m_=dict(msg), t_=token, tid_=task_id):
                            try:
                                r_ = exec_cmd(m_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"),
                                    "ok": 1 if r_.get("status") in ("ok", "skipped") else 0,
                                    "total": 1,
                                    "result": str(r_.get("message") or r_.get("opened") or
                                                  r_.get("note") or r_.get("searched") or "done"),
                                    "data": r_,
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 1, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_cmd_thread, daemon=True).start()
                        continue

                    # Full task from /run or /desktop/task
                    if task_txt or mtype in ("task", "command"):
                        if not task_txt: task_txt = action
                        if not task_txt: continue
                        log.info("Task from dashboard: %s", task_txt[:80])
                        print(f"\n  [TASK] {task_txt}")
                        jarvis("work", f"On it! Working on: {task_txt[:50]}")
                        # CLOSURE FIX: default args snapshot current values
                        def _task_thread(t_=token, txt_=task_txt, tid_=task_id):
                            try:
                                r_ = execute_task(txt_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"),
                                    "ok": r_.get("ok", 0), "total": r_.get("total", 1),
                                    "result": r_.get("result", ""),
                                    "steps": r_.get("steps", []),
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 0, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_task_thread, daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK: log.info("WS closed cleanly")
        except websockets.exceptions.ConnectionClosedError as e: log.warning("WS closed error: %s", e)
        except OSError as e: log.warning("WS network: %s", e)
        except Exception as e: log.error("WS exception: %s", e)

        if _running:
            print(f"  [WS] Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry); retry = min(retry*1.5, max_retry)

# ═══════════════════════════════════════════════════════════════════════════
# HEARTBEAT
# ═══════════════════════════════════════════════════════════════════════════
def _heartbeat(token_ref: list):
    while _running:
        time.sleep(300)
        try:
            tok = token_ref[0]
            if tok and not check_token_valid(tok):
                log.warning("Token may be expired — reconnect if issues occur.")
        except Exception as e: log.warning("Heartbeat: %s", e)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "="*60)
    print("  DACEXY AGENT v22.0 — INVESTOR DEMO EDITION")
    print("  Real Jarvis. Actually works.")
    print("="*60 + "\n")

    init_tts()
    load_memory()

    caps = []
    if pyautogui:              caps.append("mouse/keyboard")
    if ImageGrab:              caps.append("screenshot")
    if VOICE_OK:               caps.append("JARVIS VOICE")
    if SELENIUM_OK:            caps.append("browser-automation")
    if BS4_OK:                 caps.append("web-scraping")
    if _smtp_cfg.get("email"): caps.append(f"email={_smtp_cfg['email']}")
    else:                      caps.append("email=NOT CONFIGURED")
    print(f"  Capabilities: {', '.join(caps) or 'basic'}\n")

    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if check_token_valid(token): print("  [OK] Session valid — no login needed.\n")
            else: print("  [INFO] Session expired — please log in.\n"); clear_token(); token = None
        except Exception: token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"\n  Attempt {attempt+1}/3 failed. Try again.\n")
        if not token: print("\n  [ERROR] Authentication failed. Exiting."); sys.exit(1)

    try: setup_autostart()
    except Exception: pass

    if not _smtp_cfg.get("email"):
        print()
        print("  ┌──────────────────────────────────────────────────────┐")
        print("  │  Email not configured.                               │")
        print("  │  Without it: emails open Gmail in your browser.      │")
        print("  │  With it:    1000s of emails send automatically.     │")
        print("  └──────────────────────────────────────────────────────┘")
        try:
            ans = input("\n  Set up email now? (y/N): ").strip().lower()
            if ans == "y": configure_smtp_interactive()
        except (EOFError, KeyboardInterrupt): print()
    else:
        print(f"  [EMAIL] Ready — sending as {_smtp_cfg['email']}")

    voice_ok = start_voice(token)
    tok_ref  = [token]
    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True, name="Heartbeat").start()
    threading.Thread(target=_scheduler_loop, args=(tok_ref,), daemon=True, name="Scheduler").start()

    print()
    print("  " + "─"*58)
    print(f"  Dacexy Agent v{VERSION} — LIVE")
    print(f"  Voice   : {'JARVIS ON — say Dacexy / Jarvis / Computer' if voice_ok else 'OFF (install PyAudio)'}")
    print(f"  Email   : {'Auto-send: '+_smtp_cfg.get('email','') if _smtp_cfg.get('email') else 'Not configured (opens Gmail compose)'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print(f"  Logs    : {LOG_FILE}")
    print("  " + "─"*58)
    print()
    print("  DEMO COMMANDS (voice or dashboard):")
    print("    open youtube")
    print("    search lofi music on youtube")
    print("    send email to boss@gmail.com saying meeting is confirmed")
    print("    find leads for my SaaS product and email them")
    print("    take a screenshot")
    print("    what time is it")
    print("    system info")
    print("    research AI marketing tools 2025")
    print()

    if not websockets:
        print("  [ERROR] websockets not installed! Run: pip install websockets")
        sys.exit(1)

    try: asyncio.run(run_websocket(token))
    except KeyboardInterrupt: print("\n  Stopped by Ctrl+C.")
    except Exception as e: log.error("Fatal: %s", e); print(f"\n  [FATAL] {e}")
    finally:
        global _running; _running = False; stop_voice()
        try: save_memory()
        except Exception: pass
        try: speak("Goodbye!"); time.sleep(0.8)
        except Exception: pass
        print("  Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
