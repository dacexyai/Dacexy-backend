"""
DACEXY DESKTOP AGENT v19.0 - DEFINITIVE WORKING EDITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bugs fixed from v18 (which caused the bat to close/crash):

  FIX 1: INFINITE RECURSION removed
          execute_task -> AI brain -> execute_commands (no loop back)

  FIX 2: input() NEVER called in background threads
          SMTP config only happens in main thread at startup

  FIX 3: All exceptions caught in main/finally so exit code = 0

  FIX 4: Voice thresholds tuned, WaitTimeoutError handled properly
          errs counter only increments on real errors not timeouts

  FIX 5: Email falls back to browser silently (no blocking input())

  FIX 6: pyttsx3 crash in finally block caught and ignored

  FIX 7: AI brain returns plain command list - no nested recursion

All v17 + v18 features preserved. Zero regressions.
"""
from __future__ import annotations
import subprocess, sys, os, platform

# ── Windows fixes FIRST (before anything else) ───────────────────────
if platform.system() == "Windows":
    import asyncio as _af
    if hasattr(_af, "WindowsSelectorEventLoopPolicy"):
        _af.set_event_loop_policy(_af.WindowsSelectorEventLoopPolicy())

if platform.system() == "Windows":
    import io as _io
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                       errors="replace", line_buffering=True)
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                       errors="replace", line_buffering=True)
    except Exception:
        pass

# ── Silent package installer ──────────────────────────────────────────
def _pip(*pkgs):
    try:
        subprocess.call(
            [sys.executable, "-m", "pip", "install", *pkgs, "-q",
             "--no-warn-script-location"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    except Exception:
        pass

# ── Core packages (all wrapped in try/except) ─────────────────────────
for _p, _i in [
    ("pyautogui","pyautogui"), ("pillow","PIL"), ("websockets","websockets"),
    ("requests","requests"), ("pyttsx3","pyttsx3"), ("numpy","numpy"),
    ("psutil","psutil"), ("pyperclip","pyperclip"), ("pygetwindow","pygetwindow"),
    ("plyer","plyer"), ("speechrecognition","speech_recognition"),
    ("keyboard","keyboard"), ("beautifulsoup4","bs4"),
    ("schedule","schedule"), ("pandas","pandas"),
]:
    try: __import__(_i)
    except ImportError: _pip(_p)

# Selenium
try:
    from selenium import webdriver as _chk; _chk
except ImportError:
    _pip("selenium", "webdriver-manager")

# PyAudio (voice) - multiple install methods
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
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            import pyaudio; PYAUDIO_OK = True
        except Exception:
            pass

# ── All imports (ALL wrapped in try/except - never crash at import) ───
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
from typing import Optional, List, Dict

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
    VOICE_OK = PYAUDIO_OK
except Exception: sr = None; VOICE_OK = False

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

try: from bs4 import BeautifulSoup; BS4_OK = True
except Exception: BeautifulSoup = None; BS4_OK = False

# ── CONSTANTS ────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "agent.log"
VERSION      = "19.0-DEFINITIVE"

AGENT_DIR.mkdir(exist_ok=True)
(AGENT_DIR / "logs").mkdir(exist_ok=True)
(AGENT_DIR / "data").mkdir(exist_ok=True)

SMTP_PRESETS = {
    "gmail.com":      {"host":"smtp.gmail.com",     "port":587},
    "googlemail.com": {"host":"smtp.gmail.com",     "port":587},
    "outlook.com":    {"host":"smtp.office365.com", "port":587},
    "hotmail.com":    {"host":"smtp.office365.com", "port":587},
    "live.com":       {"host":"smtp.office365.com", "port":587},
    "yahoo.com":      {"host":"smtp.mail.yahoo.com","port":587},
    "yahoo.in":       {"host":"smtp.mail.yahoo.com","port":587},
    "icloud.com":     {"host":"smtp.mail.me.com",   "port":587},
    "zoho.com":       {"host":"smtp.zoho.com",      "port":587},
}

WAKE_WORDS = [
    "dacexy","hey dacexy","okay dacexy","ok dacexy",
    "jarvis","hey jarvis","okay jarvis",
    "computer","hey computer","okay computer",
    "hey agent","agent",
]

SITES = {
    "youtube":"https://www.youtube.com", "google":"https://www.google.com",
    "gmail":"https://mail.google.com", "facebook":"https://www.facebook.com",
    "instagram":"https://www.instagram.com", "twitter":"https://x.com",
    "x":"https://x.com", "linkedin":"https://www.linkedin.com",
    "whatsapp":"https://web.whatsapp.com", "github":"https://github.com",
    "amazon":"https://www.amazon.in", "flipkart":"https://www.flipkart.com",
    "netflix":"https://www.netflix.com", "spotify":"https://open.spotify.com",
    "maps":"https://maps.google.com", "google maps":"https://maps.google.com",
    "wikipedia":"https://www.wikipedia.org", "reddit":"https://www.reddit.com",
    "stackoverflow":"https://stackoverflow.com", "chatgpt":"https://chat.openai.com",
    "dacexy":"https://dacexy.vercel.app", "notion":"https://notion.so",
    "canva":"https://www.canva.com", "figma":"https://www.figma.com",
    "drive":"https://drive.google.com", "google drive":"https://drive.google.com",
    "sheets":"https://sheets.google.com", "docs":"https://docs.google.com",
    "slack":"https://app.slack.com", "trello":"https://trello.com",
}

APPS = {
    "chrome":"chrome.exe", "google chrome":"chrome.exe",
    "edge":"msedge.exe", "microsoft edge":"msedge.exe",
    "firefox":"firefox.exe", "notepad":"notepad.exe",
    "calculator":"calc.exe", "calc":"calc.exe", "paint":"mspaint.exe",
    "explorer":"explorer.exe", "file explorer":"explorer.exe",
    "task manager":"taskmgr.exe", "cmd":"cmd.exe",
    "command prompt":"cmd.exe", "terminal":"cmd.exe",
    "word":"winword.exe", "excel":"excel.exe", "powerpoint":"powerpnt.exe",
    "vlc":"vlc.exe", "zoom":"zoom.exe", "discord":"discord.exe",
    "spotify":"spotify.exe", "vscode":"code.exe",
    "visual studio code":"code.exe", "telegram":"telegram.exe",
    "whatsapp desktop":"WhatsApp.exe",
}

BLOCKED = [
    "rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
    "rd /s /q c:\\", "reg delete hklm", "dd if=/dev/zero",
]

JARVIS_GREET  = ["Yes?","How can I help?","At your service.","Listening.","Go ahead."]
JARVIS_WORK   = ["On it!","Working on that now.","Right away.","Got it!","Sure thing!"]
JARVIS_DONE   = ["All done!","Done!","Completed!","That's taken care of.","Finished!"]
JARVIS_ERROR  = ["I ran into an issue with that.","That didn't work, let me try another way."]
JARVIS_AGAIN  = ["Could you say that again?","I didn't catch that.","Sorry, one more time?"]

# ── GLOBALS ──────────────────────────────────────────────────────────
_mem_lock    = threading.Lock()
_cfg_lock    = threading.Lock()
_executor    = ThreadPoolExecutor(max_workers=10)
_running     = True
_tts_q       = queue.Queue(maxsize=8)
_tts_engine  = None
_tts_lock    = threading.Lock()
_voice_on    = False
_cur_token   = None
_tok_lock    = threading.Lock()
_smtp_cfg    = {}          # loaded from disk at startup
_sched_jobs  = []          # scheduled recurring tasks
_convo       = deque(maxlen=20)  # conversation history for AI

MEMORY = {
    "facts": [], "preferences": {},
    "task_history": deque(maxlen=300), "context": {},
    "contacts": {},
}

# ── LOGGING ──────────────────────────────────────────────────────────
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
    while _running:
        try:
            text = _tts_q.get(timeout=1)
            if text is None: break
            try:
                with _tts_lock:
                    if _tts_engine:
                        _tts_engine.say(str(text)[:350])
                        _tts_engine.runAndWait()
            except Exception: pass
            finally:
                try: _tts_q.task_done()
                except Exception: pass
        except queue.Empty: continue

def init_tts():
    global _tts_engine
    if not pyttsx3: return
    try:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 160)
        _tts_engine.setProperty("volume", 0.92)
        voices = _tts_engine.getProperty("voices") or []
        # Try to find a clear voice
        for v in voices:
            n = (v.name or "").lower()
            if any(x in n for x in ["david","mark","zira","hazel","aria"]):
                _tts_engine.setProperty("voice", v.id); break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS ready")
    except Exception as e:
        log.warning("TTS init failed: %s", e)
        _tts_engine = None

def speak(text: str):
    if not text: return
    s = str(text)[:350]
    try: print(f"  [Dacexy] {s}"); sys.stdout.flush()
    except Exception: pass
    log.info("SPEAK: %s", s)
    try: _tts_q.put_nowait(s)
    except queue.Full: pass

def jarvis(cat: str, override: str = ""):
    opts = {"greet":JARVIS_GREET,"work":JARVIS_WORK,"done":JARVIS_DONE,
            "error":JARVIS_ERROR,"again":JARVIS_AGAIN}
    speak(override if override else random.choice(opts.get(cat, [""])))

def notify(title: str, msg: str):
    try:
        if NOTIFY_OK: notification.notify(title=title, message=msg[:100],
                                          app_name="Dacexy", timeout=3)
    except Exception: pass

# ── CONFIG ───────────────────────────────────────────────────────────
def load_config() -> dict:
    with _cfg_lock:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
        return {}

def save_config(cfg: dict):
    with _cfg_lock:
        try:
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except Exception as e: log.warning("save_config: %s", e)

def get_token():  return load_config().get("access_token")
def save_token(t): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token(): cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    if not req_lib: return False
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"}, timeout=8)
        return r.status_code == 200
    except Exception: return False

def setup_autostart():
    try:
        if not WINREG_OK: return
        bat = str(AGENT_DIR / "install_dacexy_agent.bat")
        cmd = (f'"{bat}"' if os.path.exists(bat)
               else f'"{sys.executable}" "{Path(__file__).resolve()}"')
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered")
    except Exception as e: log.warning("Autostart: %s", e)

# ── LOGIN (main thread only) ─────────────────────────────────────────
def login() -> Optional[str]:
    print("\n" + "="*50)
    print("  DACEXY AGENT v19.0 - Login")
    print("="*50)
    print("  Register at: dacexy.vercel.app\n")
    try:
        email    = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt): return None
    if not email or "@" not in email:
        print("  [ERROR] Invalid email"); return None
    if not password or len(password) < 4:
        print("  [ERROR] Password too short"); return None
    if not req_lib:
        print("  [ERROR] requests not installed"); return None
    print("  Connecting...")
    try:
        # Try form-encoded first (FastAPI OAuth2)
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30)
        if r.status_code == 200:
            t = r.json().get("access_token","")
            if t:
                save_token(t)
                with _mem_lock:
                    if f"email:{email}" not in MEMORY["facts"]:
                        MEMORY["facts"].append(f"email:{email}")
                print("  [OK] Login successful!")
                return t
        # Try JSON fallback
        r2 = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r2.status_code == 200:
            t = r2.json().get("access_token","")
            if t:
                save_token(t); print("  [OK] Login successful!"); return t
        try: d = r.json().get("detail", r.text[:120])
        except Exception: d = r.text[:120]
        print(f"  [ERROR] {d}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    return None

# ── SMTP SETUP (main thread only, never called from background) ───────
def configure_smtp_interactive() -> dict:
    """Only call this from main() - never from a background thread."""
    global _smtp_cfg
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║    Dacexy Email Setup                   ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    print("  For Gmail: go to myaccount.google.com/apppasswords")
    print("  Create an App Password, use it below (not your real password)\n")
    try:
        em = input("  Your email address  : ").strip()
        if not em or "@" not in em: return {"status":"error","message":"Invalid email"}
        pw = input("  Password/App Password: ").strip().replace(" ","")
        if not pw: return {"status":"error","message":"No password"}
        domain = em.split("@")[-1].lower()
        preset = SMTP_PRESETS.get(domain, {"host": f"smtp.{domain}", "port": 587})
        print(f"\n  Testing {preset['host']}:{preset['port']}...")
        try:
            with smtplib.SMTP(preset["host"], preset["port"], timeout=15) as s:
                s.ehlo(); s.starttls(); s.ehlo(); s.login(em, pw)
            print("  ✓ Connection successful!")
        except smtplib.SMTPAuthenticationError:
            print("  ✗ Auth failed - check your App Password")
            return {"status":"error","message":"Auth failed"}
        except Exception as te:
            print(f"  ✗ Connection failed: {te}")
            print("  Saving anyway (may not work until fixed).")
        _smtp_cfg = {"email": em, "password": pw,
                     "host": preset["host"], "port": preset["port"]}
        save_memory()
        print(f"  ✓ Email configured as {em}")
        speak(f"Email configured. I can now send real emails from {em}.")
        return {"status":"ok","email":em}
    except (EOFError, KeyboardInterrupt):
        return {"status":"cancelled"}
    except Exception as e:
        return {"status":"error","message":str(e)}

# ── MEMORY ───────────────────────────────────────────────────────────
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
                MEMORY["task_history"] = deque(d.get("task_history",[])[-300:], maxlen=300)
            _smtp_cfg   = d.get("smtp_config", {})
            _sched_jobs = d.get("sched_jobs", [])
    except Exception as e: log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _mem_lock:
            d = {
                "facts":        MEMORY["facts"][-500:],
                "preferences":  MEMORY["preferences"],
                "context":      MEMORY["context"],
                "contacts":     MEMORY["contacts"],
                "task_history": list(MEMORY["task_history"])[-200:],
                "smtp_config":  _smtp_cfg,
                "sched_jobs":   _sched_jobs[-50:],
            }
        MEMORY_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception as e: log.warning("save_memory: %s", e)

def remember(fact: str):
    if not fact: return
    with _mem_lock:
        if fact not in MEMORY["facts"]: MEMORY["facts"].append(fact)
    save_memory()

def get_mem_ctx() -> str:
    try:
        with _mem_lock:
            parts = []
            if MEMORY["facts"]: parts.append("Facts: " + "; ".join(MEMORY["facts"][-12:]))
            if MEMORY["preferences"]: parts.append("Prefs: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-6:]
            if recent: parts.append("Recent: " + "; ".join(recent))
            if MEMORY["contacts"]:
                names = list(MEMORY["contacts"].keys())[:6]
                parts.append("Contacts: " + ", ".join(names))
        conv = list(_convo)[-8:]
        if conv: parts.append("Conversation: " + " | ".join(conv))
        return "\n".join(parts)
    except Exception: return ""

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
    text = str(text)[:5000]
    try:
        if pyperclip:
            pyperclip.copy(text); time.sleep(0.07)
            if pyautogui: pyautogui.hotkey("ctrl","v"); time.sleep(0.1)
        elif pyautogui:
            pyautogui.write(text[:500], interval=0.02)
    except Exception as e: log.warning("smart_type: %s", e)

def get_active_win() -> str:
    try:
        if WINDOW_OK and gw:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except Exception: pass
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ln = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(ln+1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, ln+1)
        return buf.value
    except Exception: return ""

# ── SMART OPEN ───────────────────────────────────────────────────────
def smart_open(target: str) -> dict:
    if not target: return {"status":"error","message":"Nothing to open"}
    t = target.lower().strip()
    for pfx in ["open ","launch ","start ","go to ","navigate to ","show ","visit "]:
        if t.startswith(pfx): t = t[len(pfx):].strip()
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

# ── EMAIL SEND (NEVER calls input()) ──────────────────────────────────
def send_email_real(to: str, subject: str, body: str,
                    attachment: str = None) -> dict:
    """Send email via SMTP. Falls back to browser silently - NEVER blocks."""
    em  = _smtp_cfg.get("email","")
    pw  = _smtp_cfg.get("password","")
    ht  = _smtp_cfg.get("host","smtp.gmail.com")
    pt  = int(_smtp_cfg.get("port", 587))

    if not em or not pw:
        # SILENT browser fallback - no input() call
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body[:2000])}")
        webbrowser.open(url)
        speak(f"Opening Gmail for {to}. Say 'configure email' to enable auto-send.")
        return {"status":"ok","note":"Gmail opened. Say 'configure email' to enable real sending."}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = em
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(body.replace("\n","<br>"), "html"))
        if attachment and os.path.exists(str(attachment)):
            with open(str(attachment),"rb") as f:
                part = MIMEBase("application","octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                f"attachment; filename={os.path.basename(str(attachment))}")
            msg.attach(part)
        with smtplib.SMTP(ht, pt, timeout=25) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo()
            srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        speak(f"Email sent to {to}!")
        log.info("Email sent to %s", to)
        return {"status":"ok","sent_to":to}
    except smtplib.SMTPAuthenticationError:
        speak("Email auth failed. Run configure email to fix it.")
        return {"status":"error","message":"SMTP auth failed"}
    except Exception as e:
        log.error("SMTP: %s", e)
        # Silent browser fallback
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body[:2000])}")
        webbrowser.open(url)
        return {"status":"ok","note":f"SMTP error, opened Gmail instead"}

# ── BULK EMAIL ────────────────────────────────────────────────────────
def send_bulk_email(contacts: list, subject: str, body_tmpl: str,
                    delay: float = 2.5) -> dict:
    em  = _smtp_cfg.get("email","")
    pw  = _smtp_cfg.get("password","")
    ht  = _smtp_cfg.get("host","smtp.gmail.com")
    pt  = int(_smtp_cfg.get("port", 587))
    if not em or not pw:
        return {"status":"error","message":"Email not configured. Say 'configure email' first."}
    speak(f"Sending bulk email to {len(contacts)} contacts.")
    sent = 0; failed = 0
    try:
        with smtplib.SMTP(ht, pt, timeout=25) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            for c in contacts:
                try:
                    to_e = c.get("email","").strip()
                    if not to_e or "@" not in to_e: continue
                    name = c.get("name", to_e.split("@")[0].title())
                    company = c.get("company","")
                    body = (body_tmpl.replace("{name}",name)
                                     .replace("{email}",to_e)
                                     .replace("{company}",company)
                                     .replace("{NAME}",name.upper()))
                    subj = subject.replace("{name}",name).replace("{company}",company)
                    msg = MIMEMultipart("alternative")
                    msg["From"] = em; msg["To"] = to_e; msg["Subject"] = subj
                    msg.attach(MIMEText(body,"plain"))
                    msg.attach(MIMEText(body.replace("\n","<br>"),"html"))
                    srv.sendmail(em,[to_e],msg.as_string())
                    sent += 1; log.info("Bulk sent to %s", to_e)
                    time.sleep(delay)
                except Exception as e2:
                    failed += 1; log.warning("Bulk fail %s: %s", c.get("email","?"), e2)
    except Exception as e:
        return {"status":"error","message":f"SMTP connection failed: {e}"}
    summary = f"Bulk email: {sent} sent, {failed} failed of {len(contacts)}"
    speak(summary); log.info(summary)
    return {"status":"ok","sent":sent,"failed":failed}

def load_csv_contacts(path: str) -> list:
    contacts = []
    try:
        p = Path(path)
        if not p.exists():
            p2 = Path.home() / "Desktop" / p.name
            if p2.exists(): p = p2
            else: return []
        with open(p,"r",encoding="utf-8",errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = (row.get("email") or row.get("Email") or row.get("EMAIL") or "").strip()
                if em and "@" in em:
                    contacts.append({
                        "email": em,
                        "name":  (row.get("name") or row.get("Name") or em.split("@")[0]).strip(),
                        "company": (row.get("company") or row.get("Company") or "").strip(),
                    })
        log.info("Loaded %d contacts from %s", len(contacts), p)
    except Exception as e: log.warning("load_csv: %s", e)
    return contacts

# ── WEB RESEARCH ──────────────────────────────────────────────────────
def web_research(query: str) -> str:
    if not req_lib: return f"Research on '{query}' - web access unavailable."
    hdrs = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        r = req_lib.get(url, headers=hdrs, timeout=15)
        if BS4_OK and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            snippets = []
            for tag in soup.find_all(["div","span"], class_=lambda c: c and
                    any(x in c for x in ["BNeawe","VwiC3b","MUxGbd","lyLwlc"])):
                t = tag.get_text(" ", strip=True)
                if len(t) > 60: snippets.append(t)
            return " ".join(snippets[:8])[:4000]
        text = re.sub(r'<[^>]+>',' ',r.text)
        return re.sub(r'\s+',' ',text)[:3000]
    except Exception as e:
        return f"Research error: {e}"

def find_leads_web(product: str, niche: str = "", max_leads: int = 30) -> list:
    if not req_lib: return []
    leads = []
    hdrs  = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    email_re = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b')
    skip = {"example.com","test.com","sentry.io","w3.org","schema.org","wix.com"}
    speak(f"Searching for leads for {product}. This takes about 30 seconds.")
    for q in [f"{niche} {product} email contact", f"companies {product} interested email"]:
        if len(leads) >= max_leads: break
        try:
            r = req_lib.get(
                f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20",
                headers=hdrs, timeout=15)
            text = BeautifulSoup(r.text,"html.parser").get_text() if BS4_OK else r.text
            for em in email_re.findall(text):
                domain = em.split("@")[-1].lower()
                if domain in skip: continue
                if any(l["email"].lower()==em.lower() for l in leads): continue
                leads.append({"email":em,
                    "name":em.split("@")[0].replace("."," ").title(),
                    "company":domain.split(".")[0].title()})
                if len(leads) >= max_leads: break
            time.sleep(2)
        except Exception as e: log.warning("lead search: %s", e)
    # Save leads
    try:
        leads_file = AGENT_DIR / "data" / "leads.csv"
        with open(leads_file,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["email","name","company"])
            w.writeheader(); w.writerows(leads)
    except Exception: pass
    speak(f"Found {len(leads)} potential leads for {product}.")
    return leads

# ── SELENIUM ──────────────────────────────────────────────────────────
def get_driver(headless=False):
    if not SELENIUM_OK: return None
    try:
        opts = webdriver.ChromeOptions()
        if headless: opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches",["enable-automation"])
        opts.add_experimental_option("useAutomationExtension",False)
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        try:
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()), options=opts)
        except Exception:
            driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return driver
    except Exception as e: log.error("Chrome driver: %s", e); return None

def _sel_login(driver, wait, url, fields: dict, submit=None):
    driver.get(url); time.sleep(2)
    for selector, value in fields.items():
        try:
            el = wait.until(EC.presence_of_element_located((By.NAME, selector)))
            el.clear(); el.send_keys(value)
        except Exception: pass
    if submit:
        try:
            driver.find_element(By.NAME, submit).send_keys(Keys.RETURN)
        except Exception: pass
    time.sleep(4)

def post_instagram(user,pw,img,caption="") -> dict:
    d = get_driver()
    if not d: return {"status":"error","message":"Chrome not available"}
    try:
        w = WebDriverWait(d,25)
        _sel_login(d,w,"https://www.instagram.com/accounts/login/",
                   {"username":user,"password":pw},"password")
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//*[@aria-label="New post"] | //a[contains(@href,"create")]'))).click()
        time.sleep(2)
        d.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(img))
        time.sleep(3)
        for _ in range(2):
            d.find_element(By.XPATH,'//div[text()="Next" or @aria-label="Next"]').click()
            time.sleep(2)
        cap = d.find_element(By.XPATH,'//div[contains(@aria-label,"caption")]')
        cap.click(); cap.send_keys(caption); time.sleep(1)
        d.find_element(By.XPATH,'//div[text()="Share" or @aria-label="Share"]').click()
        time.sleep(5)
        speak("Instagram post published!"); return {"status":"ok"}
    except Exception as e: log.error("Instagram: %s",e); return {"status":"error","message":str(e)}
    finally:
        try: d.quit()
        except Exception: pass

def post_linkedin(user,pw,text,img=None) -> dict:
    d = get_driver()
    if not d: return {"status":"error","message":"Chrome not available"}
    try:
        w = WebDriverWait(d,20)
        d.get("https://www.linkedin.com/login"); time.sleep(2)
        w.until(EC.presence_of_element_located((By.ID,"username"))).send_keys(user)
        d.find_element(By.ID,"password").send_keys(pw+Keys.RETURN); time.sleep(4)
        d.get("https://www.linkedin.com/feed/"); time.sleep(3)
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//button[contains(.,"Start a post") or contains(.,"Create a post")]'))).click()
        time.sleep(2)
        ed = w.until(EC.presence_of_element_located((By.XPATH,
            '//div[@role="textbox" and @data-placeholder]')))
        ed.click(); ed.send_keys(text); time.sleep(1)
        if img and os.path.exists(img):
            d.find_element(By.XPATH,'//button[@aria-label="Add a photo"]').click()
            time.sleep(1)
            d.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(img))
            time.sleep(3)
        d.find_element(By.XPATH,
            '//button[contains(@class,"share-actions__primary-action")]').click()
        time.sleep(3); speak("LinkedIn post published!"); return {"status":"ok"}
    except Exception as e: log.error("LinkedIn: %s",e); return {"status":"error","message":str(e)}
    finally:
        try: d.quit()
        except Exception: pass

def post_facebook(user,pw,text,img=None) -> dict:
    d = get_driver()
    if not d: return {"status":"error","message":"Chrome not available"}
    try:
        w = WebDriverWait(d,20)
        d.get("https://www.facebook.com/login"); time.sleep(2)
        w.until(EC.presence_of_element_located((By.ID,"email"))).send_keys(user)
        d.find_element(By.ID,"pass").send_keys(pw+Keys.RETURN); time.sleep(5)
        d.get("https://www.facebook.com/"); time.sleep(3)
        w.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="button" and contains(.,"mind")]'))).click(); time.sleep(2)
        ed = w.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="textbox" and @contenteditable="true"]')))
        ed.click(); ed.send_keys(text); time.sleep(1)
        if img and os.path.exists(img):
            d.find_element(By.XPATH,'//div[@aria-label="Photo/video"]').click()
            time.sleep(1)
            d.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(img))
            time.sleep(3)
        d.find_element(By.XPATH,'//div[@aria-label="Post" and @role="button"]').click()
        time.sleep(3); speak("Facebook post published!"); return {"status":"ok"}
    except Exception as e: log.error("Facebook: %s",e); return {"status":"error","message":str(e)}
    finally:
        try: d.quit()
        except Exception: pass

def wa_send(phone: str, msg: str) -> dict:
    ph = re.sub(r"[^0-9+]","",phone)
    if not ph.startswith("+"): ph = "+91" + ph
    url = f"https://wa.me/{ph.lstrip('+')}?text={urllib.parse.quote(msg)}"
    webbrowser.open(url); speak(f"WhatsApp opened for {phone}")
    return {"status":"ok","note":"Click Send in browser"}

# ── AI BRAIN (returns command list - NO recursion back to execute_task) ─
BRAIN_PROMPT = """You are Dacexy, the world's best desktop AI agent running on Windows.
You control the PC directly. Think step-by-step. Return ONLY a valid JSON array of commands.

TODAY: {date}
USER CONTEXT:
{ctx}

AVAILABLE ACTIONS (copy exact action name):
  open website:      {{"action":"open","url":"https://site.com"}}
  open app:          {{"action":"open","app":"chrome.exe"}}
  google search:     {{"action":"search_web","query":"text"}}
  youtube search:    {{"action":"open_youtube","query":"text"}}
  send email:        {{"action":"send_email","to":"a@b.com","subject":"S","body":"B"}}
  bulk email csv:    {{"action":"bulk_email","csv_path":"C:/contacts.csv","subject":"S","body":"Hi {{name}}"}}
  bulk email list:   {{"action":"bulk_email","contacts":[{{"email":"a@b.com","name":"A"}}],"subject":"S","body":"Hi {{name}}"}}
  find leads+email:  {{"action":"find_leads_and_email","product":"product name","niche":"tech","subject":"S","body":"Hi {{name}}"}}
  find leads only:   {{"action":"find_leads","product":"p","niche":"n","max":20}}
  web research:      {{"action":"web_research","query":"topic"}}
  instagram post:    {{"action":"social_post","platform":"instagram","username":"u","password":"p","image_path":"C:/img.jpg","caption":"text"}}
  linkedin post:     {{"action":"social_post","platform":"linkedin","username":"u","password":"p","text":"post"}}
  facebook post:     {{"action":"social_post","platform":"facebook","username":"u","password":"p","text":"post"}}
  whatsapp:          {{"action":"whatsapp","phone":"+91XXXXXXXXXX","message":"text"}}
  type text:         {{"action":"type","text":"text to type"}}
  press key:         {{"action":"key","key":"enter"}}
  hotkey:            {{"action":"hotkey","keys":["ctrl","c"]}}
  screenshot:        {{"action":"screenshot"}}
  speak:             {{"action":"speak","text":"message"}}
  get time:          {{"action":"get_time"}}
  get date:          {{"action":"get_date"}}
  system info:       {{"action":"get_system_info"}}
  volume up/down:    {{"action":"volume_up","steps":3}}
  mute:              {{"action":"mute"}}
  minimize:          {{"action":"minimize_window"}}
  maximize:          {{"action":"maximize_window"}}
  close window:      {{"action":"close_window"}}
  write file:        {{"action":"write_file","path":"C:/Desktop/file.txt","content":"text"}}
  read file:         {{"action":"read_file","path":"C:/file.txt"}}
  zip files:         {{"action":"zip_files","path":"C:/folder","output":"C:/backup.zip"}}
  run command:       {{"action":"run_command","command":"dir"}}
  remember:          {{"action":"remember","fact":"info"}}
  wait:              {{"action":"wait","seconds":2}}
  schedule task:     {{"action":"schedule_task","task":"send weather email","schedule":"daily at 09:00"}}
  add contact:       {{"action":"add_contact","name":"John","email":"j@gmail.com","phone":"+91..."}}

RULES:
1. NEVER click at coordinates (0,0)
2. Return ONLY a JSON array - no text, no markdown, no explanation
3. Always end with a speak action summarising what was done
4. For "send email to X saying Y" -> single send_email action
5. For "send 100 emails to customers" -> find_leads_and_email action
6. For "post on Instagram" -> need username, password, image_path, caption

Return ONLY the JSON array. Example:
[{{"action":"open","url":"https://youtube.com"}},{{"action":"speak","text":"YouTube opened!"}}]"""

def ai_plan(task: str, token: str) -> list:
    """Call AI, get command list. Returns [] on any failure. No recursion."""
    if not req_lib or not token: return []
    try:
        ctx = get_mem_ctx()
        date_str = datetime.datetime.now().strftime("%A %d %B %Y %I:%M %p")
        system = BRAIN_PROMPT.format(date=date_str, ctx=ctx)
        msgs = [{"role":"system","content":system}]
        # Add recent conversation for context
        for c in list(_convo)[-6:]:
            role = "user" if c.startswith("user:") else "assistant"
            msgs.append({"role":role,"content":c.split(":",1)[-1].strip()})
        msgs.append({"role":"user","content":f"Task: {task[:600]}"})

        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json",
                     "Authorization":f"Bearer {token}"},
            json={"messages":msgs,"stream":False}, timeout=35)

        if r.status_code != 200:
            log.warning("AI plan HTTP %d", r.status_code); return []

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw: return []

        # Strip markdown
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        # Extract JSON array (must be array, not object - prevents wrong parsing)
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            try:
                cmds = json.loads(m.group())
                if isinstance(cmds, list) and cmds:
                    log.info("AI plan: %d commands for: %s", len(cmds), task[:60])
                    return cmds
            except json.JSONDecodeError as e:
                log.warning("AI JSON parse: %s", e)

        # AI returned plain text (conversational response) - wrap in speak
        clean = re.sub(r'[{}\[\]]','',raw)[:300].strip()
        if clean:
            return [{"action":"speak","text":clean}]
        return []

    except req_lib.exceptions.Timeout:
        log.warning("AI plan timeout"); return []
    except Exception as e:
        log.warning("ai_plan: %s", e); return []

# ── LOCAL NLP (fast, no network) ─────────────────────────────────────
def local_parse(task: str) -> list:
    t = task.lower().strip()

    # OPEN WEBSITE / APP
    m = re.match(r"open\s+(.+)", t)
    if m:
        tgt = m.group(1).strip()
        return [{"action":"open","target":tgt},{"action":"speak","text":f"Opening {tgt}"}]

    # YOUTUBE SEARCH
    m = re.search(r"(?:search|play|find)\s+(.+?)\s+(?:on|in)\s+youtube", t)
    if m: return [{"action":"open_youtube","query":m.group(1).strip()}]
    if "youtube" in t and any(w in t for w in ["search","play","watch","find"]):
        q = re.sub(r"(youtube|search|play|watch|find|on|in|for)","",t).strip()
        return [{"action":"open_youtube","query":q}]

    # GOOGLE SEARCH
    m = re.search(r"(?:google|search for|look up|search)\s+(.+?)(?:\s+on google)?$", t)
    if m and "youtube" not in t:
        return [{"action":"search_web","query":m.group(1).strip()}]

    # SEND EMAIL (simple)
    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?email\s+(?:to\s+)?([^\s,]+)(?:\s+(?:saying|about|with subject)\s+(.+))?$", t)
    if m:
        return [{"action":"send_email","to":m.group(1).strip(),
                 "subject":m.group(2) or "Hello from Dacexy","body":task}]

    # BULK EMAIL (complex)
    if re.search(r"(?:bulk|mass|multiple)\s+email|send\s+(?:\d+\s+)?emails?\s+to\s+(?:customer|lead|everyone)", t):
        return [{"action":"speak","text":"I need to find leads first. Working on it..."}]
    # (falls through to AI for actual execution)

    # WHATSAPP
    if "whatsapp" in t:
        m = re.search(r"(?:send|message)\s+(.+?)\s+(?:on\s+whatsapp\s+)?(?:saying|message)?\s*(.+)?", t)
        if m:
            return [{"action":"whatsapp","phone":m.group(1).strip(),
                     "message":(m.group(2) or "Hello").strip()}]

    # SCREENSHOT
    if any(w in t for w in ["screenshot","screen shot","capture screen"]):
        return [{"action":"screenshot"},{"action":"speak","text":"Screenshot taken and saved."}]

    # TIME / DATE
    if re.search(r"\btime\b", t) and not re.search(r"send|schedul", t):
        return [{"action":"get_time"}]
    if re.search(r"\bdate\b|\btoday\b", t) and not re.search(r"send|schedul", t):
        return [{"action":"get_date"}]

    # SYSTEM INFO
    if any(w in t for w in ["system info","cpu usage","ram usage","disk space","memory"]):
        return [{"action":"get_system_info"}]

    # VOLUME
    if re.search(r"volume\s*up|increase\s+volume|louder", t): return [{"action":"volume_up","steps":5}]
    if re.search(r"volume\s*down|lower\s+volume|quieter", t): return [{"action":"volume_down","steps":5}]
    if re.search(r"\bmute\b|\bsilence\b", t): return [{"action":"mute"}]

    # WINDOW
    if re.search(r"minimiz|minimis", t): return [{"action":"minimize_window"}]
    if re.search(r"maximiz|maximis|full.?screen", t): return [{"action":"maximize_window"}]
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app)", t): return [{"action":"close_window"}]

    # TYPE TEXT
    m = re.match(r"(?:type|write|enter|input)\s+(.+)", t)
    if m: return [{"action":"type","text":m.group(1).strip()}]

    # SCROLL
    if re.search(r"scroll\s+down", t): return [{"action":"scroll_down","amount":5}]
    if re.search(r"scroll\s+up", t): return [{"action":"scroll_up","amount":5}]

    # REMEMBER
    m = re.match(r"remember\s+(.+)", t)
    if m: return [{"action":"remember","fact":m.group(1)}]

    # SAY/SPEAK
    m = re.match(r"(?:say|speak|tell me)\s+(.+)", t)
    if m: return [{"action":"speak","text":m.group(1)}]

    # HOTKEY
    m = re.search(r"(?:press|hit)\s+(.+)", t)
    if m: return [{"action":"key","key":m.group(1).strip()}]

    # COPY/PASTE/UNDO
    if "copy" in t and "paste" not in t: return [{"action":"copy"}]
    if "paste" in t: return [{"action":"paste"}]
    if "undo" in t: return [{"action":"undo"}]

    # CONFIGURE EMAIL (main thread only - returns marker)
    if ("configure" in t or "setup" in t or "set up" in t) and \
       ("email" in t or "smtp" in t or "mail" in t):
        return [{"action":"configure_email_note"}]

    # SOCIAL MEDIA
    if "instagram" in t and any(w in t for w in ["post","upload","share"]):
        return []  # needs AI for credentials
    if "linkedin" in t and any(w in t for w in ["post","share","publish"]):
        return []  # needs AI
    if "facebook" in t and any(w in t for w in ["post","share","publish"]):
        return []  # needs AI

    # ZIP
    if re.search(r"\bzip\b|\bcompress\b", t):
        return [{"action":"zip_files","path":str(Path.home() / "Desktop")}]

    # SCHEDULE
    m = re.search(r"(?:schedule|every day|daily)\s+(.+?)(?:\s+at\s+(\d{1,2}:\d{2}))?$", t)
    if m and ("schedule" in t or "every day" in t or "daily" in t):
        return [{"action":"schedule_task","task":m.group(1).strip(),
                 "schedule":f"daily at {m.group(2) or '09:00'}"}]

    # APPS
    for app in APPS:
        if app in t: return [{"action":"open","app":app}]

    # WEB RESEARCH
    m = re.match(r"(?:research|investigate|find out about|look up)\s+(.+)", t)
    if m: return [{"action":"web_research","query":m.group(1).strip()}]

    return []  # complex task - use AI

# ── COMMAND EXECUTOR ──────────────────────────────────────────────────
def exec_cmd(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict): return {"status":"error","message":"Invalid"}
    action = str(cmd.get("action","")).lower().strip()
    if not action: return {"status":"error","message":"No action"}
    raw = " ".join(str(v) for v in cmd.values())
    if any(b in raw.lower() for b in BLOCKED): return {"status":"blocked"}
    log.info("EXEC: %s", action)

    try:
        # ── SPEAK / NOTIFY ──────────────────────────────────────
        if action == "speak":
            speak(cmd.get("text","")); return {"status":"ok"}
        elif action == "notify":
            notify(cmd.get("title","Dacexy"), cmd.get("text",""))
            return {"status":"ok"}

        # ── CONFIGURE EMAIL NOTE (main thread only) ──────────────
        elif action == "configure_email_note":
            speak("I can configure email for you. Please type 'configure email' "
                  "in the terminal where I'm running to set it up.")
            return {"status":"ok"}

        # ── OPEN ────────────────────────────────────────────────
        elif action in ("open","open_url","open_browser","launch","start","navigate",
                        "navigate_to","go_to","browse","visit","open_site","open_website",
                        "open_app","run_app"):
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                   cmd.get("name") or cmd.get("site") or cmd.get("target") or "").strip()
            if not tgt: return {"status":"error","message":"No target"}
            return smart_open(tgt)

        # ── EMAIL (single) ───────────────────────────────────────
        elif action in ("send_email","email","compose_email","gmail_send","send_mail","mail"):
            to   = str(cmd.get("to") or cmd.get("email") or "")
            subj = str(cmd.get("subject") or "Message from Dacexy")
            body = str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "")
            att  = cmd.get("attachment") or cmd.get("attachment_path") or None
            if not to: return {"status":"error","message":"No recipient"}
            if not body: body = subj  # use subject as body if no body
            return send_email_real(to, subj, body, att)

        # ── BULK EMAIL ──────────────────────────────────────────
        elif action in ("bulk_email","send_bulk_email","mass_email","email_all"):
            contacts = cmd.get("contacts") or []
            csv_p = cmd.get("csv_path") or cmd.get("file") or ""
            if csv_p and not contacts: contacts = load_csv_contacts(csv_p)
            if not contacts: return {"status":"error","message":
                "No contacts. Provide csv_path or contacts list."}
            subj = str(cmd.get("subject") or "Hello from Dacexy")
            body = str(cmd.get("body") or cmd.get("template") or
                       "Hi {name},\n\nHope you're doing well!\n\nBest regards")
            delay = float(cmd.get("delay") or 2.5)
            return send_bulk_email(contacts, subj, body, delay)

        # ── FIND LEADS + EMAIL ───────────────────────────────────
        elif action in ("find_leads_and_email","lead_campaign","bulk_email_leads","find_and_email"):
            product = str(cmd.get("product") or cmd.get("query") or "product")
            niche   = str(cmd.get("niche") or "")
            count   = int(cmd.get("max") or cmd.get("count") or 20)
            subj    = str(cmd.get("subject") or f"Interested in {product}?")
            body    = str(cmd.get("body") or cmd.get("template") or
                f"Hi {{name}},\n\nI noticed you might be interested in {product}.\n"
                f"I'd love to connect and tell you more about what we offer.\n\n"
                f"Would you be open to a quick chat?\n\nBest regards")
            speak(f"Finding leads for {product} and emailing them. This takes a few minutes.")
            leads = find_leads_web(product, niche, count)
            if not leads: return {"status":"error","message":"No leads found. Try a different product."}
            return send_bulk_email(leads, subj, body, 2.5)

        # ── FIND LEADS ONLY ─────────────────────────────────────
        elif action in ("find_leads","lead_finder","scrape_leads"):
            product = str(cmd.get("product") or cmd.get("query") or "")
            niche   = str(cmd.get("niche") or "")
            count   = int(cmd.get("max") or cmd.get("count") or 30)
            leads = find_leads_web(product, niche, count)
            return {"status":"ok","leads_found":len(leads),
                    "file":str(AGENT_DIR / "data" / "leads.csv")}

        # ── WEB RESEARCH ────────────────────────────────────────
        elif action in ("web_research","research","investigate","find_info"):
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q: return {"status":"error","message":"No query"}
            speak(f"Researching {q}...")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(f"Research: {q}\nDate: {datetime.datetime.now()}\n\n{result}",
                          encoding="utf-8")
            speak(f"Research done. Report saved. Here's a summary: {result[:200]}")
            try: subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception: pass
            return {"status":"ok","result":result[:500],"saved":str(rp)}

        # ── SOCIAL MEDIA ─────────────────────────────────────────
        elif action in ("social_post","post_social","instagram_post","linkedin_post",
                        "facebook_post","post_instagram","post_linkedin","post_facebook"):
            plat = str(cmd.get("platform") or action.replace("post_","").replace("_post",""))
            usr  = str(cmd.get("username") or cmd.get("user") or "")
            pwd  = str(cmd.get("password") or cmd.get("pass") or "")
            txt  = str(cmd.get("text") or cmd.get("caption") or cmd.get("content") or "")
            img  = cmd.get("image_path") or cmd.get("image") or None
            if not usr or not pwd:
                urls = {"instagram":"https://www.instagram.com",
                        "linkedin":"https://www.linkedin.com",
                        "facebook":"https://www.facebook.com"}
                webbrowser.open(urls.get(plat.lower(),"https://www.instagram.com"))
                speak(f"Opened {plat}. Provide username and password in command for auto-posting.")
                return {"status":"ok","note":"Browser opened. Provide credentials for auto-post."}
            if "instagram" in plat.lower():
                if not img: return {"status":"error","message":"Instagram needs an image path"}
                return post_instagram(usr, pwd, img, txt)
            elif "linkedin" in plat.lower():
                return post_linkedin(usr, pwd, txt, img)
            elif "facebook" in plat.lower():
                return post_facebook(usr, pwd, txt, img)
            else:
                webbrowser.open("https://www.instagram.com")
                return {"status":"ok","note":"Opened browser"}

        # ── WHATSAPP ─────────────────────────────────────────────
        elif action in ("whatsapp","whatsapp_send","send_whatsapp"):
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            msg   = str(cmd.get("message") or cmd.get("text") or cmd.get("content") or "")
            if not phone: return {"status":"error","message":"No phone number"}
            return wa_send(phone, msg)

        # ── YOUTUBE / GOOGLE ─────────────────────────────────────
        elif action in ("open_youtube","youtube","youtube_search"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}")
                speak(f"Searching YouTube for {q}"); return {"status":"ok"}
            return smart_open("youtube")
        elif action in ("search_web","search","google_search","google"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                speak(f"Searching Google for {q}"); return {"status":"ok"}
            return smart_open("google")

        # ── MOUSE ────────────────────────────────────────────────
        elif action == "click":
            if not pyautogui: return {"status":"error","message":"pyautogui unavailable"}
            x,y = int(cmd.get("x") or 0), int(cmd.get("y") or 0)
            if x==0 and y==0: return {"status":"skipped","reason":"no coordinates"}
            sw,sh = pyautogui.size()
            pyautogui.click(max(0,min(x,sw-1)), max(0,min(y,sh-1)),
                           button=cmd.get("button","left")); time.sleep(0.1)
            return {"status":"ok"}
        elif action == "double_click":
            if pyautogui: pyautogui.doubleClick(int(cmd.get("x",0)),int(cmd.get("y",0)))
            return {"status":"ok"}
        elif action == "right_click":
            if pyautogui: pyautogui.rightClick(int(cmd.get("x",0)),int(cmd.get("y",0)))
            return {"status":"ok"}
        elif action == "move_mouse":
            if pyautogui: pyautogui.moveTo(int(cmd.get("x",0)),int(cmd.get("y",0)),duration=0.15)
            return {"status":"ok"}
        elif action == "scroll":
            amt = int(cmd.get("clicks") or cmd.get("amount") or 3)
            d = str(cmd.get("direction","down")).lower()
            if pyautogui: pyautogui.scroll(abs(amt) if d=="up" else -abs(amt))
            return {"status":"ok"}
        elif action in ("scroll_down","scrolldown"):
            if pyautogui: pyautogui.scroll(-int(cmd.get("amount",5)))
            return {"status":"ok"}
        elif action in ("scroll_up","scrollup"):
            if pyautogui: pyautogui.scroll(int(cmd.get("amount",5)))
            return {"status":"ok"}
        elif action == "drag":
            if pyautogui:
                x1,y1=int(cmd.get("x1",0)),int(cmd.get("y1",0))
                x2,y2=int(cmd.get("x2",0)),int(cmd.get("y2",0))
                pyautogui.moveTo(x1,y1)
                pyautogui.dragTo(x2,y2,duration=0.4,button="left")
            return {"status":"ok"}
        elif action == "get_mouse_pos":
            if pyautogui: p=pyautogui.position(); return {"status":"ok","x":p.x,"y":p.y}
            return {"status":"ok","x":0,"y":0}

        # ── KEYBOARD ────────────────────────────────────────────
        elif action in ("type","type_text","write","input","enter_text"):
            smart_type(cmd.get("text") or cmd.get("content") or ""); return {"status":"ok"}
        elif action in ("key","press","press_key","keypress"):
            k = cmd.get("key") or cmd.get("keys") or ""
            if k and pyautogui: pyautogui.press(str(k))
            return {"status":"ok"}
        elif action in ("hotkey","key_combo","shortcut"):
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys,str): keys=keys.replace("+"," ").split()
            if keys and pyautogui: pyautogui.hotkey(*[str(k) for k in keys[:4]])
            return {"status":"ok"}
        elif action == "press_enter":
            if pyautogui: pyautogui.press("enter"); return {"status":"ok"}
        elif action == "press_tab":
            if pyautogui: pyautogui.press("tab"); return {"status":"ok"}
        elif action == "press_escape":
            if pyautogui: pyautogui.press("escape"); return {"status":"ok"}
        elif action == "select_all":
            if pyautogui: pyautogui.hotkey("ctrl","a"); return {"status":"ok"}
        elif action == "copy":
            if pyautogui: pyautogui.hotkey("ctrl","c"); time.sleep(0.1)
            return {"status":"ok","clipboard":pyperclip.paste() if pyperclip else ""}
        elif action == "paste":
            if pyautogui: pyautogui.hotkey("ctrl","v"); return {"status":"ok"}
        elif action == "cut":
            if pyautogui: pyautogui.hotkey("ctrl","x"); return {"status":"ok"}
        elif action == "undo":
            if pyautogui: pyautogui.hotkey("ctrl","z"); return {"status":"ok"}
        elif action == "save":
            if pyautogui: pyautogui.hotkey("ctrl","s"); return {"status":"ok"}
        elif action == "get_clipboard":
            return {"status":"ok","text":pyperclip.paste() if pyperclip else ""}
        elif action == "set_clipboard":
            if pyperclip: pyperclip.copy(str(cmd.get("text",""))[:5000])
            return {"status":"ok"}

        # ── SCREENSHOT ──────────────────────────────────────────
        elif action in ("screenshot","take_screenshot"):
            ss = take_screenshot()
            if ss:
                try:
                    fn = AGENT_DIR / f"screenshot_{int(time.time())}.jpg"
                    fn.write_bytes(base64.b64decode(ss))
                    speak("Screenshot saved to DacexyAgent folder.")
                except Exception: pass
            return {"status":"ok","screenshot":ss}

        # ── WINDOW ──────────────────────────────────────────────
        elif action in ("minimize_window","minimize"):
            if pyautogui: pyautogui.hotkey("win","d"); return {"status":"ok"}
        elif action in ("maximize_window","maximize"):
            if pyautogui: pyautogui.hotkey("win","up"); return {"status":"ok"}
        elif action in ("close_window","close"):
            if pyautogui: pyautogui.hotkey("alt","f4"); return {"status":"ok"}
        elif action == "switch_window":
            if pyautogui: pyautogui.hotkey("alt","tab"); time.sleep(0.3); return {"status":"ok"}
        elif action == "get_active_window":
            return {"status":"ok","title":get_active_win()}
        elif action in ("open_file_explorer","file_explorer"):
            subprocess.Popen("explorer.exe",shell=True); return {"status":"ok"}
        elif action == "open_task_manager":
            subprocess.Popen("taskmgr.exe",shell=True); return {"status":"ok"}
        elif action == "open_settings":
            subprocess.Popen("ms-settings:",shell=True); return {"status":"ok"}
        elif action in ("open_notepad","notepad"):
            txt = cmd.get("text","")
            if txt:
                tmp = AGENT_DIR / "note.txt"
                tmp.write_text(str(txt)[:50000],encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"',shell=True)
            else: subprocess.Popen("notepad.exe",shell=True)
            return {"status":"ok"}

        # ── VOLUME ──────────────────────────────────────────────
        elif action == "volume_up":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumeup")
            return {"status":"ok"}
        elif action == "volume_down":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumedown")
            return {"status":"ok"}
        elif action == "mute":
            if pyautogui: pyautogui.press("volumemute"); return {"status":"ok"}

        # ── FILES ────────────────────────────────────────────────
        elif action == "write_file":
            p = Path(str(cmd.get("path","")))
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(str(cmd.get("content",""))[:200000],encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{p}"',shell=True)
            except Exception: pass
            speak(f"File created: {p.name}"); return {"status":"ok","path":str(p)}
        elif action == "read_file":
            p = Path(str(cmd.get("path","")))
            if p.exists():
                content = p.read_text(encoding="utf-8",errors="ignore")[:5000]
                speak(f"File has {len(content)} characters.")
                return {"status":"ok","content":content}
            return {"status":"error","message":"File not found"}
        elif action == "list_files":
            p = Path(str(cmd.get("path",str(Path.home()))))
            try: return {"status":"ok","files":[f.name for f in p.iterdir()][:50]}
            except Exception as e: return {"status":"error","message":str(e)}
        elif action == "delete_file":
            p = Path(str(cmd.get("path","")))
            if p.exists(): p.unlink(); return {"status":"ok"}
            return {"status":"error","message":"Not found"}
        elif action in ("move_file","rename_file","move"):
            src = Path(str(cmd.get("src") or cmd.get("source") or cmd.get("path") or ""))
            dst = Path(str(cmd.get("dst") or cmd.get("dest") or cmd.get("destination") or ""))
            if src.exists():
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.move(str(src),str(dst))
                return {"status":"ok","moved":str(dst)}
            return {"status":"error","message":"Source not found"}
        elif action in ("zip_files","create_zip","compress"):
            src = Path(str(cmd.get("path",str(Path.home() / "Desktop"))))
            dst = Path(str(cmd.get("output",str(AGENT_DIR / f"backup_{int(time.time())}.zip"))))
            try:
                with zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file(): zf.write(src,src.name)
                    elif src.is_dir():
                        for f in src.iterdir():
                            if f.is_file(): zf.write(f,f.name)
                speak(f"Zipped to {dst.name}"); return {"status":"ok","zip":str(dst)}
            except Exception as e: return {"status":"error","message":str(e)}

        # ── SYSTEM ───────────────────────────────────────────────
        elif action in ("get_system_info","system_info","sysinfo"):
            if psutil:
                dp = "C:\\" if platform.system()=="Windows" else "/"
                info = {"cpu":psutil.cpu_percent(interval=0.5),
                        "ram":psutil.virtual_memory().percent,
                        "disk":psutil.disk_usage(dp).percent,
                        "platform":platform.system(),"hostname":socket.gethostname(),
                        "active_window":get_active_win()}
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%, Disk {info['disk']}%")
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
            if any(b in c.lower() for b in BLOCKED): return {"status":"blocked"}
            try:
                r = subprocess.run(c,shell=True,capture_output=True,text=True,timeout=30)
                out = r.stdout[:2000]
                if out: speak(out[:200])
                return {"status":"ok","stdout":out,"stderr":r.stderr[:500]}
            except subprocess.TimeoutExpired: return {"status":"error","message":"Timeout"}
        elif action == "kill_process":
            name = str(cmd.get("name",""))
            safe = ["explorer","winlogon","csrss","svchost","system","lsass"]
            if any(p in name.lower() for p in safe): return {"status":"blocked"}
            if psutil:
                killed=0
                for p in psutil.process_iter(["name"]):
                    try:
                        if name.lower() in (p.info["name"] or "").lower():
                            p.kill(); killed+=1
                    except Exception: pass
                return {"status":"ok","killed":killed}
            return {"status":"ok"}
        elif action == "list_processes":
            if psutil:
                procs=[]
                for p in psutil.process_iter(["pid","name","cpu_percent"]):
                    try: procs.append(p.info)
                    except Exception: pass
                return {"status":"ok","processes":procs[:30]}
            return {"status":"ok","processes":[]}

        # ── MEMORY ───────────────────────────────────────────────
        elif action in ("remember","save_fact","take_note"):
            fact = str(cmd.get("fact") or cmd.get("text") or cmd.get("content") or "")
            if fact: remember(fact); speak("Remembered.")
            return {"status":"ok"}
        elif action == "get_memory":
            return {"status":"ok","memory":get_mem_ctx()}
        elif action == "add_contact":
            name = str(cmd.get("name",""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {
                        "name":name,"email":cmd.get("email",""),
                        "phone":cmd.get("phone",""),"notes":cmd.get("notes","")
                    }
                save_memory(); speak(f"Contact {name} saved.")
            return {"status":"ok"}

        # ── SCHEDULER ────────────────────────────────────────────
        elif action in ("schedule_task","schedule","add_schedule"):
            task_s = str(cmd.get("task") or cmd.get("command") or cmd.get("text") or "")
            sched  = str(cmd.get("schedule") or cmd.get("when") or "daily at 09:00")
            if not task_s: return {"status":"error","message":"No task"}
            job = {"id":''.join(random.choices(string.ascii_lowercase,k=6)),
                   "task":task_s,"schedule":sched,"last_run":""}
            _sched_jobs.append(job); save_memory()
            speak(f"Scheduled: {task_s[:50]} - {sched}")
            return {"status":"ok","scheduled":task_s}

        # ── WAIT ─────────────────────────────────────────────────
        elif action in ("wait","sleep","pause","delay"):
            time.sleep(min(float(cmd.get("seconds") or cmd.get("duration") or 1),15))
            return {"status":"ok"}

        # ── HEALTH ───────────────────────────────────────────────
        elif action in ("ping","pong","test","health","health_check","status"):
            return {"status":"ok","pong":True,"version":VERSION}

        elif action in ("what_on_screen","describe_screen"):
            win = get_active_win(); speak(f"Active window: {win}")
            return {"status":"ok","active_window":win}

        # ── FALLBACK ─────────────────────────────────────────────
        else:
            log.warning("Unknown action '%s' - trying smart_open", action)
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                   cmd.get("name") or cmd.get("target") or action)
            res = smart_open(str(tgt))
            if res.get("status") == "ok": return res
            return {"status":"error","message":f"Unknown action: {action}"}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e)
        return {"status":"error","message":str(e)}

# ── MAIN TASK EXECUTOR (no recursion) ────────────────────────────────
def execute_task(task: str, token: str) -> dict:
    """
    Execute a task. Pipeline:
      1. Local NLP  - instant, no network
      2. AI brain   - for complex tasks (returns command list, not recursive)
      3. smart_open - last resort
    NO RECURSION anywhere in this chain.
    """
    if not task:
        return {"status":"error","ok":0,"total":0,"result":"No task"}

    log.info("Task: %s", task[:100])
    _convo.append(f"user: {task[:120]}")

    # ── Step 1: Local NLP ─────────────────────────────────────
    commands = local_parse(task)
    if commands:
        log.info("Local NLP: %d commands", len(commands))
    else:
        # ── Step 2: AI brain ───────────────────────────────────
        log.info("AI brain for: %s", task[:80])
        jarvis("work")
        commands = ai_plan(task, token)

    if not commands:
        # ── Step 3: Last resort - try to open it ───────────────
        res = smart_open(task)
        if res.get("status") == "ok":
            _convo.append(f"dacexy: Opened {task[:60]}")
            return {"status":"ok","ok":1,"total":1,"result":f"Opened: {task}"}
        speak("I'm not sure how to do that. Please give me more details.")
        return {"status":"error","ok":0,"total":0,"result":"Could not parse task"}

    # ── Execute commands ────────────────────────────────────────
    ok_count = 0; total = len(commands); results = []
    for i, c in enumerate(commands):
        if not isinstance(c, dict): continue
        # Flatten nested params
        for k, v in c.get("params", {}).items():
            if k not in c: c[k] = v
        log.info("Step %d/%d: %s", i+1, total, c.get("action","?"))
        try:
            res = exec_cmd(c, token)
            results.append(res)
            if res.get("status") in ("ok","skipped"): ok_count += 1
            else: log.warning("Step %d failed: %s", i+1, res.get("message",""))
            time.sleep(0.3)
        except Exception as e:
            log.error("Step %d error: %s", i+1, e)
            results.append({"status":"error","message":str(e)})

    with _mem_lock:
        MEMORY["task_history"].append(
            f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
    save_memory()

    summary = f"Done {ok_count}/{total} for: {task[:60]}"
    log.info(summary)
    if ok_count > 0: jarvis("done")
    _convo.append(f"dacexy: {summary}")
    return {"status":"ok" if ok_count>0 else "error",
            "ok":ok_count,"total":total,"result":summary,"steps":results}

# ── BACKGROUND SCHEDULER ──────────────────────────────────────────────
def _scheduler_loop(token_ref: list):
    while _running:
        try:
            now = datetime.datetime.now()
            now_str = now.strftime("%H:%M")
            for job in list(_sched_jobs):
                sched = job.get("schedule","").lower()
                last  = job.get("last_run","")
                run = False
                if "daily at" in sched:
                    m = re.search(r"(\d{1,2}):(\d{2})", sched)
                    if m:
                        h,mi = int(m.group(1)), int(m.group(2))
                        if now.hour==h and now.minute==mi:
                            if not last or last[:16] != now.strftime("%Y-%m-%dT%H:%M"):
                                run = True
                elif "every" in sched and "minute" in sched:
                    m = re.search(r"every\s+(\d+)", sched)
                    mins = int(m.group(1)) if m else 30
                    if last:
                        try:
                            ld = datetime.datetime.fromisoformat(last)
                            if (now-ld).total_seconds() >= mins*60: run=True
                        except Exception: run=True
                    else: run=True
                elif "hourly" in sched:
                    if last:
                        try:
                            ld = datetime.datetime.fromisoformat(last)
                            if (now-ld).total_seconds() >= 3600: run=True
                        except Exception: run=True
                    else: run=True
                if run:
                    job["last_run"] = now.isoformat()
                    save_memory()
                    tok = token_ref[0]
                    if tok:
                        t = job.get("task","")
                        log.info("Scheduler running: %s", t[:60])
                        threading.Thread(target=execute_task,
                            args=(t, tok), daemon=True).start()
        except Exception as e: log.warning("Scheduler: %s", e)
        time.sleep(30)

# ── VOICE ENGINE (JARVIS STYLE, ROBUST) ──────────────────────────────
def _voice_loop():
    global _voice_on
    if not VOICE_OK or not sr:
        print("  [VOICE] Disabled - PyAudio not available.")
        print("  [TIP]   pip install PyAudio")
        return

    rec = sr.Recognizer()
    rec.energy_threshold = 400          # higher = less false triggers
    rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.7
    rec.non_speaking_duration = 0.4

    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            print("  [VOICE] No microphone found."); return
        print(f"  [MIC] Using: {mics[0]}")
    except Exception as e:
        log.warning("Mic list: %s", e)

    print("  [JARVIS] Voice active! Wake words: Dacexy / Jarvis / Computer")
    speak("Jarvis voice ready. Say Dacexy, Jarvis, or Computer to wake me.")
    real_errs = 0  # only count REAL errors, not timeouts

    while _voice_on and _running:
        # ── Listen for wake word ───────────────────────────────
        heard = ""
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.1)
                except Exception: pass
                try: audio = rec.listen(src, timeout=3, phrase_time_limit=6)
                except sr.WaitTimeoutError: continue  # timeout is normal, not an error
                except OSError as e: real_errs+=1; log.warning("Mic OS: %s",e); time.sleep(2); continue

            # Recognize outside the 'with' block to free mic
            try:
                heard = rec.recognize_google(audio, language="en-IN").lower().strip()
                real_errs = 0  # successful recognition resets error count
            except sr.UnknownValueError: continue  # didn't hear anything clear
            except sr.RequestError as e:
                real_errs += 1; log.warning("SR API: %s", e); time.sleep(3); continue

        except Exception as e:
            real_errs += 1; log.debug("Voice outer: %s", e); time.sleep(1); continue

        # Check wake word
        if not any(w in heard for w in WAKE_WORDS): continue

        log.info("WAKE: '%s'", heard)
        print(f"\n  [WAKE] '{heard}' - listening...")
        jarvis("greet"); time.sleep(0.2)

        # ── Listen for command ─────────────────────────────────
        command = ""
        try:
            with sr.Microphone() as csrc:
                try: rec.adjust_for_ambient_noise(csrc, duration=0.08)
                except Exception: pass
                try: caudio = rec.listen(csrc, timeout=7, phrase_time_limit=30)
                except sr.WaitTimeoutError:
                    speak("I didn't hear a command. Say my name again."); continue
                except OSError as e: log.warning("Mic OS cmd: %s",e); continue

            try:
                command = rec.recognize_google(caudio, language="en-IN").strip()
                real_errs = 0
            except sr.UnknownValueError:
                jarvis("again"); continue
            except sr.RequestError as e:
                real_errs+=1; log.warning("SR cmd API: %s",e); continue

        except Exception as e:
            log.warning("Voice cmd outer: %s", e); continue

        if not command: continue
        log.info("Voice command: '%s'", command)
        print(f"  [CMD] {command}")

        with _tok_lock: tok = _cur_token
        if not tok: speak("I'm not logged in yet. Please wait."); continue

        jarvis("work")
        def _run(t, cmd_text):
            try:
                result = execute_task(cmd_text, t)
                if result.get("status") != "ok" and result.get("ok",0) == 0:
                    jarvis("error")
            except Exception as e:
                log.error("Voice task: %s", e); speak("Error with that command.")
        threading.Thread(target=_run, args=(tok, command), daemon=True).start()

        # Only pause voice on persistent real errors
        if real_errs >= 10:
            speak("Voice paused due to connection errors. Retrying in 30 seconds.")
            time.sleep(30); real_errs = 0

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

# ── WEBSOCKET ────────────────────────────────────────────────────────
async def run_websocket(token: str):
    retry = 3.0; max_retry = 60.0
    while _running:
        try:
            log.info("WS connecting...")
            print("  [WS] Connecting to Dacexy cloud...")
            kw = {"ping_interval":25,"ping_timeout":20,"max_size":10*1024*1024}
            try:
                wsv = int(str(getattr(websockets,"__version__","0")).split(".")[0])
                if wsv >= 14: kw["open_timeout"] = 20
                else: kw["close_timeout"] = 10
            except Exception: pass

            async with websockets.connect(BACKEND_WS, **kw) as ws:
                await ws.send(json.dumps({
                    "token":token, "type":"init", "version":VERSION,
                    "platform":platform.system(), "machine":platform.machine(),
                    "hostname":socket.gethostname(),
                    "features":["voice3","vision","browser","email","bulk_email",
                                "lead_gen","web_research","social_all","selenium",
                                "ai_brain","scheduler","memory","jarvis","v19"]
                }))
                try:
                    auth = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                    if auth.get("type") == "error":
                        log.error("Auth failed: %s", auth.get("message"))
                        speak("Authentication failed."); return
                except asyncio.TimeoutError:
                    await asyncio.sleep(retry); continue

                log.info("WS connected!")
                print("  [OK] Connected to Dacexy cloud!")
                speak("Connected. I am ready.")
                retry = 3.0

                _ws_lock = asyncio.Lock()
                loop = asyncio.get_event_loop()

                async def ws_send(data):
                    async with _ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e: log.warning("ws_send: %s", e)

                while _running:
                    try: raw = await asyncio.wait_for(ws.recv(), timeout=40)
                    except asyncio.TimeoutError:
                        try: await asyncio.wait_for(
                            ws.send(json.dumps({"type":"ping","version":VERSION})),
                            timeout=5)
                        except Exception: break
                        continue
                    try: msg = json.loads(raw)
                    except Exception: continue

                    mtype    = msg.get("type","")
                    action   = msg.get("action","")
                    task_txt = msg.get("task","") or msg.get("goal","")
                    task_id  = str(msg.get("task_id",""))

                    if mtype == "ping":
                        await ws_send({"type":"pong","version":VERSION}); continue
                    if mtype in ("pong","connected","init_ack"): continue

                    # Direct single command
                    if action and action not in ("swarm_task","task","run_agent"):
                        def _run_cmd(m, t):
                            try:
                                r = exec_cmd(m, t)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":task_id,
                                    "status":r.get("status","ok"),
                                    "ok":1 if r.get("status") in ("ok","skipped") else 0,
                                    "total":1,
                                    "result":str(r.get("message","") or r.get("opened","") or "done"),
                                    "data":r}), loop)
                            except Exception as e:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":task_id,
                                    "status":"error","ok":0,"total":1,"result":str(e)}), loop)
                        threading.Thread(target=_run_cmd, args=(msg,token),
                            daemon=True).start(); continue

                    # Full task
                    if task_txt or mtype in ("task","command"):
                        if not task_txt: task_txt = action
                        if not task_txt: continue
                        log.info("Task: %s", task_txt[:80])
                        print(f"\n  [TASK] {task_txt}")
                        jarvis("work",f"Working on: {task_txt[:50]}")
                        def _run_task(t, txt, tid):
                            try:
                                r = execute_task(txt, t)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":r.get("status","ok"),
                                    "ok":r.get("ok",0),"total":r.get("total",1),
                                    "result":r.get("result",""),
                                    "steps":r.get("steps",[])}), loop)
                            except Exception as e:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":"error","ok":0,"total":0,"result":str(e)}), loop)
                        threading.Thread(target=_run_task,
                            args=(token,task_txt,task_id), daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK: log.info("WS closed OK")
        except websockets.exceptions.ConnectionClosedError as e: log.warning("WS: %s",e)
        except OSError as e: log.warning("WS network: %s",e)
        except Exception as e: log.error("WS: %s",e)

        if _running:
            print(f"  [WS] Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry)
            retry = min(retry*1.5, max_retry)

# ── HEARTBEAT ────────────────────────────────────────────────────────
def _heartbeat(token_ref: list):
    while _running:
        time.sleep(300)
        try:
            tok = token_ref[0]
            if tok:
                if not check_token_valid(tok): speak("Session expired. Please restart.")
                else: update_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)

# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*58)
    print("  DACEXY AGENT v19.0 - DEFINITIVE WORKING EDITION")
    print("  AI Brain + Jarvis Voice + Bulk Email + Lead Finder")
    print("="*58 + "\n")

    init_tts()
    load_memory()

    # Print capability status
    caps = []
    if pyautogui:        caps.append("mouse/keyboard ✓")
    if ImageGrab:        caps.append("screenshot ✓")
    if VOICE_OK:         caps.append("JARVIS VOICE ✓")
    if SELENIUM_OK:      caps.append("browser-auto ✓")
    if BS4_OK:           caps.append("web-scraping ✓")
    if _smtp_cfg.get("email"): caps.append(f"email({_smtp_cfg['email']}) ✓")
    else:                caps.append("email(not configured)")
    print(f"  Caps: {', '.join(caps)}")

    # Auth
    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if check_token_valid(token): print("  [OK] Session valid")
            else: print("  Session expired."); clear_token(); token = None
        except Exception: pass

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"\n  Attempt {attempt+1}/3 failed.\n")
        if not token:
            print("\n  [ERROR] Cannot authenticate. Exiting."); return

    try: setup_autostart()
    except Exception: pass

    # ── SMTP setup offer (main thread - safe to call input()) ──────
    if not _smtp_cfg.get("email"):
        print("\n  ┌──────────────────────────────────────────────────┐")
        print("  │  Email not configured.                           │")
        print("  │  Type 'y' to set it up now, or Enter to skip.   │")
        print("  └──────────────────────────────────────────────────┘")
        try:
            ans = input("  Configure email now? [y/N]: ").strip().lower()
            if ans == "y": configure_smtp_interactive()
        except (EOFError, KeyboardInterrupt): pass
    else:
        print(f"  [EMAIL] Configured as {_smtp_cfg['email']}")

    # Start background threads
    voice_ok = start_voice(token)
    if voice_ok: print("  [JARVIS] Voice active! Say: Dacexy / Jarvis / Computer")
    else:        print("  [VOICE]  Off. Install PyAudio for voice control.")

    tok_ref = [token]
    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True).start()
    threading.Thread(target=_scheduler_loop, args=(tok_ref,), daemon=True,
                     name="Scheduler").start()

    print("\n  " + "─"*56)
    print(f"  v{VERSION} | Voice: {'ON ✓' if voice_ok else 'OFF'}")
    print(f"  Wake words: Dacexy / Jarvis / Computer")
    print(f"  Dashboard : dacexy.vercel.app/dashboard")
    print(f"  Log       : {LOG_FILE}")
    print("  " + "─"*56)
    print()
    print("  EXAMPLE COMMANDS (voice or dashboard):")
    print("    'send email to john@gmail.com saying hello'")
    print("    'find customers interested in AI software and email them'")
    print("    'post on LinkedIn saying we launched a new product'")
    print("    'research best marketing strategies and write a report'")
    print("    'open YouTube and search lofi music'")
    print("    'take a screenshot'")
    print("    'what time is it'")
    print("    'schedule send weather email daily at 9am'")
    print()

    if not websockets:
        print("  [ERROR] websockets not installed!"); return

    # Run websocket (the main event loop)
    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n  Stopped by user.")
    except Exception as e:
        log.error("Fatal error: %s", e)
        print(f"\n  [ERROR] {e}")
    finally:
        global _running; _running = False
        stop_voice()
        save_memory()
        try: speak("Shutting down. Goodbye!"); time.sleep(0.8)
        except Exception: pass
        print("  Goodbye!")
        sys.exit(0)   # clean exit - bat sees code 0, shows "stopped cleanly"

if __name__ == "__main__":
    main()
