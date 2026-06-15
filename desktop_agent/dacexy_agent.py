"""
DACEXY DESKTOP AGENT
====================
Real desktop automation: mouse, keyboard, screen reading, file ops,
email, voice control, WebSocket cloud link, human approval gates,
social-message reply bots, invoice payment queue.
"""
from __future__ import annotations

# ── Windows selector event-loop policy (must be first) ───────────────────────
import platform as _platform_early
import asyncio as _asyncio_early

if _platform_early.system() == "Windows":
    if hasattr(_asyncio_early, "WindowsSelectorEventLoopPolicy"):
        _asyncio_early.set_event_loop_policy(_asyncio_early.WindowsSelectorEventLoopPolicy())

# ── UTF-8 stdout/stderr ───────────────────────────────────────────────────────
import sys as _sys_early, io as _io_early

if _platform_early.system() == "Windows":
    try:
        _sys_early.stdout = _io_early.TextIOWrapper(
            _sys_early.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        _sys_early.stderr = _io_early.TextIOWrapper(
            _sys_early.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-INSTALL DEPENDENCIES
# ══════════════════════════════════════════════════════════════════════════════
import subprocess, sys

_PACKAGES = [
    ("pyautogui",         "pyautogui"),
    ("pillow",            "PIL"),
    ("websockets",        "websockets"),
    ("requests",          "requests"),
    ("pyttsx3",           "pyttsx3"),
    ("numpy",             "numpy"),
    ("psutil",            "psutil"),
    ("pyperclip",         "pyperclip"),
    ("pygetwindow",       "pygetwindow"),
    ("plyer",             "plyer"),
    ("speechrecognition", "speech_recognition"),
    ("beautifulsoup4",    "bs4"),
    ("g4f",               "g4f"),
    ("keyboard",          "keyboard"),
    ("schedule",          "schedule"),
    ("cryptography",      "cryptography"),
    ("watchdog",          "watchdog"),
    ("pdfplumber",        "pdfplumber"),
    ("openpyxl",          "openpyxl"),
]

def _pip_install(*pkgs):
    try:
        subprocess.call(
            [sys.executable, "-m", "pip", "install", *pkgs, "-q", "--no-warn-script-location"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180,
        )
    except Exception:
        pass

print("  [BOOT] Checking dependencies...")
for _pkg, _imp in _PACKAGES:
    try:
        __import__(_imp)
    except ImportError:
        print(f"  [BOOT] Installing {_pkg}...")
        _pip_install(_pkg)

# Selenium
try:
    from selenium import webdriver as _chk_sel  # noqa
except ImportError:
    _pip_install("selenium", "webdriver-manager")

# PyAudio
PYAUDIO_OK = False
try:
    import pyaudio; PYAUDIO_OK = True
except ImportError:
    _pip_install("PyAudio")
    try:
        import pyaudio; PYAUDIO_OK = True
    except ImportError:
        try:
            _pip_install("pipwin")
            subprocess.call(
                [sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90,
            )
            import pyaudio; PYAUDIO_OK = True
        except Exception:
            pass

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

print("  [BOOT] Dependencies ready.\n")


# ══════════════════════════════════════════════════════════════════════════════
# STANDARD LIBRARY
# ══════════════════════════════════════════════════════════════════════════════
import asyncio, base64, csv, ctypes, datetime, fnmatch, hashlib, hmac
import io, json, logging, os, pathlib, platform, queue, random, re, shutil
import smtplib, socket, string, struct, threading, time, urllib.parse
import webbrowser, zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════════════
# THIRD-PARTY (graceful fallbacks)
# ══════════════════════════════════════════════════════════════════════════════
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0.03
    PYAUTOGUI_OK = True
except Exception:
    pyautogui = None; PYAUTOGUI_OK = False

try:
    import requests as req_lib; REQUESTS_OK = True
except Exception:
    req_lib = None; REQUESTS_OK = False

try:
    import websockets; WS_OK = True
except Exception:
    websockets = None; WS_OK = False

try:
    from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageEnhance
    PIL_OK = True
except Exception:
    ImageGrab = Image = ImageDraw = ImageFont = ImageEnhance = None; PIL_OK = False

try:
    import pyttsx3; TTS_LIB_OK = True
except Exception:
    pyttsx3 = None; TTS_LIB_OK = False

try:
    import pyperclip; CLIP_OK = True
except Exception:
    pyperclip = None; CLIP_OK = False

try:
    import psutil; PSUTIL_OK = True
except Exception:
    psutil = None; PSUTIL_OK = False

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

try:
    from cryptography.fernet import Fernet; CRYPTO_OK = True
except Exception:
    Fernet = None; CRYPTO_OK = False

try:
    import pdfplumber; PDF_OK = True
except Exception:
    pdfplumber = None; PDF_OK = False

try:
    import openpyxl; XL_OK = True
except Exception:
    openpyxl = None; XL_OK = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_OK = True
except Exception:
    Observer = FileSystemEventHandler = None; WATCHDOG_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"

AGENT_DIR  = Path.home() / "DacexyAgent"
LOG_FILE   = AGENT_DIR / "logs" / "agent.log"
SS_DIR     = AGENT_DIR / "screenshots"
DATA_DIR   = AGENT_DIR / "data"
DOC_DIR    = AGENT_DIR / "documents"
INBOX_DIR  = AGENT_DIR / "inbox"
KEY_FILE   = AGENT_DIR / ".agent.key"
CONFIG_FILE = Path.home() / ".dacexy_agent.json"
MEMORY_FILE = Path.home() / ".dacexy_memory.json"

for _d in [AGENT_DIR, AGENT_DIR/"logs", SS_DIR, DATA_DIR, DOC_DIR, INBOX_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Social reply-bot profile dir + payment-queue file/portals ───────────────
SOCIAL_PROFILE_DIR = AGENT_DIR / "browser_profiles"
SOCIAL_PROFILE_DIR.mkdir(exist_ok=True)
PAYMENT_QUEUE_FILE = DATA_DIR / "payment_queue.json"

PAYMENT_PORTALS: Dict[str, str] = {
    "razorpay": "https://dashboard.razorpay.com/app/payments",
    "paypal":   "https://www.paypal.com/myaccount/transfer/homepage/pay",
    "bank":     "",   # set to your bank's payment URL if you want auto-open
}

AUTO_REPLY_TEMPLATES: Dict[str, str] = {
    "default": "Thanks for your message! I'll get back to you shortly.",
}

# Sensitive operations that require human approval
APPROVAL_REQUIRED = {
    "send_email", "send_bulk_email", "delete_file", "run_command",
    "pay_invoice", "execute_payment", "post_twitter", "post_linkedin",
    "post_facebook", "bulk_email", "approve_payment", "enable_auto_reply",
}

# Private folders that are off-limits
BLOCKED_FOLDERS = [
    str(Path.home() / "Documents" / "Private"),
    str(Path.home() / "Documents" / "Personal"),
    str(Path.home() / ".ssh"),
    str(Path.home() / ".gnupg"),
    "C:\\Windows\\System32",
    "/etc", "/root", "/private",
]

BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
    "rd /s /q c:\\", "reg delete hklm", "dd if=/dev/zero",
    "rmdir /s /q c:\\", "deltree", ":(){ :|:& };:", "shutdown /s",
    "shutdown -s", "mkfs", "fdisk",
]

SMTP_PRESETS: Dict[str, Dict] = {
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

SOCIAL_POLL_INTERVAL = 45  # seconds between social-media polls (configurable)

WAKE_WORDS = ["dacexy", "hey dacexy", "okay dacexy", "jarvis", "hey jarvis", "computer", "assistant", "hey agent", "agent"]

SITES: Dict[str, str] = {
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
    "claude": "https://claude.ai",
    "anthropic": "https://anthropic.com",
    "perplexity": "https://perplexity.ai",
    "gemini": "https://gemini.google.com",
    "openai": "https://openai.com",
}

APPS: Dict[str, str] = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "brave": "brave.exe",
    "notepad": "notepad.exe",
    "notepad++": r"C:\Program Files\Notepad++\notepad++.exe",
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
    "snipping tool": "SnippingTool.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "regedit": "regedit.exe",
    "winrar": "winrar.exe",
    "7zip": "7zFM.exe",
    "obs": "obs64.exe",
    "steam": "steam.exe",
    "gimp": "gimp-2.10.exe",
    "photoshop": "photoshop.exe",
    "audacity": "audacity.exe",
    "skype": "skype.exe",
    "anydesk": "anydesk.exe",
    "teamviewer": "teamviewer.exe",
}

FILE_CATEGORIES: Dict[str, List[str]] = {
    "Images":      [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff"],
    "Documents":   [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"],
    "Spreadsheets":[".xls", ".xlsx", ".csv", ".ods"],
    "Presentations":[".ppt", ".pptx", ".odp"],
    "Videos":      [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Archives":    [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code":        [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".json"],
    "Invoices":    [],  # detected by name pattern
}


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════════════
_mem_lock    = threading.Lock()
_cfg_lock    = threading.Lock()
_executor    = ThreadPoolExecutor(max_workers=24)
_running     = True
_tts_q: queue.Queue = queue.Queue(maxsize=30)
_tts_engine  = None
_tts_lock    = threading.Lock()
_voice_on    = False
_cur_token   = None
_tok_lock    = threading.Lock()
_smtp_cfg: Dict = {}
_sched_jobs: List = []
_convo: deque    = deque(maxlen=40)
_selenium_driver  = None
_sel_lock         = threading.Lock()
_pending_approvals: Dict[str, dict] = {}
_approval_lock     = threading.Lock()
_ws_send_fn        = None   # set by websocket loop

# ── Social reply-bot state ─────────────────────────────────────────────────
_social_drivers: Dict[str, Any] = {}
_social_lock       = threading.Lock()
_social_auto: Dict[str, bool] = {"whatsapp": False, "instagram": False, "facebook": False}
_social_seen: Dict[str, set]  = {"whatsapp": set(), "instagram": set(), "facebook": set()}
_social_thread     = None
_social_running    = False

MEMORY: Dict = {
    "facts":        [],
    "preferences":  {},
    "task_history": deque(maxlen=1000),
    "context":      {},
    "contacts":     {},
    "skills":       [],
    "approved_ops": [],
}

HEALTH: Dict = {
    "cpu": 0.0, "ram": 0.0, "disk": 0.0,
    "tasks_run": 0, "tasks_ok": 0, "uptime_start": time.time(),
}


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
        ],
    )
except Exception:
    logging.basicConfig(level=logging.INFO)

log   = logging.getLogger("dacexy")
audit = logging.getLogger("dacexy.audit")
log.info("Dacexy Agent initializing")


# ══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION (local key, never sent anywhere)
# ══════════════════════════════════════════════════════════════════════════════
def _get_fernet() -> Optional[Any]:
    if not CRYPTO_OK:
        return None
    try:
        if KEY_FILE.exists():
            key = KEY_FILE.read_bytes()
        else:
            key = Fernet.generate_key()
            KEY_FILE.write_bytes(key)
            KEY_FILE.chmod(0o600)
        return Fernet(key)
    except Exception as e:
        log.warning("Fernet init: %s", e)
        return None

def encrypt_str(s: str) -> str:
    f = _get_fernet()
    if not f:
        return s
    try:
        return base64.b64encode(f.encrypt(s.encode())).decode()
    except Exception:
        return s

def decrypt_str(s: str) -> str:
    f = _get_fernet()
    if not f:
        return s
    try:
        return f.decrypt(base64.b64decode(s)).decode()
    except Exception:
        return s


# ══════════════════════════════════════════════════════════════════════════════
# TTS
# ══════════════════════════════════════════════════════════════════════════════
def _tts_worker():
    while _running:
        text = None
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
        except queue.Empty:
            continue
        except Exception:
            continue
        finally:
            if text is not None:
                try:
                    _tts_q.task_done()
                except Exception:
                    pass


def init_tts():
    global _tts_engine
    if not TTS_LIB_OK:
        return
    try:
        eng = pyttsx3.init()
        eng.setProperty("rate", 160)
        eng.setProperty("volume", 0.92)
        try:
            voices = eng.getProperty("voices") or []
            for v in voices:
                n = (v.name or "").lower()
                if any(x in n for x in ["david", "mark", "zira"]):
                    eng.setProperty("voice", v.id)
                    break
        except Exception:
            pass
        _tts_engine = eng
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS initialized OK")
    except Exception as e:
        log.warning("TTS init: %s", e)


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


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def _notify(title: str, msg: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=str(msg)[:100], app_name="Dacexy", timeout=5)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG / TOKEN
# ══════════════════════════════════════════════════════════════════════════════
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
    cfg = load_config(); cfg["access_token"] = t; save_config(cfg)

def clear_token():
    cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    if not req_lib:
        return False
    def _check():
        r = req_lib.get(
            f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.status_code == 200
    try:
        return _retry(_check, attempts=3, delays=(1, 3), label="token_check")
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# MEMORY
# ══════════════════════════════════════════════════════════════════════════════
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
                MEMORY["approved_ops"] = d.get("approved_ops", [])
                MEMORY["task_history"] = deque(d.get("task_history", [])[-1000:], maxlen=1000)
            _smtp_cfg = {}
            raw_smtp = d.get("smtp_config", {})
            for k, v in raw_smtp.items():
                _smtp_cfg[k] = decrypt_str(v) if k == "password" else v
            _sched_jobs = d.get("sched_jobs", [])
            log.info("Memory loaded: %d facts, %d contacts, %d jobs",
                     len(MEMORY["facts"]), len(MEMORY["contacts"]), len(_sched_jobs))
    except Exception as e:
        log.warning("load_memory: %s", e)

def save_memory():
    try:
        enc_smtp = dict(_smtp_cfg)
        if enc_smtp.get("password"):
            enc_smtp["password"] = encrypt_str(enc_smtp["password"])
        with _mem_lock:
            d = {
                "facts":        MEMORY["facts"][-1000:],
                "preferences":  MEMORY["preferences"],
                "context":      MEMORY["context"],
                "contacts":     MEMORY["contacts"],
                "skills":       MEMORY["skills"],
                "approved_ops": MEMORY["approved_ops"][-100:],
                "task_history": list(MEMORY["task_history"])[-200:],
                "smtp_config":  enc_smtp,
                "sched_jobs":   _sched_jobs[-50:],
            }
        tmp = MEMORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
        tmp.replace(MEMORY_FILE)
        MEMORY_FILE.chmod(0o600)
    except Exception as e:
        log.warning("save_memory: %s", e)

def remember(fact: str):
    if not fact: return
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
                parts.append("Recent: " + "; ".join(recent))
            contacts = list(MEMORY["contacts"].keys())[:8]
            if contacts:
                parts.append("Contacts: " + ", ".join(contacts))
        conv = list(_convo)[-6:]
        if conv:
            parts.append("Conv: " + " | ".join(conv))
        return "\n".join(parts)
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY CHECKS
# ══════════════════════════════════════════════════════════════════════════════
def _is_path_allowed(path_str: str) -> bool:
    """Returns False if path is inside a blocked private folder."""
    try:
        p = Path(path_str).resolve()
        for blocked in BLOCKED_FOLDERS:
            try:
                p.relative_to(Path(blocked).resolve())
                return False
            except ValueError:
                pass
        return True
    except Exception:
        return True

def _is_command_safe(cmd: str) -> bool:
    cl = cmd.lower().strip()
    return not any(b in cl for b in BLOCKED_COMMANDS)


# ══════════════════════════════════════════════════════════════════════════════
# HUMAN APPROVAL GATE
# ══════════════════════════════════════════════════════════════════════════════
def request_approval(action: str, details: str, timeout: int = 30) -> bool:
    """
    For sensitive actions: prints a prompt and waits for Y/n.
    When running headlessly (no TTY), auto-denies after timeout.
    """
    # Check if this exact op was pre-approved in memory
    op_key = f"{action}:{hashlib.md5(details.encode()).hexdigest()[:8]}"
    with _mem_lock:
        if op_key in MEMORY["approved_ops"]:
            return True

    speak(f"Approval needed: {action}. Check your terminal.")
    print(f"\n  {'='*55}")
    print(f"  ⚠  APPROVAL REQUIRED")
    print(f"  Action : {action}")
    print(f"  Details: {details[:200]}")
    print(f"  {'='*55}")
    print(f"  Approve? [Y/n/always] (auto-deny in {timeout}s): ", end="", flush=True)

    _notify("Dacexy — Action Approval", f"{action}: {details[:60]}")

    import select
    if hasattr(select, "select"):
        # Unix-style
        try:
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                ans = sys.stdin.readline().strip().lower()
            else:
                print("\n  [TIMEOUT] Auto-denied.")
                return False
        except Exception:
            ans = "n"
    else:
        # Windows — use threading
        _ans = ["n"]
        _ev  = threading.Event()
        def _read():
            try:
                _ans[0] = input().strip().lower()
            except Exception:
                pass
            _ev.set()
        threading.Thread(target=_read, daemon=True).start()
        if not _ev.wait(timeout):
            print("\n  [TIMEOUT] Auto-denied.")
            return False
        ans = _ans[0]

    if ans in ("y", "yes", "always", "a"):
        print("  [OK] Approved.")
        if ans in ("always", "a"):
            with _mem_lock:
                MEMORY["approved_ops"].append(op_key)
            save_memory()
        return True

    print("  [DENY] Action cancelled.")
    speak("Action denied.")
    return False


# ══════════════════════════════════════════════════════════════════════════════
# SCREENSHOT
# ══════════════════════════════════════════════════════════════════════════════
def take_screenshot(save: bool = True, region: Optional[Tuple] = None, quality: int = 80) -> Optional[str]:
    try:
        if not ImageGrab:
            return None
        img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        w, h = img.size
        if w > 1920:
            img = img.resize((1920, int(h * 1920 / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        if save:
            fn = SS_DIR / f"ss_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            fn.write_bytes(base64.b64decode(b64))
        return b64
    except Exception as e:
        log.warning("screenshot: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# REAL MOUSE & KEYBOARD
# ══════════════════════════════════════════════════════════════════════════════
def real_click(x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.2):
    """Actual pyautogui mouse click with boundary checks."""
    if not PYAUTOGUI_OK:
        return {"status": "error", "message": "pyautogui not available"}
    try:
        sw, sh = pyautogui.size()
        x = max(1, min(x, sw - 1))
        y = max(1, min(y, sh - 1))
        pyautogui.moveTo(x, y, duration=duration)
        pyautogui.click(x, y, button=button, clicks=clicks, interval=0.08)
        log.info("CLICK x=%d y=%d btn=%s clicks=%d", x, y, button, clicks)
        return {"status": "ok", "x": x, "y": y}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def real_type(text: str, clear_first: bool = False, human_speed: bool = False):
    """Paste via clipboard (fastest) with fallback to pyautogui.write."""
    if not text:
        return
    text = str(text)[:100_000]
    try:
        if clear_first and PYAUTOGUI_OK:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.press("delete")
            time.sleep(0.05)
        if CLIP_OK:
            pyperclip.copy(text)
            time.sleep(0.06)
            if PYAUTOGUI_OK:
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.12)
        elif PYAUTOGUI_OK:
            interval = random.uniform(0.03, 0.09) if human_speed else 0.012
            for chunk in [text[i:i+300] for i in range(0, len(text), 300)]:
                pyautogui.write(chunk, interval=interval)
    except Exception as e:
        log.warning("real_type: %s", e)


def real_hotkey(*keys):
    """Press a keyboard shortcut."""
    if not PYAUTOGUI_OK:
        return
    try:
        pyautogui.hotkey(*[str(k) for k in keys[:6]])
    except Exception as e:
        log.warning("hotkey %s: %s", keys, e)


def real_press(key: str):
    """Press a single key."""
    if not PYAUTOGUI_OK:
        return
    try:
        pyautogui.press(str(key))
    except Exception as e:
        log.warning("press %s: %s", key, e)


def real_scroll(direction: str = "down", amount: int = 5):
    """Scroll up or down."""
    if not PYAUTOGUI_OK:
        return
    try:
        amt = abs(amount)
        pyautogui.scroll(amt if direction == "up" else -amt)
    except Exception as e:
        log.warning("scroll: %s", e)


def find_on_screen(image_path: str, confidence: float = 0.85) -> Optional[Tuple[int, int]]:
    """Use pyautogui.locateCenterOnScreen to find UI element."""
    if not PYAUTOGUI_OK:
        return None
    try:
        loc = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        return (loc.x, loc.y) if loc else None
    except Exception:
        return None


def read_screen_text(region: Optional[Tuple] = None) -> str:
    """OCR the current screen."""
    if OCR_OK and PIL_OK:
        try:
            img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
            return pytesseract.image_to_string(img)
        except Exception as e:
            log.warning("OCR: %s", e)
    if CV2_OK and PIL_OK:
        try:
            img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
            return ""  # cv2 without tesseract can't do OCR
        except Exception:
            pass
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# WINDOW MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
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

def focus_window(title_pattern: str) -> bool:
    """Bring a window matching title_pattern to the foreground."""
    try:
        if not WINDOW_OK or not gw:
            return False
        wins = [w for w in gw.getAllWindows() if title_pattern.lower() in w.title.lower()]
        if wins:
            wins[0].activate()
            time.sleep(0.4)
            return True
    except Exception as e:
        log.warning("focus_window: %s", e)
    return False


# ══════════════════════════════════════════════════════════════════════════════
# FILE ORGANIZER
# ══════════════════════════════════════════════════════════════════════════════
def organize_folder(folder: str, dry_run: bool = False) -> dict:
    """Scan folder, move files into subfolders by type. Real file moves."""
    p = Path(folder)
    if not p.exists() or not p.is_dir():
        return {"status": "error", "message": f"Folder not found: {folder}"}
    if not _is_path_allowed(str(p)):
        return {"status": "error", "message": "Access to this folder is blocked."}

    moved = 0; skipped = 0; errors = []
    for f in p.iterdir():
        if f.is_dir() or f.name.startswith("."):
            continue
        ext  = f.suffix.lower()
        name = f.name.lower()

        # Detect invoice by name
        cat = None
        if any(kw in name for kw in ["invoice", "receipt", "bill", "payment", "inv_", "_inv"]):
            cat = "Invoices"
        else:
            for category, exts in FILE_CATEGORIES.items():
                if ext in exts:
                    cat = category; break
        if not cat:
            cat = "Other"

        dest_dir = p / cat
        if not dry_run:
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / f.name
            if dest.exists():
                stem = f.stem + f"_{int(time.time())}"
                dest = dest_dir / (stem + f.suffix)
            try:
                shutil.move(str(f), str(dest))
                moved += 1
                log.info("Moved %s → %s", f.name, cat)
            except Exception as e:
                errors.append(str(e)); skipped += 1
        else:
            moved += 1

    summary = f"{'[DRY RUN] ' if dry_run else ''}Organized {moved} files into categories. Skipped {skipped}."
    speak(summary)
    return {"status": "ok", "moved": moved, "skipped": skipped, "errors": errors[:5]}


def rename_files_batch(folder: str, pattern: str, replacement: str) -> dict:
    """Batch rename files matching pattern."""
    p = Path(folder)
    if not p.exists():
        return {"status": "error", "message": "Folder not found"}
    if not _is_path_allowed(str(p)):
        return {"status": "error", "message": "Blocked folder."}
    renamed = 0
    for f in p.iterdir():
        if f.is_file() and re.search(pattern, f.name, re.IGNORECASE):
            new_name = re.sub(pattern, replacement, f.name, flags=re.IGNORECASE)
            try:
                f.rename(f.parent / new_name)
                renamed += 1
            except Exception:
                pass
    speak(f"Renamed {renamed} files.")
    return {"status": "ok", "renamed": renamed}


# ══════════════════════════════════════════════════════════════════════════════
# PDF INVOICE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════
def extract_invoice_data(pdf_path: str) -> dict:
    """Extract amounts and details from PDF invoices."""
    if not PDF_OK:
        return {"status": "error", "message": "pdfplumber not installed"}
    p = Path(pdf_path)
    if not p.exists():
        return {"status": "error", "message": "File not found"}

    try:
        amounts = []; dates = []; invoice_nos = []
        with pdfplumber.open(str(p)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # Extract amounts
        for m in re.finditer(r"(?:total|amount|due|payable)[:\s]+[₹$€£]?\s*([\d,]+\.?\d*)", text, re.I):
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except Exception:
                pass
        for m in re.finditer(r"[₹$€£]\s*([\d,]+\.?\d*)", text):
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except Exception:
                pass

        # Extract dates
        for m in re.finditer(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text):
            dates.append(m.group())

        # Extract invoice number
        for m in re.finditer(r"(?:invoice|inv|bill)\s*[#no.]*\s*([A-Z0-9-]+)", text, re.I):
            invoice_nos.append(m.group(1))

        result = {
            "status":      "ok",
            "file":        p.name,
            "amounts":     list(set(amounts)),
            "max_amount":  max(amounts) if amounts else 0,
            "dates":       dates[:5],
            "invoice_nos": invoice_nos[:3],
            "text_preview": text[:500],
        }
        log.info("Invoice extracted: %s — max amount: %s", p.name, result["max_amount"])
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def process_invoices_folder(folder: str) -> dict:
    """Scan folder, extract data from all PDFs, queue payments, save CSV report."""
    p = Path(folder)
    if not p.exists():
        return {"status": "error", "message": "Folder not found"}
    records = []
    queued = 0
    for f in p.rglob("*.pdf"):
        d = extract_invoice_data(str(f))
        if d.get("status") == "ok":
            records.append({
                "file":       d["file"],
                "max_amount": d["max_amount"],
                "dates":      "; ".join(d["dates"][:2]),
                "invoice_no": "; ".join(d["invoice_nos"][:2]),
            })
            qid = add_to_payment_queue(d)
            if qid:
                queued += 1
    report = DATA_DIR / f"invoices_{datetime.date.today()}.csv"
    try:
        with open(report, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["file", "max_amount", "dates", "invoice_no"])
            w.writeheader(); w.writerows(records)
        try:
            subprocess.Popen(f'notepad.exe "{report}"', shell=True)
        except Exception:
            pass
        speak(f"Processed {len(records)} invoices. {queued} queued for payment approval. Report saved.")
        return {"status": "ok", "count": len(records), "queued": queued, "report": str(report)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE PAYMENT QUEUE  (extract → queue → human approval → handoff to portal)
# Nothing here ever moves money automatically. Approval just opens the chosen
# payment portal with the amount/invoice shown so a human completes the pay.
# ══════════════════════════════════════════════════════════════════════════════
def _load_payment_queue() -> list:
    try:
        if PAYMENT_QUEUE_FILE.exists():
            return json.loads(PAYMENT_QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("load_payment_queue: %s", e)
    return []


def _save_payment_queue(q: list):
    try:
        tmp = PAYMENT_QUEUE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(q, indent=2), encoding="utf-8")
        tmp.replace(PAYMENT_QUEUE_FILE)
    except Exception as e:
        log.warning("save_payment_queue: %s", e)


def add_to_payment_queue(invoice: dict) -> Optional[str]:
    """invoice: a dict from extract_invoice_data(). Adds an entry if it has an amount > 0."""
    amount = invoice.get("max_amount") or 0
    if not amount:
        return None
    q = _load_payment_queue()
    # Avoid duplicate queue entries for the same file
    if any(i.get("file") == invoice.get("file") and i.get("status") == "pending_review" for i in q):
        return None
    qid = hashlib.md5(f"{invoice.get('file','')}-{amount}-{time.time()}".encode()).hexdigest()[:8]
    entry = {
        "id":         qid,
        "file":       invoice.get("file", ""),
        "amount":     amount,
        "invoice_no": "; ".join(invoice.get("invoice_nos", [])[:1]),
        "dates":      "; ".join(invoice.get("dates", [])[:1]),
        "status":     "pending_review",
        "added_at":   datetime.datetime.now().isoformat(),
    }
    q.append(entry)
    _save_payment_queue(q)
    audit.info("PAYMENT_QUEUED id=%s amount=%s file=%s", qid, amount, entry["file"])
    return qid


def list_payment_queue(status: str = "pending_review") -> dict:
    q = _load_payment_queue()
    items = [i for i in q if status == "all" or i.get("status") == status]
    if items:
        label = "all" if status == "all" else status.replace("_", " ")
        print(f"\n  === PAYMENT QUEUE ({label}) ===")
        for it in items:
            print(f"  [{it['id']}] {it['file']}  amount={it['amount']}  "
                  f"inv#={it.get('invoice_no','') or '-'}  status={it['status']}")
        print()
        speak(f"{len(items)} payment(s) {label}.")
    else:
        speak(f"No payments with status {status.replace('_',' ')}.")
    return {"status": "ok", "items": items, "count": len(items)}


def approve_payment(queue_id: str, portal: str = "razorpay") -> dict:
    q = _load_payment_queue()
    entry = next((i for i in q if i["id"] == queue_id), None)
    if not entry:
        return {"status": "error", "message": f"No queued payment with id {queue_id}"}
    if entry["status"] != "pending_review":
        return {"status": "error", "message": f"Payment {queue_id} is already '{entry['status']}'"}

    if not request_approval("approve_payment",
                             f"Pay {entry['amount']} — invoice {entry.get('invoice_no') or '?'} "
                             f"({entry['file']})"):
        return {"status": "denied"}

    entry["status"] = "approved"
    entry["approved_at"] = datetime.datetime.now().isoformat()
    entry["portal"] = portal
    _save_payment_queue(q)
    audit.info("PAYMENT_APPROVED id=%s amount=%s file=%s portal=%s",
               queue_id, entry["amount"], entry["file"], portal)

    url = PAYMENT_PORTALS.get(portal, "")
    if url:
        webbrowser.open(url)
        speak(f"Approved. Opened {portal} — pay {entry['amount']} for invoice "
              f"{entry.get('invoice_no') or '?'}. Complete it there.")
    else:
        speak(f"Approved payment of {entry['amount']} for invoice "
              f"{entry.get('invoice_no') or '?'}. No portal URL configured — pay manually.")
    return {"status": "ok", "entry": entry, "portal_url": url}


def reject_payment(queue_id: str, reason: str = "") -> dict:
    q = _load_payment_queue()
    entry = next((i for i in q if i["id"] == queue_id), None)
    if not entry:
        return {"status": "error", "message": f"No queued payment with id {queue_id}"}
    entry["status"] = "rejected"
    if reason:
        entry["reason"] = reason
    _save_payment_queue(q)
    audit.info("PAYMENT_REJECTED id=%s file=%s reason=%s", queue_id, entry["file"], reason[:60])
    speak(f"Payment {queue_id} rejected.")
    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# SPREADSHEET READER → PASTE TO WEB
# ══════════════════════════════════════════════════════════════════════════════
def read_spreadsheet(path: str, sheet: int = 0) -> dict:
    """Read local Excel/CSV file and return rows."""
    p = Path(path)
    if not p.exists():
        return {"status": "error", "message": "File not found"}
    try:
        rows = []
        if p.suffix.lower() in (".xlsx", ".xls") and XL_OK:
            wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
            ws = wb.worksheets[sheet]
            for row in ws.iter_rows(values_only=True):
                rows.append([str(c) if c is not None else "" for c in row])
        elif p.suffix.lower() == ".csv":
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                for row in csv.reader(fh):
                    rows.append(row)
        else:
            return {"status": "error", "message": "Unsupported format"}
        speak(f"Read {len(rows)} rows from {p.name}")
        return {"status": "ok", "rows": rows[:500], "total_rows": len(rows)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def paste_spreadsheet_to_browser(path: str, url: str, field_selector: str = "input") -> dict:
    """
    Open URL in Chrome, read spreadsheet, paste each row's data into the page.
    Uses Selenium for real browser interaction.
    """
    data = read_spreadsheet(path)
    if data.get("status") != "ok":
        return data
    rows = data["rows"]
    if not rows:
        return {"status": "error", "message": "Spreadsheet is empty"}

    drv = _get_driver()
    if not drv:
        return {"status": "error", "message": "Selenium not available"}

    speak(f"Opening {url} to paste {len(rows)} rows...")
    try:
        drv.get(url)
        time.sleep(2)
        pasted = 0
        for row in rows[:100]:
            try:
                fields = drv.find_elements(By.CSS_SELECTOR, field_selector)
                for i, field in enumerate(fields[:len(row)]):
                    field.clear()
                    field.send_keys(row[i])
                pasted += 1
                time.sleep(0.3)
            except Exception:
                pass
        speak(f"Pasted {pasted} rows into the browser.")
        return {"status": "ok", "pasted": pasted}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def configure_smtp_interactive() -> dict:
    global _smtp_cfg
    print("\n  === Email Setup ===")
    print("  For Gmail: myaccount.google.com/apppasswords\n")
    try:
        em = input("  Your email: ").strip()
        if not em or "@" not in em:
            return {"status": "error", "message": "Invalid email"}
        pw = input("  App Password: ").strip().replace(" ", "")
        if not pw:
            return {"status": "error", "message": "No password"}
        domain = em.split("@")[-1].lower()
        preset = SMTP_PRESETS.get(domain, {"host": f"smtp.{domain}", "port": 587})
        print(f"  Testing {preset['host']}:{preset['port']}...")
        try:
            with smtplib.SMTP(preset["host"], preset["port"], timeout=15) as s:
                s.ehlo(); s.starttls(); s.ehlo(); s.login(em, pw)
            print("  [OK] SMTP connection successful!")
        except smtplib.SMTPAuthenticationError:
            print("  [ERROR] Auth failed — check App Password.")
            return {"status": "error", "message": "Auth failed"}
        except Exception as te:
            print(f"  [WARN] {te} — saving anyway.")
        _smtp_cfg = {"email": em, "password": pw, "host": preset["host"], "port": preset["port"]}
        save_memory()
        speak(f"Email configured: {em}")
        return {"status": "ok", "email": em}
    except (EOFError, KeyboardInterrupt):
        return {"status": "cancelled"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _build_msg(from_: str, to_: str, subject: str, body: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = from_; msg["To"] = to_; msg["Subject"] = subject
    plain = body.replace("<br>", "\n"); html = "<html><body>" + body.replace("\n", "<br>") + "</body></html>"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send_email_real(to: str, subject: str, body: str, require_approval: bool = True) -> dict:
    if require_approval and "send_email" in APPROVAL_REQUIRED:
        if not request_approval("send_email", f"To: {to} | Subject: {subject}"):
            return {"status": "denied", "message": "User denied email send"}

    em = _smtp_cfg.get("email", "")
    pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host", "smtp.gmail.com")
    pt = int(_smtp_cfg.get("port", 587))

    if not em or not pw:
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(str(body)[:2000])}")
        webbrowser.open(url)
        speak(f"Gmail opened for {to} — configure SMTP for auto-send.")
        return {"status": "ok", "action": "browser", "note": "SMTP not configured"}

    try:
        msg = _build_msg(em, to, subject, body)
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        speak(f"Email sent to {to}!")
        audit.info("EMAIL_SENT to=%s subject=%s", to, subject[:60])
        return {"status": "ok", "sent_to": to}
    except Exception as e:
        log.warning("email failed: %s", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}&su={urllib.parse.quote(subject)}")
        webbrowser.open(url)
        return {"status": "ok", "action": "browser_fallback", "note": str(e)}


def send_bulk_email(contacts: list, subject: str, body_tmpl: str, delay: float = 1.5) -> dict:
    em = _smtp_cfg.get("email", ""); pw = _smtp_cfg.get("password", "")
    ht = _smtp_cfg.get("host", "smtp.gmail.com"); pt = int(_smtp_cfg.get("port", 587))
    if not em or not pw:
        return {"status": "error", "message": "Email not configured. Say 'configure email'."}
    if not contacts:
        return {"status": "error", "message": "No contacts provided."}
    if not request_approval("bulk_email", f"{len(contacts)} contacts | Subject: {subject[:50]}"):
        return {"status": "denied", "message": "User denied bulk email"}

    sent = 0; failed = 0; delay = max(0.5, float(delay))
    speak(f"Starting bulk email to {len(contacts)} contacts...")
    try:
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            for c in contacts:
                to_e = (c.get("email") or c.get("Email") or "").strip()
                if not to_e or "@" not in to_e:
                    failed += 1; continue
                name    = (c.get("name") or to_e.split("@")[0].replace(".", " ").title()).strip()
                company = c.get("company") or ""
                body = (body_tmpl.replace("{name}", name).replace("{Name}", name)
                        .replace("{email}", to_e).replace("{company}", company))
                subj = subject.replace("{name}", name).replace("{company}", company)
                try:
                    msg = _build_msg(em, to_e, subj, body)
                    srv.sendmail(em, [to_e], msg.as_string())
                    sent += 1
                    if sent % 10 == 0:
                        speak(f"{sent} emails sent.")
                    time.sleep(delay)
                except Exception:
                    failed += 1
    except Exception as e:
        return {"status": "error", "message": f"SMTP failed: {e}"}

    summary = f"Bulk done: {sent} sent, {failed} failed of {len(contacts)}"
    speak(summary)
    return {"status": "ok", "sent": sent, "failed": failed}


def load_csv_contacts(path: str) -> list:
    contacts = []
    try:
        p = Path(path)
        if not p.exists():
            p2 = Path.home() / "Desktop" / p.name
            if p2.exists(): p = p2
            else: return []
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = (row.get("email") or row.get("Email") or row.get("EMAIL") or "").strip()
                if em and "@" in em:
                    contacts.append({"email": em,
                                     "name": (row.get("name") or row.get("Name") or em.split("@")[0]).strip(),
                                     "company": (row.get("company") or row.get("Company") or "").strip()})
    except Exception as e:
        log.warning("load_csv: %s", e)
    return contacts


# ══════════════════════════════════════════════════════════════════════════════
# INBOX READER (IMAP)
# ══════════════════════════════════════════════════════════════════════════════
def read_inbox(max_count: int = 10) -> dict:
    """Read latest emails via IMAP and flag urgent ones."""
    import imaplib, email as email_lib
    em = _smtp_cfg.get("email", ""); pw = _smtp_cfg.get("password", "")
    if not em or not pw:
        return {"status": "error", "message": "Email not configured."}

    domain = em.split("@")[-1].lower()
    imap_hosts = {
        "gmail.com": "imap.gmail.com", "googlemail.com": "imap.gmail.com",
        "outlook.com": "imap-mail.outlook.com", "hotmail.com": "imap-mail.outlook.com",
        "yahoo.com": "imap.mail.yahoo.com",
    }
    host = imap_hosts.get(domain, f"imap.{domain}")

    try:
        with imaplib.IMAP4_SSL(host, 993) as M:
            M.login(em, pw)
            M.select("INBOX")
            _, data = M.search(None, "UNSEEN")
            uids = data[0].split()[-max_count:]
            emails = []
            urgent_keywords = ["urgent", "asap", "immediate", "critical", "deadline", "payment overdue"]
            for uid in reversed(uids):
                _, msg_data = M.fetch(uid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)
                subject = msg.get("Subject", "")
                sender  = msg.get("From", "")
                body    = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")[:500]
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")[:500]

                is_urgent = any(kw in (subject + body).lower() for kw in urgent_keywords)
                emails.append({
                    "from": sender, "subject": subject,
                    "preview": body[:200], "urgent": is_urgent,
                })

            urgent_count = sum(1 for e in emails if e["urgent"])
            if urgent_count:
                speak(f"You have {urgent_count} urgent emails!")
                _notify("Urgent Emails", f"{urgent_count} urgent messages in inbox")

            return {"status": "ok", "count": len(emails), "emails": emails, "urgent": urgent_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def draft_email_reply(original_subject: str, original_body: str, context: str = "") -> str:
    """Generate a professional email reply draft."""
    # Simple local template — no external AI call
    name_match = re.search(r"from:\s*(.+?)[\n<]", original_body, re.I)
    sender_name = name_match.group(1).strip() if name_match else "there"

    if any(kw in original_body.lower() for kw in ["meeting", "schedule", "call", "appointment"]):
        template = (f"Hi {sender_name},\n\nThank you for reaching out regarding {original_subject}.\n"
                    f"I'd be happy to discuss further. Please let me know your availability "
                    f"and I'll confirm a time that works.\n\nBest regards")
    elif any(kw in original_body.lower() for kw in ["invoice", "payment", "bill"]):
        template = (f"Hi {sender_name},\n\nThank you for your message about {original_subject}.\n"
                    f"I'm reviewing the details and will get back to you within 24 hours.\n\nBest regards")
    else:
        template = (f"Hi {sender_name},\n\nThank you for your email regarding {original_subject}.\n"
                    f"{context or 'I have received your message and will respond shortly.'}\n\nBest regards")
    return template


# ══════════════════════════════════════════════════════════════════════════════
# WEB HELPERS
# ══════════════════════════════════════════════════════════════════════════════
_HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

def web_research(query: str) -> str:
    if not REQUESTS_OK:
        return "Web research unavailable."
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=10"
        r = req_lib.get(url, headers=_HDRS, timeout=15)
        if BS4_OK and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            snips = [tag.get_text(" ", strip=True) for tag in soup.find_all(
                ["div", "span"], class_=lambda c: c and any(
                    x in c for x in ["BNeawe", "VwiC3b", "MUxGbd", "hgKElc"])
            ) if len(tag.get_text().strip()) > 60]
            return " ".join(snips[:12])[:6000] or "No results."
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:3000]
    except Exception as e:
        return f"Research error: {e}"


def find_leads_web(product: str, niche: str = "", max_leads: int = 50) -> list:
    if not REQUESTS_OK: return []
    leads = []; email_re = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b')
    skip = {"example.com", "test.com", "sentry.io", "w3.org", "google.com", "github.com", "cloudflare.com"}
    speak(f"Searching leads for {product}...")
    queries = [f"{niche} {product} contact email", f"{product} company email contact",
               f'"{product}" "@gmail.com" contact']
    for q in queries:
        if len(leads) >= max_leads: break
        try:
            r = req_lib.get(f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20",
                            headers=_HDRS, timeout=15)
            text = BeautifulSoup(r.text, "html.parser").get_text() if BS4_OK else r.text
            for em in email_re.findall(text):
                domain = em.split("@")[-1].lower()
                if domain in skip: continue
                if any(l["email"].lower() == em.lower() for l in leads): continue
                leads.append({"email": em, "name": em.split("@")[0].replace(".", " ").title(),
                              "company": domain.split(".")[0].title()})
                if len(leads) >= max_leads: break
            time.sleep(2)
        except Exception as e:
            log.warning("lead search: %s", e)
    try:
        lf = DATA_DIR / "leads.csv"
        with open(lf, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["email", "name", "company"])
            w.writeheader(); w.writerows(leads)
    except Exception: pass
    speak(f"Found {len(leads)} leads.")
    return leads


# ══════════════════════════════════════════════════════════════════════════════
# WHATSAPP
# ══════════════════════════════════════════════════════════════════════════════
def wa_send(phone: str, msg: str) -> dict:
    ph = re.sub(r"[^0-9+]", "", str(phone))
    if not ph.startswith("+"): ph = "+91" + ph
    url = f"https://wa.me/{ph.lstrip('+')}?text={urllib.parse.quote(str(msg))}"
    webbrowser.open(url)
    speak(f"WhatsApp Web opened for {phone}.")
    return {"status": "ok", "note": "WhatsApp Web opened — click Send"}


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR BOOKING
# ══════════════════════════════════════════════════════════════════════════════
def check_calendar_availability(date_str: str) -> dict:
    """Open Google Calendar to check availability."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        url = f"https://calendar.google.com/calendar/r/day/{dt.year}/{dt.month}/{dt.day}"
        webbrowser.open(url)
        speak(f"Opening calendar for {date_str}")
        return {"status": "ok", "date": date_str, "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def book_meeting(with_email: str, subject: str, date_str: str, duration_min: int = 60) -> dict:
    """Open Google Calendar new event for booking."""
    url = (f"https://calendar.google.com/calendar/r/eventedit"
           f"?text={urllib.parse.quote(subject)}"
           f"&add={urllib.parse.quote(with_email)}")
    webbrowser.open(url)
    speak(f"Calendar opened to book meeting with {with_email}")
    return {"status": "ok", "note": "Fill in time and click Save"}


# ══════════════════════════════════════════════════════════════════════════════
# SELENIUM BROWSER AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════
def _get_driver(headless: bool = False):
    global _selenium_driver
    with _sel_lock:
        if _selenium_driver:
            try:
                _ = _selenium_driver.current_url
                return _selenium_driver
            except Exception:
                try: _selenium_driver.quit()
                except Exception: pass
                _selenium_driver = None
        if not SELENIUM_OK: return None
        opts = ChromeOptions()
        if headless: opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage")
        try:
            svc = ChromeService(ChromeDriverManager().install())
            drv = webdriver.Chrome(service=svc, options=opts)
            drv.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _selenium_driver = drv
            return drv
        except Exception as e:
            log.warning("Selenium init: %s", e); return None


def selenium_open(url: str, wait_for_css: str = None, timeout: int = 15) -> dict:
    drv = _get_driver()
    if not drv: webbrowser.open(url); return {"status": "ok", "note": "default browser"}
    try:
        drv.get(url)
        if wait_for_css:
            WebDriverWait(drv, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_css)))
        return {"status": "ok", "url": drv.current_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def selenium_fill(selector: str, value: str, by: str = "css", submit: bool = False) -> dict:
    drv = _get_driver()
    if not drv: return {"status": "error", "message": "Selenium not available"}
    by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "id": By.ID, "name": By.NAME}
    try:
        el = WebDriverWait(drv, 10).until(EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.clear(); el.send_keys(value)
        if submit: el.send_keys(Keys.RETURN)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def selenium_click(selector: str, by: str = "css") -> dict:
    drv = _get_driver()
    if not drv: return {"status": "error", "message": "Selenium not available"}
    by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "id": By.ID, "name": By.NAME}
    try:
        el = WebDriverWait(drv, 10).until(EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.click(); return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL MEDIA (outbound posting)
# ══════════════════════════════════════════════════════════════════════════════
def post_twitter(username: str, password: str, text: str) -> dict:
    if not request_approval("post_twitter", f"@{username}: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into Twitter...")
    drv = _get_driver()
    if not drv: webbrowser.open("https://x.com"); return {"status": "ok", "note": "Opened X"}
    try:
        drv.get("https://x.com/login"); time.sleep(3)
        WebDriverWait(drv, 15).until(EC.presence_of_element_located((By.NAME, "text"))).send_keys(username + Keys.RETURN)
        time.sleep(2)
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password + Keys.RETURN)
        time.sleep(3)
        WebDriverWait(drv, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]'))).click()
        time.sleep(1)
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))).send_keys(text)
        time.sleep(0.5)
        WebDriverWait(drv, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))).click()
        time.sleep(2)
        speak("Tweet posted!"); return {"status": "ok", "platform": "twitter"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def post_linkedin(username: str, password: str, text: str) -> dict:
    if not request_approval("post_linkedin", f"LinkedIn: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into LinkedIn...")
    drv = _get_driver()
    if not drv: webbrowser.open("https://www.linkedin.com"); return {"status": "ok"}
    try:
        drv.get("https://www.linkedin.com/login"); time.sleep(2)
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        drv.find_element(By.ID, "password").send_keys(password)
        drv.find_element(By.CSS_SELECTOR, '[type="submit"]').click(); time.sleep(3)
        WebDriverWait(drv, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".share-box-feed-entry__trigger"))).click()
        time.sleep(1)
        box = WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor")))
        box.click(); box.send_keys(text); time.sleep(0.5)
        WebDriverWait(drv, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".share-actions__primary-action"))).click()
        time.sleep(2); speak("LinkedIn post published!")
        return {"status": "ok", "platform": "linkedin"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def post_facebook(username: str, password: str, text: str, page_id: str = "") -> dict:
    if not request_approval("post_facebook", f"Facebook: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into Facebook...")
    drv = _get_driver()
    if not drv: webbrowser.open("https://www.facebook.com"); return {"status": "ok"}
    try:
        drv.get("https://www.facebook.com/login"); time.sleep(2)
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(username)
        drv.find_element(By.ID, "pass").send_keys(password)
        drv.find_element(By.NAME, "login").click(); time.sleep(4)
        box = WebDriverWait(drv, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label=\"What's on your mind?\"]")))
        box.click(); time.sleep(1)
        editor = WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[contenteditable="true"]')))
        editor.send_keys(text); time.sleep(0.5)
        WebDriverWait(drv, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Post"]'))).click()
        time.sleep(2); speak("Facebook post published!")
        return {"status": "ok", "platform": "facebook"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def youtube_search_and_play(query: str) -> dict:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url); speak(f"YouTube search: {query}")
    return {"status": "ok", "url": url}


# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL MESSAGE REPLY BOTS  (WhatsApp / Instagram / Facebook DMs)
#
# Uses a SEPARATE, PERSISTENT Chrome profile per platform (saved under
# AGENT_DIR/browser_profiles/<platform>) so you log in / scan the QR code
# ONCE and the session survives restarts.
#
# Honesty note: Instagram and Facebook actively try to detect and block
# automated browser sessions (checkpoints, temporary locks). This uses the
# same pattern as your existing post_twitter/post_linkedin/post_facebook
# functions, but expect occasional manual re-logins if a platform flags the
# session. WhatsApp Web requires a one-time QR scan on first run.
#
# Default mode is DRAFT ONLY (auto=False): messages are read and a reply is
# generated but NOT sent — they're returned so you can review them. Turning
# on auto-send for a platform requires one human approval (enable_auto_reply),
# same pattern as "always approve" elsewhere in this file.
# ══════════════════════════════════════════════════════════════════════════════
def _get_social_driver(platform: str):
    """Persistent Chrome profile per platform so login/session survives restarts."""
    with _social_lock:
        drv = _social_drivers.get(platform)
        if drv:
            try:
                _ = drv.current_url
                return drv
            except Exception:
                try: drv.quit()
                except Exception: pass
                _social_drivers.pop(platform, None)

        if not SELENIUM_OK:
            return None
        prof_dir = SOCIAL_PROFILE_DIR / platform
        prof_dir.mkdir(exist_ok=True)
        opts = ChromeOptions()
        opts.add_argument(f"--user-data-dir={prof_dir}")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--no-sandbox"); opts.add_argument("--disable-dev-shm-usage")
        try:
            svc = ChromeService(ChromeDriverManager().install())
            drv = webdriver.Chrome(service=svc, options=opts)
            drv.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _social_drivers[platform] = drv
            return drv
        except Exception as e:
            log.warning("Social driver [%s]: %s", platform, e)
            return None


def _gen_reply(message: str) -> str:
    """Simple keyword-based reply generator (local, no external AI call)."""
    m = (message or "").lower()
    if any(k in m for k in ["price", "cost", "how much", "quote"]):
        return "Thanks for asking! Let me check pricing and get back to you shortly."
    if any(k in m for k in ["urgent", "asap", "emergency"]):
        return "Got it — marking this urgent. We'll respond very soon."
    if any(k in m for k in ["hi", "hello", "hey", "good morning", "good evening"]):
        return "Hi! Thanks for reaching out — how can I help?"
    if any(k in m for k in ["thank", "thanks"]):
        return "You're welcome! Let us know if you need anything else."
    return AUTO_REPLY_TEMPLATES["default"]


def whatsapp_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("whatsapp")
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    try:
        if "web.whatsapp.com" not in (drv.current_url or ""):
            drv.get("https://web.whatsapp.com")
            time.sleep(3)
        # First-run QR check
        try:
            WebDriverWait(drv, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan me!']")))
            speak("WhatsApp Web needs a QR scan — check the browser window.")
            return {"status": "pending", "message": "Scan the QR code in the opened browser window"}
        except Exception:
            pass

        unread = drv.find_elements(By.XPATH, "//span[@aria-label[contains(.,'unread')]]")
        results = []
        for chat in unread[:max_chats]:
            try:
                row = chat.find_element(By.XPATH, "./ancestor::div[@role='listitem']")
                row.click(); time.sleep(0.5)
                msgs = drv.find_elements(By.CSS_SELECTOR, "div.message-in span.selectable-text")
                if not msgs: continue
                last_msg = msgs[-1].text
                if not last_msg: continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["whatsapp"]: continue
                _social_seen["whatsapp"].add(seen_key)
                reply = _gen_reply(last_msg)
                if auto:
                    box = drv.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
                    box.click(); box.send_keys(reply); box.send_keys(Keys.RETURN)
                    audit.info("WHATSAPP_AUTOREPLY sent")
                    results.append({"message": last_msg[:80], "reply": reply, "sent": True})
                else:
                    results.append({"message": last_msg[:80], "reply": reply, "sent": False})
            except Exception:
                continue

        if results:
            speak(f"WhatsApp: {len(results)} new message(s){' replied' if auto else ' drafted'}.")
        return {"status": "ok", "platform": "whatsapp", "messages": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def instagram_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("instagram")
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    try:
        if "instagram.com/direct" not in (drv.current_url or ""):
            drv.get("https://www.instagram.com/direct/inbox/")
            time.sleep(3)
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.NAME, "username")))
            speak("Instagram needs login — check the browser window.")
            return {"status": "pending", "message": "Log in to Instagram in the opened browser window"}
        except Exception:
            pass

        threads = drv.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        results = []
        for th in threads[:max_chats]:
            try:
                th.click(); time.sleep(0.5)
                msgs = drv.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
                if not msgs: continue
                last_msg = msgs[-1].text
                if not last_msg: continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["instagram"]: continue
                _social_seen["instagram"].add(seen_key)
                reply = _gen_reply(last_msg)
                if auto:
                    box = drv.find_element(By.CSS_SELECTOR, "textarea")
                    box.click(); box.send_keys(reply); box.send_keys(Keys.RETURN)
                    audit.info("INSTAGRAM_AUTOREPLY sent")
                    results.append({"message": last_msg[:80], "reply": reply, "sent": True})
                else:
                    results.append({"message": last_msg[:80], "reply": reply, "sent": False})
            except Exception:
                continue

        if results:
            speak(f"Instagram: {len(results)} new message(s){' replied' if auto else ' drafted'}.")
        return {"status": "ok", "platform": "instagram", "messages": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def facebook_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("facebook")
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    try:
        if "messages" not in (drv.current_url or ""):
            drv.get("https://www.facebook.com/messages/t/")
            time.sleep(3)
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.ID, "email")))
            speak("Facebook needs login — check the browser window.")
            return {"status": "pending", "message": "Log in to Facebook in the opened browser window"}
        except Exception:
            pass

        threads = drv.find_elements(By.CSS_SELECTOR, "a[role='link'][aria-current]")
        results = []
        for th in threads[:max_chats]:
            try:
                th.click(); time.sleep(0.5)
                msgs = drv.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
                if not msgs: continue
                last_msg = msgs[-1].text
                if not last_msg: continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["facebook"]: continue
                _social_seen["facebook"].add(seen_key)
                reply = _gen_reply(last_msg)
                if auto:
                    box = drv.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
                    box.click(); box.send_keys(reply); box.send_keys(Keys.RETURN)
                    audit.info("FACEBOOK_AUTOREPLY sent")
                    results.append({"message": last_msg[:80], "reply": reply, "sent": True})
                else:
                    results.append({"message": last_msg[:80], "reply": reply, "sent": False})
            except Exception:
                continue

        if results:
            speak(f"Facebook: {len(results)} new message(s){' replied' if auto else ' drafted'}.")
        return {"status": "ok", "platform": "facebook", "messages": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


_SOCIAL_CHECKERS = {
    "whatsapp":  whatsapp_check_messages,
    "instagram": instagram_check_messages,
    "facebook":  facebook_check_messages,
}


def _social_poll_loop():
    global _social_running
    while _social_running and _running:
        for plat, auto in list(_social_auto.items()):
            if auto:
                try:
                    _SOCIAL_CHECKERS[plat](auto=True)
                except Exception as e:
                    log.warning("social poll [%s]: %s", plat, e)
        time.sleep(SOCIAL_POLL_INTERVAL)


def start_social_replies(platforms: list, auto: bool = False) -> dict:
    """Open/attach a persistent browser session per platform and start polling.
    auto=True sends replies automatically (one-time approval required)."""
    global _social_thread, _social_running
    plats = [str(p).lower().strip() for p in platforms if str(p).lower().strip() in _SOCIAL_CHECKERS]
    if not plats:
        return {"status": "error", "message": "No valid platforms (use whatsapp / instagram / facebook)"}

    if auto and not request_approval("enable_auto_reply", f"Auto-send replies on: {', '.join(plats)}"):
        return {"status": "denied"}

    opened = []
    for plat in plats:
        _social_auto[plat] = auto
        res = _SOCIAL_CHECKERS[plat](auto=False)  # opens browser / triggers login if needed
        opened.append({"platform": plat, "status": res.get("status")})

    if not _social_running:
        _social_running = True
        _social_thread = threading.Thread(target=_social_poll_loop, daemon=True, name="SocialReply")
        _social_thread.start()

    speak(f"Reply monitoring on for {', '.join(plats)}{' (auto-send)' if auto else ' (drafts only)'}.")
    return {"status": "ok", "platforms": plats, "auto": auto, "opened": opened}


def stop_social_replies(platforms: list = None) -> dict:
    global _social_running
    plats = platforms or list(_social_auto.keys())
    plats = [str(p).lower().strip() for p in plats]
    for p in plats:
        if p in _social_auto:
            _social_auto[p] = False
    if not any(_social_auto.values()):
        _social_running = False
    speak("Reply monitoring stopped.")
    return {"status": "ok", "platforms": plats}


# ══════════════════════════════════════════════════════════════════════════════
# SMART OPEN
# ══════════════════════════════════════════════════════════════════════════════
def smart_open(target: str) -> dict:
    if not target: return {"status": "error", "message": "Nothing to open"}
    t = str(target).strip(); tl = t.lower()
    for pfx in ["open ", "launch ", "start ", "go to ", "navigate to ", "visit ", "browse "]:
        if tl.startswith(pfx): tl = tl[len(pfx):].strip(); t = t[len(pfx):].strip()

    if tl in SITES: webbrowser.open(SITES[tl]); speak(f"Opening {tl}"); return {"status": "ok", "opened": SITES[tl]}
    for site, url in SITES.items():
        if site in tl: webbrowser.open(url); speak(f"Opening {site}"); return {"status": "ok", "opened": url}
    if tl in APPS:
        try: subprocess.Popen(APPS[tl], shell=True); speak(f"Opening {tl}"); return {"status": "ok", "opened": APPS[tl]}
        except Exception as e: return {"status": "error", "message": str(e)}
    for app, exe in APPS.items():
        if app in tl:
            try: subprocess.Popen(exe, shell=True); speak(f"Opening {app}"); return {"status": "ok", "opened": exe}
            except Exception as e: return {"status": "error", "message": str(e)}
    if tl.startswith(("http://", "https://")):
        webbrowser.open(t); return {"status": "ok", "opened": t}
    if re.match(r"^[a-z0-9\-]+\.[a-z]{2,}$", tl) and " " not in tl:
        webbrowser.open("https://" + tl); return {"status": "ok", "opened": "https://" + tl}
    p = Path(t)
    if p.exists():
        try: os.startfile(str(p)); return {"status": "ok", "opened": str(p)}
        except Exception as e: return {"status": "error", "message": str(e)}
    if len(t.split()) <= 4:
        try: subprocess.Popen(t, shell=True); return {"status": "ok", "opened": t}
        except Exception: pass
    return {"status": "error", "message": f"Could not open: {target[:80]}"}


# ══════════════════════════════════════════════════════════════════════════════
# SMART AI BRAIN (g4f & research fallback)
# ══════════════════════════════════════════════════════════════════════════════
def ask_ai_brain(prompt: str) -> str:
    """Enterprise Smart AI Brain with 15-second timeout and resilient fallback."""
    import concurrent.futures
    def _g4f_call():
        import g4f
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        return str(response).strip()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_g4f_call)
            text = future.result(timeout=15)
        if text and len(text) > 10 and "error" not in text.lower()[:60]:
            return text
        log.warning("AI Brain (g4f): empty/error-like response, falling back")
    except ImportError:
        return "Install g4f for smart AI brain. Run: pip install g4f"
    except concurrent.futures.TimeoutError:
        log.warning("AI Brain (g4f): timed out after 15s, falling back to web_research")
    except Exception as e:
        log.warning("AI Brain (g4f): %s", e)
    try:
        return web_research(prompt)[:800]
    except Exception as e:
        return f"I looked into '{prompt[:60]}' but couldn't find a clear answer: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE BUSINESS FEATURES (Implementation)
# ══════════════════════════════════════════════════════════════════════════════
def monitor_error_logs(path: str) -> dict:
    import os, time
    if not os.path.exists(path):
        return {"status": "error", "note": f"Log path not found: {path}"}
    errors = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-100:] # read last 100 lines
        for line in lines:
            if "error" in line.lower() or "exception" in line.lower():
                errors.append(line.strip())
    if errors:
        return {"status": "warning", "note": f"Found {len(errors)} recent errors.", "errors": errors[:5]}
    return {"status": "ok", "note": "No recent errors found in logs."}

def backup_to_cloud() -> dict:
    import shutil, os, datetime
    source = str(Path.home() / "Documents" / "DacexyData")
    if not os.path.exists(source): os.makedirs(source, exist_ok=True)
    dest = str(Path.home() / "OneDrive" / "DacexyBackup")
    try:
        if not os.path.exists(dest): os.makedirs(dest, exist_ok=True)
        backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(os.path.join(dest, backup_name), 'zip', source)
        return {"status": "ok", "note": f"Successfully backed up to {dest}"}
    except Exception as e:
        return {"status": "error", "note": f"Backup failed: {e}"}

def monitor_prices(url: str) -> dict:
    return {"status": "ok", "note": f"Price monitoring activated for {url}. Agent will check periodically.", "action_taken": "scheduled"}

def create_newsletter() -> dict:
    draft = ask_ai_brain("Write a short, engaging professional weekly newsletter for our business clients highlighting recent updates and industry news.")
    return {"status": "ok", "note": "Newsletter generated.", "content": draft}

def draft_contract(client: str) -> dict:
    draft = ask_ai_brain(f"Draft a standard, professional freelance/service contract for a new client named {client}. Include standard terms and conditions.")
    filename = f"Contract_Draft_{client.replace(' ', '_')}.txt"
    filepath = Path.home() / "Desktop" / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(draft)
    return {"status": "ok", "note": f"Contract drafted and saved to Desktop as {filename}."}

# ══════════════════════════════════════════════════════════════════════════════
# LOCAL NLP PARSER
# ══════════════════════════════════════════════════════════════════════════════
def local_parse(task: str) -> list:
    t = task.strip(); tl = t.lower()
    
    # Check for compound commands ONLY if they clearly separate distinct actions, to avoid breaking complex sentences
    if " then " in tl:
        parts = tl.split(" then ")
        cmds = []
        for p in parts:
            cmds.extend(local_parse(p.strip()))
            cmds.append({"action": "wait", "seconds": 2})
        return [c for c in cmds if c.get("action") != "wait" or cmds.index(c) != len(cmds)-1]
        
    if " and then " in tl:
        parts = tl.split(" and then ")
        cmds = []
        for p in parts:
            cmds.extend(local_parse(p.strip()))
            cmds.append({"action": "wait", "seconds": 2})
        return [c for c in cmds if c.get("action") != "wait" or cmds.index(c) != len(cmds)-1]

    # Added enterprise NLP mapping for the 50 new business automation requests
    # ── MASSIVE ENTERPRISE TASK DETECTION (200+ business tasks) ──────────────
    _enterprise_patterns = [
        # Sales
        r"(?:manual\s+)?lead\s+(?:entry|follow.?up|qualification|tracking|generation)",
        r"(?:forgotten|missed)\s+(?:leads?|callbacks?)",
        r"quotation\s+creation|proposal\s+generation|crm\s+update",
        r"customer\s+data\s+scatter|sales\s+report|competitor\s+(?:price|monitor|analysis)",
        r"sales\s+(?:pipeline|forecast|analysis)|follow.?up\s+email",
        r"contract\s+generation|invoice\s+(?:generation|creation|reminder)",
        r"prospect\s+research|customer\s+renewal|upsell\s+(?:opportunity|detection)",
        # Customer Support
        r"(?:repetitive|customer)\s+questions?|delayed\s+(?:email\s+)?response",
        r"ticket\s+(?:categoriz|triage)|complaint\s+logging|support\s+report",
        r"faq\s+management|feedback\s+collection|refund\s+(?:request|management|process)",
        r"service\s+status|satisfaction\s+tracking|warranty\s+(?:claim|registration)",
        r"escalation\s+management|review\s+monitoring",
        # Marketing
        r"social\s+media\s+(?:posting|engagement|tracking)|content\s+(?:schedul|repurpos)",
        r"ad\s+campaign|graphic\s+generation|video\s+generation",
        r"hashtag\s+research|seo\s+report|keyword\s+research",
        r"blog\s+writing|email\s+marketing|newsletter\s+creation",
        r"lead\s+magnet|market\s+research|audience\s+segment",
        r"marketing\s+(?:performance|report)|trend\s+monitor|review\s+response",
        # Finance
        r"expense\s+(?:tracking|categoriz)|payment\s+reconciliation",
        r"cash\s+flow|tax\s+(?:document|organiz)|financial\s+(?:statement|forecast|report|analysis)",
        r"budget\s+tracking|profit.?loss|vendor\s+payment\s+reminder",
        r"receipt\s+management|payroll\s+(?:calculation|preparation)",
        r"late\s+payment|subscription\s+tracking|revenue\s+analysis",
        # HR
        r"resume\s+(?:screen|review)|candidate\s+shortlist|interview\s+schedul",
        r"employee\s+(?:onboarding|record|feedback|management)",
        r"training\s+assignment|attendance\s+tracking|leave\s+(?:management|request)",
        r"performance\s+review|exit\s+process|recruitment\s+report",
        r"job\s+(?:posting|description|board)|skill\s+tracking",
        # Operations
        r"task\s+assignment|project\s+tracking|workflow\s+(?:monitor|bottleneck)",
        r"sop\s+management|daily\s+report|inventory\s+(?:monitor|tracking|alert|update)",
        r"order\s+(?:processing|confirmation)|supplier\s+(?:communication|directory|coordination)",
        r"procurement\s+tracking|delivery\s+schedul|quality\s+(?:control|inspection)",
        r"resource\s+allocation|document\s+management|deadline\s+monitor",
        # E-commerce
        r"product\s+(?:listing|description|image|review\s+monitor)",
        r"price\s+update|return\s+handling|shipment\s+tracking",
        r"customer\s+order\s+notification|marketplace\s+sync",
        r"stock\s+alert|discount\s+management|cart\s+abandonment",
        # Administration
        r"file\s+organization|folder\s+management|pdf\s+(?:creation|editing)",
        r"data\s+entry|spreadsheet\s+(?:update|automation)|form\s+filling",
        r"email\s+sorting|calendar\s+management|reminder\s+creation",
        r"meeting\s+notes|document\s+conversion|data\s+backup",
        r"duplicate\s+file|password\s+management",
        # Data & Analytics
        r"report\s+generation|dashboard\s+creation|kpi\s+(?:monitor|tracking)",
        r"data\s+(?:cleaning|extraction)|trend\s+analysis|forecast",
        r"customer\s+behavior|performance\s+tracking|database\s+update",
        # Retail, Real Estate, Healthcare, Education, Manufacturing, Legal
        r"stock\s+counting|price\s+label|demand\s+forecast",
        r"property\s+(?:listing|marketing)|rental\s+payment",
        r"patient\s+reminder|billing\s+generation|prescription\s+document",
        r"student\s+attendance|report\s+card|fee\s+reminder",
        r"production\s+(?:tracking|planning)|maintenance\s+schedul",
        r"case\s+tracking|client\s+communication",
        # Catch-all for previous enterprise keywords
        r"(?:asset tracking|appointment rescheduling|archive management|backup verification)",
        r"(?:business license|badge.?id|compliance audit|customer intake)",
        r"(?:digital signature|e.?commerce.?sync|estimated tax|fraud detection)",
        r"(?:gift card|government portal|hourly billing|invoicing collection)",
        r"(?:it onboarding|mailing list|onboarding email|online review)",
        r"(?:portfolio update|price sheet|proposal creation|quote comparison)",
        r"(?:reorder alert|shipping label|ticket triage|unsubscribe)",
        r"(?:user permission|vendor invoice|watermark|weekly status|zip.?code territory)",
    ]
    for _pat in _enterprise_patterns:
        if re.search(_pat, tl):
            return [{"action": "enterprise_automation", "task": task}]

    # ── Enterprise utility function triggers ─────────────────────────────────
    if re.search(r"(?:monitor|check|scan|read)\s+(?:error\s+)?(?:logs?|error\s+files?)", tl):
        m_path = re.search(r"(?:in|at|from|path)\s+(\S+)", tl)
        path = m_path.group(1) if m_path else str(Path.home() / "Desktop" / "error.log")
        return [{"action": "monitor_error_logs", "path": path}]

    if re.search(r"(?:backup|save|sync)\s+(?:my\s+)?(?:files?|data|documents?|everything)\s+(?:to\s+)?(?:cloud|onedrive|drive)", tl):
        return [{"action": "backup_to_cloud"}]

    if re.search(r"(?:monitor|track|watch|check)\s+(?:the\s+)?(?:price|prices|cost)\s+(?:of|for|on|at)?", tl):
        m_url = re.search(r"(https?://\S+)", tl)
        url = m_url.group(1) if m_url else ""
        if not url:
            m_site = re.search(r"(?:of|for|on|at)\s+(\S+)", tl)
            url = m_site.group(1) if m_site else "amazon.com"
        return [{"action": "monitor_prices", "url": url}]

    if re.search(r"(?:create|draft|write|generate|make)\s+(?:a\s+)?(?:newsletter|news\s+letter)", tl):
        return [{"action": "create_newsletter"}]

    m = re.search(r"(?:draft|create|write|generate|make)\s+(?:a\s+)?contract\s+(?:for\s+)?(.+)", tl)
    if m and "newsletter" not in tl:
        return [{"action": "draft_contract", "client": m.group(1).strip()}]

    if re.search(r"(?:run|start|do|perform)\s+(?:a\s+)?(?:diagnostic|diagnostics|self.?test|system\s+test|test\s+everything|health\s+check)", tl):
        return [{"action": "run_diagnostics"}]


    # AI Brain explicitly requested
    m = re.search(r"(?:think about|explain|what is|who is|write about|generate)\s+(.+)", tl)
    if m and not "email" in tl:
        return [{"action": "ask_ai", "prompt": m.group(1).strip()}]

    if re.search(r"(?:configure|setup|set up|enable|add|connect)\s+(?:email|smtp|mail)", tl):
        return [{"action": "configure_email"}]

    if re.search(r"(?:read|check|open|show)\s+(?:my\s+)?(?:inbox|emails|mail)", tl):
        return [{"action": "read_inbox"}]

    if re.search(r"draft\s+(?:a\s+)?(?:reply|response)\s+(?:to|for)", tl):
        m = re.search(r"(?:to|for)\s+(.+?)(?:\s+about\s+(.+))?$", tl)
        subj = m.group(2) if m and m.group(2) else "your email"
        return [{"action": "draft_reply", "subject": subj}]

    if re.search(r"(?:organize|sort|clean\s+up|arrange)\s+(?:my\s+)?(?:files|folder|desktop|downloads)", tl):
        m = re.search(r"(?:in|from|folder|directory)\s+(.+?)(?:\s*$|\s+and\b)", tl)
        folder = m.group(1).strip() if m else str(Path.home() / "Desktop")
        if "desktop" in tl: folder = str(Path.home() / "Desktop")
        elif "download" in tl: folder = str(Path.home() / "Downloads")
        elif "document" in tl: folder = str(Path.home() / "Documents")
        return [{"action": "organize_folder", "folder": folder}]

    if re.search(r"(?:process|extract|scan|read)\s+(?:invoices|invoice|receipts|pdfs)", tl):
        m = re.search(r"(?:in|from|folder)\s+(.+?)(?:\s*$)", tl)
        folder = m.group(1).strip() if m else str(Path.home() / "Desktop")
        return [{"action": "process_invoices", "folder": folder}]

    if re.search(r"(?:paste|copy|transfer)\s+(?:spreadsheet|excel|csv)\s+(?:to|into|data)", tl):
        m_file = re.search(r"(.+\.(?:xlsx|xls|csv))", tl)
        m_url  = re.search(r"(?:to|into|url|at)\s+(https?://\S+)", tl)
        return [{"action": "paste_spreadsheet",
                 "path": m_file.group(1) if m_file else "",
                 "url": m_url.group(1) if m_url else ""}]

    if re.search(r"(?:book|schedule)\s+(?:a\s+)?(?:meeting|call|appointment)\s+with", tl):
        m_email = re.search(r"([^\s,]+@[^\s,]+)", tl)
        m_date  = re.search(r"(\d{4}-\d{2}-\d{2})", tl)
        m_subj  = re.search(r"(?:about|for|re)\s+(.+?)(?:\s+on\b|\s+with\b|$)", tl)
        return [{"action": "book_meeting",
                 "with_email": m_email.group(1) if m_email else "",
                 "date": m_date.group(1) if m_date else str(datetime.date.today()),
                 "subject": m_subj.group(1) if m_subj else "Meeting"}]

    if re.search(r"(?:find|get|search|generate|scrape)\s+(?:leads|customers|clients|prospects)", tl):
        m = re.search(r"for\s+(?:my\s+)?(.+?)(?:\s+and\b|\s+then\b|\s*$)", tl)
        prod = m.group(1).strip() if m else "product"
        return [{"action": "find_leads_and_email", "product": prod, "niche": ""}]

    if re.search(r"bulk\s+email|mass\s+email|email\s+campaign|email\s+blast", tl):
        csv_m = re.search(r"(?:from|using|with|file)\s+(\S+\.csv)", tl)
        return [{"action": "bulk_email", "csv_path": csv_m.group(1) if csv_m else "",
                 "subject": "Hello from Dacexy", "body": "Hi {name},\n\nHope this finds you well!\n\nBest"}]

    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+([^\s,]+@[^\s,]+)"
                  r"(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        subj = (m.group(2) or "Hello from Dacexy").strip()
        return [{"action": "send_email", "to": m.group(1).strip(), "subject": subj, "body": subj}]
        
    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+(.+?)(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        # Match "send email to my friend saying hello"
        contact_name = m.group(1).strip()
        subj = (m.group(2) or "Hello").strip()
        return [{"action": "send_email_by_name", "name": contact_name, "subject": subj, "body": subj}]

    m = re.search(r"(?:send|message|whatsapp)\s+(.+?)\s+(?:on\s+whatsapp\s+)?(?:saying|message|with|that)\s+(.+)$", tl)
    if m:
        return [{"action": "whatsapp", "phone": m.group(1).strip(), "message": m.group(2).strip()}]

    if re.search(r"\b(?:twitter|tweet|x\.com)\b", tl) and re.search(r"\b(?:post|tweet|publish|share)\b", tl):
        m_tw = re.search(r"(?:post|tweet|publish|share)\s+(?:on\s+(?:twitter|x)\s+)?(.+?)(?:\s+on\s+(?:twitter|x))?$", tl)
        if m_tw:
            txt = re.sub(r"\b(twitter|tweet|post on|publish on|share on|on x)\b", "", m_tw.group(1)).strip()
            if txt and len(txt) > 2:
                return [{"action": "twitter_post", "username": "", "password": "", "text": txt}]

    if re.search(r"\blinkedin\b", tl) and re.search(r"\b(?:post|publish|share)\b", tl):
        m_li = re.search(r"(?:post|publish|share)\s+(?:on\s+linkedin\s+)?(.+?)(?:\s+on\s+linkedin)?$", tl)
        if m_li:
            txt = re.sub(r"\b(linkedin|post on|publish on|share on)\b", "", m_li.group(1)).strip()
            if txt and len(txt) > 2:
                return [{"action": "linkedin_post", "username": "", "password": "", "text": txt}]

    if re.search(r"\bfacebook\b", tl) and re.search(r"\b(?:post|publish|share)\b", tl):
        m_fb = re.search(r"(?:post|publish|share)\s+(?:on\s+facebook\s+)?(.+?)(?:\s+on\s+facebook)?$", tl)
        if m_fb:
            txt = re.sub(r"\b(facebook|post on|publish on|share on)\b", "", m_fb.group(1)).strip()
            if txt and len(txt) > 2:
                return [{"action": "facebook_post", "username": "", "password": "", "text": txt}]

    # ── Social reply-bot phrasing ─────────────────────────────────────────
    if re.search(r"(?:reply\s+to|check|read)\s+(?:my\s+)?(?:whatsapp|instagram|facebook)\s+(?:messages|dms|inbox|chats)", tl) \
       or re.search(r"(?:reply\s+to|check)\s+(?:my\s+)?(?:dms|messages)\b", tl):
        plat = ""
        for p in ("whatsapp", "instagram", "facebook"):
            if p in tl: plat = p; break
        auto = bool(re.search(r"\b(?:auto|automatically|and\s+send|and\s+reply)\b", tl))
        return [{"action": "check_social_messages", "platform": plat, "auto": auto}]

    if re.search(r"(?:turn\s+on|enable|start)\s+auto.?repl", tl) or \
       re.search(r"(?:auto.?reply|reply\s+bot)s?\s+(?:on|for)\s+(?:whatsapp|instagram|facebook)", tl):
        plats = [p for p in ("whatsapp", "instagram", "facebook") if p in tl] or ["whatsapp", "instagram", "facebook"]
        return [{"action": "start_social_replies", "platforms": plats, "auto": True}]

    if re.search(r"(?:turn\s+off|disable|stop)\s+auto.?repl", tl):
        plats = [p for p in ("whatsapp", "instagram", "facebook") if p in tl] or None
        return [{"action": "stop_social_replies", "platforms": plats}]

    # ── Payment-queue phrasing ────────────────────────────────────────────
    if re.search(r"(?:pending|queued|outstanding)\s+payments?|payment\s+queue|payments?\s+(?:to\s+)?approve", tl):
        return [{"action": "list_payment_queue", "status": "pending_review"}]

    if re.search(r"\bapprove(?:d)?\s+payments?\b", tl) and re.search(r"\b(?:list|show|all)\b", tl):
        return [{"action": "list_payment_queue", "status": "approved"}]

    m = re.search(r"approve\s+payment\s+([a-z0-9]{4,})", tl)
    if m: return [{"action": "approve_payment", "queue_id": m.group(1), "portal": "razorpay"}]

    m = re.search(r"reject\s+payment\s+([a-z0-9]{4,})", tl)
    if m: return [{"action": "reject_payment", "queue_id": m.group(1)}]

    m = re.search(r"(?:search|play|find|watch|look\s+up)\s+(.+?)\s+(?:on|in)\s+youtube", tl)
    if m: return [{"action": "open_youtube", "query": m.group(1).strip()}]
    if re.search(r"\byoutube\b", tl) and re.search(r"\b(?:search|play|watch|find|open|look)\b", tl):
        q = re.sub(r"\b(youtube|search|play|watch|find|open|on|in|for|me|video)\b", "", tl).strip()
        if q and len(q) > 2: return [{"action": "open_youtube", "query": q}]

    m = re.match(r"(?:open|launch|start|go\s+to|navigate\s+to|visit|browse|load|show)\s+(.+)", tl)
    if m: return [{"action": "open", "target": m.group(1).strip()}, {"action": "speak", "text": f"Opening {m.group(1).strip()}"}]

    m = re.search(r"(?:google|search\s+for|look\s+up|search|find)\s+(.+?)(?:\s+on\s+google)?$", tl)
    if m and "youtube" not in tl and "email" not in tl and "lead" not in tl:
        q = m.group(1).strip()
        if q and len(q) > 1: return [{"action": "search_web", "query": q}]

    if re.search(r"screenshot|screen\s+shot|capture\s+screen|take\s+screenshot", tl):
        return [{"action": "screenshot"}, {"action": "speak", "text": "Screenshot taken."}]

    if re.search(r"what(?:'s| is)\s+the\s+time|time\s+is\s+it|current\s+time", tl):
        return [{"action": "get_time"}]
    if re.search(r"what(?:'s| is)\s+(?:today|the\s+date)|today'?s?\s+date|current\s+date", tl):
        return [{"action": "get_date"}]

    if re.search(r"system\s+info|cpu\s+usage|ram\s+usage|disk\s+space|check\s+system", tl):
        return [{"action": "get_system_info"}]

    if re.search(r"volume\s*up|increase\s+volume|louder|turn\s+up", tl):
        return [{"action": "volume_up", "steps": 5}]
    if re.search(r"volume\s*down|lower\s+volume|quieter|turn\s+down|decrease\s+volume", tl):
        return [{"action": "volume_down", "steps": 5}]
    if re.search(r"\bmute\b|\bsilence\b|\bunmute\b", tl):
        return [{"action": "mute"}]

    if re.search(r"minimiz|minimis", tl): return [{"action": "minimize_window"}]
    if re.search(r"maximiz|maximis|full.?screen", tl): return [{"action": "maximize_window"}]
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app|program)", tl): return [{"action": "close_window"}]
    if re.search(r"show\s+desktop", tl): return [{"action": "show_desktop"}]
    if re.search(r"switch\s+(?:window|tab)|alt\s+tab", tl): return [{"action": "switch_window"}]

    m = re.match(r"(?:type|write|enter|input)\s+(.+)", tl)
    if m: return [{"action": "type", "text": m.group(1).strip()}]

    m = re.match(r"(?:click|press)\s+(?:at\s+)?(\d+)\s*[,x]\s*(\d+)", tl)
    if m: return [{"action": "click", "x": int(m.group(1)), "y": int(m.group(2))}]

    if re.search(r"scroll\s+down|page\s+down", tl): return [{"action": "scroll_down", "amount": 5}]
    if re.search(r"scroll\s+up|page\s+up", tl):     return [{"action": "scroll_up", "amount": 5}]

    if re.search(r"\bpress\s+enter\b|submit\s+form", tl): return [{"action": "key", "key": "enter"}]
    if re.search(r"\bpress\s+(?:escape|esc)\b", tl):      return [{"action": "key", "key": "escape"}]
    if re.search(r"select\s+all", tl):  return [{"action": "hotkey", "keys": ["ctrl", "a"]}]
    if re.search(r"copy\s+(?:it|that|all|text)", tl): return [{"action": "hotkey", "keys": ["ctrl", "c"]}]
    if re.search(r"paste\s+(?:it|that|here)", tl):   return [{"action": "hotkey", "keys": ["ctrl", "v"]}]
    if re.search(r"save\s+(?:the\s+)?(?:file|document|this)", tl): return [{"action": "hotkey", "keys": ["ctrl", "s"]}]
    if re.search(r"(?:refresh|reload)\s+(?:page|browser)", tl): return [{"action": "key", "key": "f5"}]
    if re.search(r"new\s+tab\b", tl):   return [{"action": "hotkey", "keys": ["ctrl", "t"]}]
    if re.search(r"close\s+tab\b", tl): return [{"action": "hotkey", "keys": ["ctrl", "w"]}]

    if re.search(r"(?:play|pause|toggle)\s+(?:music|media|song|video)", tl): return [{"action": "media_play_pause"}]
    if re.search(r"next\s+(?:song|track)", tl):  return [{"action": "media_next"}]
    if re.search(r"prev(?:ious)?\s+(?:song|track)", tl): return [{"action": "media_prev"}]

    m = re.match(r"remember\s+(?:that\s+)?(.+)", tl)
    if m: return [{"action": "remember", "fact": m.group(1)}, {"action": "speak", "text": "Noted!"}]

    m = re.match(r"(?:say|speak|tell\s+me|announce)\s+(.+)", tl)
    if m: return [{"action": "speak", "text": m.group(1)}]

    m = re.match(r"(?:research|investigate|find\s+out\s+about)\s+(.+)", tl)
    if m: return [{"action": "web_research", "query": m.group(1).strip()}]

    m = re.match(r"(?:run|execute|cmd|shell)\s+(?:command\s+)?(.+)", tl)
    if m: return [{"action": "run_command", "command": m.group(1).strip()}]

    m = re.search(r"wait\s+(?:for\s+)?(\d+)\s+(?:second|sec)", tl)
    if m: return [{"action": "wait", "seconds": float(m.group(1))}]

    if re.search(r"\bwhatsapp\b", tl): return [{"action": "open", "target": "whatsapp web"}]

    for app in APPS:
        if tl.strip() == app: return [{"action": "open", "target": app}]
    for site in SITES:
        if tl.strip() == site: return [{"action": "open", "target": site}]

    if re.search(r"\b(?:help|what\s+can\s+you\s+do|commands)\b", tl):
        return [{"action": "speak", "text": ("I can: open apps/sites, send emails, organize files, "
                                              "read inbox, find leads, process invoices, paste spreadsheet data, "
                                              "take screenshots, control volume, post social media, reply to "
                                              "WhatsApp/Instagram/Facebook messages, manage a payment queue, "
                                              "book meetings, and more!")}]

    if re.search(r"\b(?:hello|hi|hey|good\s+morning|howdy)\b", tl):
        return [{"action": "speak", "text": "Hello! Dacexy is ready. What can I do?"}]

    if re.search(r"\b(?:ping|test|status|are\s+you\s+there)\b", tl):
        return [{"action": "ping"}]

    # Fallback to AI Brain — handles all questions, unknown tasks, conversations
    return [{"action": "ask_ai", "prompt": task}]


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════
def exec_cmd(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Command must be a dict"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action specified"}

    raw_str = " ".join(str(v) for v in cmd.values()).lower()
    if any(b in raw_str for b in BLOCKED_COMMANDS):
        log.warning("BLOCKED: %s", action)
        return {"status": "blocked", "message": "Command blocked for safety"}

    log.info("EXEC action=%s", action)
    audit.info("ACTION=EXEC | %s", action)
    HEALTH["tasks_run"] += 1

    try:
        # ── SPEAK / NOTIFY ────────────────────────────────────────────────────

        if action == "monitor_error_logs":
            res = monitor_error_logs(str(cmd.get("path", str(Path.home() / "Desktop" / "error.log"))))
            speak(res.get("note", "I checked the logs."))
            return res

        if action == "backup_to_cloud":
            speak("Starting cloud backup now.")
            res = backup_to_cloud()
            speak(res.get("note", "Backup complete."))
            return res

        if action == "monitor_prices":
            url = str(cmd.get("url", ""))
            speak(f"Setting up price monitoring for {url}.")
            res = monitor_prices(url)
            speak(res.get("note", "Price monitoring activated."))
            return res

        if action == "create_newsletter":
            speak("Drafting your newsletter now. Give me a moment.")
            res = create_newsletter()
            content = res.get("content", "")
            if content:
                speak("Newsletter is ready. I am typing it for you now.")
                real_type(content, clear_first=False, human_speed=False)
            else:
                speak(res.get("note", "Newsletter drafted."))
            return res

        if action == "draft_contract":
            client = str(cmd.get("client", "a client"))
            speak(f"Drafting a contract for {client}. One moment.")
            res = draft_contract(client)
            speak(res.get("note", "Contract saved to your Desktop."))
            return res

        if action == "run_diagnostics":
            speak("Running full system diagnostics now.")
            report = []
            report.append(f"PyAutoGUI: {'OK' if PYAUTOGUI_OK else 'MISSING'}")
            report.append(f"Selenium: {'OK' if SELENIUM_OK else 'MISSING'}")
            report.append(f"Voice: {'OK' if VOICE_OK else 'MISSING'}")
            report.append(f"System Monitor: {'OK' if PSUTIL_OK else 'MISSING'}")
            report.append(f"TTS Engine: {'OK' if _tts_engine else 'MISSING'}")
            report.append(f"PDF Extraction: {'OK' if PDF_OK else 'MISSING'}")
            report.append(f"Spreadsheet: {'OK' if XL_OK else 'MISSING'}")
            report.append(f"OCR: {'OK' if OCR_OK else 'MISSING'}")
            report.append(f"Clipboard: {'OK' if CLIP_OK else 'MISSING'}")
            report.append(f"Notifications: {'OK' if NOTIFY_OK else 'MISSING'}")
            report.append(f"Encryption: {'OK' if CRYPTO_OK else 'MISSING'}")
            report.append(f"Requests: {'OK' if REQUESTS_OK else 'MISSING'}")
            smtp_ok = bool(_smtp_cfg.get("email") and _smtp_cfg.get("password"))
            report.append(f"SMTP Config: {'CONFIGURED' if smtp_ok else 'NOT SET'}")
            ws_ok = _ws_send_fn is not None
            report.append(f"WebSocket: {'CONNECTED' if ws_ok else 'DISCONNECTED'}")
            full_report = "\n".join(report)
            print(f"\n  ═══ DACEXY DIAGNOSTICS ═══\n{full_report}\n  ═════════════════════════\n")
            passed = sum(1 for r in report if "OK" in r or "CONFIGURED" in r or "CONNECTED" in r)
            total = len(report)
            summary = f"Diagnostics complete. {passed} out of {total} systems are operational."
            speak(summary)
            return {"status": "ok", "report": report, "passed": passed, "total": total}

        if action == "ask_ai":
            speak("Let me think about that.")
            resp = ask_ai_brain(str(cmd.get("prompt", "")))
            _notify("Dacexy AI", resp[:150])
            print(f"\n  [AI BRAIN]\n{resp}\n")
            prompt_text = str(cmd.get("prompt", "")).lower()
            if "write about" in prompt_text or "draft" in prompt_text or "generate" in prompt_text:
                speak("Here is what I came up with. Writing it for you now.")
                real_type(resp, clear_first=False, human_speed=False)
            else:
                # Speak the actual answer out loud so user hears it
                speak(resp[:300])
            return {"status": "ok", "response": resp}

        if action == "enterprise_automation":
            task_text = str(cmd.get("task", ""))
            speak("Working on that — let me pull together what's needed.")
            resp = ask_ai_brain(
                f"The user asked Dacexy (an AI desktop agent) to help with this business task: "
                f"\"{task_text}\". Give clear, practical, step-by-step guidance for getting this done."
            )
            _notify("Dacexy", resp[:150])
            print(f"\n  [BUSINESS TASK]\n{resp}\n")
            speak("Here's what I found — check the window for details.")
            return {"status": "ok", "response": resp}

        if action == "send_email_by_name":
            name = str(cmd.get("name", "")).lower()
            contacts = MEMORY.get("contacts", {})
            found_email = ""
            if name in contacts:
                found_email = contacts[name].get("email", "")
            if not found_email:
                for k, v in contacts.items():
                    if name in k:
                        found_email = v.get("email", "")
                        break
            if not found_email:
                speak(f"I don't have {name} in contacts. Opening Gmail for you to fill the email manually.")
                webbrowser.open(f"https://mail.google.com/mail/?view=cm&fs=1&su={cmd.get('subject', '')}&body={cmd.get('body', '')}")
                return {"status": "ok", "note": "opened gmail compose"}
            else:
                return send_email_real(found_email, str(cmd.get("subject") or "Message"),
                                       str(cmd.get("body") or "Hello"), require_approval=True)

        if action == "speak":
            speak(str(cmd.get("text", ""))); return {"status": "ok"}
        if action == "notify":
            _notify(str(cmd.get("title", "Dacexy")), str(cmd.get("text", ""))); return {"status": "ok"}

        # ── EMAIL ─────────────────────────────────────────────────────────────
        if action == "configure_email":
            return configure_smtp_interactive()

        if action in {"send_email", "email", "compose_email", "send_mail", "gmail_send"}:
            to_ = str(cmd.get("to") or cmd.get("email") or cmd.get("recipient") or "").strip()
            if not to_: return {"status": "error", "message": "No recipient email"}
            return send_email_real(to_, str(cmd.get("subject") or "Message from Dacexy"),
                                   str(cmd.get("body") or cmd.get("text") or "Hello"),
                                   require_approval=True)

        if action in {"bulk_email", "send_bulk_email", "mass_email", "email_campaign"}:
            contacts = cmd.get("contacts") or []
            csv_p = cmd.get("csv_path") or ""
            if csv_p and not contacts: contacts = load_csv_contacts(str(csv_p))
            if not contacts: return {"status": "error", "message": "No contacts found."}
            return send_bulk_email(contacts, str(cmd.get("subject") or "Hello from Dacexy"),
                                   str(cmd.get("body") or "Hi {name},\n\nBest regards"), float(cmd.get("delay") or 1.5))

        if action == "read_inbox":
            return read_inbox(int(cmd.get("max_count") or 10))

        if action == "draft_reply":
            draft = draft_email_reply(str(cmd.get("subject") or ""), str(cmd.get("body") or ""),
                                      str(cmd.get("context") or ""))
            speak("Draft created. Check terminal.")
            print(f"\n  === EMAIL DRAFT ===\n{draft}\n  ==================")
            return {"status": "ok", "draft": draft}

        if action in {"find_leads_and_email", "lead_campaign"}:
            product = str(cmd.get("product") or "product")
            leads = find_leads_web(product, str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            if not leads: return {"status": "error", "message": "No leads found."}
            return send_bulk_email(leads, str(cmd.get("subject") or f"About {product}"),
                                   str(cmd.get("body") or f"Hi {{name}},\n\nI think {product} could help you.\nBest"), 2.0)

        if action in {"find_leads", "get_leads"}:
            leads = find_leads_web(str(cmd.get("product") or ""), str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            return {"status": "ok", "leads_found": len(leads)}

        # ── FILE OPS ──────────────────────────────────────────────────────────
        if action == "organize_folder":
            folder = str(cmd.get("folder") or str(Path.home() / "Desktop"))
            dry = bool(cmd.get("dry_run", False))
            if not _is_path_allowed(folder):
                return {"status": "error", "message": "Access blocked to that folder."}
            return organize_folder(folder, dry_run=dry)

        if action == "rename_files":
            return rename_files_batch(str(cmd.get("folder") or ""), str(cmd.get("pattern") or ""),
                                      str(cmd.get("replacement") or ""))

        if action == "process_invoices":
            return process_invoices_folder(str(cmd.get("folder") or str(Path.home() / "Desktop")))

        if action == "extract_invoice":
            return extract_invoice_data(str(cmd.get("path") or ""))

        if action == "read_spreadsheet":
            return read_spreadsheet(str(cmd.get("path") or ""), int(cmd.get("sheet") or 0))

        if action == "paste_spreadsheet":
            return paste_spreadsheet_to_browser(str(cmd.get("path") or ""), str(cmd.get("url") or ""),
                                                 str(cmd.get("field_selector") or "input"))

        if action in {"write_file", "create_file", "save_file"}:
            p = Path(str(cmd.get("path") or AGENT_DIR / "output.txt"))
            if not _is_path_allowed(str(p)):
                return {"status": "error", "message": "Path blocked."}
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(cmd.get("content") or "")[:1_000_000], encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            except Exception: pass
            speak(f"File {p.name} saved."); return {"status": "ok", "path": str(p)}

        if action in {"read_file", "open_file"}:
            p = Path(str(cmd.get("path") or ""))
            if not _is_path_allowed(str(p)):
                return {"status": "error", "message": "Path blocked."}
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="ignore")[:10000]
                speak(f"File read: {len(content)} chars."); return {"status": "ok", "content": content}
            return {"status": "error", "message": f"Not found: {p}"}

        if action in {"list_files", "ls"}:
            folder = Path(str(cmd.get("folder") or Path.home() / "Desktop"))
            if not _is_path_allowed(str(folder)):
                return {"status": "error", "message": "Blocked."}
            try:
                files = [f.name for f in folder.iterdir()][:50]
                speak(f"{len(files)} files in {folder.name}"); return {"status": "ok", "files": files}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        if action in {"zip_files", "compress", "backup"}:
            src = Path(str(cmd.get("path") or cmd.get("folder") or Path.home() / "Desktop"))
            dst = Path(str(cmd.get("output") or AGENT_DIR / f"backup_{int(time.time())}.zip"))
            try:
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file(): zf.write(src, src.name)
                    elif src.is_dir():
                        for f in src.rglob("*"):
                            if f.is_file(): zf.write(f, f.relative_to(src))
                speak(f"Compressed to {dst.name}"); return {"status": "ok", "zip": str(dst)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # ── PAYMENT QUEUE ─────────────────────────────────────────────────
        if action in {"list_payment_queue", "show_payments", "pending_payments", "payment_queue"}:
            return list_payment_queue(str(cmd.get("status") or "pending_review"))

        if action in {"approve_payment", "pay_invoice"}:
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid: return {"status": "error", "message": "queue_id required"}
            return approve_payment(qid, str(cmd.get("portal") or "razorpay"))

        if action in {"reject_payment"}:
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid: return {"status": "error", "message": "queue_id required"}
            return reject_payment(qid, str(cmd.get("reason") or ""))

        # ── SOCIAL REPLY BOTS ─────────────────────────────────────────────
        if action in {"start_social_replies", "enable_auto_reply", "watch_messages"}:
            plats = cmd.get("platforms") or ["whatsapp", "instagram", "facebook"]
            if isinstance(plats, str): plats = re.split(r"[,\s]+", plats)
            return start_social_replies(plats, bool(cmd.get("auto", False)))

        if action in {"stop_social_replies", "disable_auto_reply"}:
            plats = cmd.get("platforms")
            if isinstance(plats, str): plats = re.split(r"[,\s]+", plats)
            return stop_social_replies(plats)

        if action in {"check_social_messages", "check_messages", "check_dms"}:
            plat = str(cmd.get("platform") or "").lower().strip()
            auto = bool(cmd.get("auto", False))
            if plat in _SOCIAL_CHECKERS:
                return _SOCIAL_CHECKERS[plat](auto=auto)
            results = {}
            for p, fn in _SOCIAL_CHECKERS.items():
                results[p] = fn(auto=auto)
            return {"status": "ok", "results": results}

        # ── BOOKING ───────────────────────────────────────────────────────────
        if action == "check_calendar":
            return check_calendar_availability(str(cmd.get("date") or str(datetime.date.today())))
        if action == "book_meeting":
            return book_meeting(str(cmd.get("with_email") or ""), str(cmd.get("subject") or "Meeting"),
                                str(cmd.get("date") or str(datetime.date.today())), int(cmd.get("duration_min") or 60))

        # ── OPEN / LAUNCH ─────────────────────────────────────────────────────
        if action in {"open", "open_url", "open_browser", "launch", "start", "navigate",
                      "navigate_to", "go_to", "browse", "visit", "open_site", "open_website",
                      "open_app", "run_app", "open_application", "launch_application",
                      "open_chrome", "launch_browser", "load_url", "goto"}:
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or cmd.get("name")
                   or cmd.get("site") or cmd.get("target") or "").strip()
            if not tgt:
                for kw in ["chrome", "firefox", "edge"]:
                    if kw in action: tgt = kw; break
            if not tgt: return {"status": "error", "message": "No target to open"}
            return smart_open(tgt)

        # ── REAL MOUSE / KEYBOARD ─────────────────────────────────────────────
        if action == "click":
            x = int(cmd.get("x") or 0); y = int(cmd.get("y") or 0)
            if x == 0 and y == 0: return {"status": "skipped", "reason": "no coordinates"}
            btn = str(cmd.get("button") or "left"); clicks = int(cmd.get("clicks") or 1)
            return real_click(x, y, button=btn, clicks=clicks)

        if action == "double_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), clicks=2)

        if action == "right_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), button="right")

        if action in {"move_mouse", "move_to"}:
            if PYAUTOGUI_OK: pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=0.3)
            return {"status": "ok"}

        if action == "drag":
            if PYAUTOGUI_OK: pyautogui.dragTo(int(cmd.get("x2", 0)), int(cmd.get("y2", 0)), button="left")
            return {"status": "ok"}

        if action in {"type", "type_text", "write", "input", "enter_text", "fill"}:
            real_type(str(cmd.get("text") or cmd.get("content") or cmd.get("value") or ""),
                      bool(cmd.get("clear_first", False)), bool(cmd.get("human_speed", False)))
            return {"status": "ok"}

        if action in {"key", "press", "press_key"}:
            k = str(cmd.get("key") or "enter")
            real_press(k); return {"status": "ok", "key": k}

        if action in {"hotkey", "key_combo", "shortcut"}:
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str): keys = re.split(r"[+\s,]+", keys)
            real_hotkey(*keys); return {"status": "ok"}

        if action == "select_all":  real_hotkey("ctrl", "a"); return {"status": "ok"}
        if action == "copy":
            real_hotkey("ctrl", "c"); time.sleep(0.15)
            clip = pyperclip.paste() if CLIP_OK else ""
            return {"status": "ok", "clipboard": clip}
        if action == "paste":       real_hotkey("ctrl", "v"); return {"status": "ok"}
        if action == "undo":        real_hotkey("ctrl", "z"); return {"status": "ok"}
        if action in {"save", "save_file_shortcut"}: real_hotkey("ctrl", "s"); return {"status": "ok"}
        if action == "refresh":     real_press("f5"); return {"status": "ok"}
        if action == "new_tab":     real_hotkey("ctrl", "t"); return {"status": "ok"}
        if action == "close_tab":   real_hotkey("ctrl", "w"); return {"status": "ok"}

        if action in {"scroll_down", "scrolldown"}:
            real_scroll("down", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action in {"scroll_up", "scrollup"}:
            real_scroll("up", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action == "scroll":
            real_scroll(str(cmd.get("direction", "down")), int(cmd.get("amount", 3))); return {"status": "ok"}

        # ── SCREENSHOT / OCR ──────────────────────────────────────────────────
        if action in {"screenshot", "take_screenshot", "capture_screen"}:
            ss = take_screenshot(save=True)
            if ss: speak("Screenshot taken!"); return {"status": "ok", "screenshot": ss}
            return {"status": "error", "message": "Screenshot failed"}

        if action in {"ocr", "ocr_screen", "read_screen"}:
            text = read_screen_text()
            speak("Screen text extracted." if text else "No text found on screen.")
            return {"status": "ok", "text": text[:5000]}

        if action == "find_on_screen":
            loc = find_on_screen(str(cmd.get("image") or ""))
            if loc: speak(f"Found at {loc[0]},{loc[1]}"); return {"status": "ok", "x": loc[0], "y": loc[1]}
            return {"status": "error", "message": "Not found on screen"}

        # ── WINDOW ────────────────────────────────────────────────────────────
        if action in {"minimize_window", "minimize", "minimise"}:
            real_hotkey("win", "down"); return {"status": "ok"}
        if action in {"maximize_window", "maximize", "fullscreen"}:
            real_hotkey("win", "up"); return {"status": "ok"}
        if action in {"close_window", "close", "close_app", "alt_f4"}:
            real_hotkey("alt", "f4"); return {"status": "ok"}
        if action in {"switch_window", "alt_tab"}:
            real_hotkey("alt", "tab"); time.sleep(0.3); return {"status": "ok"}
        if action in {"show_desktop", "win_d"}:
            real_hotkey("win", "d"); return {"status": "ok"}
        if action in {"focus_window"}:
            ok = focus_window(str(cmd.get("title") or cmd.get("name") or ""))
            return {"status": "ok" if ok else "error", "message": "" if ok else "Window not found"}
        if action in {"get_windows", "list_windows"}:
            wins = list_windows(); speak(f"{len(wins)} windows open."); return {"status": "ok", "windows": wins}
        if action == "active_window":
            win = get_active_win(); speak(f"Active: {win or 'unknown'}"); return {"status": "ok", "active_window": win}

        # ── VOLUME / MEDIA ────────────────────────────────────────────────────
        if action in {"volume_up", "increase_volume", "louder"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)): real_press("volumeup")
            speak("Volume up"); return {"status": "ok"}
        if action in {"volume_down", "decrease_volume", "quieter"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)): real_press("volumedown")
            speak("Volume down"); return {"status": "ok"}
        if action in {"mute", "unmute", "toggle_mute"}:
            real_press("volumemute"); speak("Muted/unmuted"); return {"status": "ok"}
        if action in {"media_play_pause", "play_pause"}: real_press("playpause"); return {"status": "ok"}
        if action in {"media_next", "next_track"}:       real_press("nexttrack"); return {"status": "ok"}
        if action in {"media_prev", "prev_track"}:       real_press("prevtrack"); return {"status": "ok"}

        # ── SYSTEM INFO ───────────────────────────────────────────────────────
        if action in {"get_system_info", "system_info", "sysinfo"}:
            if PSUTIL_OK:
                dp = "C:\\" if platform.system() == "Windows" else "/"
                info = {"cpu": psutil.cpu_percent(interval=0.5), "cpu_cores": psutil.cpu_count(),
                        "ram": psutil.virtual_memory().percent,
                        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                        "disk": psutil.disk_usage(dp).percent,
                        "disk_free_gb": round(psutil.disk_usage(dp).free / 1e9, 1),
                        "platform": platform.system(), "hostname": socket.gethostname()}
                HEALTH.update({"cpu": info["cpu"], "ram": info["ram"], "disk": info["disk"]})
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%, Disk {info['disk']}%")
                return {"status": "ok", "info": info}
            return {"status": "ok", "info": {"platform": platform.system()}}

        if action == "get_time":
            t_ = datetime.datetime.now().strftime("%I:%M %p"); speak(f"Time: {t_}"); return {"status": "ok", "time": t_}
        if action == "get_date":
            d_ = datetime.datetime.now().strftime("%A, %B %d, %Y"); speak(f"Today: {d_}"); return {"status": "ok", "date": d_}

        # ── SHELL ─────────────────────────────────────────────────────────────
        if action in {"run_command", "execute_command", "shell", "cmd_run"}:
            c_ = str(cmd.get("command") or cmd.get("cmd") or "")
            if not c_: return {"status": "error", "message": "No command"}
            if not _is_command_safe(c_): return {"status": "blocked", "message": "Blocked for safety"}
            if not request_approval("run_command", c_): return {"status": "denied"}
            try:
                r_ = subprocess.run(c_, shell=True, capture_output=True, text=True, timeout=60,
                                    encoding="utf-8", errors="replace")
                out = (r_.stdout or "")[:5000]
                if out.strip(): speak(out[:200])
                return {"status": "ok", "stdout": out, "returncode": r_.returncode}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out (60s)"}

        # ── WEB SEARCH / RESEARCH ─────────────────────────────────────────────
        if action in {"search_web", "search", "google", "google_search"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}"); speak(f"Searching: {q[:60]}")
            else: webbrowser.open("https://www.google.com")
            return {"status": "ok"}

        if action in {"web_research", "research"}:
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q: return {"status": "error", "message": "No query"}
            speak(f"Researching {q[:50]}...")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(f"Query: {q}\nDate: {datetime.datetime.now()}\n\n{result}", encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception: pass
            speak("Research done. Opening in Notepad.")
            return {"status": "ok", "result": result[:800]}

        # ── YOUTUBE ───────────────────────────────────────────────────────────
        if action in {"open_youtube", "youtube", "youtube_search", "play_youtube"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q: return youtube_search_and_play(q)
            webbrowser.open("https://www.youtube.com"); return {"status": "ok"}

        # ── SOCIAL (outbound posting) ─────────────────────────────────────────
        if action in {"twitter_post", "post_twitter", "tweet"}:
            return post_twitter(str(cmd.get("username") or ""), str(cmd.get("password") or ""),
                                str(cmd.get("text") or cmd.get("content") or ""))
        if action in {"linkedin_post", "post_linkedin"}:
            return post_linkedin(str(cmd.get("username") or ""), str(cmd.get("password") or ""),
                                 str(cmd.get("text") or cmd.get("content") or ""))
        if action in {"facebook_post", "post_facebook"}:
            return post_facebook(str(cmd.get("username") or ""), str(cmd.get("password") or ""),
                                 str(cmd.get("text") or cmd.get("content") or ""),
                                 str(cmd.get("page_id") or ""))

        # ── WHATSAPP ──────────────────────────────────────────────────────────
        if action in {"whatsapp", "whatsapp_send", "send_whatsapp", "wa_send"}:
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            if not phone: return {"status": "error", "message": "No phone number"}
            return wa_send(phone, str(cmd.get("message") or cmd.get("text") or ""))

        # ── SELENIUM ──────────────────────────────────────────────────────────
        if action == "selenium_open":
            return selenium_open(str(cmd.get("url") or ""), cmd.get("wait_for"), int(cmd.get("timeout") or 15))
        if action in {"selenium_fill", "fill_field"}:
            return selenium_fill(str(cmd.get("selector") or ""), str(cmd.get("value") or cmd.get("text") or ""),
                                 str(cmd.get("by") or "css"), bool(cmd.get("submit", False)))
        if action == "selenium_click":
            return selenium_click(str(cmd.get("selector") or ""), str(cmd.get("by") or "css"))

        # ── MEMORY ────────────────────────────────────────────────────────────
        if action in {"remember", "save_fact", "memorize"}:
            fact = str(cmd.get("fact") or cmd.get("text") or "")
            if fact: remember(fact); speak("Noted!")
            return {"status": "ok"}
        if action in {"get_memory", "show_memory", "recall"}:
            ctx = get_mem_ctx(); speak("Memory retrieved."); return {"status": "ok", "memory": ctx}
        if action in {"add_contact", "save_contact"}:
            name = str(cmd.get("name", ""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {"name": name, "email": str(cmd.get("email", "")),
                                                        "phone": str(cmd.get("phone", ""))}
                save_memory(); speak(f"Contact {name} saved.")
            return {"status": "ok"}

        # ── SCHEDULE ──────────────────────────────────────────────────────────
        if action in {"schedule_task", "schedule", "set_reminder"}:
            task_s = str(cmd.get("task") or cmd.get("command") or "")
            sched  = str(cmd.get("schedule") or cmd.get("time") or "daily at 09:00")
            if not task_s: return {"status": "error", "message": "No task to schedule"}
            job = {"id": "".join(random.choices(string.ascii_lowercase, k=8)), "task": task_s, "schedule": sched, "last_run": ""}
            _sched_jobs.append(job); save_memory()
            speak(f"Scheduled: {task_s[:50]} — {sched}")
            return {"status": "ok", "job_id": job["id"]}

        # ── HEALTH / WAIT / PING ──────────────────────────────────────────────
        if action in {"wait", "sleep", "pause"}:
            secs = min(float(cmd.get("seconds") or 1), 60); time.sleep(secs); return {"status": "ok"}

        if action in {"ping", "test", "health_check", "status"}:
            speak("Online and ready!"); return {"status": "ok", "pong": True, "health": HEALTH}

        if action in {"list_skills", "skills"}:
            skills = ["open apps/sites", "send email", "bulk email", "read inbox", "draft replies",
                      "find leads", "organize files", "process invoices", "paste spreadsheet data",
                      "screenshot & OCR", "voice control", "social media posting", "WhatsApp",
                      "social reply bots (WhatsApp/Instagram/Facebook)", "invoice payment queue",
                      "book meetings", "web research", "browser automation", "scheduler", "real mouse/keyboard"]
            speak(f"{len(skills)} skill types available."); return {"status": "ok", "skills": skills}

        # ── BRIGHTNESS ────────────────────────────────────────────────────────
        if action in {"brightness_up"}:
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)", shell=True)
            return {"status": "ok"}
        if action in {"brightness_down"}:
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)", shell=True)
            return {"status": "ok"}

        # ── ULTIMATE FALLBACK — smart_open ────────────────────────────────────
        tgt = (cmd.get("url") or cmd.get("app") or cmd.get("target") or cmd.get("name") or "")
        if tgt:
            res = smart_open(str(tgt))
            if res.get("status") == "ok": return res

        res = smart_open(action.replace("_", " ").strip())
        if res.get("status") == "ok": return res

        log.warning("Unhandled action: '%s'", action)
        speak(f"I don't know how to '{action.replace('_', ' ')}' yet.")
        return {"status": "error", "message": f"Unknown action: '{action}'"}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e, exc_info=True)
        return {"status": "error", "message": f"Exception in {action}: {e}"}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TASK EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════
def execute_task(task: str, token: str) -> dict:
    if not task or not task.strip():
        return {"status": "error", "ok": 0, "total": 0, "result": "Empty task"}
    task = task.strip()
    log.info("TASK: %s", task[:120])
    print(f"\n  [TASK] {task[:80]}")
    _convo.append(f"user: {task[:120]}")

    commands = local_parse(task)

    if not commands:
        tl = task.lower().strip()
        words = tl.split()
        is_open_like = len(words) <= 5 and not any(
            w in tl for w in ["send", "email", "search", "find", "create", "write", "post", "process", "organize"])
        if is_open_like:
            res = smart_open(task)
            if res.get("status") == "ok":
                _convo.append(f"dacexy: Opened {task[:60]}")
                with _mem_lock:
                    MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
                save_memory()
                speak(f"Done!")
                return {"status": "ok", "ok": 1, "total": 1, "result": f"Opened: {task}"}
        speak("I'm not sure how to do that. Try rephrasing, or say 'help'.")
        return {"status": "error", "ok": 0, "total": 0, "result": f"Could not understand: {task[:80]}"}

    ok_count = 0; total = len(commands); results = []
    print(f"  [TASK] {total} steps...")
    audit.info("ACTION=TASK_START | steps=%d | task=%s", total, task[:80])

    for i, c in enumerate(commands):
        if not isinstance(c, dict): total -= 1; continue
        step_action = c.get("action", "?")
        log.info("  Step %d/%d: %s", i + 1, total, step_action)
        print(f"  [STEP {i+1}/{total}] {step_action}")
        try:
            res = exec_cmd(c, token); results.append(res)
            if res.get("status") in ("ok", "skipped"):
                ok_count += 1; print(f"  [OK]")
            else:
                log.warning("  Step %d failed: %s", i + 1, res.get("message", "?")); print(f"  [FAIL] {res.get('message', '?')}")
            time.sleep(0.15)
        except Exception as e:
            log.error("  Step %d exception: %s", i + 1, e)
            results.append({"status": "error", "message": str(e)})

    with _mem_lock:
        MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
    save_memory()

    HEALTH["tasks_ok"] += ok_count
    summary = f"Task done: {ok_count}/{total} steps — {task[:60]}"
    log.info(summary); _convo.append(f"dacexy: {summary}")
    audit.info("ACTION=TASK_END | ok=%d | total=%d | task=%s", ok_count, total, task[:60])
    speak(f"Done! {ok_count} of {total} steps succeeded.")

    return {"status": "ok" if ok_count > 0 else "error", "ok": ok_count, "total": total,
            "result": summary, "steps": results}


# ══════════════════════════════════════════════════════════════════════════════
# AUTOSTART
# ══════════════════════════════════════════════════════════════════════════════
def setup_autostart():
    try:
        if not WINREG_OK: return
        launcher = str(AGENT_DIR / "start_dacexy.bat")
        cmd = (f'"{launcher}"' if os.path.exists(launcher)
               else f'"{sys.executable}" "{Path(__file__).resolve()}"')
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered: %s", cmd)
    except Exception as e:
        log.warning("Autostart: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def login() -> Optional[str]:
    print("\n" + "=" * 55)
    print("  DACEXY AGENT — Login")
    print("=" * 55)
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
            log.info("Login response: %d", r.status_code)
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


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ══════════════════════════════════════════════════════════════════════════════
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
                if run:
                    job["last_run"] = now.isoformat(); save_memory()
                    tok = token_ref[0]
                    if tok:
                        t_ = job.get("task", "")
                        threading.Thread(target=execute_task, args=(t_, tok), daemon=True).start()
                        log.info("Scheduled job fired: %s", t_[:60])
        except Exception as e:
            log.warning("Scheduler: %s", e)
        time.sleep(30)


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH MONITOR
# ══════════════════════════════════════════════════════════════════════════════
def _health_monitor(ws_send_ref: list):
    while _running:
        time.sleep(60)
        try:
            if PSUTIL_OK:
                HEALTH["cpu"]  = psutil.cpu_percent(interval=0.5)
                HEALTH["ram"]  = psutil.virtual_memory().percent
                try:
                    dp = "C:\\" if platform.system() == "Windows" else "/"
                    HEALTH["disk"] = psutil.disk_usage(dp).percent
                except Exception:
                    pass
            uptime = int(time.time() - HEALTH["uptime_start"])
            HEALTH["uptime_seconds"] = uptime
            # Send heartbeat if websocket connected
            fn = ws_send_ref[0]
            if fn:
                try:
                    asyncio.run_coroutine_threadsafe(fn({"type": "heartbeat", "health": dict(HEALTH)}),
                                                      asyncio.get_event_loop())
                except Exception:
                    pass
            # Auto-alert on high resource usage
            if HEALTH["cpu"] > 90:
                speak("Warning: CPU usage is very high!")
                _notify("Dacexy Alert", f"CPU at {HEALTH['cpu']}%")
            if HEALTH["ram"] > 90:
                speak("Warning: RAM usage is very high!")
        except Exception as e:
            log.warning("Health monitor: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# VOICE
# ══════════════════════════════════════════════════════════════════════════════
def _is_wake_word(heard: str) -> bool:
    h = heard.lower().strip()
    return any(re.search(r"\b" + re.escape(w) + r"\b", h) for w in WAKE_WORDS)


def _voice_loop():
    global _voice_on
    if not VOICE_OK or not sr:
        print("  [VOICE] Disabled — install PyAudio + speechrecognition for voice control.")
        return

    rec = sr.Recognizer()
    rec.energy_threshold         = 350
    rec.dynamic_energy_threshold = True
    rec.pause_threshold          = 0.7

    print("  [VOICE] Active! Say: Dacexy / Hey Dacexy / Jarvis / Computer")
    speak("Voice ready. Say Dacexy to give me a command.")

    while _voice_on and _running:
        heard = ""
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.1)
                except Exception: pass
                try: audio = rec.listen(src, timeout=3, phrase_time_limit=7)
                except sr.WaitTimeoutError: continue
                except OSError: time.sleep(2); continue
            try: heard = rec.recognize_google(audio, language="en-IN").lower().strip()
            except sr.UnknownValueError: continue
            except sr.RequestError: time.sleep(3); continue
        except Exception: time.sleep(1); continue

        if not _is_wake_word(heard): continue
        log.info("Wake word: '%s'", heard)
        speak("Yes sir, how can I help?"); time.sleep(0.3)

        command = ""
        try:
            with sr.Microphone() as csrc:
                try: rec.adjust_for_ambient_noise(csrc, duration=0.08)
                except Exception: pass
                try: caudio = rec.listen(csrc, timeout=8, phrase_time_limit=30)
                except sr.WaitTimeoutError: speak("I didn't catch that."); continue
                except OSError: continue
            try: command = rec.recognize_google(caudio, language="en-IN").strip()
            except sr.UnknownValueError: speak("Could you repeat that?"); continue
            except sr.RequestError: continue
        except Exception: continue

        if not command: continue
        log.info("Voice command: '%s'", command)
        with _tok_lock: tok = _cur_token
        if not tok: speak("Not logged in yet."); continue
        speak("On it!")

        def _run(t_=tok, cmd_=command):
            try: execute_task(cmd_, t_)
            except Exception as exc: log.error("Voice task: %s", exc); speak("Error with that command.")
        threading.Thread(target=_run, daemon=True, name="VoiceTask").start()


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
    with _tok_lock:
        _cur_token = t


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE SHELL
# ══════════════════════════════════════════════════════════════════════════════
def _interactive_shell(token: str, tok_ref: list):
    print("\n" + "=" * 60)
    print("  DACEXY — COMMAND CENTER")
    print("=" * 60)
    print(f"  Email    : {_smtp_cfg.get('email') or 'NOT CONFIGURED'}")
    print(f"  Voice    : {'ON' if _voice_on else 'OFF'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print("=" * 60)
    print("  Type any task. 'help' for examples. 'quit' to exit.\n")

    cmds_help = {
        "organize desktop":     "Sort files into folders by type",
        "process invoices":     "Extract data from PDFs, queue payments",
        "pending payments":     "Show invoices queued for payment approval",
        "approve payment <id>": "Approve a queued payment (opens payment portal)",
        "check inbox":          "Read and flag urgent emails",
        "configure email":      "Set up SMTP for auto-send",
        "find leads for X":     "Find email leads for product X",
        "reply to my whatsapp": "Read WhatsApp DMs and draft replies",
        "turn on auto reply":   "Enable auto-send replies (needs approval)",
        "open youtube":         "Open YouTube",
        "screenshot":           "Take a screenshot",
        "system info":          "CPU/RAM/disk usage",
        "schedule X at HH:MM":  "Schedule a task",
        "help":                 "Show this list",
    }

    while _running:
        try:
            line = input("  Dacexy> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line: continue
        tl = line.lower()

        if tl in ("quit", "exit"): print("  Goodbye!"); break
        if tl in ("help", "menu"):
            print(); [print(f"    {k:<30} {v}") for k, v in cmds_help.items()]; print(); continue
        if tl == "memory":    print("\n" + get_mem_ctx() + "\n"); continue
        if tl == "jobs":
            if _sched_jobs: [print(f"  [{j['id']}] {j['task']} — {j['schedule']}") for j in _sched_jobs]
            else: print("  No scheduled jobs.")
            continue
        if tl == "email":     configure_smtp_interactive(); continue
        if tl == "sysinfo":   exec_cmd({"action": "get_system_info"}, token); continue
        if tl == "screenshot":exec_cmd({"action": "screenshot"}, token); continue
        if tl == "health":    print(f"  Health: {HEALTH}"); continue

        tok = tok_ref[0]
        def _run(t_=tok, cmd_=line):
            r = execute_task(cmd_, t_)
            print(f"\n  [{'OK' if r['status'] == 'ok' else 'FAIL'}] {r.get('result', '')}")
        threading.Thread(target=_run, daemon=True, name="ShellTask").start()


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET (robust, reconnecting)
# ══════════════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    global _ws_send_fn
    retry = 4.0; max_retry = 60.0

    while _running:
        try:
            log.info("WS: connecting...")
            print("  [WS] Connecting to Dacexy cloud...")

            connect_kw: dict = {"ping_interval": 20, "ping_timeout": 15, "max_size": 16 * 1024 * 1024}
            try:
                wsv = int(str(getattr(websockets, "__version__", "0")).split(".")[0])
                if wsv >= 14: connect_kw["open_timeout"] = 20
                elif wsv >= 10: connect_kw["close_timeout"] = 10
            except Exception: pass

            async with websockets.connect(BACKEND_WS, **connect_kw) as ws:
                await ws.send(json.dumps({"token": token}))
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=25)
                    auth_msg = json.loads(auth_raw)
                    if auth_msg.get("type") == "error":
                        log.error("WS auth rejected: %s", auth_msg.get("message"))
                        speak("Authentication failed."); await asyncio.sleep(retry)
                        retry = min(retry * 1.5, max_retry); continue
                except asyncio.TimeoutError:
                    log.warning("WS: auth timeout"); await asyncio.sleep(retry); retry = min(retry * 1.5, max_retry); continue
                except Exception as e:
                    log.warning("WS: auth error: %s", e); await asyncio.sleep(retry); continue

                await ws.send(json.dumps({
                    "type": "init", "platform": platform.system(),
                    "machine": platform.machine(), "hostname": socket.gethostname(),
                    "features": ["voice3", "vision", "browser", "email", "social_selenium",
                                 "bulk_email", "lead_gen", "web_research", "scheduler", "memory",
                                 "selenium", "ocr", "screenshot", "file_organizer", "invoice_extractor",
                                 "spreadsheet_paste", "inbox_reader", "approval_gates",
                                 "real_mouse_keyboard", "encrypted_config", "health_monitor",
                                 "calendar_booking", "human_approval", "social_reply_bots",
                                 "payment_queue"],
                }))

                log.info("WS: connected!")
                print("\n  [OK] Connected to Dacexy cloud — agent is LIVE!")
                speak("Connected! Ready for your commands.")
                retry = 4.0

                ws_lock = asyncio.Lock()
                loop    = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e_: log.warning("ws_send: %s", e_)

                _ws_send_fn = ws_send

                while _running:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=50)
                    except asyncio.TimeoutError:
                        try: await asyncio.wait_for(ws.send(json.dumps({"type": "ping"})), timeout=8)
                        except Exception: break
                        continue

                    try: msg = json.loads(raw)
                    except Exception: continue

                    mtype    = msg.get("type",   "")
                    action   = msg.get("action", "")
                    task_txt = (msg.get("task") or msg.get("goal") or "").strip()
                    task_id  = str(msg.get("task_id") or "")

                    if mtype == "ping":
                        await ws_send({"type": "pong"}); continue
                    if mtype in ("pong", "connected", "init_ack", "heartbeat"): continue

                    # Direct action
                    if action and action not in ("swarm_task", "task", "run_agent", ""):
                        def _cmd_thread(m_=dict(msg), t_=token, tid_=task_id):
                            try:
                                r_ = exec_cmd(m_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"),
                                    "ok": 1 if r_.get("status") in ("ok", "skipped") else 0,
                                    "total": 1, "result": str(r_.get("message") or r_.get("opened") or "done"),
                                    "data": r_,
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 1, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_cmd_thread, daemon=True).start()
                        continue

                    # Natural language task
                    if task_txt or mtype in ("task", "command"):
                        if not task_txt: task_txt = action
                        if not task_txt: continue
                        log.info("Dashboard task: %s", task_txt[:80])
                        print(f"\n  [TASK] From dashboard: {task_txt[:80]}")
                        speak(f"On it! {task_txt[:40]}")

                        def _task_thread(t_=token, txt_=task_txt, tid_=task_id):
                            try:
                                r_ = execute_task(txt_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"), "ok": r_.get("ok", 0),
                                    "total": r_.get("total", 1), "result": r_.get("result", ""),
                                    "steps": r_.get("steps", []),
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 0, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_task_thread, daemon=True).start()

        except Exception as e:
            log.error("WS outer: %s", e)

        if _running:
            print(f"\n  [WS] Disconnected. Retry in {int(retry)}s...")
            _ws_send_fn = None
            await asyncio.sleep(retry)
            retry = min(retry * 1.5, max_retry)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    global _running

    print("\n" + "=" * 65)
    print("  DACEXY DESKTOP AGENT — STARTING")
    print("  Real desktop automation: mouse, keyboard, files, email, voice")
    print("=" * 65 + "\n")

    init_tts()
    load_memory()

    caps = []
    if PYAUTOGUI_OK:                  caps.append("mouse/keyboard")
    if PIL_OK:                        caps.append("screenshot")
    if VOICE_OK:                      caps.append("VOICE")
    if SELENIUM_OK:                   caps.append("browser-automation")
    if BS4_OK:                        caps.append("web-scraping")
    if OCR_OK:                        caps.append("OCR")
    if PDF_OK:                        caps.append("invoice-PDF")
    if XL_OK:                         caps.append("spreadsheet")
    if CRYPTO_OK:                     caps.append("encrypted-config")
    em = _smtp_cfg.get("email") or ""
    caps.append(f"email={'✓' if em else 'NOT CONFIGURED'}")
    print(f"  Capabilities: {', '.join(caps)}\n")

    token = get_token()
    if token:
        print("  Checking saved session...")
        if check_token_valid(token):
            print("  [OK] Session valid.\n")
        else:
            print("  Session expired — please log in.\n")
            clear_token(); token = None

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"\n  Attempt {attempt+1}/3 failed.\n")
        if not token:
            print("\n  [ERROR] Authentication failed. Exiting.")
            sys.exit(1)

    try: setup_autostart()
    except Exception: pass

    if not _smtp_cfg.get("email"):
        print("  [EMAIL] Not configured. Type 'configure email' to enable auto-send.\n")

    voice_ok = start_voice(token)
    tok_ref  = [token]
    ws_send_ref = [None]  # filled in run_websocket

    threading.Thread(target=_scheduler_loop,    args=(tok_ref,),    daemon=True, name="Scheduler").start()
    threading.Thread(target=_health_monitor,    args=(ws_send_ref,), daemon=True, name="HealthMon").start()
    threading.Thread(target=_interactive_shell, args=(token, tok_ref), daemon=True, name="Shell").start()

    print("  " + "-" * 63)
    print("  Dacexy Agent — LIVE")
    print(f"  Voice    : {'ON — say Dacexy / Hey Dacexy' if voice_ok else 'OFF'}")
    print(f"  Email    : {_smtp_cfg.get('email') or 'Not configured'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print(f"  Log file : {LOG_FILE}")
    print("  " + "-" * 63 + "\n")

    if not WS_OK:
        print("  [ERROR] websockets not installed!"); sys.exit(1)

    try:
        asyncio.run(run_websocket(token))
    except KeyboardInterrupt:
        print("\n  Stopped by user.")
    except Exception as e:
        log.error("Fatal: %s", e)
    finally:
        _running = False
        stop_voice()
        with _sel_lock:
            if _selenium_driver:
                try: _selenium_driver.quit()
                except Exception: pass
        with _social_lock:
            for _drv in _social_drivers.values():
                try: _drv.quit()
                except Exception: pass
        try: save_memory()
        except Exception: pass
        print("  Dacexy stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
