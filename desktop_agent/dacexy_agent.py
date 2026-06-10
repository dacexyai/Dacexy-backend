"""
DACEXY DESKTOP AGENT v18.0 - WORLD'S BEST DESKTOP AI AGENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPGRADES OVER v17.0 (all original code preserved):
  ★ PLANNER BRAIN      - Thinks step-by-step like a human. Breaks any
                         complex task into sub-goals, executes each,
                         verifies, retries on failure (ReAct loop).
  ★ JARVIS VOICE       - Always-on, natural conversation. Says "On it!",
                         confirms completion, asks clarifying questions.
  ★ BULK EMAIL ENGINE  - Send emails to 100s of contacts with
                         personalised content. CSV import supported.
  ★ LEAD FINDER        - Scrapes web for interested customers, builds
                         a lead list, then bulk-emails them.
  ★ SOCIAL SCHEDULER   - Queue posts for Instagram / LinkedIn / Facebook.
                         Runs on a background timer.
  ★ SMART EMAIL SETUP  - Auto-detects Gmail / Outlook / Yahoo SMTP.
                         Guides user through App Password in plain English.
  ★ MEMORY UPGRADE     - Remembers conversation context across turns.
                         Uses it automatically in every AI call.
  ★ SELF-HEALING       - Detects when a step fails, re-plans around it.
  ★ WEB RESEARCH       - Searches Google, scrapes pages, summarises
                         findings and acts on them (research + action).
  ★ FILE OPS UPGRADE   - Create, read, edit, move, rename, zip files.
  ★ SCHEDULER          - "Every day at 9am send me weather" style tasks.
  ★ MULTI-AGENT SWARM  - Splits huge tasks across parallel worker threads.

All v17.0 commands work exactly as before. Zero regressions.
"""
from __future__ import annotations
import subprocess, sys, os, platform

# Windows event loop fix FIRST
if platform.system() == "Windows":
    import asyncio as _af
    if hasattr(_af, "WindowsSelectorEventLoopPolicy"):
        _af.set_event_loop_policy(_af.WindowsSelectorEventLoopPolicy())

# UTF-8 stdout fix
if platform.system() == "Windows":
    import io as _io
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

def _pip(*args):
    subprocess.call([sys.executable, "-m", "pip", "install", *args, "-q",
                     "--no-warn-script-location"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Core packages
for _pkg, _imp in [
    ("pyautogui","pyautogui"), ("pillow","PIL"), ("websockets","websockets"),
    ("requests","requests"), ("pyttsx3","pyttsx3"), ("numpy","numpy"),
    ("psutil","psutil"), ("pyperclip","pyperclip"), ("pygetwindow","pygetwindow"),
    ("plyer","plyer"), ("speechrecognition","speech_recognition"),
    ("keyboard","keyboard"),
]:
    try: __import__(_imp)
    except ImportError: _pip(_pkg)

# NEW v18: extra packages
for _pkg, _imp in [
    ("beautifulsoup4","bs4"), ("lxml","lxml"), ("schedule","schedule"),
    ("pandas","pandas"), ("openpyxl","openpyxl"),
]:
    try: __import__(_imp)
    except ImportError: _pip(_pkg)

# Selenium for browser automation
try: from selenium import webdriver as _sdw; _sdw  # noqa
except ImportError:
    _pip("selenium", "webdriver-manager")

# PyAudio - try multiple methods
PYAUDIO_OK = False
try:
    import pyaudio; PYAUDIO_OK = True
except ImportError:
    for _cmd in [
        [sys.executable, "-m", "pip", "install", "PyAudio", "-q"],
        [sys.executable, "-m", "pip", "install",
         "https://files.pythonhosted.org/packages/source/P/PyAudio/PyAudio-0.2.14.tar.gz", "-q"],
    ]:
        try:
            subprocess.call(_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True; break
        except Exception: pass
    if not PYAUDIO_OK:
        try:
            subprocess.call([sys.executable, "-m", "pip", "install", "pipwin", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True
        except Exception: pass

import asyncio, base64, io, json, logging, threading, time, re, datetime
import webbrowser, ctypes, queue, socket, urllib.parse, shutil, csv, zipfile
import smtplib, random, string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# ── Optional imports ─────────────────────────────────────────────────
try: import pyautogui; pyautogui.FAILSAFE = False; pyautogui.PAUSE = 0.05
except Exception: pyautogui = None

try: import requests as req_lib
except Exception: req_lib = None

try: import websockets
except Exception: websockets = None

try: from PIL import ImageGrab, Image
except Exception: ImageGrab = Image = None

try: import pyttsx3
except Exception: pyttsx3 = None

try: import pyperclip
except Exception: pyperclip = None

try: import psutil
except Exception: psutil = None

try: import winreg; WINREG_OK = True
except Exception: WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except Exception: sr = None; VOICE_AVAILABLE = False

try: import pygetwindow as gw; WINDOW_OK = True
except Exception: gw = None; WINDOW_OK = False

try: from plyer import notification; NOTIFY_OK = True
except Exception: NOTIFY_OK = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except Exception: SELENIUM_OK = False; webdriver = None

# NEW v18 optional imports
try: from bs4 import BeautifulSoup; BS4_OK = True
except Exception: BeautifulSoup = None; BS4_OK = False

try: import schedule as sched_lib; SCHED_OK = True
except Exception: sched_lib = None; SCHED_OK = False

try: import pandas as pd; PANDAS_OK = True
except Exception: pd = None; PANDAS_OK = False

# ── CONSTANTS ────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "agent.log"
LEADS_FILE   = AGENT_DIR / "data" / "leads.csv"
SCHEDULE_FILE= AGENT_DIR / "data" / "schedule.json"
VERSION      = "18.0-BEST"

AGENT_DIR.mkdir(exist_ok=True)
(AGENT_DIR / "logs").mkdir(exist_ok=True)
(AGENT_DIR / "data").mkdir(exist_ok=True)

WAKE_WORDS = [
    "dacexy","hey dacexy","okay dacexy","ok dacexy",
    "computer","hey computer","okay computer","ok computer",
    "hey agent","agent","daisy","hey daisy","jarvis","hey jarvis",
]

SITES = {
    "youtube":"https://www.youtube.com","google":"https://www.google.com",
    "gmail":"https://mail.google.com","facebook":"https://www.facebook.com",
    "instagram":"https://www.instagram.com","twitter":"https://x.com",
    "x":"https://x.com","linkedin":"https://www.linkedin.com",
    "whatsapp":"https://web.whatsapp.com","github":"https://github.com",
    "amazon":"https://www.amazon.in","flipkart":"https://www.flipkart.com",
    "netflix":"https://www.netflix.com","spotify":"https://open.spotify.com",
    "maps":"https://maps.google.com","google maps":"https://maps.google.com",
    "wikipedia":"https://www.wikipedia.org","reddit":"https://www.reddit.com",
    "stackoverflow":"https://stackoverflow.com","chatgpt":"https://chat.openai.com",
    "dacexy":"https://dacexy.vercel.app",
}

APPS = {
    "chrome":"chrome.exe","google chrome":"chrome.exe",
    "edge":"msedge.exe","microsoft edge":"msedge.exe",
    "firefox":"firefox.exe","notepad":"notepad.exe",
    "calculator":"calc.exe","calc":"calc.exe","paint":"mspaint.exe",
    "explorer":"explorer.exe","file explorer":"explorer.exe",
    "task manager":"taskmgr.exe","cmd":"cmd.exe",
    "command prompt":"cmd.exe","terminal":"cmd.exe",
    "word":"winword.exe","excel":"excel.exe","powerpoint":"powerpnt.exe",
    "vlc":"vlc.exe","zoom":"zoom.exe","discord":"discord.exe",
    "spotify":"spotify.exe","vscode":"code.exe",
    "visual studio code":"code.exe","telegram":"telegram.exe",
    "whatsapp desktop":"WhatsApp.exe",
}

BLOCKED = [
    "rm -rf /","rm -rf ~","format c:","del /s /q c:\\windows",
    "rd /s /q c:\\","reg delete hklm","dd if=/dev/zero",
]

# SMTP presets for major providers
SMTP_PRESETS = {
    "gmail.com":     {"host":"smtp.gmail.com",    "port":587},
    "googlemail.com":{"host":"smtp.gmail.com",    "port":587},
    "outlook.com":   {"host":"smtp.office365.com","port":587},
    "hotmail.com":   {"host":"smtp.office365.com","port":587},
    "live.com":      {"host":"smtp.office365.com","port":587},
    "yahoo.com":     {"host":"smtp.mail.yahoo.com","port":587},
    "yahoo.in":      {"host":"smtp.mail.yahoo.com","port":587},
    "icloud.com":    {"host":"smtp.mail.me.com",  "port":587},
    "zoho.com":      {"host":"smtp.zoho.com",     "port":587},
    "protonmail.com":{"host":"smtp.protonmail.ch","port":587},
}

# ── GLOBALS ──────────────────────────────────────────────────────────
_memory_lock   = threading.Lock()
_config_lock   = threading.Lock()
_executor      = ThreadPoolExecutor(max_workers=12)
_agent_running = True
_tts_q: queue.Queue = queue.Queue(maxsize=10)
_tts_engine    = None
_tts_lock      = threading.Lock()
_voice_active  = False
_cur_token     = None
_token_lock    = threading.Lock()
_smtp_config   = {}
_social_queue: list = []   # NEW v18: scheduled social posts
_sched_jobs: list  = []    # NEW v18: scheduled recurring tasks
_convo_history: deque = deque(maxlen=20)  # NEW v18: voice conversation memory

MEMORY = {
    "facts":[], "preferences":{},
    "task_history":deque(maxlen=200), "context":{}
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
    ]
)
log = logging.getLogger("dacexy")
log.info("Dacexy Agent v%s starting", VERSION)

# ── TTS ──────────────────────────────────────────────────────────────
def _tts_worker():
    while _agent_running:
        try:
            text = _tts_q.get(timeout=1)
            if text is None: break
            try:
                with _tts_lock:
                    if _tts_engine:
                        _tts_engine.say(str(text)[:300])
                        _tts_engine.runAndWait()
            except Exception: pass
            finally: _tts_q.task_done()
        except queue.Empty: continue

def init_tts():
    global _tts_engine
    if not pyttsx3: return
    try:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 155)
        _tts_engine.setProperty("volume", 0.9)
        for v in (_tts_engine.getProperty("voices") or []):
            if any(x in (v.name or "").lower() for x in ["zira","hazel","aria","female","india"]):
                _tts_engine.setProperty("voice", v.id); break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS ready")
    except Exception as e: log.warning("TTS init: %s", e)

def speak(text: str):
    if not text: return
    s = str(text)[:300]
    try: print(f"  [Dacexy] {s}"); sys.stdout.flush()
    except: pass
    log.info("SPEAK: %s", s)
    try: _tts_q.put_nowait(s)
    except queue.Full: pass

def notify_desktop(title: str, msg: str):
    try:
        if NOTIFY_OK: notification.notify(title=title, message=msg[:100], app_name="Dacexy", timeout=3)
    except: pass

# ── CONFIG / AUTH ────────────────────────────────────────────────────
def load_config() -> dict:
    with _config_lock:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
        return {}

def save_config(cfg: dict):
    with _config_lock:
        try:
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except Exception as e: log.warning("save_config: %s", e)

def get_token(): return load_config().get("access_token")
def save_token(t): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token(): cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    if not req_lib: return False
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization":f"Bearer {token}"}, timeout=8)
        return r.status_code == 200
    except: return False

def setup_autostart():
    try:
        if not WINREG_OK: return
        bat = str(AGENT_DIR / "install_dacexy_agent.bat")
        cmd = f'"{bat}"' if os.path.exists(bat) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception as e: log.warning("Autostart: %s", e)

def login() -> Optional[str]:
    print("\n" + "="*44)
    print("  Dacexy Agent v18.0 - Login")
    print("="*44)
    print("  Register at: dacexy.vercel.app\n")
    try:
        email    = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt): return None
    if not email or "@" not in email: print("  [ERROR] Invalid email"); return None
    if not password or len(password) < 4: print("  [ERROR] Password too short"); return None
    if not req_lib: print("  [ERROR] requests not installed"); return None
    print("  Connecting...")
    try:
        r = req_lib.post(
            f"{BACKEND_HTTP}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                save_token(token)
                with _memory_lock:
                    if f"email:{email}" not in MEMORY["facts"]:
                        MEMORY["facts"].append(f"email:{email}")
                print("  [OK] Login successful!")
                return token
        r2 = req_lib.post(
            f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if r2.status_code == 200:
            token = r2.json().get("access_token", "")
            if token:
                save_token(token)
                print("  [OK] Login successful!")
                return token
        try: d = r.json().get("detail", r.text[:100])
        except: d = r.text[:100]
        print(f"  [ERROR] {d}")
    except Exception as e: print(f"  [ERROR] {e}")
    return None

# ── MEMORY ───────────────────────────────────────────────────────────
def load_memory():
    try:
        if MEMORY_FILE.exists():
            d = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            with _memory_lock:
                MEMORY["facts"]        = d.get("facts", [])
                MEMORY["preferences"]  = d.get("preferences", {})
                MEMORY["context"]      = d.get("context", {})
                MEMORY["task_history"] = deque(d.get("task_history", [])[-200:], maxlen=200)
                global _smtp_config, _social_queue, _sched_jobs
                _smtp_config  = d.get("smtp_config", {})
                _social_queue = d.get("social_queue", [])
                _sched_jobs   = d.get("sched_jobs", [])
    except Exception as e: log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _memory_lock:
            d = {
                "facts": MEMORY["facts"][-300:], "preferences": MEMORY["preferences"],
                "context": MEMORY["context"], "task_history": list(MEMORY["task_history"])[-200:],
                "smtp_config": _smtp_config,
                "social_queue": _social_queue[-50:],
                "sched_jobs": _sched_jobs[-50:],
            }
        MEMORY_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception as e: log.warning("save_memory: %s", e)

def remember(fact: str):
    if not fact: return
    with _memory_lock:
        if fact not in MEMORY["facts"]: MEMORY["facts"].append(fact)
    save_memory()

def get_memory_ctx() -> str:
    try:
        with _memory_lock:
            parts = []
            if MEMORY["facts"]: parts.append("Facts: " + "; ".join(MEMORY["facts"][-10:]))
            if MEMORY["preferences"]: parts.append("Prefs: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-5:]
            if recent: parts.append("Recent tasks: " + "; ".join(recent))
            # NEW v18: include conversation context
            if _convo_history:
                conv = list(_convo_history)[-6:]
                parts.append("Conversation: " + " | ".join(conv))
        return "\n".join(parts)
    except: return ""

def add_to_convo(role: str, text: str):
    _convo_history.append(f"{role}: {text[:120]}")

# ── SCREENSHOT ───────────────────────────────────────────────────────
def take_screenshot(quality=75) -> Optional[str]:
    try:
        if not ImageGrab: return None
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1440: img = img.resize((1440, int(h*1440/w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e: log.warning("screenshot: %s", e); return None

# ── SMART TYPE ───────────────────────────────────────────────────────
def smart_type(text: str):
    if not text: return
    text = str(text)[:3000]
    try:
        if pyperclip:
            pyperclip.copy(text); time.sleep(0.07)
            if pyautogui: pyautogui.hotkey("ctrl","v"); time.sleep(0.1)
        elif pyautogui:
            pyautogui.write(text[:500], interval=0.02)
    except Exception as e: log.warning("smart_type: %s", e)

def get_active_window() -> str:
    try:
        if WINDOW_OK and gw:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except: pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        l = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(l+1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, l+1)
        return buf.value
    except: return ""

# ── SMART OPEN ───────────────────────────────────────────────────────
def smart_open(target: str) -> dict:
    if not target: return {"status":"error","message":"Nothing to open"}
    t = target.lower().strip()
    for prefix in ["open ","launch ","start ","go to ","navigate to ","show ","visit "]:
        if t.startswith(prefix): t = t[len(prefix):].strip()
    for site, url in SITES.items():
        if site in t:
            webbrowser.open(url); speak(f"Opening {site}")
            return {"status":"ok","opened":url}
    for app, exe in APPS.items():
        if app in t:
            subprocess.Popen(exe, shell=True); speak(f"Opening {app}")
            return {"status":"ok","opened":exe}
    if t.startswith("http://") or t.startswith("https://"):
        webbrowser.open(t); return {"status":"ok","opened":t}
    if "." in t and " " not in t:
        url = "https://" + t; webbrowser.open(url)
        return {"status":"ok","opened":url}
    try:
        subprocess.Popen(target, shell=True)
        return {"status":"ok","opened":target}
    except Exception as e:
        return {"status":"error","message":str(e)}

# ══════════════════════════════════════════════════════════════════════
# NEW v18: SMART EMAIL SETUP
# ══════════════════════════════════════════════════════════════════════
def auto_detect_smtp(email: str) -> dict:
    """Auto-detect SMTP settings from email domain."""
    domain = email.split("@")[-1].lower().strip() if "@" in email else ""
    preset = SMTP_PRESETS.get(domain, {"host": f"smtp.{domain}", "port": 587})
    return preset

def smart_configure_smtp() -> dict:
    """Interactive SMTP setup with auto-detection and plain-English guidance."""
    global _smtp_config
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║    Dacexy Email Setup (One-Time)        ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    print("  This lets Dacexy send emails FOR REAL from your account.")
    print()
    try:
        em = input("  Your email address : ").strip()
        if not em or "@" not in em:
            return {"status":"error","message":"Invalid email"}

        domain = em.split("@")[-1].lower()
        preset = auto_detect_smtp(em)

        print(f"\n  Detected provider: {domain}")
        print(f"  SMTP server      : {preset['host']}:{preset['port']}")

        # Gmail-specific guidance
        if "gmail" in domain:
            print("\n  IMPORTANT - Gmail requires an 'App Password' (not your real password):")
            print("  1. Go to: myaccount.google.com/apppasswords")
            print("  2. Click 'Create App Password'")
            print("  3. Choose 'Mail' and 'Windows Computer'")
            print("  4. Copy the 16-character password shown")
            print("  5. Paste it below (spaces are OK)")
        elif "outlook" in domain or "hotmail" in domain or "live" in domain:
            print("\n  NOTE: Use your normal Microsoft account password.")
            print("  If 2FA is on, create an App Password at account.microsoft.com")
        elif "yahoo" in domain:
            print("\n  NOTE: Yahoo requires an App Password.")
            print("  Go to: security.yahoo.com/security/app-passwords")

        pw = input("\n  Password / App Password : ").strip().replace(" ", "")
        if not pw:
            return {"status":"error","message":"No password entered"}

        # Test the connection
        print("\n  Testing connection...")
        try:
            with smtplib.SMTP(preset["host"], preset["port"], timeout=15) as srv:
                srv.ehlo()
                srv.starttls()
                srv.ehlo()
                srv.login(em, pw)
            print("  ✓ Connected successfully!")
        except smtplib.SMTPAuthenticationError:
            print("  ✗ Authentication failed.")
            if "gmail" in domain:
                print("  → Make sure you used an App Password, not your Gmail password.")
                print("  → Also enable: myaccount.google.com/lesssecureapps")
            return {"status":"error","message":"Authentication failed"}
        except Exception as te:
            print(f"  ✗ Connection test failed: {te}")
            print("  → Saving anyway. Email may not work until connection is fixed.")

        _smtp_config = {
            "email": em, "password": pw,
            "host": preset["host"], "port": preset["port"]
        }
        save_memory()
        speak(f"Email configured! I can now send real emails from {em}.")
        print(f"\n  ✓ Email configured! Dacexy will now send real emails from {em}")
        return {"status":"ok","email":em,"host":preset["host"]}

    except (EOFError, KeyboardInterrupt):
        return {"status":"cancelled","message":"Setup cancelled"}
    except Exception as e:
        return {"status":"error","message":str(e)}

# ── EMAIL (REAL SMTP SEND) ────────────────────────────────────────────
def send_email_smtp(to: str, subject: str, body: str,
                    attachment_path: str = None) -> dict:
    global _smtp_config
    smtp_email    = _smtp_config.get("email","")
    smtp_password = _smtp_config.get("password","")
    smtp_host     = _smtp_config.get("host","smtp.gmail.com")
    smtp_port     = int(_smtp_config.get("port", 587))

    if not smtp_email or not smtp_password:
        # Try to auto-setup
        print("\n  [INFO] Email not configured yet. Starting smart setup...")
        result = smart_configure_smtp()
        if result.get("status") != "ok":
            # Fallback to browser
            url = (f"https://mail.google.com/mail/?view=cm&fs=1"
                   f"&to={urllib.parse.quote(to)}"
                   f"&su={urllib.parse.quote(subject)}"
                   f"&body={urllib.parse.quote(body)}")
            webbrowser.open(url)
            speak(f"Opening Gmail to compose email to {to}.")
            return {"status":"ok","note":"Opened Gmail compose."}
        smtp_email    = _smtp_config.get("email","")
        smtp_password = _smtp_config.get("password","")
        smtp_host     = _smtp_config.get("host","smtp.gmail.com")
        smtp_port     = int(_smtp_config.get("port", 587))

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = smtp_email
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(f"<pre>{body}</pre>", "html"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [to], msg.as_string())

        speak(f"Email sent to {to} successfully!")
        log.info("Email sent to %s", to)
        return {"status":"ok","sent_to":to,"subject":subject}
    except Exception as e:
        log.error("Email SMTP error: %s", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body)}")
        webbrowser.open(url)
        return {"status":"ok","note":f"SMTP failed ({e}), opened Gmail compose instead."}

# ══════════════════════════════════════════════════════════════════════
# NEW v18: BULK EMAIL ENGINE
# ══════════════════════════════════════════════════════════════════════
def send_bulk_email(contacts: list, subject: str, body_template: str,
                    delay_seconds: float = 2.0) -> dict:
    """
    Send personalised emails to a list of contacts.
    contacts = [{"email":"x@y.com","name":"John","company":"Acme"}, ...]
    body_template supports {name}, {company}, {email} placeholders.
    """
    if not contacts:
        return {"status":"error","message":"No contacts provided"}

    smtp_email    = _smtp_config.get("email","")
    smtp_password = _smtp_config.get("password","")
    smtp_host     = _smtp_config.get("host","smtp.gmail.com")
    smtp_port     = int(_smtp_config.get("port", 587))

    if not smtp_email or not smtp_password:
        return {"status":"error","message":"Email not configured. Say 'configure email' first."}

    sent = 0; failed = 0; errors = []
    speak(f"Starting bulk email to {len(contacts)} contacts. This will take a moment.")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)

            for contact in contacts:
                try:
                    to_email = contact.get("email","").strip()
                    if not to_email or "@" not in to_email: continue

                    name    = contact.get("name", to_email.split("@")[0].title())
                    company = contact.get("company","your company")

                    personalised_body = body_template
                    for k, v in [("{name}",name),("{company}",company),
                                  ("{email}",to_email),("{NAME}",name.upper())]:
                        personalised_body = personalised_body.replace(k, v)

                    msg = MIMEMultipart("alternative")
                    msg["From"]    = smtp_email
                    msg["To"]      = to_email
                    msg["Subject"] = subject.replace("{name}",name).replace("{company}",company)
                    msg.attach(MIMEText(personalised_body, "plain"))
                    msg.attach(MIMEText(personalised_body.replace("\n","<br>"), "html"))
                    server.sendmail(smtp_email, [to_email], msg.as_string())
                    sent += 1
                    log.info("Bulk email sent to %s", to_email)
                    time.sleep(delay_seconds)
                except Exception as e:
                    failed += 1
                    errors.append(f"{contact.get('email','?')}: {e}")
                    log.warning("Bulk email failed for %s: %s", contact.get("email","?"), e)

    except Exception as e:
        return {"status":"error","message":f"SMTP connection failed: {e}"}

    summary = f"Bulk email done: {sent} sent, {failed} failed out of {len(contacts)} contacts."
    speak(summary)
    log.info(summary)
    return {"status":"ok","sent":sent,"failed":failed,"errors":errors[:10]}

def load_contacts_from_csv(csv_path: str) -> list:
    """Load contacts from a CSV file with columns: email, name, company (any order)."""
    contacts = []
    try:
        path = Path(csv_path)
        if not path.exists():
            # Try desktop
            alt = Path.home() / "Desktop" / path.name
            if alt.exists(): path = alt
            else: return []

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # flexible column name matching
                email = (row.get("email") or row.get("Email") or row.get("EMAIL") or
                         row.get("e-mail") or "").strip()
                if email and "@" in email:
                    contacts.append({
                        "email": email,
                        "name":  (row.get("name") or row.get("Name") or row.get("NAME") or
                                  email.split("@")[0]).strip(),
                        "company": (row.get("company") or row.get("Company") or
                                    row.get("org") or "").strip(),
                    })
        log.info("Loaded %d contacts from %s", len(contacts), path)
    except Exception as e:
        log.warning("load_contacts_from_csv: %s", e)
    return contacts

# ══════════════════════════════════════════════════════════════════════
# NEW v18: LEAD FINDER (Web Scraping)
# ══════════════════════════════════════════════════════════════════════
def find_leads_web(product: str, niche: str = "", max_leads: int = 30) -> list:
    """
    Search Google for potential customers / leads for a product.
    Returns a list of contact dicts. Uses public web data only.
    """
    if not req_lib:
        return []

    leads = []
    queries = [
        f"{niche} business email contact {product}",
        f"companies interested in {product} email",
        f"site:linkedin.com {niche} {product} contact",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    email_pattern = re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b'
    )
    # Domains to skip
    skip_domains = {"example.com","test.com","sentry.io","wix.com",
                    "wordpress.com","w3.org","schema.org"}

    speak(f"Searching for leads interested in {product}. This takes about 30 seconds.")

    for q in queries:
        if len(leads) >= max_leads: break
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20"
            r = req_lib.get(url, headers=headers, timeout=15)
            if r.status_code != 200: continue

            if BS4_OK:
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(" ", strip=True)
            else:
                text = r.text

            found_emails = email_pattern.findall(text)
            for em in found_emails:
                domain = em.split("@")[-1].lower()
                if domain in skip_domains: continue
                if any(c.get("email","").lower() == em.lower() for c in leads): continue
                leads.append({
                    "email": em,
                    "name":  em.split("@")[0].replace("."," ").replace("_"," ").title(),
                    "company": domain.split(".")[0].title(),
                    "source": "web_search",
                })
                if len(leads) >= max_leads: break
            time.sleep(2)  # respectful delay
        except Exception as e:
            log.warning("Lead search: %s", e)

    # Save leads
    if leads:
        try:
            with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["email","name","company","source"])
                writer.writeheader()
                writer.writerows(leads)
            log.info("Saved %d leads to %s", len(leads), LEADS_FILE)
        except Exception as e:
            log.warning("Save leads: %s", e)

    speak(f"Found {len(leads)} potential leads for {product}.")
    return leads

# ══════════════════════════════════════════════════════════════════════
# NEW v18: WEB RESEARCH ENGINE
# ══════════════════════════════════════════════════════════════════════
def web_research(query: str, max_pages: int = 5) -> str:
    """Search and scrape web pages, return summarized text."""
    if not req_lib:
        return f"Web research unavailable (requests not installed)"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    results_text = []
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        r = req_lib.get(url, headers=headers, timeout=15)

        if BS4_OK:
            soup = BeautifulSoup(r.text, "html.parser")
            # Extract result snippets
            for div in soup.find_all("div", class_=["BNeawe","VwiC3b","MUxGbd"])[:max_pages*2]:
                txt = div.get_text(" ", strip=True)
                if len(txt) > 50: results_text.append(txt)
        else:
            # Basic extraction
            text_clean = re.sub(r'<[^>]+>', ' ', r.text)
            text_clean = re.sub(r'\s+', ' ', text_clean)
            results_text.append(text_clean[:3000])

    except Exception as e:
        log.warning("web_research: %s", e)

    combined = " ".join(results_text[:10])[:4000]
    return combined if combined else f"No results found for: {query}"

# ══════════════════════════════════════════════════════════════════════
# NEW v18: PLANNER BRAIN (ReAct Loop)
# ══════════════════════════════════════════════════════════════════════
PLANNER_SYSTEM = """You are Dacexy, the world's most capable desktop AI agent.
You think step-by-step like a human, then act. You can do ANYTHING a human
can do on a computer, 100x faster.

REASONING STYLE:
1. Understand the full goal
2. Break it into clear sub-steps
3. For each step: choose the right action, execute it, verify success
4. If a step fails: re-plan and try a different approach
5. Always complete the full goal, never give up

You respond with a JSON object:
{
  "thought": "What I'm thinking about this task",
  "plan": ["step 1", "step 2", ...],
  "commands": [
    {"action": "...", ...},
    ...
  ],
  "needs_clarification": false,
  "clarification_question": ""
}

AVAILABLE ACTIONS (use exact action names):
- open / search_web / open_youtube / send_email / send_bulk_email
- bulk_email_leads (find leads + email them)
- web_research (research a topic and return findings)
- social_post / whatsapp_send
- type / click / key / hotkey / screenshot
- speak / notify / wait
- get_time / get_date / get_system_info
- volume_up / volume_down / mute
- write_file / read_file / list_files / delete_file / zip_files
- run_command / kill_process / list_processes
- minimize_window / maximize_window / close_window
- remember / get_memory
- configure_email (smart SMTP setup)
- schedule_task (run a command on a schedule)
- scroll_up / scroll_down / drag / move_mouse

COMPLEX TASK EXAMPLES:
- "send 100 emails to customers interested in my product"
  → find_leads + send_bulk_email with personalised template
- "post on instagram every day at 9am"
  → schedule_task with social_post
- "research competitors and write a report"
  → web_research + write_file
- "email my friend john@gmail.com saying hello"
  → send_email with to=john@gmail.com, subject="Hello", body="Hello!"

RULES:
- NEVER use coordinates (0,0) for clicks
- Always end complex tasks with a speak confirming completion
- If you need info (like email address), ask via needs_clarification
- For email tasks: if no SMTP configured, use configure_email first
- Always include a speak action at the end summarising what was done
- Return ONLY valid JSON, no markdown, no extra text
"""

def planner_brain(task: str, token: str, context: str = "") -> list:
    """
    The core AI brain. Thinks about the task, makes a plan, returns commands.
    Uses ReAct (Reason + Act) approach.
    """
    if not req_lib or not token:
        return []

    mem = get_memory_ctx()
    user_content = f"""Task: {task}

User context:
{mem}

Additional context: {context}

Return a JSON object with thought, plan, and commands array."""

    try:
        r = req_lib.post(
            f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json",
                     "Authorization":f"Bearer {token}"},
            json={
                "messages":[
                    {"role":"system","content":PLANNER_SYSTEM},
                    {"role":"user","content":user_content}
                ],
                "stream":False
            },
            timeout=30,
        )
        if r.status_code != 200:
            log.warning("Planner API %d", r.status_code)
            return []

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw: return []

        # Strip markdown fences
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        # Extract JSON object
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m: return []

        parsed = json.loads(m.group())

        thought = parsed.get("thought","")
        plan    = parsed.get("plan",[])
        commands= parsed.get("commands",[])
        needs_q = parsed.get("needs_clarification", False)
        q_text  = parsed.get("clarification_question","")

        if thought:
            log.info("[BRAIN] %s", thought[:200])
            print(f"\n  [🧠 Brain] {thought[:150]}")

        if plan:
            print(f"  [📋 Plan ] {' → '.join(str(p) for p in plan[:5])}")

        if needs_q and q_text:
            speak(q_text)
            return [{"action":"speak","text":q_text}]

        return commands if isinstance(commands, list) else []

    except Exception as e:
        log.warning("planner_brain: %s", e)
        return []

def planner_react_loop(task: str, token: str, max_iterations: int = 5) -> dict:
    """
    ReAct loop: Plan → Execute → Observe → Re-plan if needed.
    This is what makes Dacexy think like a human.
    """
    iteration = 0
    context = ""
    total_ok = 0
    total_steps = 0

    while iteration < max_iterations:
        iteration += 1
        log.info("[ReAct] Iteration %d for: %s", iteration, task[:80])

        # Get plan from brain
        commands = planner_brain(task, token, context)
        if not commands:
            # Brain failed - try local NLP
            commands = parse_task_locally(task)
        if not commands:
            break

        # Execute commands
        results = []
        all_ok = True
        for cmd in commands:
            if not isinstance(cmd, dict): continue
            # Flatten nested params
            for k, v in cmd.get("params", {}).items():
                if k not in cmd: cmd[k] = v
            try:
                res = execute_command(cmd, token)
                results.append(res)
                if res.get("status") in ("ok","skipped"):
                    total_ok += 1
                else:
                    all_ok = False
                    log.warning("[ReAct] Step failed: %s", res.get("message",""))
                total_steps += 1
                time.sleep(0.3)
            except Exception as e:
                log.error("[ReAct] Command error: %s", e)
                results.append({"status":"error","message":str(e)})
                all_ok = False

        if all_ok:
            break  # Task completed successfully

        # Build observation for re-planning
        failed = [r.get("message","unknown") for r in results if r.get("status") == "error"]
        if failed:
            context = f"Previous attempt had failures: {'; '.join(failed[:3])}. Please adjust the plan."
        else:
            break

    # Record in history
    with _memory_lock:
        MEMORY["task_history"].append(
            f"{datetime.datetime.now().strftime('%H:%M')} - {task[:80]}")
    save_memory()

    summary = f"Done: {total_ok}/{total_steps} steps for '{task[:60]}'"
    log.info("[ReAct] %s", summary)
    return {
        "status": "ok" if total_ok > 0 else "error",
        "ok": total_ok, "total": total_steps,
        "result": summary
    }

# ── SELENIUM BROWSER AUTOMATION ───────────────────────────────────────
def get_chrome_driver(headless=False):
    if not SELENIUM_OK: return None
    try:
        opts = webdriver.ChromeOptions()
        if headless: opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        try:
            svc = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
        except Exception:
            driver = webdriver.Chrome(options=opts)
        driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return driver
    except Exception as e:
        log.error("Chrome driver: %s", e)
        return None

def selenium_post_instagram(username:str, password:str, image_path:str, caption:str="") -> dict:
    driver = get_chrome_driver()
    if not driver:
        return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver, 25)
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        wait.until(EC.presence_of_element_located((By.NAME,"username"))).send_keys(username)
        driver.find_element(By.NAME,"password").send_keys(password)
        driver.find_element(By.NAME,"password").send_keys(Keys.RETURN)
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="menuitem"]//div[contains(@class,"_abl-")]|//a[@href="/create/style/"]|'
            '//*[@aria-label="New post"]'))).click()
        time.sleep(2)
        file_input = driver.find_element(By.XPATH,'//input[@type="file"]')
        file_input.send_keys(os.path.abspath(image_path))
        time.sleep(3)
        for _ in range(2):
            driver.find_element(By.XPATH,
                '//*[text()="Next" or @aria-label="Next"]').click()
            time.sleep(2)
        cap_area = driver.find_element(By.XPATH,
            '//div[@aria-label="Write a caption..." or @aria-label="Write a caption"]')
        cap_area.click(); cap_area.send_keys(caption)
        time.sleep(1)
        driver.find_element(By.XPATH,
            '//*[text()="Share" or @aria-label="Share"]').click()
        time.sleep(5)
        speak("Instagram post published!")
        return {"status":"ok","message":"Posted to Instagram"}
    except Exception as e:
        log.error("Instagram post: %s", e)
        return {"status":"error","message":str(e)}
    finally:
        try: driver.quit()
        except: pass

def selenium_post_linkedin(username:str, password:str, text:str,
                           image_path:str=None) -> dict:
    driver = get_chrome_driver()
    if not driver:
        return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID,"username"))).send_keys(username)
        driver.find_element(By.ID,"password").send_keys(password)
        driver.find_element(By.ID,"password").send_keys(Keys.RETURN)
        time.sleep(4)
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        start_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            '//button[contains(.,"Start a post") or contains(.,"Create a post")]')))
        start_btn.click(); time.sleep(2)
        editor = wait.until(EC.presence_of_element_located((By.XPATH,
            '//div[@role="textbox" and @data-placeholder]')))
        editor.click(); editor.send_keys(text)
        time.sleep(1)
        if image_path and os.path.exists(image_path):
            img_btn = driver.find_element(By.XPATH, '//button[@aria-label="Add a photo"]')
            img_btn.click(); time.sleep(1)
            inp = driver.find_element(By.XPATH,'//input[@type="file"]')
            inp.send_keys(os.path.abspath(image_path)); time.sleep(3)
        driver.find_element(By.XPATH,
            '//button[contains(.,"Post") and @data-control-name="share.post"]|'
            '//button[contains(@class,"share-actions__primary-action")]').click()
        time.sleep(3)
        speak("LinkedIn post published!")
        return {"status":"ok","message":"Posted to LinkedIn"}
    except Exception as e:
        log.error("LinkedIn post: %s", e)
        return {"status":"error","message":str(e)}
    finally:
        try: driver.quit()
        except: pass

def selenium_post_facebook(username:str, password:str, text:str,
                           image_path:str=None) -> dict:
    driver = get_chrome_driver()
    if not driver:
        return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://www.facebook.com/login")
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID,"email"))).send_keys(username)
        driver.find_element(By.ID,"pass").send_keys(password)
        driver.find_element(By.ID,"pass").send_keys(Keys.RETURN)
        time.sleep(5)
        driver.get("https://www.facebook.com/")
        time.sleep(3)
        post_area = wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="button" and (contains(.,"mind") or contains(.,"Mind"))]')))
        post_area.click(); time.sleep(2)
        editor = wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="textbox" and @contenteditable="true"]')))
        editor.click(); editor.send_keys(text)
        time.sleep(1)
        if image_path and os.path.exists(image_path):
            photo_btn = driver.find_element(By.XPATH,'//div[@aria-label="Photo/video"]')
            photo_btn.click(); time.sleep(1)
            inp = driver.find_element(By.XPATH,'//input[@type="file"]')
            inp.send_keys(os.path.abspath(image_path)); time.sleep(3)
        driver.find_element(By.XPATH,
            '//div[@aria-label="Post" and @role="button"]').click()
        time.sleep(3)
        speak("Facebook post published!")
        return {"status":"ok","message":"Posted to Facebook"}
    except Exception as e:
        log.error("Facebook post: %s", e)
        return {"status":"error","message":str(e)}
    finally:
        try: driver.quit()
        except: pass

def selenium_youtube_search(query:str) -> dict:
    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
    speak(f"Searching YouTube for {query}")
    return {"status":"ok","searched":query}

def selenium_google_search(query:str) -> dict:
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    speak(f"Searching Google for {query}")
    return {"status":"ok","searched":query}

def whatsapp_send_web(phone:str, message:str) -> dict:
    phone_clean = re.sub(r"[^0-9+]","",phone)
    if not phone_clean.startswith("+"): phone_clean = "+91" + phone_clean
    url = f"https://wa.me/{phone_clean.lstrip('+')}?text={urllib.parse.quote(message)}"
    webbrowser.open(url)
    speak(f"Opening WhatsApp to send message to {phone}")
    return {"status":"ok","note":"WhatsApp Web opened - click Send in browser"}

# ══════════════════════════════════════════════════════════════════════
# NEW v18: TASK SCHEDULER
# ══════════════════════════════════════════════════════════════════════
def schedule_task(command_or_task: str, schedule_str: str, token_ref: list) -> dict:
    """
    Schedule a recurring task.
    schedule_str examples: "daily at 09:00", "every 30 minutes", "hourly"
    """
    global _sched_jobs

    job = {
        "id": ''.join(random.choices(string.ascii_lowercase, k=8)),
        "task": command_or_task,
        "schedule": schedule_str,
        "created": datetime.datetime.now().isoformat(),
    }
    _sched_jobs.append(job)
    save_memory()

    log.info("Scheduled: '%s' [%s]", command_or_task[:60], schedule_str)
    speak(f"Task scheduled: {command_or_task[:50]} will run {schedule_str}")
    return {"status":"ok","job_id":job["id"],"schedule":schedule_str}

def _scheduler_loop(token_ref: list):
    """Background thread that runs scheduled tasks."""
    if not SCHED_OK: return

    while _agent_running:
        try:
            now = datetime.datetime.now()
            for job in list(_sched_jobs):
                sched = job.get("schedule","").lower()
                last  = job.get("last_run","")

                should_run = False
                # Parse schedule
                if "daily at" in sched:
                    m = re.search(r"(\d{1,2}):(\d{2})", sched)
                    if m:
                        h, mi = int(m.group(1)), int(m.group(2))
                        if now.hour == h and now.minute == mi:
                            # Check not already run this minute
                            if not last or last[:16] != now.strftime("%Y-%m-%dT%H:%M"):
                                should_run = True
                elif "every" in sched and "minute" in sched:
                    m = re.search(r"every\s+(\d+)\s+minute", sched)
                    interval = int(m.group(1)) if m else 30
                    if last:
                        last_dt = datetime.datetime.fromisoformat(last)
                        if (now - last_dt).total_seconds() >= interval * 60:
                            should_run = True
                    else:
                        should_run = True
                elif "hourly" in sched:
                    if last:
                        last_dt = datetime.datetime.fromisoformat(last)
                        if (now - last_dt).total_seconds() >= 3600:
                            should_run = True
                    else:
                        should_run = True

                if should_run:
                    job["last_run"] = now.isoformat()
                    save_memory()
                    tok = token_ref[0]
                    task_text = job.get("task","")
                    log.info("[Scheduler] Running: %s", task_text[:60])
                    if tok:
                        threading.Thread(
                            target=execute_task,
                            args=(task_text, tok),
                            daemon=True
                        ).start()

        except Exception as e:
            log.warning("Scheduler loop: %s", e)

        time.sleep(30)  # Check every 30 seconds

# ── LOCAL NLP COMMAND PARSER ─────────────────────────────────────────
def parse_task_locally(task: str) -> list:
    """Convert natural language task into a list of command dicts (no AI needed)."""
    t = task.lower().strip()
    cmds = []

    # ── OPEN WEBSITE / APP ─────────────────────────────────────────
    open_m = re.match(r"open\s+(.+)", t)
    if open_m:
        target = open_m.group(1).strip()
        cmds.append({"action":"open","target":target})
        cmds.append({"action":"speak","text":f"Opening {target}"})
        return cmds

    # ── SEARCH YOUTUBE ─────────────────────────────────────────────
    yt_m = re.search(r"(?:search|play|find|look up)\s+(.+?)\s+(?:on|in)\s+youtube|"
                     r"youtube\s+(?:search|play)\s+(.+)", t)
    if yt_m:
        q = (yt_m.group(1) or yt_m.group(2) or "").strip()
        cmds.append({"action":"open_youtube","query":q})
        return cmds
    if "youtube" in t and any(w in t for w in ["search","play","watch","find"]):
        q = re.sub(r"(youtube|search|play|watch|find|on|in|for)", "", t).strip()
        cmds.append({"action":"open_youtube","query":q})
        return cmds

    # ── SEARCH GOOGLE ──────────────────────────────────────────────
    g_m = re.search(r"(?:google|search|look up|search for)\s+(.+?)(?:\s+on google)?$", t)
    if g_m and "youtube" not in t:
        q = g_m.group(1).strip()
        cmds.append({"action":"search_web","query":q})
        return cmds

    # ── SEND EMAIL ─────────────────────────────────────────────────
    email_m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?email\s+(?:to\s+)?(.+?)(?:\s+(?:saying|about|with subject|subject)\s+(.+))?$", t)
    if email_m:
        to      = email_m.group(1).strip()
        subject = email_m.group(2) or "Hello from Dacexy"
        body    = task
        cmds.append({"action":"send_email","to":to,"subject":subject,"body":body})
        return cmds

    # NEW v18: BULK EMAIL ──────────────────────────────────────────
    bulk_m = re.search(r"(?:send|email)\s+(?:\d+\s+)?(?:bulk|mass|multiple|batch)\s+email", t)
    if bulk_m or ("send email" in t and ("customers" in t or "leads" in t or "everyone" in t)):
        cmds.append({"action":"bulk_email_leads","product":"my product","niche":""})
        return cmds

    # NEW v18: WEB RESEARCH ────────────────────────────────────────
    research_m = re.match(r"(?:research|find out|look up|investigate)\s+(.+)", t)
    if research_m:
        q = research_m.group(1).strip()
        cmds.append({"action":"web_research","query":q})
        return cmds

    # ── WHATSAPP ───────────────────────────────────────────────────
    wa_m = re.search(r"(?:send|message|whatsapp)\s+(.+?)\s+(?:on\s+whatsapp\s+)?(?:saying|message|text)?\s*(.+)?", t)
    if "whatsapp" in t and wa_m:
        contact = wa_m.group(1).strip()
        msg = wa_m.group(2) or "Hello"
        cmds.append({"action":"whatsapp_send","phone":contact,"message":msg.strip()})
        return cmds

    # ── SCREENSHOT ─────────────────────────────────────────────────
    if any(w in t for w in ["screenshot","screen shot","capture screen","take a screenshot"]):
        cmds.append({"action":"screenshot"})
        cmds.append({"action":"speak","text":"Screenshot taken and saved."})
        return cmds

    # ── TIME / DATE ────────────────────────────────────────────────
    if re.search(r"\btime\b", t): cmds.append({"action":"get_time"}); return cmds
    if re.search(r"\bdate\b|\bday\b|\btoday\b", t): cmds.append({"action":"get_date"}); return cmds

    # ── SYSTEM INFO ────────────────────────────────────────────────
    if any(w in t for w in ["system info","cpu","ram","battery","disk space","memory usage"]):
        cmds.append({"action":"get_system_info"})
        return cmds

    # ── VOLUME ─────────────────────────────────────────────────────
    if re.search(r"volume\s*up|increase\s+volume|louder", t):
        cmds.append({"action":"volume_up","steps":5}); return cmds
    if re.search(r"volume\s*down|decrease\s+volume|quieter|lower\s+volume", t):
        cmds.append({"action":"volume_down","steps":5}); return cmds
    if re.search(r"\bmute\b|\bsilence\b", t):
        cmds.append({"action":"mute"}); return cmds

    # ── WINDOW CONTROLS ────────────────────────────────────────────
    if re.search(r"minimize|minimise", t): cmds.append({"action":"minimize_window"}); return cmds
    if re.search(r"maximize|maximise|full.?screen", t): cmds.append({"action":"maximize_window"}); return cmds
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app)", t): cmds.append({"action":"close_window"}); return cmds

    # ── TYPE TEXT ─────────────────────────────────────────────────
    type_m = re.match(r"(?:type|write|enter|input)\s+(.+)", t)
    if type_m:
        text = type_m.group(1).strip()
        cmds.append({"action":"type","text":text})
        return cmds

    # ── SCROLL ────────────────────────────────────────────────────
    if re.search(r"scroll\s+down", t): cmds.append({"action":"scroll_down","amount":5}); return cmds
    if re.search(r"scroll\s+up", t): cmds.append({"action":"scroll_up","amount":5}); return cmds

    # ── REMEMBER ──────────────────────────────────────────────────
    rem_m = re.match(r"remember\s+(.+)", t)
    if rem_m: cmds.append({"action":"remember","fact":rem_m.group(1)}); return cmds

    # ── WRITE FILE ────────────────────────────────────────────────
    note_m = re.match(r"(?:create|write|make|save)\s+(?:a\s+)?(?:note|file|document)\s+(?:called|named)?\s*(.+?)\s+(?:with|containing|about)?\s*(.+)?", t)
    if note_m:
        fname = re.sub(r"[^\w\s-]","",note_m.group(1)).strip() or "note"
        content = note_m.group(2) or task
        path = str(Path.home() / "Desktop" / f"{fname}.txt")
        cmds.append({"action":"write_file","path":path,"content":content})
        cmds.append({"action":"speak","text":f"Created {fname}.txt on Desktop"})
        return cmds

    # ── INSTAGRAM POST ────────────────────────────────────────────
    if "instagram" in t and any(w in t for w in ["post","upload","share","publish"]):
        img_m = re.search(r"(?:image|photo|picture|file)\s+(?:at\s+|from\s+)?(.+?)(?:\s+with\s+caption\s+(.+))?$", t)
        image_path = img_m.group(1).strip() if img_m else ""
        caption = img_m.group(2) if img_m and img_m.group(2) else task
        cmds.append({"action":"social_post","platform":"instagram",
                     "image_path":image_path,"caption":caption})
        return cmds

    # ── LINKEDIN POST ─────────────────────────────────────────────
    if "linkedin" in t and any(w in t for w in ["post","share","publish","update"]):
        text_m = re.search(r"(?:post|share|publish)\s+(?:on\s+linkedin\s+)?(.+)", t)
        post_text = text_m.group(1).strip() if text_m else task
        cmds.append({"action":"social_post","platform":"linkedin","text":post_text})
        return cmds

    # ── FACEBOOK POST ─────────────────────────────────────────────
    if "facebook" in t and any(w in t for w in ["post","share","publish","update"]):
        text_m = re.search(r"(?:post|share|publish)\s+(?:on\s+facebook\s+)?(.+)", t)
        post_text = text_m.group(1).strip() if text_m else task
        cmds.append({"action":"social_post","platform":"facebook","text":post_text})
        return cmds

    # ── RUN COMMAND ──────────────────────────────────────────────
    run_m = re.match(r"run\s+(?:command\s+)?[\"']?(.+)[\"']?", t)
    if run_m:
        cmds.append({"action":"run_command","command":run_m.group(1)}); return cmds

    # ── OPEN CALCULATOR / NOTEPAD / APPS ─────────────────────────
    for app_name in APPS:
        if app_name in t:
            cmds.append({"action":"open","app":app_name}); return cmds

    # ── SPEAK / SAY ───────────────────────────────────────────────
    say_m = re.match(r"(?:say|speak|tell me)\s+(.+)", t)
    if say_m:
        cmds.append({"action":"speak","text":say_m.group(1)}); return cmds

    # ── HOTKEY / SHORTCUT ─────────────────────────────────────────
    if re.search(r"(?:press|hit)\s+(.+)", t):
        m = re.search(r"(?:press|hit)\s+(.+)", t)
        key = m.group(1).strip() if m else ""
        cmds.append({"action":"key","key":key}); return cmds

    # ── COPY / PASTE / UNDO ───────────────────────────────────────
    if "copy" in t: cmds.append({"action":"copy"}); return cmds
    if "paste" in t: cmds.append({"action":"paste"}); return cmds
    if "undo" in t: cmds.append({"action":"undo"}); return cmds
    if "save" in t and "file" in t: cmds.append({"action":"save"}); return cmds

    # ── CONFIGURE EMAIL / SMTP ────────────────────────────────────
    if "configure" in t and ("email" in t or "smtp" in t or "mail" in t):
        cmds.append({"action":"configure_email"})
        return cmds
    if "smtp" in t:
        cmds.append({"action":"configure_email"})
        return cmds

    # NEW v18: ZIP FILES ───────────────────────────────────────────
    if "zip" in t:
        cmds.append({"action":"zip_files","path":str(Path.home() / "Desktop")})
        return cmds

    # NEW v18: SCHEDULE ────────────────────────────────────────────
    sched_m = re.search(r"(?:schedule|every day|daily|every hour)\s+(.+?)(?:\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?", t)
    if sched_m and ("schedule" in t or "every day" in t or "daily" in t):
        task_part = sched_m.group(1).strip()
        time_part = sched_m.group(2) or "09:00"
        cmds.append({"action":"schedule_task","task":task_part,"schedule":f"daily at {time_part}"})
        return cmds

    return []  # Nothing matched - will fall through to AI

# ── COMMAND EXECUTOR ─────────────────────────────────────────────────
def execute_command(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status":"error","message":"Invalid command"}
    action = str(cmd.get("action","")).lower().strip()
    if not action: return {"status":"error","message":"No action"}
    raw_str = " ".join(str(v) for v in cmd.values())
    if any(b in raw_str.lower() for b in BLOCKED):
        return {"status":"blocked","message":"Blocked for safety"}
    log.info("EXEC: %s", action)

    try:
        # ══ SPEAK / NOTIFY ═══════════════════════════════════════
        if action == "speak":
            speak(cmd.get("text","")); return {"status":"ok"}

        elif action == "notify":
            notify_desktop(cmd.get("title","Dacexy"), cmd.get("text",""))
            return {"status":"ok"}

        # ══ OPEN (website / app / url) ════════════════════════════
        elif action in ("open","open_url","open_browser","launch","start",
                        "navigate","navigate_to","go_to","browse","visit",
                        "open_site","open_website","open_app","run_app"):
            target = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                      cmd.get("name") or cmd.get("site") or cmd.get("target") or "").strip()
            if not target: return {"status":"error","message":"No target"}
            return smart_open(target)

        # ══ EMAIL (single) ════════════════════════════════════════
        elif action in ("send_email","email","compose_email","gmail_send","send_mail","mail"):
            to      = str(cmd.get("to") or cmd.get("email") or "")
            subject = str(cmd.get("subject") or "Message from Dacexy")
            body    = str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "")
            attach  = cmd.get("attachment") or cmd.get("attachment_path") or None
            if not to: return {"status":"error","message":"No recipient"}
            return send_email_smtp(to, subject, body, attach)

        # NEW v18 ══ BULK EMAIL ════════════════════════════════════
        elif action in ("send_bulk_email","bulk_email","mass_email","email_all"):
            contacts = cmd.get("contacts") or []
            csv_path = cmd.get("csv_path") or cmd.get("file") or ""
            if csv_path:
                contacts = load_contacts_from_csv(csv_path)
            subject  = str(cmd.get("subject") or "Hello from Dacexy")
            body     = str(cmd.get("body") or cmd.get("template") or
                           "Hi {name},\n\nHope you are doing well!\n\nBest regards")
            delay    = float(cmd.get("delay",2.0))
            if not contacts:
                return {"status":"error","message":"No contacts. Provide csv_path or contacts list."}
            return send_bulk_email(contacts, subject, body, delay)

        # NEW v18 ══ BULK EMAIL WITH LEAD FINDING ═════════════════
        elif action in ("bulk_email_leads","find_and_email","lead_campaign"):
            product = str(cmd.get("product") or cmd.get("query") or "product")
            niche   = str(cmd.get("niche") or "")
            count   = int(cmd.get("count") or cmd.get("max_leads") or 20)
            subject = str(cmd.get("subject") or f"Interested in {product}?")
            body    = str(cmd.get("body") or cmd.get("template") or
                         f"Hi {{name}},\n\nI noticed you might be interested in {product}.\n"
                         f"I'd love to connect and share how we can help {'{company}'}.\n\n"
                         f"Would you be open to a quick chat?\n\nBest regards")
            speak(f"Finding leads interested in {product} and preparing to email them.")
            leads = find_leads_web(product, niche, count)
            if not leads:
                return {"status":"error","message":"No leads found. Try a different product or niche."}
            return send_bulk_email(leads, subject, body)

        # NEW v18 ══ FIND LEADS ONLY ═══════════════════════════════
        elif action in ("find_leads","lead_finder","scrape_leads"):
            product = str(cmd.get("product") or cmd.get("query") or "")
            niche   = str(cmd.get("niche") or "")
            count   = int(cmd.get("count") or 30)
            leads   = find_leads_web(product, niche, count)
            return {"status":"ok","leads_found":len(leads),"file":str(LEADS_FILE)}

        # NEW v18 ══ CONFIGURE EMAIL ═══════════════════════════════
        elif action in ("configure_email","configure_smtp","setup_email","setup_smtp"):
            return smart_configure_smtp()

        # NEW v18 ══ WEB RESEARCH ══════════════════════════════════
        elif action in ("web_research","research","investigate","find_info"):
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q: return {"status":"error","message":"No query"}
            result = web_research(q)
            # Save to file
            report_path = AGENT_DIR / f"research_{int(time.time())}.txt"
            report_path.write_text(
                f"Research: {q}\nDate: {datetime.datetime.now()}\n\n{result}",
                encoding="utf-8"
            )
            speak(f"Research complete. Found information about {q}. Report saved.")
            if pyautogui:
                subprocess.Popen(f'notepad.exe "{report_path}"', shell=True)
            return {"status":"ok","query":q,"result":result[:500],"saved":str(report_path)}

        # NEW v18 ══ SCHEDULE TASK ═════════════════════════════════
        elif action in ("schedule_task","schedule","add_schedule"):
            task_str = str(cmd.get("task") or cmd.get("command") or cmd.get("text") or "")
            sched    = str(cmd.get("schedule") or cmd.get("when") or "daily at 09:00")
            return schedule_task(task_str, sched, [token])

        # NEW v18 ══ ZIP FILES ══════════════════════════════════════
        elif action in ("zip_files","create_zip","compress"):
            src  = Path(str(cmd.get("path") or Path.home() / "Desktop"))
            dest = Path(str(cmd.get("output") or AGENT_DIR / f"backup_{int(time.time())}.zip"))
            try:
                with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file():
                        zf.write(src, src.name)
                    elif src.is_dir():
                        for f in src.iterdir():
                            if f.is_file(): zf.write(f, f.name)
                speak(f"Zipped files to {dest.name}")
                return {"status":"ok","zip":str(dest)}
            except Exception as e:
                return {"status":"error","message":str(e)}

        # ══ WHATSAPP ══════════════════════════════════════════════
        elif action in ("whatsapp_send","whatsapp","send_whatsapp"):
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            msg   = str(cmd.get("message") or cmd.get("text") or cmd.get("content") or "")
            if not phone: return {"status":"error","message":"No phone number"}
            return whatsapp_send_web(phone, msg)

        # ══ SOCIAL MEDIA POSTING ══════════════════════════════════
        elif action in ("social_post","post_social","instagram_post","linkedin_post",
                        "facebook_post","post_instagram","post_linkedin","post_facebook"):
            platform = str(cmd.get("platform") or action.replace("post_","").replace("_post","") or "")
            username = str(cmd.get("username") or cmd.get("user") or "")
            password = str(cmd.get("password") or cmd.get("pass") or "")
            text     = str(cmd.get("text") or cmd.get("caption") or cmd.get("content") or "")
            img      = cmd.get("image_path") or cmd.get("image") or None
            video    = cmd.get("video_path") or cmd.get("video") or None

            if not username or not password:
                urls = {"instagram":"https://www.instagram.com",
                        "linkedin":"https://www.linkedin.com",
                        "facebook":"https://www.facebook.com",
                        "twitter":"https://x.com","x":"https://x.com"}
                url = urls.get(platform.lower(), "https://www.instagram.com")
                webbrowser.open(url)
                speak(f"Opening {platform}. Provide username and password in the command for auto-posting.")
                return {"status":"ok","note":f"Opened {platform}. Provide credentials for auto-post."}

            if "instagram" in platform.lower():
                if not img:
                    return {"status":"error","message":"Instagram requires an image path"}
                return selenium_post_instagram(username, password, img, text)
            elif "linkedin" in platform.lower():
                return selenium_post_linkedin(username, password, text, img)
            elif "facebook" in platform.lower():
                return selenium_post_facebook(username, password, text, img)
            else:
                webbrowser.open("https://www.instagram.com")
                return {"status":"ok","note":f"Platform {platform} - opened browser"}

        # ══ YOUTUBE SEARCH ════════════════════════════════════════
        elif action in ("open_youtube","youtube","youtube_search"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            return selenium_youtube_search(q) if q else smart_open("youtube")

        # ══ WEB SEARCH ════════════════════════════════════════════
        elif action in ("search_web","search","google_search","google"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q: return selenium_google_search(q)
            return smart_open("google")

        # ══ MOUSE ════════════════════════════════════════════════
        elif action == "click":
            if not pyautogui: return {"status":"error","message":"pyautogui not available"}
            x = int(cmd.get("x") or 0); y = int(cmd.get("y") or 0)
            if x == 0 and y == 0: return {"status":"skipped","reason":"no coordinates"}
            sw, sh = pyautogui.size()
            x = max(0,min(x,sw-1)); y = max(0,min(y,sh-1))
            pyautogui.click(x, y, button=cmd.get("button","left"))
            time.sleep(0.12); return {"status":"ok","at":f"({x},{y})"}

        elif action == "double_click":
            if pyautogui: pyautogui.doubleClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            return {"status":"ok"}

        elif action == "right_click":
            if pyautogui: pyautogui.rightClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            return {"status":"ok"}

        elif action == "move_mouse":
            if pyautogui: pyautogui.moveTo(int(cmd.get("x",0)), int(cmd.get("y",0)), duration=0.15)
            return {"status":"ok"}

        elif action == "scroll":
            amt = int(cmd.get("clicks") or cmd.get("amount") or 3)
            direction = str(cmd.get("direction","down")).lower()
            amt = abs(amt) if direction == "up" else -abs(amt)
            if pyautogui: pyautogui.scroll(amt)
            return {"status":"ok"}

        elif action in ("scroll_down","scrolldown"):
            if pyautogui: pyautogui.scroll(-int(cmd.get("amount",5)))
            return {"status":"ok"}

        elif action in ("scroll_up","scrollup"):
            if pyautogui: pyautogui.scroll(int(cmd.get("amount",5)))
            return {"status":"ok"}

        elif action == "drag":
            if pyautogui:
                x1,y1 = int(cmd.get("x1",0)), int(cmd.get("y1",0))
                x2,y2 = int(cmd.get("x2",0)), int(cmd.get("y2",0))
                pyautogui.moveTo(x1,y1); pyautogui.dragTo(x2,y2,duration=0.4,button="left")
            return {"status":"ok"}

        elif action == "get_mouse_pos":
            if pyautogui: p = pyautogui.position(); return {"status":"ok","x":p.x,"y":p.y}
            return {"status":"ok","x":0,"y":0}

        # ══ KEYBOARD ═════════════════════════════════════════════
        elif action in ("type","type_text","write","input","enter_text"):
            smart_type(cmd.get("text") or cmd.get("content") or "")
            return {"status":"ok"}

        elif action in ("key","press","press_key","keypress"):
            k = cmd.get("key") or cmd.get("keys") or ""
            if k and pyautogui: pyautogui.press(str(k))
            return {"status":"ok"}

        elif action in ("hotkey","key_combo","shortcut"):
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str): keys = keys.replace("+"," ").split()
            if keys and pyautogui: pyautogui.hotkey(*[str(k) for k in keys[:4]])
            return {"status":"ok"}

        elif action == "press_enter":
            if pyautogui: pyautogui.press("enter")
            return {"status":"ok"}

        elif action == "press_tab":
            if pyautogui: pyautogui.press("tab")
            return {"status":"ok"}

        elif action == "press_escape":
            if pyautogui: pyautogui.press("escape")
            return {"status":"ok"}

        elif action == "select_all":
            if pyautogui: pyautogui.hotkey("ctrl","a")
            return {"status":"ok"}

        elif action == "copy":
            if pyautogui: pyautogui.hotkey("ctrl","c"); time.sleep(0.1)
            clip = pyperclip.paste() if pyperclip else ""
            return {"status":"ok","clipboard":clip}

        elif action == "paste":
            if pyautogui: pyautogui.hotkey("ctrl","v")
            return {"status":"ok"}

        elif action == "cut":
            if pyautogui: pyautogui.hotkey("ctrl","x")
            return {"status":"ok"}

        elif action == "undo":
            if pyautogui: pyautogui.hotkey("ctrl","z")
            return {"status":"ok"}

        elif action == "save":
            if pyautogui: pyautogui.hotkey("ctrl","s")
            return {"status":"ok"}

        elif action == "get_clipboard":
            return {"status":"ok","text": pyperclip.paste() if pyperclip else ""}

        elif action == "set_clipboard":
            if pyperclip: pyperclip.copy(str(cmd.get("text",""))[:5000])
            return {"status":"ok"}

        # ══ SCREENSHOT ═══════════════════════════════════════════
        elif action in ("screenshot","take_screenshot"):
            ss = take_screenshot()
            if ss:
                try:
                    import base64 as b64m
                    fname = AGENT_DIR / f"screenshot_{int(time.time())}.jpg"
                    fname.write_bytes(b64m.b64decode(ss))
                    log.info("Screenshot saved: %s", fname)
                    speak(f"Screenshot saved to DacexyAgent folder")
                except: pass
            return {"status":"ok","screenshot":ss}

        # ══ WINDOW ═══════════════════════════════════════════════
        elif action in ("minimize_window","minimize"):
            if pyautogui: pyautogui.hotkey("win","d")
            return {"status":"ok"}

        elif action in ("maximize_window","maximize"):
            if pyautogui: pyautogui.hotkey("win","up")
            return {"status":"ok"}

        elif action in ("close_window","close"):
            if pyautogui: pyautogui.hotkey("alt","f4")
            return {"status":"ok"}

        elif action == "switch_window":
            if pyautogui: pyautogui.hotkey("alt","tab"); time.sleep(0.3)
            return {"status":"ok"}

        elif action == "get_active_window":
            return {"status":"ok","title":get_active_window()}

        elif action in ("open_file_explorer","file_explorer"):
            subprocess.Popen("explorer.exe", shell=True)
            return {"status":"ok"}

        elif action == "open_task_manager":
            subprocess.Popen("taskmgr.exe", shell=True)
            return {"status":"ok"}

        elif action == "open_settings":
            subprocess.Popen("ms-settings:", shell=True)
            return {"status":"ok"}

        elif action in ("open_notepad","notepad"):
            txt = cmd.get("text","")
            if txt:
                tmp = AGENT_DIR / "note.txt"
                tmp.write_text(str(txt)[:50000], encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"', shell=True)
            else:
                subprocess.Popen("notepad.exe", shell=True)
            return {"status":"ok"}

        # ══ VOLUME ═══════════════════════════════════════════════
        elif action == "volume_up":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumeup")
            return {"status":"ok"}

        elif action == "volume_down":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumedown")
            return {"status":"ok"}

        elif action == "mute":
            if pyautogui: pyautogui.press("volumemute")
            return {"status":"ok"}

        # ══ FILES ════════════════════════════════════════════════
        elif action == "write_file":
            p = Path(str(cmd.get("path","")))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(cmd.get("content",""))[:100000], encoding="utf-8")
            if pyautogui:
                subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            return {"status":"ok","path":str(p)}

        elif action == "read_file":
            p = Path(str(cmd.get("path","")))
            if p.exists(): return {"status":"ok","content":p.read_text(encoding="utf-8",errors="ignore")[:5000]}
            return {"status":"error","message":"File not found"}

        elif action == "list_files":
            p = Path(str(cmd.get("path", str(Path.home()))))
            try: return {"status":"ok","files":[f.name for f in p.iterdir()][:50]}
            except Exception as e: return {"status":"error","message":str(e)}

        elif action == "delete_file":
            p = Path(str(cmd.get("path","")))
            if p.exists(): p.unlink(); return {"status":"ok"}
            return {"status":"error","message":"Not found"}

        # NEW v18 ══ MOVE / RENAME FILE ═══════════════════════════
        elif action in ("move_file","rename_file","move"):
            src  = Path(str(cmd.get("src") or cmd.get("source") or cmd.get("path") or ""))
            dest = Path(str(cmd.get("dst") or cmd.get("dest") or cmd.get("destination") or ""))
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                return {"status":"ok","moved":str(dest)}
            return {"status":"error","message":"Source not found"}

        # ══ SYSTEM ═══════════════════════════════════════════════
        elif action in ("get_system_info","system_info","sysinfo"):
            if psutil:
                dp = "C:\\" if platform.system()=="Windows" else "/"
                info = {
                    "cpu":psutil.cpu_percent(interval=0.5),
                    "ram":psutil.virtual_memory().percent,
                    "disk":psutil.disk_usage(dp).percent,
                    "platform":platform.system(),
                    "hostname":socket.gethostname(),
                    "active_window":get_active_window(),
                }
                speak(f"CPU at {info['cpu']} percent, RAM at {info['ram']} percent")
                return {"status":"ok","info":info}
            return {"status":"ok","info":{"platform":platform.system()}}

        elif action == "get_time":
            t = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {t}"); return {"status":"ok","time":t}

        elif action == "get_date":
            d = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {d}"); return {"status":"ok","date":d}

        elif action == "run_command":
            c = str(cmd.get("command",""))
            if any(b in c.lower() for b in BLOCKED): return {"status":"blocked","reason":"Blocked"}
            try:
                r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=30)
                out = r.stdout[:2000]
                if out: speak(out[:200])
                return {"status":"ok","stdout":out,"stderr":r.stderr[:500]}
            except subprocess.TimeoutExpired: return {"status":"error","message":"Timeout"}

        elif action == "kill_process":
            name = str(cmd.get("name",""))
            safe = ["explorer","winlogon","csrss","svchost","system","lsass"]
            if any(p in name.lower() for p in safe): return {"status":"blocked","reason":"System process"}
            if psutil:
                killed = 0
                for p in psutil.process_iter(["name"]):
                    try:
                        if name.lower() in (p.info["name"] or "").lower(): p.kill(); killed+=1
                    except: pass
                return {"status":"ok","killed":killed}
            return {"status":"ok"}

        elif action == "list_processes":
            if psutil:
                procs = []
                for p in psutil.process_iter(["pid","name","cpu_percent"]):
                    try: procs.append(p.info)
                    except: pass
                return {"status":"ok","processes":procs[:30]}
            return {"status":"ok","processes":[]}

        # ══ MEMORY ════════════════════════════════════════════════
        elif action in ("remember","save_fact","take_note"):
            fact = str(cmd.get("fact") or cmd.get("text") or cmd.get("content") or "")
            if fact: remember(fact); speak("Got it, remembered.")
            return {"status":"ok"}

        elif action == "get_memory":
            return {"status":"ok","memory":get_memory_ctx()}

        # ══ WAIT ══════════════════════════════════════════════════
        elif action in ("wait","sleep","pause","delay"):
            secs = min(float(cmd.get("seconds") or cmd.get("duration") or 1), 15)
            time.sleep(secs); return {"status":"ok"}

        # ══ HEALTH ════════════════════════════════════════════════
        elif action in ("ping","pong","test","health","health_check"):
            return {"status":"ok","pong":True,"version":VERSION}

        # ══ DESCRIBE SCREEN ═══════════════════════════════════════
        elif action in ("what_on_screen","describe_screen"):
            win = get_active_window()
            speak(f"Active window: {win}")
            return {"status":"ok","active_window":win}

        # ══ FALLBACK ══════════════════════════════════════════════
        else:
            log.warning("Unknown action '%s' - trying smart_open", action)
            target = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                      cmd.get("name") or cmd.get("target") or action)
            result = smart_open(str(target))
            if result.get("status") == "ok": return result
            return {"status":"error","message":f"Unknown action: {action}"}

    except Exception as e:
        log.error("execute_command [%s]: %s", action, e)
        return {"status":"error","message":str(e)}


# ── TASK EXECUTOR (LOCAL FIRST → PLANNER BRAIN → SMART OPEN) ──────────
def execute_task(task: str, token: str) -> dict:
    """
    Execute a task with the full intelligence stack:
    1. Local NLP (instant, no network)
    2. Planner Brain with ReAct loop (AI + step verification)
    3. Last resort: smart_open
    """
    if not task:
        return {"status":"error","ok":0,"total":0,"result":"No task provided"}

    log.info("Task: %s", task)
    add_to_convo("user", task)

    # Step 1: Try local NLP parser first (fast, no network needed)
    commands = parse_task_locally(task)

    if commands:
        log.info("Local NLP matched: %d commands", len(commands))
        ok_count = 0
        total = len(commands)
        results_list = []
        for i, c in enumerate(commands):
            if not isinstance(c, dict): continue
            for k, v in c.get("params", {}).items():
                if k not in c: c[k] = v
            log.info("Step %d/%d: %s", i+1, total, c.get("action","?"))
            try:
                res = execute_command(c, token)
                results_list.append(res)
                if res.get("status") in ("ok","skipped"): ok_count += 1
                else: log.warning("Step %d failed: %s", i+1, res.get("message",""))
                time.sleep(0.3)
            except Exception as ce:
                log.error("Step %d: %s", i+1, ce)
                results_list.append({"status":"error","message":str(ce)})

        with _memory_lock:
            MEMORY["task_history"].append(
                f"{datetime.datetime.now().strftime('%H:%M')} - {task[:80]}")
        save_memory()

        if ok_count > 0:
            summary = f"Done: {ok_count}/{total} steps for '{task[:60]}'"
            log.info(summary)
            if ok_count > 0: speak(f"Done! {ok_count} out of {total} steps completed.")
            add_to_convo("dacexy", f"Done - {ok_count}/{total} steps")
            return {"status":"ok","ok":ok_count,"total":total,"result":summary,"steps":results_list}

    # Step 2: Use Planner Brain (ReAct loop)
    log.info("Using Planner Brain for: %s", task[:80])
    speak(f"Thinking about how to handle that...")
    result = planner_react_loop(task, token)
    if result.get("ok",0) > 0:
        add_to_convo("dacexy", result.get("result","done"))
        return result

    # Step 3: Last resort - just try to open whatever was said
    log.info("Trying smart_open as last resort")
    res = smart_open(task)
    if res.get("status") == "ok":
        add_to_convo("dacexy", f"Opened: {task}")
        return {"status":"ok","ok":1,"total":1,"result":f"Opened: {task}"}

    speak("I'm not sure how to do that yet. Please try rephrasing or give me more details.")
    return {"status":"error","ok":0,"total":0,"result":"Could not parse task"}


def _get_ai_commands(task: str, token: str) -> list:
    """Legacy fallback - calls backend AI to get command list."""
    if not req_lib or not token: return []
    try:
        mem = get_memory_ctx()
        prompt = f"""You are Dacexy Desktop Agent. Return ONLY a valid JSON array of commands. No text, no markdown.

EXACT ACTION NAMES:
- open website: {{"action":"open","url":"https://youtube.com"}}
- open app: {{"action":"open","app":"chrome.exe"}}
- search google: {{"action":"search_web","query":"weather today"}}
- search youtube: {{"action":"open_youtube","query":"music"}}
- send email: {{"action":"send_email","to":"x@gmail.com","subject":"Hi","body":"Hello"}}
- bulk email with leads: {{"action":"bulk_email_leads","product":"my product","niche":"tech","count":20}}
- send bulk email from csv: {{"action":"send_bulk_email","csv_path":"contacts.csv","subject":"Hi","body":"Hello {{name}}"}}
- web research: {{"action":"web_research","query":"AI trends 2025"}}
- configure email: {{"action":"configure_email"}}
- type text: {{"action":"type","text":"hello"}}
- press key: {{"action":"key","key":"enter"}}
- hotkey: {{"action":"hotkey","keys":["ctrl","c"]}}
- screenshot: {{"action":"screenshot"}}
- speak: {{"action":"speak","text":"Done!"}}
- get time: {{"action":"get_time"}}
- get date: {{"action":"get_date"}}
- volume up: {{"action":"volume_up","steps":3}}
- volume down: {{"action":"volume_down","steps":3}}
- mute: {{"action":"mute"}}
- system info: {{"action":"get_system_info"}}
- write file: {{"action":"write_file","path":"C:/Users/user/Desktop/file.txt","content":"text"}}
- schedule task: {{"action":"schedule_task","task":"send me weather","schedule":"daily at 09:00"}}
- post instagram: {{"action":"social_post","platform":"instagram","username":"u","password":"p","image_path":"C:/img.jpg","caption":"text"}}
- post linkedin: {{"action":"social_post","platform":"linkedin","username":"u","password":"p","text":"post text"}}
- whatsapp: {{"action":"whatsapp_send","phone":"+91XXXXXXXXXX","message":"Hello"}}
- remember: {{"action":"remember","fact":"user likes Python"}}

RULES:
1. NEVER click at 0,0
2. Return ONLY a JSON array, nothing else
3. Always end with a speak action summarizing what was done
4. For emails: if no SMTP set up, use configure_email first

User context: {mem}

Return ONLY JSON array."""

        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":[
                {"role":"system","content":prompt},
                {"role":"user","content":f"Task: {task[:500]}"}
            ],"stream":False}, timeout=25)

        if r.status_code != 200: return []
        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw: return []

        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if not m: return []

        commands = json.loads(m.group())
        return commands if isinstance(commands, list) else []

    except Exception as e:
        log.warning("AI commands: %s", e)
        return []


# ══════════════════════════════════════════════════════════════════════
# NEW v18: JARVIS VOICE ENGINE (full conversational AI)
# ══════════════════════════════════════════════════════════════════════
JARVIS_RESPONSES = {
    "greet":      ["Yes?", "How can I help?", "At your service.", "Listening.", "Go ahead."],
    "working":    ["On it!", "Working on that now.", "Right away.", "Got it, doing that!",
                   "Sure thing!", "Let me handle that.", "Consider it done."],
    "done":       ["All done!", "Done!", "Completed!", "That's taken care of.",
                   "Done, anything else?", "Finished!"],
    "error":      ["I ran into an issue with that.", "That didn't work, let me try another way.",
                   "Hmm, couldn't do that. Want me to try differently?"],
    "unclear":    ["Could you say that again?", "I didn't catch that.",
                   "Sorry, could you repeat?", "One more time?"],
    "thinking":   ["Let me think about that...", "Processing...", "One moment..."],
}

def jarvis_say(category: str, override: str = ""):
    """Say a natural Jarvis-style response."""
    if override:
        speak(override)
    else:
        speak(random.choice(JARVIS_RESPONSES.get(category, [""])))

def _voice_loop():
    global _voice_active
    if not VOICE_AVAILABLE or not sr:
        print("  [WARN] Voice disabled - PyAudio not installed")
        print("  [WARN] Run: pip install PyAudio")
        return

    rec = sr.Recognizer()
    rec.energy_threshold = 350
    rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.6
    rec.non_speaking_duration = 0.3

    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            print("  [WARN] No microphone detected"); return
        print(f"  [MIC] Found {len(mics)} microphone(s): {mics[0]}")
    except Exception as e:
        log.warning("Mic list: %s", e)

    print(f"\n  [VOICE] Jarvis Voice Active!")
    print(f"  Wake words: dacexy / computer / jarvis / hey dacexy")
    speak("Jarvis voice control ready. Say Dacexy, Computer, or Jarvis to wake me up.")
    errs = 0

    while _voice_active and _agent_running:
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.15)
                except: pass
                try:
                    audio = rec.listen(src, timeout=3, phrase_time_limit=6)
                except sr.WaitTimeoutError: continue

            try:
                heard = rec.recognize_google(audio, language="en-IN").lower().strip()
            except sr.UnknownValueError: continue
            except sr.RequestError as e:
                errs += 1; log.warning("SR API: %s", e); time.sleep(2); continue

            log.info("Heard: '%s'", heard)
            errs = 0

            if not any(w in heard for w in WAKE_WORDS): continue

            print(f"\n  [WAKE] '{heard}' detected!")
            jarvis_say("greet")
            time.sleep(0.2)

            # Listen for command
            try:
                with sr.Microphone() as csrc:
                    try: rec.adjust_for_ambient_noise(csrc, duration=0.08)
                    except: pass
                    caudio = rec.listen(csrc, timeout=6, phrase_time_limit=25)

                command = rec.recognize_google(caudio, language="en-IN").strip()
                if not command: continue
                log.info("Voice command: '%s'", command)
                print(f"  [CMD] {command}")

                with _token_lock: tok = _cur_token
                if not tok:
                    speak("I'm not logged in yet. Please wait a moment.")
                    continue

                jarvis_say("working")

                def _run_voice(t, cmd_text):
                    try:
                        result = execute_task(cmd_text, t)
                        if result.get("status") == "ok":
                            if result.get("total",0) == 0:
                                jarvis_say("done")
                        else:
                            jarvis_say("error")
                    except Exception as e:
                        log.error("Voice task: %s", e)
                        speak("Sorry, there was an error with that command.")

                threading.Thread(target=_run_voice, args=(tok, command),
                    daemon=True).start()

            except sr.WaitTimeoutError:
                speak("I didn't hear a command. Just say my name again when you're ready.")
            except sr.UnknownValueError:
                jarvis_say("unclear")
            except Exception as e: log.warning("Command listen: %s", e)

        except OSError as e:
            errs += 1; log.warning("Mic OS error: %s", e); time.sleep(3)
        except Exception as e:
            errs += 1; log.debug("Voice loop: %s", e); time.sleep(0.5)

        if errs >= 8:
            speak("Voice paused due to errors. Resuming in 30 seconds.")
            time.sleep(30); errs = 0

def start_voice(token: str) -> bool:
    global _voice_active, _cur_token
    with _token_lock: _cur_token = token
    if not VOICE_AVAILABLE:
        log.warning("Voice unavailable: PyAudio not installed")
        return False
    _voice_active = True
    threading.Thread(target=_voice_loop, daemon=True, name="Voice").start()
    return True

def stop_voice():
    global _voice_active; _voice_active = False

def update_voice_token(t: str):
    global _cur_token
    with _token_lock: _cur_token = t


# ── WEBSOCKET ────────────────────────────────────────────────────────
async def run_websocket(token: str):
    retry = 3.0; max_retry = 60.0

    while _agent_running:
        try:
            log.info("Connecting to Dacexy backend WebSocket...")
            print("  [WS] Connecting...")

            kw = {"ping_interval":25, "ping_timeout":20, "max_size":10*1024*1024}
            try:
                wsv = int(str(getattr(websockets,"__version__","0")).split(".")[0])
                if wsv >= 14: kw["open_timeout"] = 20
                else: kw["close_timeout"] = 10
            except: pass

            async with websockets.connect(BACKEND_WS, **kw) as ws:
                await ws.send(json.dumps({
                    "token": token,
                    "type": "init",
                    "version": VERSION,
                    "platform": platform.system(),
                    "machine": platform.machine(),
                    "hostname": socket.gethostname(),
                    "features": [
                        "voice3","vision_super","browser_enterprise",
                        "email_enterprise","swarm","memory_vector",
                        "scheduler","self_healing","social_all","selenium",
                        "bulk_email","lead_finder","web_research",
                        "planner_brain","react_loop","jarvis_voice",
                        "smart_smtp_setup","file_ops_v2","task_scheduler",
                    ]
                }))

                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    auth = json.loads(auth_raw)
                    if auth.get("type") == "error":
                        log.error("Auth failed: %s", auth.get("message"))
                        speak("Authentication failed. Please check your login.")
                        return
                except asyncio.TimeoutError:
                    log.error("Auth timeout"); await asyncio.sleep(retry); continue

                log.info("WebSocket connected and authenticated.")
                print("  [OK] Connected - dashboard control active!")
                speak("Connected to Dacexy cloud. All systems ready. I am at your service.")
                retry = 3.0

                _ws_lock = asyncio.Lock()
                loop = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with _ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e: log.warning("ws_send: %s", e)

                while _agent_running:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=40)
                    except asyncio.TimeoutError:
                        try:
                            await asyncio.wait_for(
                                ws.send(json.dumps({"type":"ping","version":VERSION})), timeout=5)
                        except: break
                        continue

                    try: msg = json.loads(raw)
                    except: continue

                    mtype    = msg.get("type","")
                    action   = msg.get("action","")
                    task_text= msg.get("task","") or msg.get("goal","")
                    task_id  = str(msg.get("task_id",""))

                    if mtype == "ping":
                        await ws_send({"type":"pong","version":VERSION}); continue
                    if mtype in ("pong","connected","init_ack"): continue

                    # Direct single command from dashboard
                    if action and action not in ("swarm_task","task","run_agent"):
                        log.info("Direct command: %s", action)
                        def _run_cmd(m, t):
                            try:
                                result = execute_command(m, t)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":task_id,
                                    "status":result.get("status","ok"),
                                    "ok":1 if result.get("status") in ("ok","skipped") else 0,
                                    "total":1,
                                    "result":str(result.get("message","") or result.get("opened","") or "done"),
                                    "data":result
                                }), loop)
                            except Exception as e:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":task_id,
                                    "status":"error","ok":0,"total":1,"result":str(e)
                                }), loop)
                        threading.Thread(target=_run_cmd, args=(msg, token), daemon=True).start()
                        continue

                    # Task (needs full execution)
                    if task_text or mtype in ("task","command"):
                        if not task_text: task_text = action
                        if not task_text: continue
                        log.info("Task from dashboard: %s", task_text)
                        print(f"\n  [TASK] {task_text}")
                        speak(f"Working on it: {task_text[:50]}")

                        def _run_task(t, txt, tid):
                            try:
                                result = execute_task(txt, t)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":result.get("status","ok"),
                                    "ok":result.get("ok",0),"total":result.get("total",1),
                                    "result":result.get("result",""),
                                    "steps":result.get("steps",[])
                                }), loop)
                            except Exception as e:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":"error","ok":0,"total":0,"result":str(e)
                                }), loop)

                        threading.Thread(target=_run_task,
                            args=(token, task_text, task_id), daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK: log.info("WS closed OK")
        except websockets.exceptions.ConnectionClosedError as e: log.warning("WS closed: %s", e)
        except OSError as e: log.warning("WS network: %s", e)
        except Exception as e: log.error("WS: %s", e)

        if _agent_running:
            log.info("Reconnecting in %.0fs", retry)
            print(f"  [WS] Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry)
            retry = min(retry * 1.5, max_retry)


# ── HEARTBEAT ────────────────────────────────────────────────────────
def _heartbeat(token_ref: list):
    while _agent_running:
        time.sleep(300)
        try:
            tok = token_ref[0]
            if tok:
                if not check_token_valid(tok):
                    log.warning("Token expired")
                    speak("My session has expired. Please restart the agent to log in again.")
                else:
                    update_voice_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  DACEXY DESKTOP AGENT v18.0 - WORLD'S BEST DESKTOP AI")
    print("  Powered by Planner Brain + ReAct Loop + Jarvis Voice")
    print("="*60 + "\n")

    init_tts()
    load_memory()

    # Check capabilities
    caps = []
    if pyautogui:       caps.append("mouse/keyboard")
    if ImageGrab:       caps.append("screenshot")
    if VOICE_AVAILABLE: caps.append("jarvis-voice")
    if SELENIUM_OK:     caps.append("browser-automation")
    if _smtp_config.get("email"): caps.append(f"email({_smtp_config['email']})")
    if BS4_OK:          caps.append("web-scraping")
    if PANDAS_OK:       caps.append("data-processing")
    caps.append("planner-brain")
    caps.append("bulk-email")
    caps.append("lead-finder")
    print(f"  Capabilities: {', '.join(caps)}")

    # Auth
    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if check_token_valid(token):
                print("  [OK] Session valid")
            else:
                print("  Session expired."); clear_token(); token = None
        except: pass

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"\n  Attempt {attempt+1}/3 failed.\n")
        if not token:
            print("\n  [ERROR] Cannot authenticate. Exiting.")
            return

    try: setup_autostart()
    except: pass

    # Check if SMTP not configured
    if not _smtp_config.get("email"):
        print("\n  ┌─────────────────────────────────────────────────────┐")
        print("  │  TIP: For real email, say or type: configure email  │")
        print("  │  I'll guide you through it step by step!            │")
        print("  └─────────────────────────────────────────────────────┘")
    else:
        print(f"\n  [EMAIL] Configured as {_smtp_config['email']}")

    tok_ref = [token]

    # Start background threads
    voice_ok = start_voice(token)
    if voice_ok:
        print("  [VOICE] Jarvis Voice Active!")
        print("          Say 'Dacexy' / 'Computer' / 'Jarvis' to wake!")
    else:
        print("  [VOICE] Off (install PyAudio for voice)")

    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True).start()
    threading.Thread(target=_scheduler_loop, args=(tok_ref,), daemon=True, name="Scheduler").start()

    print("\n  " + "─"*58)
    print(f"  Agent v{VERSION}")
    print(f"  Voice   : {'Jarvis ON 🎙️' if voice_ok else 'OFF (install PyAudio)'}")
    print(f"  Brain   : Planner Brain + ReAct Loop ✓")
    print(f"  Email   : {'✓ ' + _smtp_config.get('email','') if _smtp_config.get('email') else '⚠ Not configured (say configure email)'}")
    print(f"  Scraping: {'✓' if BS4_OK else '⚠ install beautifulsoup4'}")
    print(f"  Dashboard: dacexy.vercel.app/dashboard")
    print(f"  Log file: {LOG_FILE}")
    print("  " + "─"*58)
    print()
    print("  POWER COMMANDS:")
    print("    'send 50 emails to people interested in my product'")
    print("    'research top AI tools and write a report'")
    print("    'configure email'  ← smart guided setup")
    print("    'post on instagram every day at 9am'")
    print("    'find leads for my Python course'")
    print("    'send email to friend@gmail.com saying hello'")
    print("    'open youtube'  /  'take screenshot'")
    print("    'what time is it'  /  'open chrome'")
    print()

    if not websockets:
        print("  [ERROR] websockets not installed!"); return

    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n  Stopped by user.")
    except Exception as e:
        log.error("Fatal: %s", e)
        print(f"\n  Fatal error: {e}")
    finally:
        global _agent_running; _agent_running = False
        stop_voice(); save_memory()
        speak("Shutting down. Goodbye!")
        time.sleep(1)
        print("  Goodbye!")


if __name__ == "__main__":
    main()
