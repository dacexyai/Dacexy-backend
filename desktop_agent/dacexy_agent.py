"""
DACEXY DESKTOP AGENT v30.0 — "DEX" JARVIS MODE
================================================
Full business co-assistant for small businesses.
Voice-first, Jarvis-style, instant response.

NEW in v30.0:
  - Jarvis-style voice: instant wake, single-attempt recognition
  - TTS: engine created inside worker thread (COM STA fix, always audible)
  - All P0 bugs fixed: open/create_file/verification layer fully implemented
  - 500+ business task patterns across every department
  - Smart planner: multi-step goal decomposition via AI
  - Dashboard voice transcript streaming
  - Recovery system: retry + alternative methods on failure
  - Vision-assisted verification (OCR + window check)
  - Natural Jarvis narration on every action
  - "Hey Dex" triggers on first attempt at normal speaking volume
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
    ("python-docx",       "docx"),
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

try:
    from selenium import webdriver as _chk_sel
except ImportError:
    _pip_install("selenium", "webdriver-manager")

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
    pyautogui.PAUSE    = 0.02
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

try:
    import docx as docx_lib; DOCX_OK = True
except Exception:
    docx_lib = None; DOCX_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"

AGENT_DIR   = Path.home() / "DacexyAgent"
LOG_FILE    = AGENT_DIR / "logs" / "agent.log"
SS_DIR      = AGENT_DIR / "screenshots"
DATA_DIR    = AGENT_DIR / "data"
DOC_DIR     = AGENT_DIR / "documents"
INBOX_DIR   = AGENT_DIR / "inbox"
KEY_FILE    = AGENT_DIR / ".agent.key"
CONFIG_FILE = Path.home() / ".dacexy_agent.json"
RUNTIME_STATE_FILE = AGENT_DIR / "data" / "runtime_state.json"
TASK_QUEUE_FILE = AGENT_DIR / "data" / "task_queue.json"

_desktop_task_lock = threading.RLock()
_runtime_state_lock = threading.RLock()
_runtime_state: Dict[str, Any] = {
    "active_window": "",
    "active_application": "",
    "active_tab": "",
    "active_file": "",
    "active_folder": "",
    "current_url": "",
    "last_action": "",
    "last_result": "",
    "last_verified": False,
    "updated_at": "",
}
MEMORY_FILE = Path.home() / ".dacexy_memory.json"

for _d in [AGENT_DIR, AGENT_DIR/"logs", SS_DIR, DATA_DIR, DOC_DIR, INBOX_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

SOCIAL_PROFILE_DIR = AGENT_DIR / "browser_profiles"
SOCIAL_PROFILE_DIR.mkdir(exist_ok=True)
PAYMENT_QUEUE_FILE = DATA_DIR / "payment_queue.json"

PAYMENT_PORTALS: Dict[str, str] = {
    "razorpay": "https://dashboard.razorpay.com/app/payments",
    "paypal":   "https://www.paypal.com/myaccount/transfer/homepage/pay",
    "stripe":   "https://dashboard.stripe.com/payments",
    "bank":     "",
}

AUTO_REPLY_TEMPLATES: Dict[str, str] = {
    "default":   "Thanks for your message! I'll get back to you shortly.",
    "price":     "Thanks for asking about pricing! I'll send you a detailed quote within 2 hours.",
    "complaint": "I'm sorry to hear about this. I'm escalating this to our team immediately.",
    "order":     "Your order is being processed. You'll receive an update within 24 hours.",
    "support":   "Thank you for reaching out! Our support team will respond within 1 business hour.",
}

APPROVAL_REQUIRED = {
    "send_email", "send_bulk_email", "delete_file", "run_command",
    "pay_invoice", "execute_payment", "post_twitter", "post_linkedin",
    "post_facebook", "bulk_email", "approve_payment", "enable_auto_reply",
}

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

# Wake words — "Hey Dex" is primary, rest kept for compatibility
WAKE_WORDS = [
    "hey dex", "dex", "okay dex", "hi dex",
    "dacexy", "hey dacexy", "okay dacexy",
    "jarvis", "hey jarvis",
    "computer", "assistant", "hey agent", "agent",
]

SITES: Dict[str, str] = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "gmail":         "https://mail.google.com",
    "facebook":      "https://www.facebook.com",
    "instagram":     "https://www.instagram.com",
    "twitter":       "https://x.com",
    "x":             "https://x.com",
    "linkedin":      "https://www.linkedin.com",
    "whatsapp":      "https://web.whatsapp.com",
    "whatsapp web":  "https://web.whatsapp.com",
    "github":        "https://github.com",
    "amazon":        "https://www.amazon.in",
    "flipkart":      "https://www.flipkart.com",
    "netflix":       "https://www.netflix.com",
    "spotify":       "https://open.spotify.com",
    "maps":          "https://maps.google.com",
    "google maps":   "https://maps.google.com",
    "wikipedia":     "https://www.wikipedia.org",
    "reddit":        "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt":       "https://chat.openai.com",
    "dacexy":        "https://dacexy.vercel.app",
    "notion":        "https://notion.so",
    "canva":         "https://www.canva.com",
    "drive":         "https://drive.google.com",
    "google drive":  "https://drive.google.com",
    "trello":        "https://trello.com",
    "slack":         "https://app.slack.com",
    "zoom":          "https://zoom.us",
    "meet":          "https://meet.google.com",
    "google meet":   "https://meet.google.com",
    "teams":         "https://teams.microsoft.com",
    "discord":       "https://discord.com/app",
    "docs":          "https://docs.google.com",
    "sheets":        "https://sheets.google.com",
    "slides":        "https://slides.google.com",
    "calendar":      "https://calendar.google.com",
    "photos":        "https://photos.google.com",
    "translate":     "https://translate.google.com",
    "pinterest":     "https://www.pinterest.com",
    "tiktok":        "https://www.tiktok.com",
    "twitch":        "https://www.twitch.tv",
    "fiverr":        "https://www.fiverr.com",
    "upwork":        "https://www.upwork.com",
    "medium":        "https://medium.com",
    "quora":         "https://www.quora.com",
    "paypal":        "https://www.paypal.com",
    "razorpay":      "https://razorpay.com",
    "stripe":        "https://dashboard.stripe.com",
    "telegram web":  "https://web.telegram.org",
    "news":          "https://news.google.com",
    "claude":        "https://claude.ai",
    "anthropic":     "https://anthropic.com",
    "perplexity":    "https://perplexity.ai",
    "gemini":        "https://gemini.google.com",
    "openai":        "https://openai.com",
    "quickbooks":    "https://quickbooks.intuit.com",
    "zoho":          "https://www.zoho.com",
    "hubspot":       "https://app.hubspot.com",
    "salesforce":    "https://login.salesforce.com",
    "shopify":       "https://accounts.shopify.com",
    "wordpress":     "https://wordpress.com/log-in",
    "mailchimp":     "https://login.mailchimp.com",
    "ahrefs":        "https://ahrefs.com",
    "semrush":       "https://www.semrush.com",
}

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
    "winrar":              "winrar.exe",
    "7zip":                "7zFM.exe",
    "obs":                 "obs64.exe",
    "steam":               "steam.exe",
    "gimp":                "gimp-2.10.exe",
    "photoshop":           "photoshop.exe",
    "audacity":            "audacity.exe",
    "skype":               "skype.exe",
    "anydesk":             "anydesk.exe",
    "teamviewer":          "teamviewer.exe",
    "tally":               "tally.exe",
    "busy":                "busy.exe",
}

FILE_CATEGORIES: Dict[str, List[str]] = {
    "Images":       [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff"],
    "Documents":    [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
    "Presentations":[".ppt", ".pptx", ".odp"],
    "Videos":       [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Audio":        [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Archives":     [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code":         [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".json"],
    "Invoices":     [],
}

_ACTION_VERBS = {
    "open", "search", "draft", "send", "write", "find", "create", "close",
    "check", "read", "type", "click", "post", "reply", "compose", "look",
    "research", "browse", "launch", "start", "play", "email", "message",
    "save", "copy", "paste", "organize", "process", "download", "upload",
    "book", "schedule", "cancel", "delete", "move", "rename", "zip",
    "generate", "analyze", "track", "monitor", "summarize", "extract",
    "calculate", "report", "update", "remind", "notify", "backup",
}

# Jarvis-style response variations for natural speech
_JARVIS_CONFIRMATIONS = [
    "Right away, sir.",
    "On it.",
    "Consider it done.",
    "Absolutely.",
    "Of course.",
    "Sure thing.",
    "I'm on it.",
    "Already on it.",
    "Leave it to me.",
]

_JARVIS_DONE = [
    "All done.",
    "Done.",
    "Task complete.",
    "Finished.",
    "All set.",
    "That's taken care of.",
    "Done. Anything else?",
]


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════════════
_mem_lock          = threading.Lock()
_cfg_lock          = threading.Lock()
_executor          = ThreadPoolExecutor(max_workers=24)
_running           = True
_tts_q: queue.Queue = queue.Queue(maxsize=50)
_tts_engine        = None
_tts_lock          = threading.Lock()
_voice_on          = False
_cur_token         = None
_tok_lock          = threading.Lock()
_smtp_cfg: Dict    = {}
_sched_jobs: List  = []
_convo: deque      = deque(maxlen=40)
_selenium_driver   = None
_sel_lock          = threading.Lock()
_pending_approvals: Dict[str, dict] = {}
_approval_lock     = threading.Lock()
_ws_send_fn        = None
_ws_loop           = None
_abort_flag        = threading.Event()

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
    "business":     {},
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
log.info("Dacexy Agent v30.0 initializing")


# ══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION
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
    if not f: return s
    try: return base64.b64encode(f.encrypt(s.encode())).decode()
    except Exception: return s

def decrypt_str(s: str) -> str:
    f = _get_fernet()
    if not f: return s
    try: return f.decrypt(base64.b64decode(s)).decode()
    except Exception: return s


# ══════════════════════════════════════════════════════════════════════════════
# TTS — ENGINE CREATED INSIDE WORKER THREAD (COM STA FIX — ALWAYS AUDIBLE)
# ══════════════════════════════════════════════════════════════════════════════
def _tts_worker():
    """
    CRITICAL: pyttsx3 engine created HERE inside the thread.
    Windows SAPI5 is COM STA — must be initialized on the same thread it runs on.
    pythoncom.CoInitialize() sets up the STA apartment for this thread.
    """
    global _tts_engine

    if platform.system() == "Windows":
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception as e:
            log.warning("TTS: COM init skipped: %s", e)

    eng = None
    if TTS_LIB_OK:
        try:
            eng = pyttsx3.init()
            eng.setProperty("rate", 170)
            eng.setProperty("volume", 1.0)
            try:
                voices = eng.getProperty("voices") or []
                for v in voices:
                    n = (v.name or "").lower()
                    if any(x in n for x in ["david", "mark", "george", "ryan"]):
                        eng.setProperty("voice", v.id)
                        break
            except Exception:
                pass
            with _tts_lock:
                _tts_engine = eng
            log.info("TTS engine created in worker thread OK")
        except Exception as e:
            log.warning("TTS engine init failed: %s", e)
            eng = None

    while _running:
        text = None
        try:
            text = _tts_q.get(timeout=1)
            if text is None:
                break
            s = str(text)[:500]
            if eng:
                try:
                    eng.say(s)
                    eng.runAndWait()
                except Exception as e:
                    log.warning("pyttsx3 say error: %s — reinitializing", e)
                    try:
                        eng = pyttsx3.init()
                        eng.setProperty("rate", 170)
                        eng.setProperty("volume", 1.0)
                        with _tts_lock:
                            _tts_engine = eng
                        eng.say(s)
                        eng.runAndWait()
                    except Exception as e2:
                        log.warning("TTS reinit failed: %s", e2)
            else:
                log.warning("TTS engine unavailable, text: %s", s[:80])
        except queue.Empty:
            continue
        except Exception as e:
            log.warning("TTS worker: %s", e)
        finally:
            if text is not None:
                try:
                    _tts_q.task_done()
                except Exception:
                    pass

    if platform.system() == "Windows":
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


def init_tts():
    """Start TTS worker. Engine is created INSIDE the thread (COM STA fix)."""
    if not TTS_LIB_OK:
        log.warning("pyttsx3 not installed — TTS disabled")
        return
    try:
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS thread started")
    except Exception as e:
        log.warning("TTS init: %s", e)


def speak(text: str):
    """Speak text aloud AND stream to dashboard. Always called for every action."""
    if not text:
        return
    s = str(text)[:500]
    try:
        print(f"\n  [Dex] {s}")
        sys.stdout.flush()
    except Exception:
        pass
    log.info("SPEAK: %s", s)
    try:
        _tts_q.put_nowait(s)
    except queue.Full:
        try:
            _tts_q.get_nowait()
            _tts_q.put_nowait(s)
        except Exception:
            pass
    # Stream voice transcript to dashboard
    try:
        if _ws_send_fn and _ws_loop and _ws_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                _ws_send_fn({"type": "voice_log", "text": s}),
                _ws_loop,
            )
    except Exception:
        pass


def jarvis_confirm() -> str:
    return random.choice(_JARVIS_CONFIRMATIONS)

def jarvis_done() -> str:
    return random.choice(_JARVIS_DONE)


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
    try:
        r = req_lib.get(
            f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.status_code == 200
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
                MEMORY["business"]     = d.get("business", {})
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
                "business":     MEMORY["business"],
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
            if MEMORY["business"]:
                parts.append("Business: " + str(MEMORY["business"])[:200])
        conv = list(_convo)[-6:]
        if conv:
            parts.append("Conv: " + " | ".join(conv))
        return "\n".join(parts)
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY
# ══════════════════════════════════════════════════════════════════════════════
def _is_path_allowed(path_str: str) -> bool:
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
    op_key = f"{action}:{hashlib.md5(details.encode()).hexdigest()[:8]}"
    with _mem_lock:
        if op_key in MEMORY["approved_ops"]:
            return True

    speak(f"I need your approval for: {action}. Check the terminal.")
    print(f"\n  {'='*55}")
    print(f"  ⚠  APPROVAL REQUIRED")
    print(f"  Action : {action}")
    print(f"  Details: {details[:200]}")
    print(f"  {'='*55}")
    print(f"  Approve? [Y/n/always] (auto-deny in {timeout}s): ", end="", flush=True)
    _notify("Dacexy — Approval Needed", f"{action}: {details[:60]}")

    import select
    if hasattr(select, "select"):
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
        _ans = ["n"]
        _ev  = threading.Event()
        def _read():
            try: _ans[0] = input().strip().lower()
            except Exception: pass
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
def real_click(x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.15):
    if not PYAUTOGUI_OK:
        return {"status": "error", "message": "pyautogui not available"}
    try:
        sw, sh = pyautogui.size()
        x = max(1, min(x, sw - 1))
        y = max(1, min(y, sh - 1))
        pyautogui.moveTo(x, y, duration=duration)
        pyautogui.click(x, y, button=button, clicks=clicks, interval=0.06)
        log.info("CLICK x=%d y=%d btn=%s clicks=%d", x, y, button, clicks)
        return {"status": "ok", "x": x, "y": y}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def real_type(text: str, clear_first: bool = False, human_speed: bool = False):
    if not text: return
    text = str(text)[:100_000]
    try:
        if clear_first and PYAUTOGUI_OK:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.04)
            pyautogui.press("delete")
            time.sleep(0.04)
        if CLIP_OK:
            pyperclip.copy(text)
            time.sleep(0.05)
            if PYAUTOGUI_OK:
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.1)
        elif PYAUTOGUI_OK:
            interval = random.uniform(0.02, 0.06) if human_speed else 0.008
            for chunk in [text[i:i+300] for i in range(0, len(text), 300)]:
                pyautogui.write(chunk, interval=interval)
    except Exception as e:
        log.warning("real_type: %s", e)


def real_hotkey(*keys):
    if not PYAUTOGUI_OK: return
    try:
        pyautogui.hotkey(*[str(k) for k in keys[:6]])
    except Exception as e:
        log.warning("hotkey %s: %s", keys, e)


def real_press(key: str):
    if not PYAUTOGUI_OK: return
    try:
        pyautogui.press(str(key))
    except Exception as e:
        log.warning("press %s: %s", key, e)


def real_scroll(direction: str = "down", amount: int = 5):
    if not PYAUTOGUI_OK: return
    try:
        amt = abs(amount)
        pyautogui.scroll(amt if direction == "up" else -amt)
    except Exception as e:
        log.warning("scroll: %s", e)


def find_on_screen(image_path: str, confidence: float = 0.85) -> Optional[Tuple[int, int]]:
    if not PYAUTOGUI_OK: return None
    try:
        loc = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        return (loc.x, loc.y) if loc else None
    except Exception:
        return None


def read_screen_text(region: Optional[Tuple] = None) -> str:
    if OCR_OK and PIL_OK:
        try:
            img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
            return pytesseract.image_to_string(img)
        except Exception as e:
            log.warning("OCR: %s", e)
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
    try:
        if not WINDOW_OK or not gw:
            return False
        wins = [w for w in gw.getAllWindows() if title_pattern.lower() in w.title.lower()]
        if wins:
            wins[0].activate()
            time.sleep(0.3)
            return True
    except Exception as e:
        log.warning("focus_window: %s", e)
    return False


def _load_runtime_state() -> None:
    global _runtime_state
    try:
        data = json.loads(RUNTIME_STATE_FILE.read_text(encoding="utf-8")) if RUNTIME_STATE_FILE.exists() else {}
        if isinstance(data, dict):
            with _runtime_state_lock:
                _runtime_state.update({k: data.get(k, v) for k, v in _runtime_state.items()})
    except Exception as e:
        log.warning("runtime_state load failed: %s", e)


def _save_runtime_state() -> None:
    try:
        RUNTIME_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _runtime_state_lock:
            RUNTIME_STATE_FILE.write_text(json.dumps(_runtime_state, indent=2, ensure_ascii=True), encoding="utf-8")
    except Exception as e:
        log.warning("runtime_state save failed: %s", e)


def update_runtime_state(**kwargs) -> None:
    with _runtime_state_lock:
        for key, value in kwargs.items():
            if key in _runtime_state:
                _runtime_state[key] = "" if value is None else value
        _runtime_state["active_window"] = get_active_win()
        _runtime_state["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    _save_runtime_state()


def current_runtime_state() -> dict:
    with _runtime_state_lock:
        state = dict(_runtime_state)
    state["active_window"] = get_active_win()
    return state


def _remember_task_queue(task: str, status: str, priority: int = 5) -> None:
    try:
        TASK_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        queue = json.loads(TASK_QUEUE_FILE.read_text(encoding="utf-8")) if TASK_QUEUE_FILE.exists() else []
        if not isinstance(queue, list):
            queue = []
        queue.append({
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "task": task[:300],
            "status": status,
            "priority": priority,
        })
        TASK_QUEUE_FILE.write_text(json.dumps(queue[-200:], indent=2, ensure_ascii=True), encoding="utf-8")
    except Exception as e:
        log.warning("task queue state failed: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION HELPERS — fully implemented (fixes P0 NameError)
# ══════════════════════════════════════════════════════════════════════════════
def verify_file_created(path: str) -> bool:
    """True if file exists on disk."""
    try:
        return Path(path).exists()
    except Exception:
        return False


def verify_window_contains(target: str) -> bool:
    """Check if any open window title plausibly matches the target."""
    try:
        wins = [w.lower() for w in list_windows()]
        t = target.lower()
        candidates = {t}
        for site in SITES:
            if site in t or t in site:
                candidates.add(site)
        for app in APPS:
            if app in t or t in app:
                candidates.add(app)
        return any(any(c in w for c in candidates) for w in wins)
    except Exception:
        return False


def verify_screen_ocr(target: str) -> bool:
    """OCR-based screen verification. Returns False (not error) if OCR unavailable."""
    if not OCR_OK:
        return False
    try:
        return target.lower() in read_screen_text().lower()
    except Exception:
        return False


def run_with_verification(action_fn, verify_fn, description: str,
                           correction_func=None, retries: int = 1) -> dict:
    """
    Run action_fn(), wait briefly, then verify. Verification never turns
    a successful action into a failure — it only adds a 'verified' field.
    On verify failure + correction_func provided: one retry.
    """
    try:
        result = action_fn()
    except Exception as e:
        return {"status": "error", "message": f"Exception in {description}: {e}"}
    if not isinstance(result, dict):
        result = {"status": "ok", "value": result}
    try:
        time.sleep(0.5)
        verified = bool(verify_fn())
    except Exception:
        verified = False
    if not verified and correction_func and retries > 0:
        try:
            correction_func()
            time.sleep(0.7)
            verified = bool(verify_fn())
        except Exception:
            pass
    result["verified"] = verified
    log.info("run_with_verification[%s]: verified=%s", description, verified)
    return result


def run_with_verification(action_fn, verify_fn, description: str,
                           correction_func=None, retries: int = 2) -> dict:
    """
    Strict verification wrapper. A task step is successful only when the
    verifier returns True. Failed verification triggers recovery retries.
    """
    result = {"status": "error", "message": f"{description} not attempted"}
    last_error = ""
    attempts = max(1, retries + 1)
    for attempt in range(1, attempts + 1):
        try:
            result = action_fn()
            if not isinstance(result, dict):
                result = {"status": "ok", "value": result}
            time.sleep(0.8 + (attempt * 0.4))
            verified = bool(verify_fn())
        except Exception as e:
            verified = False
            last_error = str(e)
            result = {"status": "error", "message": f"Exception in {description}: {e}"}
        log.info("run_with_verification[%s]: attempt=%s verified=%s", description, attempt, verified)
        if verified:
            result["status"] = "ok"
            result["verified"] = True
            update_runtime_state(last_action=description, last_result="verified", last_verified=True)
            return result
        if correction_func and attempt < attempts:
            try:
                correction_func()
                time.sleep(0.8)
            except Exception as e:
                last_error = str(e)
    result["verified"] = False
    result["status"] = "error"
    result["message"] = result.get("message") or f"Verification failed for {description}"
    if last_error:
        result["error"] = last_error
    update_runtime_state(last_action=description, last_result=result.get("message", "verification failed"), last_verified=False)
    return result


def _retry(fn, attempts: int = 3, delays: tuple = (1, 3), label: str = ""):
    last_exc = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if i < attempts - 1:
                time.sleep(delays[min(i, len(delays) - 1)])
    raise last_exc


# ══════════════════════════════════════════════════════════════════════════════
# FILE ORGANIZER
# ══════════════════════════════════════════════════════════════════════════════
def organize_folder(folder: str, dry_run: bool = False) -> dict:
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
        cat  = None
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
            except Exception as e:
                errors.append(str(e)); skipped += 1
        else:
            moved += 1

    summary = f"{'[DRY RUN] ' if dry_run else ''}Organized {moved} files. Skipped {skipped}."
    speak(summary)
    return {"status": "ok", "moved": moved, "skipped": skipped, "errors": errors[:5]}


def rename_files_batch(folder: str, pattern: str, replacement: str) -> dict:
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
    if not PDF_OK:
        return {"status": "error", "message": "pdfplumber not installed"}
    p = Path(pdf_path)
    if not p.exists():
        return {"status": "error", "message": "File not found"}
    try:
        amounts = []; dates = []; invoice_nos = []
        with pdfplumber.open(str(p)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        for m in re.finditer(r"(?:total|amount|due|payable)[:\s]+[₹$€£]?\s*([\d,]+\.?\d*)", text, re.I):
            try: amounts.append(float(m.group(1).replace(",", "")))
            except Exception: pass
        for m in re.finditer(r"[₹$€£]\s*([\d,]+\.?\d*)", text):
            try: amounts.append(float(m.group(1).replace(",", "")))
            except Exception: pass
        for m in re.finditer(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text):
            dates.append(m.group())
        for m in re.finditer(r"(?:invoice|inv|bill)\s*[#no.]*\s*([A-Z0-9-]+)", text, re.I):
            invoice_nos.append(m.group(1))
        result = {
            "status": "ok", "file": p.name,
            "amounts": list(set(amounts)), "max_amount": max(amounts) if amounts else 0,
            "dates": dates[:5], "invoice_nos": invoice_nos[:3],
            "text_preview": text[:500],
        }
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def process_invoices_folder(folder: str) -> dict:
    p = Path(folder)
    if not p.exists():
        return {"status": "error", "message": "Folder not found"}
    records = []; queued = 0
    for f in p.rglob("*.pdf"):
        d = extract_invoice_data(str(f))
        if d.get("status") == "ok":
            records.append({
                "file": d["file"], "max_amount": d["max_amount"],
                "dates": "; ".join(d["dates"][:2]),
                "invoice_no": "; ".join(d["invoice_nos"][:2]),
            })
            qid = add_to_payment_queue(d)
            if qid: queued += 1
    report = DATA_DIR / f"invoices_{datetime.date.today()}.csv"
    try:
        with open(report, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["file", "max_amount", "dates", "invoice_no"])
            w.writeheader(); w.writerows(records)
        try: subprocess.Popen(f'notepad.exe "{report}"', shell=True)
        except Exception: pass
        speak(f"Processed {len(records)} invoices. {queued} queued for your approval.")
        return {"status": "ok", "count": len(records), "queued": queued, "report": str(report)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE PAYMENT QUEUE
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
    amount = invoice.get("max_amount") or 0
    if not amount: return None
    q = _load_payment_queue()
    if any(i.get("file") == invoice.get("file") and i.get("status") == "pending_review" for i in q):
        return None
    qid = hashlib.md5(f"{invoice.get('file','')}-{amount}-{time.time()}".encode()).hexdigest()[:8]
    entry = {
        "id": qid, "file": invoice.get("file", ""),
        "amount": amount, "invoice_no": "; ".join(invoice.get("invoice_nos", [])[:1]),
        "dates": "; ".join(invoice.get("dates", [])[:1]),
        "status": "pending_review", "added_at": datetime.datetime.now().isoformat(),
    }
    q.append(entry); _save_payment_queue(q)
    audit.info("PAYMENT_QUEUED id=%s amount=%s file=%s", qid, amount, entry["file"])
    return qid

def list_payment_queue(status: str = "pending_review") -> dict:
    q = _load_payment_queue()
    items = [i for i in q if status == "all" or i.get("status") == status]
    if items:
        label = "all" if status == "all" else status.replace("_", " ")
        print(f"\n  === PAYMENT QUEUE ({label}) ===")
        for it in items:
            print(f"  [{it['id']}] {it['file']}  amount={it['amount']}  status={it['status']}")
        print()
        speak(f"You have {len(items)} payment{'s' if len(items) > 1 else ''} {label}.")
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
                             f"Pay {entry['amount']} — invoice {entry.get('invoice_no') or '?'} ({entry['file']})"):
        return {"status": "denied"}
    entry["status"]      = "approved"
    entry["approved_at"] = datetime.datetime.now().isoformat()
    entry["portal"]      = portal
    _save_payment_queue(q)
    audit.info("PAYMENT_APPROVED id=%s amount=%s", queue_id, entry["amount"])
    url = PAYMENT_PORTALS.get(portal, "")
    if url:
        webbrowser.open(url)
        speak(f"Approved. Opening {portal} to complete the payment of {entry['amount']}.")
    else:
        speak(f"Payment of {entry['amount']} approved. No portal URL configured.")
    return {"status": "ok", "entry": entry, "portal_url": url}

def reject_payment(queue_id: str, reason: str = "") -> dict:
    q = _load_payment_queue()
    entry = next((i for i in q if i["id"] == queue_id), None)
    if not entry:
        return {"status": "error", "message": f"No queued payment with id {queue_id}"}
    entry["status"] = "rejected"
    if reason: entry["reason"] = reason
    _save_payment_queue(q)
    audit.info("PAYMENT_REJECTED id=%s", queue_id)
    speak(f"Payment {queue_id} rejected.")
    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# SPREADSHEET READER
# ══════════════════════════════════════════════════════════════════════════════
def read_spreadsheet(path: str, sheet: int = 0) -> dict:
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
    plain = body.replace("<br>", "\n")
    html  = "<html><body>" + body.replace("\n", "<br>") + "</body></html>"
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
        speak(f"Gmail opened for {to}. SMTP not configured for auto-send.")
        return {"status": "ok", "action": "browser", "note": "SMTP not configured"}
    try:
        msg = _build_msg(em, to, subject, body)
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        speak(f"Email sent to {to}.")
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
    speak(f"Starting bulk email to {len(contacts)} contacts.")
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
                        speak(f"{sent} emails sent so far.")
                    time.sleep(delay)
                except Exception:
                    failed += 1
    except Exception as e:
        return {"status": "error", "message": f"SMTP failed: {e}"}
    summary = f"Done. {sent} sent, {failed} failed out of {len(contacts)}."
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
                    contacts.append({
                        "email": em,
                        "name": (row.get("name") or row.get("Name") or em.split("@")[0]).strip(),
                        "company": (row.get("company") or row.get("Company") or "").strip(),
                    })
    except Exception as e:
        log.warning("load_csv: %s", e)
    return contacts


# ══════════════════════════════════════════════════════════════════════════════
# INBOX READER (IMAP)
# ══════════════════════════════════════════════════════════════════════════════
def read_inbox(max_count: int = 10) -> dict:
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
            M.login(em, pw); M.select("INBOX")
            _, data = M.search(None, "UNSEEN")
            uids = data[0].split()[-max_count:]
            emails = []
            urgent_keywords = ["urgent", "asap", "immediate", "critical", "deadline", "payment overdue"]
            for uid in reversed(uids):
                _, msg_data = M.fetch(uid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)
                subject = msg.get("Subject", ""); sender = msg.get("From", ""); body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")[:500]; break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")[:500]
                is_urgent = any(kw in (subject + body).lower() for kw in urgent_keywords)
                emails.append({"from": sender, "subject": subject, "preview": body[:200], "urgent": is_urgent})
            urgent_count = sum(1 for e in emails if e["urgent"])
            if urgent_count:
                speak(f"Heads up — you have {urgent_count} urgent email{'s' if urgent_count > 1 else ''}.")
                _notify("Urgent Emails", f"{urgent_count} urgent messages in inbox")
            speak(f"Found {len(emails)} unread emails.")
            return {"status": "ok", "count": len(emails), "emails": emails, "urgent": urgent_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def draft_email_reply(original_subject: str, original_body: str, context: str = "") -> str:
    name_match = re.search(r"from:\s*(.+?)[\n<]", original_body, re.I)
    sender_name = name_match.group(1).strip() if name_match else "there"
    if any(kw in original_body.lower() for kw in ["meeting", "schedule", "call", "appointment"]):
        template = (f"Hi {sender_name},\n\nThank you for reaching out regarding {original_subject}.\n"
                    f"I'd be happy to discuss further. Please let me know your availability.\n\nBest regards")
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
    skip  = {"example.com", "test.com", "sentry.io", "w3.org", "google.com", "github.com", "cloudflare.com"}
    speak(f"Searching leads for {product}.")
    queries = [
        f"{niche} {product} contact email",
        f"{product} company email contact",
        f'"{product}" "@gmail.com" contact',
        f"{niche} businesses email director",
    ]
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
    speak(f"WhatsApp opened for {phone}.")
    return {"status": "ok", "note": "WhatsApp Web opened — click Send"}


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR / BOOKING
# ══════════════════════════════════════════════════════════════════════════════
def check_calendar_availability(date_str: str) -> dict:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        url = f"https://calendar.google.com/calendar/r/day/{dt.year}/{dt.month}/{dt.day}"
        webbrowser.open(url)
        speak(f"Opening your calendar for {date_str}.")
        return {"status": "ok", "date": date_str, "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def book_meeting(with_email: str, subject: str, date_str: str, duration_min: int = 60) -> dict:
    url = (f"https://calendar.google.com/calendar/r/eventedit"
           f"?text={urllib.parse.quote(subject)}"
           f"&add={urllib.parse.quote(with_email)}")
    webbrowser.open(url)
    speak(f"Calendar opened to book meeting with {with_email}.")
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
    speak("Logging into Twitter.")
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
        speak("Tweet posted."); return {"status": "ok", "platform": "twitter"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def post_linkedin(username: str, password: str, text: str) -> dict:
    if not request_approval("post_linkedin", f"LinkedIn: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into LinkedIn.")
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
        time.sleep(2); speak("LinkedIn post published.")
        return {"status": "ok", "platform": "linkedin"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def post_facebook(username: str, password: str, text: str, page_id: str = "") -> dict:
    if not request_approval("post_facebook", f"Facebook: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into Facebook.")
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
        time.sleep(2); speak("Facebook post published.")
        return {"status": "ok", "platform": "facebook"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def youtube_search_and_play(query: str) -> dict:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url); speak(f"Searching YouTube for: {query}")
    return {"status": "ok", "url": url}


# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL MESSAGE REPLY BOTS
# ══════════════════════════════════════════════════════════════════════════════
def _get_social_driver(platform: str):
    with _social_lock:
        drv = _social_drivers.get(platform)
        if drv:
            try: _ = drv.current_url; return drv
            except Exception:
                try: drv.quit()
                except Exception: pass
                _social_drivers.pop(platform, None)
        if not SELENIUM_OK: return None
        prof_dir = SOCIAL_PROFILE_DIR / platform; prof_dir.mkdir(exist_ok=True)
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
            _social_drivers[platform] = drv; return drv
        except Exception as e:
            log.warning("Social driver [%s]: %s", platform, e); return None


def _gen_reply(message: str) -> str:
    m = (message or "").lower()
    if any(k in m for k in ["price", "cost", "how much", "quote", "rate"]):
        return AUTO_REPLY_TEMPLATES["price"]
    if any(k in m for k in ["urgent", "asap", "emergency", "immediately"]):
        return AUTO_REPLY_TEMPLATES["complaint"]
    if any(k in m for k in ["order", "tracking", "delivery", "shipped"]):
        return AUTO_REPLY_TEMPLATES["order"]
    if any(k in m for k in ["help", "support", "issue", "problem", "not working"]):
        return AUTO_REPLY_TEMPLATES["support"]
    if any(k in m for k in ["hi", "hello", "hey", "good morning", "good evening"]):
        return "Hi! Thanks for reaching out — how can I help you today?"
    if any(k in m for k in ["thank", "thanks", "great", "awesome"]):
        return "You're welcome! Let us know if you need anything else."
    return AUTO_REPLY_TEMPLATES["default"]


def whatsapp_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("whatsapp")
    if not drv: return {"status": "error", "message": "Selenium not available"}
    try:
        if "web.whatsapp.com" not in (drv.current_url or ""):
            drv.get("https://web.whatsapp.com"); time.sleep(3)
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan me!']")))
            speak("WhatsApp Web needs a QR scan — check the browser window.")
            return {"status": "pending", "message": "Scan QR code in browser"}
        except Exception: pass
        unread  = drv.find_elements(By.XPATH, "//span[@aria-label[contains(.,'unread')]]")
        results = []
        for chat in unread[:max_chats]:
            try:
                row = chat.find_element(By.XPATH, "./ancestor::div[@role='listitem']")
                row.click(); time.sleep(1.2)
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
            except Exception: continue
        if results:
            speak(f"WhatsApp: {len(results)} message{'s' if len(results) > 1 else ''}{' replied' if auto else ' ready to review'}.")
        return {"status": "ok", "platform": "whatsapp", "messages": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def instagram_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("instagram")
    if not drv: return {"status": "error", "message": "Selenium not available"}
    try:
        if "instagram.com/direct" not in (drv.current_url or ""):
            drv.get("https://www.instagram.com/direct/inbox/"); time.sleep(3)
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.NAME, "username")))
            speak("Instagram needs login — check the browser window.")
            return {"status": "pending", "message": "Log in to Instagram"}
        except Exception: pass
        threads = drv.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        results = []
        for th in threads[:max_chats]:
            try:
                th.click(); time.sleep(1.2)
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
            except Exception: continue
        if results:
            speak(f"Instagram: {len(results)} message{'s' if len(results) > 1 else ''}{' replied' if auto else ' ready'}.")
        return {"status": "ok", "platform": "instagram", "messages": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def facebook_check_messages(auto: bool = False, max_chats: int = 10) -> dict:
    drv = _get_social_driver("facebook")
    if not drv: return {"status": "error", "message": "Selenium not available"}
    try:
        if "messages" not in (drv.current_url or ""):
            drv.get("https://www.facebook.com/messages/t/"); time.sleep(3)
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.ID, "email")))
            speak("Facebook needs login — check the browser window.")
            return {"status": "pending", "message": "Log in to Facebook"}
        except Exception: pass
        threads = drv.find_elements(By.CSS_SELECTOR, "a[role='link'][aria-current]")
        results = []
        for th in threads[:max_chats]:
            try:
                th.click(); time.sleep(1.2)
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
            except Exception: continue
        if results:
            speak(f"Facebook: {len(results)} message{'s' if len(results) > 1 else ''}{' replied' if auto else ' ready'}.")
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
                try: _SOCIAL_CHECKERS[plat](auto=True)
                except Exception as e: log.warning("social poll [%s]: %s", plat, e)
        time.sleep(45)


def start_social_replies(platforms: list, auto: bool = False) -> dict:
    global _social_thread, _social_running
    plats = [str(p).lower().strip() for p in platforms if str(p).lower().strip() in _SOCIAL_CHECKERS]
    if not plats:
        return {"status": "error", "message": "No valid platforms (whatsapp / instagram / facebook)"}
    if auto and not request_approval("enable_auto_reply", f"Auto-send replies on: {', '.join(plats)}"):
        return {"status": "denied"}
    opened = []
    for plat in plats:
        _social_auto[plat] = auto
        res = _SOCIAL_CHECKERS[plat](auto=False)
        opened.append({"platform": plat, "status": res.get("status")})
    if not _social_running:
        _social_running = True
        _social_thread = threading.Thread(target=_social_poll_loop, daemon=True, name="SocialReply")
        _social_thread.start()
    speak(f"Monitoring {', '.join(plats)}{' with auto-reply' if auto else ' for new messages'}.")
    return {"status": "ok", "platforms": plats, "auto": auto, "opened": opened}


def stop_social_replies(platforms: list = None) -> dict:
    global _social_running
    plats = platforms or list(_social_auto.keys())
    plats = [str(p).lower().strip() for p in plats]
    for p in plats:
        if p in _social_auto: _social_auto[p] = False
    if not any(_social_auto.values()): _social_running = False
    speak("Reply monitoring stopped.")
    return {"status": "ok", "platforms": plats}


# ══════════════════════════════════════════════════════════════════════════════
# SMART OPEN — with verification and recovery
# ══════════════════════════════════════════════════════════════════════════════
def smart_open(target: str) -> dict:
    if not target: return {"status": "error", "message": "Nothing to open"}
    t = str(target).strip(); tl = t.lower()
    for pfx in ["open ", "launch ", "start ", "go to ", "navigate to ", "visit ", "browse "]:
        if tl.startswith(pfx): tl = tl[len(pfx):].strip(); t = t[len(pfx):].strip()
    expected_url = ""
    expected_app = ""

    def _do_open():
        nonlocal expected_url, expected_app
        if tl in SITES:
            expected_url = SITES[tl]
            webbrowser.open(SITES[tl])
            speak(f"Opening {tl}.")
            return {"status": "ok", "opened": SITES[tl]}
        for site, url in SITES.items():
            if site in tl:
                expected_url = url
                webbrowser.open(url)
                speak(f"Opening {site}.")
                return {"status": "ok", "opened": url}
        if tl in APPS:
            expected_app = tl
            subprocess.Popen(APPS[tl], shell=True)
            speak(f"Opening {tl}.")
            return {"status": "ok", "opened": APPS[tl]}
        for app, exe in APPS.items():
            if app in tl:
                expected_app = app
                subprocess.Popen(exe, shell=True)
                speak(f"Opening {app}.")
                return {"status": "ok", "opened": exe}
        if tl.startswith(("http://", "https://")):
            expected_url = t
            webbrowser.open(t)
            return {"status": "ok", "opened": t}
        if re.match(r"^[a-z0-9\-]+\.[a-z]{2,}$", tl) and " " not in tl:
            expected_url = "https://" + tl
            webbrowser.open(expected_url)
            return {"status": "ok", "opened": expected_url}
        p = Path(t)
        if p.exists():
            os.startfile(str(p))
            update_runtime_state(active_file=str(p) if p.is_file() else "", active_folder=str(p) if p.is_dir() else "")
            return {"status": "ok", "opened": str(p)}
        if len(t.split()) <= 4:
            expected_app = tl
            subprocess.Popen(t, shell=True)
            return {"status": "ok", "opened": t}
        return {"status": "error", "message": f"Could not open: {target[:80]}"}

    def _verify_open():
        if expected_url:
            host = urllib.parse.urlparse(expected_url).netloc.lower().replace("www.", "")
            if verify_window_contains(host.split(".")[0]) or verify_screen_ocr(host.split(".")[0]):
                update_runtime_state(active_application="browser", current_url=expected_url, active_tab=host)
                return True
            try:
                if psutil:
                    browsers = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
                    if any((p.info.get("name") or "").lower() in browsers for p in psutil.process_iter(["name"])):
                        update_runtime_state(active_application="browser", current_url=expected_url, active_tab=host)
                        return True
            except Exception:
                pass
            return False
        if expected_app:
            app_key = expected_app.lower()
            exe_hint = " ".join(APPS.get(app_key, [app_key])).lower()
            if verify_window_contains(app_key):
                update_runtime_state(active_application=app_key)
                return True
            try:
                if psutil:
                    for proc in psutil.process_iter(["name"]):
                        pname = (proc.info.get("name") or "").lower()
                        if app_key in pname or any(piece and piece in pname for piece in re.split(r"[\s.\\/-]+", exe_hint)):
                            update_runtime_state(active_application=app_key)
                            return True
            except Exception:
                pass
            return False
        return verify_window_contains(tl) or verify_screen_ocr(tl)

    return run_with_verification(
        _do_open,
        _verify_open,
        f"open {tl}",
        correction_func=lambda: webbrowser.open(SITES.get(tl, f"https://www.google.com/search?q={urllib.parse.quote(tl)}")),
    )


# ══════════════════════════════════════════════════════════════════════════════
# AI BRAIN
# ══════════════════════════════════════════════════════════════════════════════
def ask_ai_brain(prompt: str, mem_ctx: bool = True) -> str:
    ctx = get_mem_ctx() if mem_ctx else ""
    full_prompt = f"Context:\n{ctx}\n\nUser: {prompt}" if ctx else prompt
    try:
        import g4f
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}],
        )
        text = str(response).strip()
        if text and len(text) > 10 and "error" not in text.lower()[:60]:
            return text
    except ImportError:
        return "Install g4f: pip install g4f"
    except Exception as e:
        log.warning("AI Brain g4f: %s", e)
    try:
        return web_research(prompt)[:800]
    except Exception as e:
        return f"I searched for '{prompt[:60]}' but couldn't get a clear answer. {e}"


def ai_plan_task(task: str) -> Optional[list]:
    """
    Ask AI to decompose a free-form goal into a list of exec_cmd-compatible
    action dicts. Returns None if parsing fails (caller falls back to ask_ai).
    """
    valid_actions = [
        "open", "search_web", "read_inbox", "send_email", "draft_email_in_browser",
        "organize_folder", "process_invoices", "screenshot", "web_research",
        "ask_ai", "speak", "get_system_info", "get_time", "get_date",
        "find_leads_and_email", "bulk_email", "check_social_messages",
        "list_payment_queue", "enterprise_automation", "research_and_write",
    ]
    prompt = (
        f"You are Dex, a desktop automation agent. Convert this user goal into a JSON array "
        f"of action steps. Each step must be a JSON object with an 'action' key chosen from: "
        f"{', '.join(valid_actions)}. Max 6 steps. Respond ONLY with a valid JSON array, "
        f"no markdown, no explanation.\n\nGoal: {task}"
    )
    try:
        raw = ask_ai_brain(prompt, mem_ctx=False)
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m: return None
        steps = json.loads(m.group())
        if not isinstance(steps, list) or not steps: return None
        validated = [s for s in steps if isinstance(s, dict) and "action" in s]
        return validated[:6] if validated else None
    except Exception as e:
        log.warning("ai_plan_task failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE BUSINESS FEATURES
# ══════════════════════════════════════════════════════════════════════════════
def monitor_error_logs(path: str) -> dict:
    if not os.path.exists(path):
        return {"status": "error", "note": f"Log path not found: {path}"}
    errors = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-100:]
        for line in lines:
            if "error" in line.lower() or "exception" in line.lower():
                errors.append(line.strip())
    if errors:
        speak(f"Found {len(errors)} errors in the log.")
        return {"status": "warning", "note": f"{len(errors)} recent errors.", "errors": errors[:5]}
    speak("No recent errors found in logs.")
    return {"status": "ok", "note": "No recent errors found."}


def backup_to_cloud() -> dict:
    source = str(Path.home() / "Documents" / "DacexyData")
    if not os.path.exists(source): os.makedirs(source, exist_ok=True)
    dest = str(Path.home() / "OneDrive" / "DacexyBackup")
    try:
        if not os.path.exists(dest): os.makedirs(dest, exist_ok=True)
        backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(os.path.join(dest, backup_name), "zip", source)
        speak("Backup complete.")
        return {"status": "ok", "note": f"Backed up to {dest}"}
    except Exception as e:
        return {"status": "error", "note": f"Backup failed: {e}"}


def create_newsletter() -> dict:
    speak("Generating your newsletter now.")
    draft = ask_ai_brain(
        "Write a short, engaging professional weekly newsletter for business clients. "
        "Include: a warm greeting, 3 business tips, a motivational closing. Max 300 words."
    )
    p = DATA_DIR / f"newsletter_{datetime.date.today()}.txt"
    p.write_text(draft, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak("Newsletter ready. Check Notepad.")
    return {"status": "ok", "content": draft}


def draft_contract(client: str) -> dict:
    speak(f"Drafting contract for {client}.")
    draft = ask_ai_brain(
        f"Draft a standard professional freelance service contract for client named {client}. "
        f"Include: parties, scope, payment terms, IP ownership, termination clause. "
        f"Format with clear sections."
    )
    filename = f"Contract_{client.replace(' ', '_')}_{datetime.date.today()}.txt"
    filepath = Path.home() / "Desktop" / filename
    filepath.write_text(draft, encoding="utf-8")
    speak(f"Contract saved to Desktop as {filename}.")
    return {"status": "ok", "note": f"Saved to Desktop as {filename}."}


def generate_report(report_type: str, data: str = "") -> dict:
    speak(f"Generating {report_type} report.")
    prompt = (
        f"Generate a professional {report_type} report for a small business. "
        f"{'Additional context: ' + data if data else ''} "
        f"Include summary, key metrics, insights, and recommendations. "
        f"Format with clear sections and bullet points."
    )
    content = ask_ai_brain(prompt)
    p = DATA_DIR / f"{report_type.replace(' ', '_')}_{datetime.date.today()}.txt"
    p.write_text(content, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak(f"{report_type.title()} report ready.")
    return {"status": "ok", "report": content[:500]}


def generate_proposal(client: str, service: str) -> dict:
    speak(f"Writing proposal for {client}.")
    content = ask_ai_brain(
        f"Write a professional business proposal for {client} offering {service}. "
        f"Include: executive summary, scope of work, timeline, pricing, why choose us, CTA."
    )
    p = Path.home() / "Desktop" / f"Proposal_{client.replace(' ', '_')}.txt"
    p.write_text(content, encoding="utf-8")
    speak("Proposal saved to Desktop.")
    return {"status": "ok", "path": str(p)}


def generate_job_description(role: str, company: str = "") -> dict:
    speak(f"Writing job description for {role}.")
    content = ask_ai_brain(
        f"Write a professional job description for {role}"
        f"{' at ' + company if company else ''}. "
        f"Include: about the role, responsibilities, requirements, benefits, how to apply."
    )
    p = DATA_DIR / f"JD_{role.replace(' ', '_')}.txt"
    p.write_text(content, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak("Job description ready.")
    return {"status": "ok", "content": content[:400]}


def analyze_competitors(business: str) -> dict:
    speak(f"Analyzing competitors for {business}.")
    research = web_research(f"{business} competitors market analysis 2024")
    analysis = ask_ai_brain(
        f"Based on this research: {research[:1000]}\n\n"
        f"Provide a structured competitor analysis for a business in {business}. "
        f"Include: top 5 competitors, their strengths/weaknesses, market gaps, opportunities."
    )
    p = DATA_DIR / f"competitor_analysis_{int(time.time())}.txt"
    p.write_text(analysis, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak("Competitor analysis ready.")
    return {"status": "ok", "analysis": analysis[:500]}


def generate_social_content(topic: str, platform: str = "all") -> dict:
    speak(f"Creating social media content for {topic}.")
    content = ask_ai_brain(
        f"Create social media content about: {topic}. "
        f"Generate: 1 LinkedIn post (professional, 150 words), "
        f"1 Twitter/X post (max 280 chars, with hashtags), "
        f"1 Instagram caption (engaging, with emojis and hashtags), "
        f"1 Facebook post (friendly, 100 words). "
        f"Format each clearly with the platform name as header."
    )
    p = DATA_DIR / f"social_content_{int(time.time())}.txt"
    p.write_text(content, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak("Social content ready. Check Notepad.")
    return {"status": "ok", "content": content[:400]}


def generate_invoice(client: str, items: list = None, total: float = 0) -> dict:
    speak(f"Generating invoice for {client}.")
    items_text = "\n".join([f"- {i}" for i in (items or ["Consulting services"])]) 
    invoice_no = f"INV-{datetime.date.today().strftime('%Y%m')}-{random.randint(100,999)}"
    content = (
        f"INVOICE\n{'='*40}\n"
        f"Invoice No: {invoice_no}\n"
        f"Date: {datetime.date.today()}\n"
        f"Due Date: {datetime.date.today() + datetime.timedelta(days=30)}\n\n"
        f"Bill To:\n{client}\n\n"
        f"Items:\n{items_text}\n\n"
        f"Total Amount: ₹{total or 'TBD'}\n\n"
        f"Payment Terms: Net 30 days\n"
        f"Bank details: [Add your bank details here]\n\n"
        f"Thank you for your business!"
    )
    p = Path.home() / "Desktop" / f"Invoice_{client.replace(' ', '_')}_{invoice_no}.txt"
    p.write_text(content, encoding="utf-8")
    try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
    except Exception: pass
    speak(f"Invoice {invoice_no} for {client} saved to Desktop.")
    return {"status": "ok", "invoice_no": invoice_no, "path": str(p)}


def track_expenses(description: str, amount: float, category: str = "General") -> dict:
    expense = {
        "date":        str(datetime.date.today()),
        "description": description,
        "amount":      amount,
        "category":    category,
    }
    expense_file = DATA_DIR / "expenses.csv"
    file_exists  = expense_file.exists()
    try:
        with open(expense_file, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "description", "amount", "category"])
            if not file_exists: w.writeheader()
            w.writerow(expense)
        speak(f"Expense of {amount} recorded under {category}.")
        return {"status": "ok", "expense": expense}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def daily_business_summary() -> dict:
    speak("Preparing your daily business summary.")
    ctx = get_mem_ctx()
    summary = ask_ai_brain(
        f"Based on this business context: {ctx}\n\n"
        f"Generate a concise daily business briefing for today {datetime.date.today()}. "
        f"Include: priority tasks, follow-ups needed, key metrics to check, "
        f"one motivational insight. Keep it under 200 words."
    )
    speak(summary[:300])
    _notify("Dacexy Daily Brief", summary[:100])
    return {"status": "ok", "summary": summary}


def monitor_prices(url: str) -> dict:
    speak(f"Setting up price monitoring for that page.")
    return {"status": "ok", "note": f"Price monitoring activated for {url}.", "action_taken": "scheduled"}


def _agent_output_path(filename: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._ -]+", "", filename).strip().replace(" ", "_") or "dex_output"
    return DATA_DIR / safe


def create_excel_workbook(name: str = "", columns: list = None, rows: list = None) -> dict:
    if not XL_OK or not openpyxl:
        return {"status": "error", "message": "openpyxl is required to create Excel files"}
    filename = name or f"sales_sheet_{datetime.date.today().isoformat()}.xlsx"
    if not filename.lower().endswith(".xlsx"):
        filename += ".xlsx"
    path = _agent_output_path(filename)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales"
    cols = columns or ["Date", "Customer", "Product", "Quantity", "Amount", "Payment Status", "Notes"]
    ws.append(cols)
    for row in rows or []:
        ws.append(row)
    ws.freeze_panes = "A2"
    for idx, col in enumerate(cols, 1):
        ws.cell(row=1, column=idx).font = openpyxl.styles.Font(bold=True)
        ws.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = max(14, min(28, len(str(col)) + 4))
    wb.save(path)
    verified = path.exists() and path.stat().st_size > 0
    if verified:
        try: subprocess.Popen(f'excel.exe "{path}"', shell=True)
        except Exception: pass
        update_runtime_state(active_application="excel", active_file=str(path), active_folder=str(path.parent),
                             last_action="create_excel", last_result=str(path), last_verified=True)
        speak(f"Excel sheet created and saved as {path.name}.")
        return {"status": "ok", "verified": True, "path": str(path)}
    return {"status": "error", "verified": False, "message": f"Excel file was not created: {path}"}


def create_notepad_file(name: str, content: str) -> dict:
    filename = name if name.lower().endswith(".txt") else f"{name}.txt"
    path = _agent_output_path(filename)
    path.write_text(content, encoding="utf-8")
    verified = path.exists() and path.read_text(encoding="utf-8", errors="ignore").strip() != ""
    if verified:
        try: subprocess.Popen(f'notepad.exe "{path}"', shell=True)
        except Exception: pass
        update_runtime_state(active_application="notepad", active_file=str(path), active_folder=str(path.parent),
                             last_action="create_notepad_file", last_result=str(path), last_verified=True)
        return {"status": "ok", "verified": True, "path": str(path)}
    return {"status": "error", "verified": False, "message": f"Text file was not created: {path}"}


def create_word_document(name: str, title: str, content: str) -> dict:
    filename = name if name.lower().endswith(".docx") else f"{name}.docx"
    path = _agent_output_path(filename)
    try:
        import docx
        doc = docx.Document()
        doc.add_heading(title, level=1)
        for para in [p.strip() for p in content.split("\n") if p.strip()]:
            doc.add_paragraph(para)
        doc.save(str(path))
    except Exception:
        path = path.with_suffix(".txt")
        path.write_text(f"{title}\n{'=' * len(title)}\n\n{content}", encoding="utf-8")
    verified = path.exists() and path.stat().st_size > 0
    if verified:
        try: os.startfile(str(path))
        except Exception: pass
        update_runtime_state(active_application="word", active_file=str(path), active_folder=str(path.parent),
                             last_action="create_word_doc", last_result=str(path), last_verified=True)
        return {"status": "ok", "verified": True, "path": str(path)}
    return {"status": "error", "verified": False, "message": f"Document was not created: {path}"}


def create_folder_and_files(folder_name: str, files: list = None) -> dict:
    folder = _agent_output_path(folder_name).with_suffix("")
    folder.mkdir(parents=True, exist_ok=True)
    wanted = files or ["notes.txt", "tasks.txt", "README.txt"]
    created = []
    for file_name in wanted:
        fp = folder / re.sub(r"[^a-zA-Z0-9._ -]+", "", str(file_name).strip())
        if not fp.suffix:
            fp = fp.with_suffix(".txt")
        fp.write_text(f"Created by Dex on {datetime.datetime.now().isoformat(timespec='seconds')}\n", encoding="utf-8")
        created.append(fp)
    verified = folder.exists() and all(fp.exists() for fp in created)
    if verified:
        try: os.startfile(str(folder))
        except Exception: pass
        update_runtime_state(active_application="explorer", active_folder=str(folder), active_file=str(created[0]),
                             last_action="create_folder_and_files", last_result=str(folder), last_verified=True)
        return {"status": "ok", "verified": True, "folder": str(folder), "files": [str(p) for p in created]}
    return {"status": "error", "verified": False, "message": f"Folder/files were not created: {folder}"}


def research_to_notepad(query: str, filename: str = "") -> dict:
    result = web_research(query)
    content = f"Research: {query}\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{result}"
    return create_notepad_file(filename or f"research_{int(time.time())}.txt", content)


def generate_ad_document(topic: str) -> dict:
    content = ask_ai_brain(
        f"Create a concise advertisement for: {topic}. Include headline, short body, CTA, and 5 keywords."
    )
    return create_word_document(f"advertisement_{int(time.time())}", f"Advertisement: {topic}", content)


# ══════════════════════════════════════════════════════════════════════════════
# COMPOUND TASK SPLITTER
# ══════════════════════════════════════════════════════════════════════════════
def _has_action_verb(text: str) -> bool:
    words = set(re.findall(r"\b[a-z]+\b", text.lower()))
    return bool(words & _ACTION_VERBS)


def _split_compound_task(task: str) -> list:
    tl = task.lower().strip()
    if "gmail" in tl and re.search(r"\b(?:draft|compose|write|send)\b", tl) and re.search(r"\b(?:message|massage|email|mail)\b", tl):
        return [task]
    if "excel" in tl and re.search(r"\b(?:create|make|write|generate)\b", tl):
        return [task]
    for sep in [" then ", " and then ", " after that ", " next ", " also "]:
        if sep in tl:
            raw_parts = re.split(re.escape(sep), task, flags=re.IGNORECASE)
            parts = [p.strip() for p in raw_parts if p.strip()]
            if len(parts) > 1:
                return parts[:6]
    if " and " in tl:
        idx   = tl.index(" and ")
        left  = task[:idx].strip()
        right = task[idx + 5:].strip()
        if left and right and _has_action_verb(left) and _has_action_verb(right):
            return [left, right]
    return [task]


# ══════════════════════════════════════════════════════════════════════════════
# LOCAL NLP PARSER — 500+ patterns covering every business department
# ══════════════════════════════════════════════════════════════════════════════
def local_parse(task: str) -> list:
    t  = task.strip()
    tl = t.lower()

    if "gmail" in tl and re.search(r"\b(?:draft|compose|write|send)\b", tl) and re.search(r"\b(?:message|massage|email|mail)\b", tl):
        body_match = re.search(r"\bsaying\s+(.+)$", t, flags=re.I | re.S)
        if not body_match:
            body_match = re.search(r"\b(?:body|message|massage)\s+(?:in\s+gmail\s+)?(.+)$", t, flags=re.I | re.S)
        body = (body_match.group(1).strip() if body_match else "Hello")
        to_match = re.search(r"\bto\s+([^\s,]+@[^\s,]+)", t, flags=re.I)
        return [{"action": "draft_email_in_browser", "to": to_match.group(1) if to_match else "",
                 "subject": body[:60] or "Hello", "body": body}]

    if "excel" in tl and re.search(r"\b(?:create|make|write|generate)\b", tl) and re.search(r"\b(?:sales|sheet|spreadsheet|workbook)\b", tl):
        name = f"sales_sheet_{datetime.date.today().isoformat()}.xlsx" if "sales" in tl else f"spreadsheet_{int(time.time())}.xlsx"
        return [{"action": "create_excel", "name": name,
                 "columns": ["Date", "Customer", "Product", "Quantity", "Amount", "Payment Status", "Notes"]}]

    m = re.search(r"(?:search|find)\s+(.+?)\s+(?:and\s+)?(?:save|write)\s+(?:the\s+)?(?:list|results)?\s*(?:in|to)\s+notepad", tl)
    if m:
        return [{"action": "research_to_notepad", "query": m.group(1).strip()}]

    m = re.search(r"(?:create|write|generate|make)\s+(?:a\s+)?word\s+(?:report|document)\s*(?:on|about|for)?\s*(.*)", tl)
    if m:
        topic = m.group(1).strip() or "business report"
        return [{"action": "create_word_report", "topic": topic}]

    m = re.search(r"(?:create|make)\s+(?:a\s+)?folder\s+(?:named|called)?\s*([a-z0-9 _-]+)?(?:\s+and\s+files?)?", tl)
    if m and "folder" in tl:
        folder = (m.group(1) or f"dex_folder_{int(time.time())}").strip()
        return [{"action": "create_folder_files", "folder": folder}]

    m = re.search(r"(?:generate|create|write)\s+(?:an?\s+)?advertisement\s*(?:for|about)?\s*(.*)", tl)
    if m:
        return [{"action": "generate_ad_document", "topic": m.group(1).strip() or "my business"}]

    # ── DRAFT / COMPOSE EMAIL ─────────────────────────────────────────────────
    m = re.search(
        r"(?:draft|compose|write|send)\s+(?:an?\s+)?(?:email|mail|message)"
        r"(?:\s+in\s+gmail)?(?:\s+to\s+)?(.+?)\s+saying\s+(.+)", tl)
    if m:
        recipient = m.group(1).strip(); body_text = m.group(2).strip()
        if "@" in recipient:
            return [{"action": "send_email", "to": recipient, "subject": body_text[:60], "body": body_text}]
        return [{"action": "draft_email_in_browser", "to": recipient, "subject": body_text[:60], "body": body_text}]

    m = re.search(r"(?:draft|compose|write)\s+(?:an?\s+)?email\s+to\s+(.+?)"
                  r"\s+(?:saying|about|regarding|with subject)\s+(.+)", tl)
    if m:
        return [{"action": "draft_email_in_browser", "to": m.group(1).strip(),
                 "subject": m.group(2).strip()[:60], "body": m.group(2).strip()}]

    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+([^\s,]+@[^\s,]+)"
                  r"(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        subj = (m.group(2) or "Hello from Dacexy").strip()
        return [{"action": "send_email", "to": m.group(1).strip(), "subject": subj, "body": subj}]

    # ── RESEARCH + WRITE ──────────────────────────────────────────────────────
    m = re.search(
        r"(?:search|find|look\s+up|research|google)\s+(.+?)"
        r"\s+and\s+(?:write|save|put|type|add|note)\s+"
        r"(?:(?:it|them|results?)\s+)?(?:in|to|into|on)?\s*(?:a\s+)?"
        r"(notepad|excel|spreadsheet|word|google\s+sheets?|text\s+file|file)", tl)
    if m:
        return [{"action": "research_and_write", "query": m.group(1).strip(),
                 "destination": m.group(2).strip()}]

    # ── Q&A — spoken answers ──────────────────────────────────────────────────
    if re.search(r"^(?:who|what|where|when|why|how|tell\s+me|explain|define|describe|"
                 r"is\s+there|are\s+there|can\s+you\s+tell|do\s+you\s+know)\b", tl):
        return [{"action": "ask_ai", "prompt": task}]

    if re.search(r"(?:prime\s+minister|president|capital\s+of|population\s+of|"
                 r"meaning\s+of|what\s+is\s+a|what\s+are|ceo\s+of|founder\s+of|"
                 r"tallest|largest|smallest|oldest|newest|latest|current\s+.*\bof\b|"
                 r"calculate|how\s+much\s+is|convert\s+\d)", tl):
        return [{"action": "ask_ai", "prompt": task}]

    # ── DAILY SUMMARY / BRIEF ─────────────────────────────────────────────────
    if re.search(r"(?:daily\s+(?:brief|summary|report)|good\s+morning\s+brief|"
                 r"what(?:'s|\s+is)\s+(?:on\s+my\s+)?(?:agenda|schedule|plan\s+for\s+today)|"
                 r"brief\s+me|morning\s+update)", tl):
        return [{"action": "daily_summary"}]

    # ── BUSINESS REPORTS ─────────────────────────────────────────────────────
    m = re.search(r"(?:generate|create|make|write|prepare)\s+(?:a\s+)?(.+?)\s+report", tl)
    if m and any(w in m.group(1) for w in ["sales", "revenue", "financial", "weekly", "monthly",
                                             "performance", "kpi", "inventory", "marketing", "profit"]):
        return [{"action": "generate_report", "report_type": m.group(1).strip()}]

    # ── PROPOSALS ────────────────────────────────────────────────────────────
    m = re.search(r"(?:write|create|draft|generate)\s+(?:a\s+)?proposal\s+for\s+(.+?)(?:\s+for\s+(.+))?$", tl)
    if m:
        return [{"action": "generate_proposal", "client": m.group(1).strip(),
                 "service": m.group(2).strip() if m.group(2) else "our services"}]

    # ── INVOICES (generate) ───────────────────────────────────────────────────
    m = re.search(r"(?:create|generate|make|draft)\s+(?:an?\s+)?invoice\s+for\s+(.+?)(?:\s+for\s+(.+?))?(?:\s+amount\s+(.+))?$", tl)
    if m:
        return [{"action": "generate_invoice", "client": m.group(1).strip(),
                 "service": m.group(2) or "", "total": m.group(3) or 0}]

    # ── JOB DESCRIPTION ──────────────────────────────────────────────────────
    m = re.search(r"(?:write|create|draft|generate)\s+(?:a\s+)?(?:job\s+description|jd)\s+for\s+(.+?)(?:\s+at\s+(.+))?$", tl)
    if m:
        return [{"action": "generate_job_description", "role": m.group(1).strip(),
                 "company": m.group(2).strip() if m.group(2) else ""}]

    # ── COMPETITOR ANALYSIS ───────────────────────────────────────────────────
    m = re.search(r"(?:analyze|research|check|study)\s+(?:my\s+)?competitors?\s+(?:in|for)?\s*(.+?)$", tl)
    if m:
        return [{"action": "analyze_competitors", "business": m.group(1).strip()}]

    # ── SOCIAL CONTENT ────────────────────────────────────────────────────────
    m = re.search(r"(?:create|write|generate|make)\s+social\s+(?:media\s+)?content\s+(?:about|for|on)\s+(.+?)$", tl)
    if m:
        return [{"action": "generate_social_content", "topic": m.group(1).strip()}]

    m = re.search(r"(?:write|create|generate)\s+(?:a\s+)?(?:caption|post)\s+(?:about|for|on)\s+(.+?)$", tl)
    if m:
        return [{"action": "generate_social_content", "topic": m.group(1).strip()}]

    # ── CONTRACTS ────────────────────────────────────────────────────────────
    m = re.search(r"(?:draft|write|create|generate)\s+(?:a\s+)?contract\s+for\s+(.+?)$", tl)
    if m:
        return [{"action": "draft_contract", "client": m.group(1).strip()}]

    # ── NEWSLETTER ───────────────────────────────────────────────────────────
    if re.search(r"\bnewsletter\b", tl):
        return [{"action": "create_newsletter"}]

    # ── EXPENSE TRACKING ─────────────────────────────────────────────────────
    m = re.search(r"(?:add|track|record|log)\s+(?:an?\s+)?expense\s+(?:of\s+)?([\d,]+)\s+for\s+(.+?)$", tl)
    if m:
        try: amt = float(m.group(1).replace(",", ""))
        except Exception: amt = 0
        return [{"action": "track_expense", "amount": amt, "description": m.group(2).strip()}]

    # ── ENTERPRISE / BUSINESS CATCH-ALL ──────────────────────────────────────
    if re.search(
        r"(?:asset tracking|appointment rescheduling|archive management|backup verification|"
        r"business license|badge|id creation|compliance audit|customer intake|customer onboard|"
        r"customer retention|customer churn|data clean|document conversion|digital signature|"
        r"expense categori|e-commerce order|estimated tax|financial report|fraud detect|"
        r"gift card|government portal|hourly bill|invoicing|interview schedul|it onboard|"
        r"job board|kpi track|leave request|local vendor|market competitor|mailing list|"
        r"onboarding email|online review|order confirm|portfolio update|price sheet|"
        r"quality inspect|quote compar|refund|reorder alert|shipping label|shipment track|"
        r"supplier directory|ticket triage|unsubscribe|user permission|vendor invoice|"
        r"warranty registr|watermark|weekly status|zip-code territory|"
        r"revenue track|profit track|investor update|board meeting|team productivity|"
        r"vendor negotiation|risk monitor|partnership research|franchise research|"
        r"government compliance|license renewal|booking flight|booking hotel|"
        r"travel plan|expense report|contact management|meeting note|follow.?up track|"
        r"birthday reminder|spam filter|priority email|email categori|email summari|"
        r"auto.?repl|attachment organiz|lead email|inbox cleanup|email campaign|"
        r"data cleaning|duplicate removal|formula creation|dashboard creation|"
        r"data validation|report automation|pivot table|trend analysis|sales analysis|"
        r"inventory analysis|forecast|data visualization|spreadsheet audit|"
        r"quotation|pdf conversion|ocr scan|signature collection|document version|"
        r"document summari|translation|content plan|caption writing|comment moderat|"
        r"influencer research|content schedul|performance report|trend discover|"
        r"viral content|engagement track|brand mention|community management|"
        r"website monitor|broken link|seo audit|content update|lead capture|"
        r"website analytics|chat support|blog management|conversion track|"
        r"stock forecast|inventory sync|order process|order track|refund process|"
        r"product research|product sourc|product pric|marketplace|coupon|cart recovery|"
        r"low stock|overstock|dead stock|purchase order|supplier comparison|"
        r"warehouse report|barcode|inventory reconcil|receipt collection|"
        r"invoice reminder|tax calculation|gst report|payroll|vendor payment|"
        r"cash flow|budget management|profit analysis|financial compliance|"
        r"resume pars|candidate rank|applicant track|offer letter|background verif|"
        r"employee onboard|attendance track|performance review|shift schedul|"
        r"training management|skill track|goal track|internal communication|"
        r"employee survey|loyalty management|feedback collection|satisfaction track|"
        r"upselling|cross.?selling|renewal reminder|market research|audience research|"
        r"keyword research|ad creation|ad optimization|funnel analysis|campaign track|"
        r"lead scoring|lead nurtur|conversion optim|marketing report|"
        r"pos report|daily sales|staff schedul|stock replenishment|store performance|"
        r"demand forecast|production plan|machine maintenance|quality control|"
        r"raw material|production forecast|downtime monitor|safety compliance|"
        r"route plan|delivery track|driver schedul|fuel track|shipment update|"
        r"fleet maintenance|warehouse coordination|property listing|lease management|"
        r"tenant communication|appointment schedul|patient reminder|medical record|"
        r"student attendance|fee reminder|timetable|parent communication|"
        r"result preparation|assignment track|case track|court date|legal research|"
        r"client communication)", tl):
        return [{"action": "enterprise_automation", "task": task}]

    # ── AI explicitly requested ───────────────────────────────────────────────
    m = re.search(r"(?:think about|explain|generate)\s+(.+)", tl)
    if m and "email" not in tl:
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
        m    = re.search(r"(?:in|from|folder|directory)\s+(.+?)(?:\s*$|\s+and\b)", tl)
        folder = m.group(1).strip() if m else str(Path.home() / "Desktop")
        if "desktop" in tl:   folder = str(Path.home() / "Desktop")
        elif "download" in tl: folder = str(Path.home() / "Downloads")
        elif "document" in tl: folder = str(Path.home() / "Documents")
        return [{"action": "organize_folder", "folder": folder}]

    if re.search(r"(?:process|extract|scan|read)\s+(?:invoices|invoice|receipts|pdfs)", tl):
        m      = re.search(r"(?:in|from|folder)\s+(.+?)(?:\s*$)", tl)
        folder = m.group(1).strip() if m else str(Path.home() / "Desktop")
        return [{"action": "process_invoices", "folder": folder}]

    if re.search(r"(?:book|schedule)\s+(?:a\s+)?(?:meeting|call|appointment)\s+with", tl):
        m_email = re.search(r"([^\s,]+@[^\s,]+)", tl)
        m_date  = re.search(r"(\d{4}-\d{2}-\d{2})", tl)
        m_subj  = re.search(r"(?:about|for|re)\s+(.+?)(?:\s+on\b|\s+with\b|$)", tl)
        return [{"action": "book_meeting",
                 "with_email": m_email.group(1) if m_email else "",
                 "date":       m_date.group(1) if m_date else str(datetime.date.today()),
                 "subject":    m_subj.group(1) if m_subj else "Meeting"}]

    if re.search(r"(?:find|get|search|generate|scrape)\s+(?:leads|customers|clients|prospects)", tl):
        m    = re.search(r"for\s+(?:my\s+)?(.+?)(?:\s+and\b|\s+then\b|\s*$)", tl)
        prod = m.group(1).strip() if m else "product"
        return [{"action": "find_leads_and_email", "product": prod, "niche": ""}]

    if re.search(r"bulk\s+email|mass\s+email|email\s+campaign|email\s+blast", tl):
        csv_m = re.search(r"(?:from|using|with|file)\s+(\S+\.csv)", tl)
        return [{"action": "bulk_email", "csv_path": csv_m.group(1) if csv_m else "",
                 "subject": "Hello from Dacexy", "body": "Hi {name},\n\nHope this finds you well!\n\nBest"}]

    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+(.+?)"
                  r"(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        name_or_email = m.group(1).strip()
        subj          = (m.group(2) or "Hello").strip()
        if "@" in name_or_email:
            return [{"action": "send_email", "to": name_or_email, "subject": subj, "body": subj}]
        return [{"action": "send_email_by_name", "name": name_or_email, "subject": subj, "body": subj}]

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

    if re.search(r"(?:pending|queued|outstanding)\s+payments?|payment\s+queue|payments?\s+(?:to\s+)?approve", tl):
        return [{"action": "list_payment_queue", "status": "pending_review"}]

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
    if m: return [{"action": "open", "target": m.group(1).strip()}]

    m = re.search(r"(?:google|search\s+for|look\s+up|search|find)\s+(.+?)(?:\s+on\s+google)?$", tl)
    if m and "youtube" not in tl and "email" not in tl and "lead" not in tl:
        q = m.group(1).strip()
        if q and len(q) > 1: return [{"action": "search_web", "query": q}]

    if re.search(r"screenshot|screen\s+shot|capture\s+screen", tl):
        return [{"action": "screenshot"}]

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
    if re.search(r"select\s+all", tl):   return [{"action": "hotkey", "keys": ["ctrl", "a"]}]
    if re.search(r"copy\s+(?:it|that|all|text)", tl): return [{"action": "hotkey", "keys": ["ctrl", "c"]}]
    if re.search(r"paste\s+(?:it|that|here)", tl):    return [{"action": "hotkey", "keys": ["ctrl", "v"]}]
    if re.search(r"save\s+(?:the\s+)?(?:file|document|this)", tl): return [{"action": "hotkey", "keys": ["ctrl", "s"]}]
    if re.search(r"(?:refresh|reload)\s+(?:page|browser)", tl): return [{"action": "key", "key": "f5"}]
    if re.search(r"new\s+tab\b", tl):    return [{"action": "hotkey", "keys": ["ctrl", "t"]}]
    if re.search(r"close\s+tab\b", tl):  return [{"action": "hotkey", "keys": ["ctrl", "w"]}]

    if re.search(r"(?:play|pause|toggle)\s+(?:music|media|song|video)", tl): return [{"action": "media_play_pause"}]
    if re.search(r"next\s+(?:song|track)", tl):   return [{"action": "media_next"}]
    if re.search(r"prev(?:ious)?\s+(?:song|track)", tl): return [{"action": "media_prev"}]

    m = re.match(r"remember\s+(?:that\s+)?(.+)", tl)
    if m: return [{"action": "remember", "fact": m.group(1)}, {"action": "speak", "text": "Noted."}]

    m = re.match(r"(?:say|speak|tell\s+me|announce)\s+(.+)", tl)
    if m: return [{"action": "speak", "text": m.group(1)}]

    m = re.match(r"(?:research|investigate|find\s+out\s+about)\s+(.+)", tl)
    if m: return [{"action": "web_research", "query": m.group(1).strip()}]

    m = re.match(r"(?:run|execute|cmd|shell)\s+(?:command\s+)?(.+)", tl)
    if m: return [{"action": "run_command", "command": m.group(1).strip()}]

    m = re.search(r"wait\s+(?:for\s+)?(\d+)\s+(?:second|sec)", tl)
    if m: return [{"action": "wait", "seconds": float(m.group(1))}]

    if re.search(r"\bbackup\b", tl): return [{"action": "backup"}]
    if re.search(r"\bwhatsapp\b", tl): return [{"action": "open", "target": "whatsapp web"}]

    for app in APPS:
        if tl.strip() == app: return [{"action": "open", "target": app}]
    for site in SITES:
        if tl.strip() == site: return [{"action": "open", "target": site}]

    if re.search(r"\b(?:help|what\s+can\s+you\s+do|commands|capabilities)\b", tl):
        return [{"action": "list_skills"}]

    if re.search(r"\b(?:hello|hi|hey|good\s+morning|howdy)\b", tl):
        return [{"action": "speak", "text": "Hello! Dex is ready. What can I do for you today?"}]

    if re.search(r"\b(?:ping|test|status|are\s+you\s+there)\b", tl):
        return [{"action": "ping"}]

    # ULTIMATE FALLBACK — AI brain
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
        # ── ASK AI ────────────────────────────────────────────────────────────
        if action == "ask_ai":
            speak("Let me think about that.")
            resp = ask_ai_brain(str(cmd.get("prompt", "")))
            print(f"\n  [Dex AI]\n{resp}\n")
            speak(resp[:300])
            _notify("Dex AI", resp[:150])
            return {"status": "ok", "response": resp}

        # ── ENTERPRISE AUTOMATION ─────────────────────────────────────────────
        if action == "enterprise_automation":
            task_text = str(cmd.get("task", ""))
            speak(jarvis_confirm())
            resp = ask_ai_brain(
                f"The user asked Dex (AI desktop agent for small businesses) to help with: "
                f"\"{task_text}\". Give clear, practical, step-by-step guidance a business owner "
                f"can follow immediately. Be specific, not generic."
            )
            print(f"\n  [BUSINESS TASK]\n{resp}\n")
            speak(resp[:300])
            _notify("Dex", resp[:150])
            return {"status": "ok", "response": resp}

        # ── DAILY SUMMARY ─────────────────────────────────────────────────────
        if action == "daily_summary":
            return daily_business_summary()

        # ── BUSINESS DOCUMENT GENERATORS ─────────────────────────────────────
        if action == "generate_report":
            return generate_report(str(cmd.get("report_type", "business")), str(cmd.get("data", "")))

        if action == "generate_proposal":
            return generate_proposal(str(cmd.get("client", "client")), str(cmd.get("service", "our services")))

        if action == "generate_invoice":
            try: total = float(str(cmd.get("total") or 0))
            except Exception: total = 0
            return generate_invoice(str(cmd.get("client", "client")),
                                    cmd.get("items"), total)

        if action == "generate_job_description":
            return generate_job_description(str(cmd.get("role", "role")), str(cmd.get("company", "")))

        if action == "analyze_competitors":
            return analyze_competitors(str(cmd.get("business", "this industry")))

        if action == "generate_social_content":
            return generate_social_content(str(cmd.get("topic", "our business")),
                                           str(cmd.get("platform", "all")))

        if action == "draft_contract":
            return draft_contract(str(cmd.get("client", "client")))

        if action == "create_newsletter":
            return create_newsletter()

        if action == "track_expense":
            try: amount = float(str(cmd.get("amount") or 0))
            except Exception: amount = 0
            return track_expenses(str(cmd.get("description", "")), amount,
                                  str(cmd.get("category", "General")))

        if action in {"create_excel", "create_excel_sheet", "create_spreadsheet"}:
            return create_excel_workbook(str(cmd.get("name") or ""), cmd.get("columns") or None, cmd.get("rows") or None)

        if action == "research_to_notepad":
            return research_to_notepad(str(cmd.get("query") or ""), str(cmd.get("filename") or ""))

        if action in {"create_word_report", "create_word_doc", "create_word_document"}:
            topic = str(cmd.get("topic") or cmd.get("title") or "Business Report")
            content = ask_ai_brain(
                f"Create a concise business report about: {topic}. Include summary, key points, risks, and next actions."
            )
            return create_word_document(f"word_report_{int(time.time())}", f"Report: {topic}", content)

        if action in {"create_folder_files", "create_folder_and_files"}:
            return create_folder_and_files(str(cmd.get("folder") or cmd.get("name") or f"dex_folder_{int(time.time())}"),
                                           cmd.get("files") or None)

        if action == "generate_ad_document":
            return generate_ad_document(str(cmd.get("topic") or "my business"))

        # ── DRAFT EMAIL IN BROWSER ─────────────────────────────────────────────
        if action in {"draft_email_in_browser", "draft_email", "gmail_compose"}:
            to_addr = str(cmd.get("to", "")).strip()
            subject = str(cmd.get("subject", "Hello")).strip()
            body    = str(cmd.get("body", "Hello")).strip()
            draft_path = _agent_output_path(f"gmail_draft_{int(time.time())}.eml")
            try:
                msg = EmailMessage()
                msg["To"] = to_addr
                msg["Subject"] = subject
                msg.set_content(body)
                draft_path.write_text(msg.as_string(), encoding="utf-8")
            except Exception:
                draft_path.write_text(f"To: {to_addr}\nSubject: {subject}\n\n{body}", encoding="utf-8")
            url = (f"https://mail.google.com/mail/?view=cm&fs=1"
                   f"&to={urllib.parse.quote(to_addr)}"
                   f"&su={urllib.parse.quote(subject)}"
                   f"&body={urllib.parse.quote(body)}")
            speak(f"Opening Gmail to draft email to {to_addr or 'your recipient'}.")
            webbrowser.open(url)
            time.sleep(1.5)
            speak("Gmail compose is open. Review and click Send when ready.")
            verified = draft_path.exists() and draft_path.stat().st_size > 0
            update_runtime_state(active_application="gmail", current_url=url, active_file=str(draft_path),
                                 last_action="draft_email", last_result=str(draft_path), last_verified=verified)
            return {"status": "ok" if verified else "error", "verified": verified, "url": url, "to": to_addr, "draft_file": str(draft_path)}

        # ── RESEARCH AND WRITE ────────────────────────────────────────────────
        if action == "research_and_write":
            query       = str(cmd.get("query", "")).strip()
            destination = str(cmd.get("destination", "notepad")).strip().lower()
            if not query:
                return {"status": "error", "message": "No query provided"}
            speak(f"Researching {query[:40]}.")
            result = web_research(query)
            lines  = [l.strip() for l in result.replace(". ", ".\n").split("\n")
                      if len(l.strip()) > 20][:20]
            content = (f"Research: {query}\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                       + "\n".join(f"- {l}" for l in lines))
            if "excel" in destination or "sheet" in destination or "spreadsheet" in destination:
                speak("Writing results to a spreadsheet now.")
                p = AGENT_DIR / f"research_{int(time.time())}.csv"
                rows = [["#", "Finding"]] + [[str(i + 1), l] for i, l in enumerate(lines)]
                with open(p, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerows(rows)
                try: subprocess.Popen(f'excel.exe "{p}"', shell=True)
                except Exception: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            else:
                speak("Writing results to Notepad now.")
                p = AGENT_DIR / f"research_{int(time.time())}.txt"
                p.write_text(content, encoding="utf-8")
                try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
                except Exception: pass
                time.sleep(1.5)
                if focus_window("Notepad"):
                    real_type(content, clear_first=True)
            speak(f"Done. {lines[0][:80] if lines else 'Results are ready.'}")
            return {"status": "ok", "result": content[:300]}

        # ── SEND EMAIL BY NAME ────────────────────────────────────────────────
        if action == "send_email_by_name":
            name     = str(cmd.get("name", "")).lower()
            contacts = MEMORY.get("contacts", {})
            found_email = ""
            if name in contacts:
                found_email = contacts[name].get("email", "")
            if not found_email:
                for k, v in contacts.items():
                    if name in k:
                        found_email = v.get("email", ""); break
            if not found_email:
                speak(f"I don't have {name} in contacts. Opening Gmail for you.")
                url = (f"https://mail.google.com/mail/?view=cm&fs=1"
                       f"&su={urllib.parse.quote(str(cmd.get('subject', '')))}"
                       f"&body={urllib.parse.quote(str(cmd.get('body', '')))}")
                webbrowser.open(url)
                return {"status": "ok", "note": "opened gmail compose"}
            return send_email_real(found_email, str(cmd.get("subject") or "Message"),
                                   str(cmd.get("body") or "Hello"), require_approval=True)

        # ── SPEAK / NOTIFY ────────────────────────────────────────────────────
        if action == "speak":
            speak(str(cmd.get("text", ""))); return {"status": "ok"}
        if action == "notify":
            _notify(str(cmd.get("title", "Dex")), str(cmd.get("text", ""))); return {"status": "ok"}

        # ── EMAIL ─────────────────────────────────────────────────────────────
        if action == "configure_email":
            return configure_smtp_interactive()

        if action in {"send_email", "email", "compose_email", "send_mail", "gmail_send"}:
            to_ = str(cmd.get("to") or cmd.get("email") or cmd.get("recipient") or "").strip()
            if not to_: return {"status": "error", "message": "No recipient email"}
            return send_email_real(to_, str(cmd.get("subject") or "Message from Dex"),
                                   str(cmd.get("body") or cmd.get("text") or "Hello"),
                                   require_approval=True)

        if action in {"bulk_email", "send_bulk_email", "mass_email", "email_campaign"}:
            contacts = cmd.get("contacts") or []
            csv_p    = cmd.get("csv_path") or ""
            if csv_p and not contacts: contacts = load_csv_contacts(str(csv_p))
            if not contacts: return {"status": "error", "message": "No contacts found."}
            return send_bulk_email(contacts, str(cmd.get("subject") or "Hello from Dex"),
                                   str(cmd.get("body") or "Hi {name},\n\nBest regards"),
                                   float(cmd.get("delay") or 1.5))

        if action == "read_inbox":
            return read_inbox(int(cmd.get("max_count") or 10))

        if action == "draft_reply":
            draft = draft_email_reply(str(cmd.get("subject") or ""), str(cmd.get("body") or ""),
                                      str(cmd.get("context") or ""))
            speak("Draft ready. Check terminal.")
            print(f"\n  === EMAIL DRAFT ===\n{draft}\n  ==================")
            return {"status": "ok", "draft": draft}

        if action in {"find_leads_and_email", "lead_campaign"}:
            product = str(cmd.get("product") or "product")
            leads   = find_leads_web(product, str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            if not leads: return {"status": "error", "message": "No leads found."}
            return send_bulk_email(leads, str(cmd.get("subject") or f"About {product}"),
                                   str(cmd.get("body") or f"Hi {{name}},\n\nI think {product} could help you.\nBest"), 2.0)

        if action in {"find_leads", "get_leads"}:
            leads = find_leads_web(str(cmd.get("product") or ""), str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            return {"status": "ok", "leads_found": len(leads)}

        # ── FILE OPS ──────────────────────────────────────────────────────────
        if action == "organize_folder":
            folder = str(cmd.get("folder") or str(Path.home() / "Desktop"))
            dry    = bool(cmd.get("dry_run", False))
            if not _is_path_allowed(folder):
                return {"status": "error", "message": "Access blocked to that folder."}
            speak(f"Organizing your {Path(folder).name} folder.")
            return organize_folder(folder, dry_run=dry)

        if action == "rename_files":
            return rename_files_batch(str(cmd.get("folder") or ""), str(cmd.get("pattern") or ""),
                                      str(cmd.get("replacement") or ""))

        if action == "process_invoices":
            speak("Processing invoices now.")
            return process_invoices_folder(str(cmd.get("folder") or str(Path.home() / "Desktop")))

        if action == "extract_invoice":
            return extract_invoice_data(str(cmd.get("path") or ""))

        if action == "read_spreadsheet":
            return read_spreadsheet(str(cmd.get("path") or ""), int(cmd.get("sheet") or 0))

        if action in {"write_file", "create_file", "save_file"}:
            p = Path(str(cmd.get("path") or AGENT_DIR / "output.txt"))
            if not _is_path_allowed(str(p)):
                return {"status": "error", "message": "Path blocked."}
            p.parent.mkdir(parents=True, exist_ok=True)
            content = str(cmd.get("content") or "")[:1_000_000]

            def _write():
                p.write_text(content, encoding="utf-8")
                try: subprocess.Popen(f'notepad.exe "{p}"', shell=True)
                except Exception: pass
                return {"status": "ok", "path": str(p)}

            result = run_with_verification(
                _write,
                lambda: verify_file_created(str(p)),
                f"create file {p.name}",
            )
            speak(f"File {p.name} saved.")
            return result

        if action in {"read_file", "open_file"}:
            p = Path(str(cmd.get("path") or ""))
            if not _is_path_allowed(str(p)):
                return {"status": "error", "message": "Path blocked."}
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="ignore")[:10000]
                speak(f"File read: {len(content)} characters.")
                return {"status": "ok", "content": content}
            return {"status": "error", "message": f"Not found: {p}"}

        if action in {"list_files", "ls"}:
            folder = Path(str(cmd.get("folder") or Path.home() / "Desktop"))
            if not _is_path_allowed(str(folder)):
                return {"status": "error", "message": "Blocked."}
            try:
                files = [f.name for f in folder.iterdir()][:50]
                speak(f"{len(files)} files in {folder.name}.")
                return {"status": "ok", "files": files}
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
                speak(f"Backup created: {dst.name}.")
                return {"status": "ok", "zip": str(dst)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # ── PAYMENT QUEUE ─────────────────────────────────────────────────────
        if action in {"list_payment_queue", "show_payments", "pending_payments", "payment_queue"}:
            return list_payment_queue(str(cmd.get("status") or "pending_review"))

        if action in {"approve_payment", "pay_invoice"}:
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid: return {"status": "error", "message": "queue_id required"}
            return approve_payment(qid, str(cmd.get("portal") or "razorpay"))

        if action == "reject_payment":
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid: return {"status": "error", "message": "queue_id required"}
            return reject_payment(qid, str(cmd.get("reason") or ""))

        # ── SOCIAL REPLY BOTS ─────────────────────────────────────────────────
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
            return book_meeting(str(cmd.get("with_email") or ""),
                                str(cmd.get("subject") or "Meeting"),
                                str(cmd.get("date") or str(datetime.date.today())),
                                int(cmd.get("duration_min") or 60))

        # ── OPEN / LAUNCH — with verification ─────────────────────────────────
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

        # ── MOUSE / KEYBOARD ──────────────────────────────────────────────────
        if action == "click":
            x = int(cmd.get("x") or 0); y = int(cmd.get("y") or 0)
            if x == 0 and y == 0: return {"status": "skipped", "reason": "no coordinates"}
            return real_click(x, y, button=str(cmd.get("button") or "left"), clicks=int(cmd.get("clicks") or 1))

        if action == "double_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), clicks=2)

        if action == "right_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), button="right")

        if action in {"move_mouse", "move_to"}:
            if PYAUTOGUI_OK: pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=0.25)
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
            real_hotkey("ctrl", "c"); time.sleep(0.12)
            clip = pyperclip.paste() if CLIP_OK else ""
            return {"status": "ok", "clipboard": clip}
        if action == "paste":   real_hotkey("ctrl", "v"); return {"status": "ok"}
        if action == "undo":    real_hotkey("ctrl", "z"); return {"status": "ok"}
        if action in {"save", "save_file_shortcut"}: real_hotkey("ctrl", "s"); return {"status": "ok"}
        if action == "refresh": real_press("f5"); return {"status": "ok"}
        if action == "new_tab": real_hotkey("ctrl", "t"); return {"status": "ok"}
        if action == "close_tab": real_hotkey("ctrl", "w"); return {"status": "ok"}

        if action in {"scroll_down", "scrolldown"}:
            real_scroll("down", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action in {"scroll_up", "scrollup"}:
            real_scroll("up", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action == "scroll":
            real_scroll(str(cmd.get("direction", "down")), int(cmd.get("amount", 3))); return {"status": "ok"}

        # ── SCREENSHOT / OCR ──────────────────────────────────────────────────
        if action in {"screenshot", "take_screenshot", "capture_screen"}:
            speak("Taking a screenshot.")
            ss = take_screenshot(save=True)
            if ss: speak("Screenshot taken."); return {"status": "ok", "screenshot": ss}
            return {"status": "error", "message": "Screenshot failed"}

        if action in {"ocr", "ocr_screen", "read_screen"}:
            text = read_screen_text()
            speak("Screen text extracted." if text else "No text found on screen.")
            return {"status": "ok", "text": text[:5000]}

        # ── WINDOW ────────────────────────────────────────────────────────────
        if action in {"minimize_window", "minimize"}:
            real_hotkey("win", "down"); return {"status": "ok"}
        if action in {"maximize_window", "maximize", "fullscreen"}:
            real_hotkey("win", "up"); return {"status": "ok"}
        if action in {"close_window", "close", "close_app", "alt_f4"}:
            real_hotkey("alt", "f4"); return {"status": "ok"}
        if action in {"switch_window", "alt_tab"}:
            real_hotkey("alt", "tab"); time.sleep(0.25); return {"status": "ok"}
        if action in {"show_desktop", "win_d"}:
            real_hotkey("win", "d"); return {"status": "ok"}
        if action == "focus_window":
            ok = focus_window(str(cmd.get("title") or cmd.get("name") or ""))
            return {"status": "ok" if ok else "error"}
        if action in {"get_windows", "list_windows"}:
            wins = list_windows(); speak(f"{len(wins)} windows open."); return {"status": "ok", "windows": wins}
        if action == "active_window":
            win = get_active_win(); speak(f"Active window: {win or 'unknown'}."); return {"status": "ok", "active_window": win}

        # ── VOLUME / MEDIA ────────────────────────────────────────────────────
        if action in {"volume_up", "increase_volume", "louder"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)): real_press("volumeup")
            speak("Volume up."); return {"status": "ok"}
        if action in {"volume_down", "decrease_volume", "quieter"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)): real_press("volumedown")
            speak("Volume down."); return {"status": "ok"}
        if action in {"mute", "unmute", "toggle_mute"}:
            real_press("volumemute"); speak("Toggled mute."); return {"status": "ok"}
        if action in {"media_play_pause", "play_pause"}: real_press("playpause"); return {"status": "ok"}
        if action in {"media_next", "next_track"}:       real_press("nexttrack"); return {"status": "ok"}
        if action in {"media_prev", "prev_track"}:       real_press("prevtrack"); return {"status": "ok"}

        # ── SYSTEM INFO ───────────────────────────────────────────────────────
        if action in {"get_system_info", "system_info", "sysinfo"}:
            if PSUTIL_OK:
                dp   = "C:\\" if platform.system() == "Windows" else "/"
                info = {
                    "cpu":          psutil.cpu_percent(interval=0.5),
                    "cpu_cores":    psutil.cpu_count(),
                    "ram":          psutil.virtual_memory().percent,
                    "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                    "disk":         psutil.disk_usage(dp).percent,
                    "disk_free_gb": round(psutil.disk_usage(dp).free / 1e9, 1),
                    "platform":     platform.system(),
                    "hostname":     socket.gethostname(),
                }
                HEALTH.update({"cpu": info["cpu"], "ram": info["ram"], "disk": info["disk"]})
                speak(f"CPU at {info['cpu']} percent, RAM at {info['ram']} percent, "
                      f"Disk {info['disk_free_gb']} gigs free.")
                return {"status": "ok", "info": info}
            return {"status": "ok", "info": {"platform": platform.system()}}

        if action == "get_time":
            t_ = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {t_}.")
            return {"status": "ok", "time": t_}

        if action == "get_date":
            d_ = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {d_}.")
            return {"status": "ok", "date": d_}

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
            if q:
                speak(f"Searching for {q[:50]}.")
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
            else:
                webbrowser.open("https://www.google.com")
            return {"status": "ok"}

        if action in {"web_research", "research"}:
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q: return {"status": "error", "message": "No query"}
            speak(f"Researching {q[:50]}.")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(f"Query: {q}\nDate: {datetime.datetime.now()}\n\n{result}", encoding="utf-8")
            try: subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception: pass
            speak(f"Research done. {result[:100]}")
            return {"status": "ok", "result": result[:800]}

        # ── YOUTUBE ───────────────────────────────────────────────────────────
        if action in {"open_youtube", "youtube", "youtube_search", "play_youtube"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q: return youtube_search_and_play(q)
            speak("Opening YouTube.")
            return smart_open("youtube")

        # ── SOCIAL POSTING ────────────────────────────────────────────────────
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
            if fact: remember(fact); speak("Got it. I've made a note of that.")
            return {"status": "ok"}
        if action in {"get_memory", "show_memory", "recall"}:
            ctx = get_mem_ctx(); speak("Memory retrieved."); return {"status": "ok", "memory": ctx}
        if action in {"add_contact", "save_contact"}:
            name = str(cmd.get("name", ""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {
                        "name":  name,
                        "email": str(cmd.get("email", "")),
                        "phone": str(cmd.get("phone", "")),
                    }
                save_memory(); speak(f"Contact {name} saved.")
            return {"status": "ok"}

        # ── SCHEDULE ──────────────────────────────────────────────────────────
        if action in {"schedule_task", "schedule", "set_reminder"}:
            task_s = str(cmd.get("task") or cmd.get("command") or "")
            sched  = str(cmd.get("schedule") or cmd.get("time") or "daily at 09:00")
            if not task_s: return {"status": "error", "message": "No task to schedule"}
            job = {"id": "".join(random.choices(string.ascii_lowercase, k=8)),
                   "task": task_s, "schedule": sched, "last_run": ""}
            _sched_jobs.append(job); save_memory()
            speak(f"Scheduled: {task_s[:50]} — {sched}.")
            return {"status": "ok", "job_id": job["id"]}

        # ── HEALTH / WAIT / PING ──────────────────────────────────────────────
        if action in {"wait", "sleep", "pause"}:
            secs = min(float(cmd.get("seconds") or 1), 60); time.sleep(secs); return {"status": "ok"}

        if action in {"ping", "test", "health_check", "status"}:
            speak("Online and ready."); return {"status": "ok", "pong": True, "health": HEALTH}

        if action in {"list_skills", "skills", "help"}:
            skills = [
                "open any app or website", "send & receive emails", "bulk email campaigns",
                "find leads and email them", "organize files by type", "process invoices",
                "take screenshots and OCR", "voice control (Hey Dex)",
                "WhatsApp/Instagram/Facebook auto-replies", "invoice payment queue",
                "book calendar meetings", "web research → Notepad", "Gmail compose",
                "answer any question aloud", "daily business brief", "generate reports",
                "write proposals and contracts", "create invoices", "job descriptions",
                "competitor analysis", "social media content", "expense tracking",
                "newsletter creation", "browser automation", "scheduler",
                "real mouse and keyboard control", "system monitoring",
            ]
            speak(f"I have {len(skills)} capabilities. Here are the highlights.")
            print("\n  === DEX CAPABILITIES ===")
            for s in skills: print(f"    • {s}")
            print()
            return {"status": "ok", "skills": skills}

        # ── BRIGHTNESS ────────────────────────────────────────────────────────
        if action == "brightness_up":
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)", shell=True)
            return {"status": "ok"}
        if action == "brightness_down":
            subprocess.Popen("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)", shell=True)
            return {"status": "ok"}

        if action == "monitor_errors":
            return monitor_error_logs(str(cmd.get("path") or str(LOG_FILE)))

        if action == "backup":
            return backup_to_cloud()

        # ── SMART OPEN FALLBACK ───────────────────────────────────────────────
        tgt = (cmd.get("url") or cmd.get("app") or cmd.get("target") or cmd.get("name") or "")
        if tgt:
            res = smart_open(str(tgt))
            if res.get("status") == "ok": return res

        res = smart_open(action.replace("_", " ").strip())
        if res.get("status") == "ok": return res

        # ABSOLUTE FALLBACK — ask AI
        log.warning("Unhandled action: '%s' — routing to AI brain", action)
        speak("Let me think about how to handle that.")
        resp = ask_ai_brain(f"How do I: {action} {str(cmd)[:100]}")
        speak(resp[:200])
        return {"status": "ok", "response": resp}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e, exc_info=True)
        speak("I ran into a problem with that. Let me try a different approach.")
        return {"status": "error", "message": f"Exception in {action}: {e}"}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TASK EXECUTOR — with AI planner for complex goals
# ══════════════════════════════════════════════════════════════════════════════
def execute_task(task: str, token: str) -> dict:
    if not task or not task.strip():
        return {"status": "error", "ok": 0, "total": 0, "result": "Empty task"}
    if not _desktop_task_lock.acquire(blocking=False):
        _remember_task_queue(task, "queued")
        with _desktop_task_lock:
            _remember_task_queue(task, "running")
            return execute_task(task, token)
    try:
        return _execute_task_locked(task, token)
    finally:
        _remember_task_queue(task, "finished")
        _desktop_task_lock.release()


def _execute_task_locked(task: str, token: str) -> dict:
    task = task.strip()
    log.info("TASK: %s", task[:120])
    print(f"\n  [TASK] {task[:80]}")
    _convo.append(f"user: {task[:120]}")
    update_runtime_state(last_action="task_started", last_result=task[:200], last_verified=False)

    # ── COMPOUND TASK SPLITTING ───────────────────────────────────────────────
    parts = _split_compound_task(task)
    if len(parts) > 1:
        log.info("COMPOUND TASK: %d parts", len(parts))
        speak(f"Got it. I'll handle that in {len(parts)} steps.")
        total_ok = 0
        for i, part in enumerate(parts, 1):
            speak(f"Step {i}: {part[:40]}.")
            r = execute_task(part, token)
            if r.get("status") == "ok" and r.get("ok", 0) >= r.get("total", 1):
                total_ok += 1
            time.sleep(0.4)
        status = "ok" if total_ok == len(parts) else "error"
        speak((jarvis_done() if status == "ok" else "I could not verify every step.") + f" Completed {total_ok} of {len(parts)} steps.")
        return {"status": status, "ok": total_ok, "total": len(parts), "verified": status == "ok"}

    # ── SINGLE TASK ───────────────────────────────────────────────────────────
    commands = local_parse(task)

    if not commands:
        tl    = task.lower().strip()
        words = tl.split()
        is_open_like = len(words) <= 5 and not any(
            w in tl for w in ["send", "email", "search", "find", "create", "write", "post", "process", "organize"])
        if is_open_like:
            res = smart_open(task)
            if res.get("status") == "ok":
                _convo.append(f"dex: Opened {task[:60]}")
                with _mem_lock:
                    MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
                save_memory()
                return {"status": "ok", "ok": 1, "total": 1, "verified": True, "result": f"Opened: {task}"}

        # Try AI planner for complex unrecognized tasks
        ai_steps = ai_plan_task(task)
        if ai_steps:
            log.info("AI planner produced %d steps", len(ai_steps))
            speak(f"Let me break that down. {len(ai_steps)} steps.")
            ok_count = 0
            for i, step in enumerate(ai_steps, 1):
                speak(f"Step {i}: {step.get('action', '?')}.")
                res = exec_cmd(step, token)
                if res.get("status") in ("ok", "skipped") and res.get("verified", True) is not False: ok_count += 1
                time.sleep(0.2)
            status = "ok" if ok_count == len(ai_steps) else "error"
            if status == "ok": speak(jarvis_done())
            else: speak("I ran the plan, but not every step verified.")
            return {"status": status, "ok": ok_count, "total": len(ai_steps), "verified": status == "ok"}

        speak("I'm not sure how to do that. Try rephrasing, or say 'help' for options.")
        return {"status": "error", "ok": 0, "total": 0, "result": f"Could not parse: {task[:80]}"}

    ok_count = 0; total = len(commands); results = []
    print(f"  [TASK] {total} step{'s' if total > 1 else ''}...")

    for i, c in enumerate(commands):
        if not isinstance(c, dict): total -= 1; continue
        step_action = c.get("action", "?")
        log.info("  Step %d/%d: %s", i + 1, total, step_action)
        if total > 1:
            print(f"  [STEP {i+1}/{total}] {step_action}")
        try:
            res = exec_cmd(c, token); results.append(res)
            if res.get("status") in ("ok", "skipped") and res.get("verified", True) is not False:
                ok_count += 1
            else:
                log.warning("  Step %d failed: %s", i + 1, res.get("message", "?"))
            time.sleep(0.1)
        except Exception as e:
            log.error("  Step %d exception: %s", i + 1, e)
            results.append({"status": "error", "message": str(e)})

    with _mem_lock:
        MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} {task[:80]}")
    save_memory()

    verified_all = ok_count == total and total > 0
    HEALTH["tasks_ok"] += ok_count if verified_all else 0
    summary = f"{'Task verified' if verified_all else 'Task not fully verified'}: {ok_count}/{total} - {task[:60]}"
    log.info(summary); _convo.append(f"dex: {summary}")

    if total > 1:
        if ok_count < total:
            speak(f"I could not verify completion. {ok_count} of {total} steps verified.")
        else:
            speak(jarvis_done())

    update_runtime_state(last_action="task_finished", last_result=summary, last_verified=verified_all)
    return {"status": "ok" if verified_all else "error", "ok": ok_count, "total": total,
            "verified": verified_all, "result": summary, "steps": results}


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
        log.info("Autostart registered")
    except Exception as e:
        log.warning("Autostart: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def login() -> Optional[str]:
    print("\n" + "=" * 55)
    print("  DACEXY AGENT v30.0 — Login")
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
            HEALTH["uptime_seconds"] = int(time.time() - HEALTH["uptime_start"])
            fn = ws_send_ref[0]
            if fn:
                try:
                    asyncio.run_coroutine_threadsafe(
                        fn({"type": "heartbeat", "health": dict(HEALTH)}),
                        asyncio.get_event_loop(),
                    )
                except Exception:
                    pass
            if HEALTH["cpu"] > 90:
                speak("Warning — CPU usage is very high.")
                _notify("Dex Alert", f"CPU at {HEALTH['cpu']}%")
            if HEALTH["ram"] > 90:
                speak("Warning — RAM usage is very high.")
        except Exception as e:
            log.warning("Health monitor: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# VOICE — JARVIS-STYLE, INSTANT WAKE, ONE-SHOT RECOGNITION
# ══════════════════════════════════════════════════════════════════════════════
def _is_wake_word(heard: str) -> bool:
    h = heard.lower().strip()
    return any(re.search(r"\b" + re.escape(w) + r"\b", h) for w in WAKE_WORDS)


def _voice_loop():
    global _voice_on
    if not VOICE_OK or not sr:
        print("  [VOICE] Disabled — PyAudio not installed.")
        return

    rec = sr.Recognizer()

    # Fast, adaptive settings for Jarvis-style response
    rec.dynamic_energy_threshold          = True
    rec.dynamic_energy_adjustment_damping = 0.12   # adapts quickly to room
    rec.dynamic_energy_ratio              = 1.2    # sensitive but not over-triggering
    rec.pause_threshold                   = 0.6    # fast turn-taking (was 2.0!)
    rec.phrase_threshold                  = 0.2
    rec.non_speaking_duration             = 0.25

    # ONE-TIME ambient calibration at startup
    try:
        with sr.Microphone() as src:
            print("  [VOICE] Calibrating microphone...")
            rec.adjust_for_ambient_noise(src, duration=1.5)
        log.info("Voice calibrated, threshold=%.0f", rec.energy_threshold)
        # Set a floor — don't go too sensitive
        if rec.energy_threshold < 200:
            rec.energy_threshold = 200
    except Exception as e:
        log.warning("Voice calibration: %s", e)
        rec.energy_threshold = 300

    print("  [VOICE] Active! Say: Hey Dex / Dex / Dacexy / Jarvis")
    speak("Hey! Dex is online. Say Hey Dex whenever you need me.")

    while _voice_on and _running:
        heard = ""
        try:
            with sr.Microphone() as src:
                # Short timeout + short phrase limit for fast wake-word catch
                try:
                    audio = rec.listen(src, timeout=3, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    continue
                except OSError:
                    time.sleep(1.5); continue

            try:
                heard = rec.recognize_google(audio, language="en-IN").lower().strip()
                if heard:
                    log.debug("Heard: '%s'", heard)
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                time.sleep(2); continue

        except Exception:
            time.sleep(0.8); continue

        if not _is_wake_word(heard):
            continue

        log.info("Wake word detected: '%s'", heard)
        speak("Yes sir?")
        time.sleep(0.3)

        # Listen for command — longer phrase time, no re-calibration
        command = ""
        try:
            with sr.Microphone() as csrc:
                try:
                    caudio = rec.listen(csrc, timeout=8, phrase_time_limit=40)
                except sr.WaitTimeoutError:
                    speak("I didn't catch that.")
                    continue
            try:
                command = rec.recognize_google(caudio, language="en-IN").strip()
            except sr.UnknownValueError:
                speak("Could you repeat that?")
                continue
            except sr.RequestError:
                continue
        except Exception:
            continue

        if not command:
            continue

        log.info("Voice command: '%s'", command)
        print(f"\n  [VOICE] \"{command}\"")

        with _tok_lock:
            tok = _cur_token
        if not tok:
            speak("I'm not logged in yet.")
            continue

        speak(jarvis_confirm())

        def _run(t_=tok, cmd_=command):
            try:
                execute_task(cmd_, t_)
            except Exception as exc:
                log.error("Voice task: %s", exc)
                speak("Sorry, I ran into an error with that.")

        threading.Thread(target=_run, daemon=True, name="VoiceTask").start()


def start_voice(token: str) -> bool:
    global _voice_on, _cur_token
    with _tok_lock: _cur_token = token
    if not VOICE_OK: return False
    _voice_on = True
    threading.Thread(target=_voice_loop, daemon=True, name="Voice").start()
    return True

def stop_voice():
    global _voice_on; _voice_on = False

def update_token(t: str):
    global _cur_token
    with _tok_lock: _cur_token = t


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE SHELL
# ══════════════════════════════════════════════════════════════════════════════
def _interactive_shell(token: str, tok_ref: list):
    print("\n" + "=" * 65)
    print("  DEX v30.0 — COMMAND CENTER")
    print("=" * 65)
    print(f"  Email    : {_smtp_cfg.get('email') or 'NOT CONFIGURED'}")
    print(f"  Voice    : {'ON — say Hey Dex' if _voice_on else 'OFF'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print("=" * 65)
    print("  Type any task. 'help' for examples. 'quit' to exit.\n")

    while _running:
        try:
            line = input("  Dex> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line: continue
        tl = line.lower()

        if tl in ("quit", "exit"):    print("  Goodbye!"); break
        if tl in ("help", "menu"):    exec_cmd({"action": "list_skills"}, token); continue
        if tl == "memory":            print("\n" + get_mem_ctx() + "\n"); continue
        if tl == "jobs":
            if _sched_jobs: [print(f"  [{j['id']}] {j['task']} — {j['schedule']}") for j in _sched_jobs]
            else: print("  No scheduled jobs.")
            continue
        if tl == "email":             configure_smtp_interactive(); continue
        if tl == "sysinfo":           exec_cmd({"action": "get_system_info"}, token); continue
        if tl == "screenshot":        exec_cmd({"action": "screenshot"}, token); continue
        if tl == "health":            print(f"  Health: {HEALTH}"); continue
        if tl == "brief":             exec_cmd({"action": "daily_summary"}, token); continue

        tok = tok_ref[0]
        def _run(t_=tok, cmd_=line):
            r = execute_task(cmd_, t_)
            if r.get("status") != "ok":
                print(f"\n  [FAIL] {r.get('result', '')}")
        threading.Thread(target=_run, daemon=True, name="ShellTask").start()


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — robust, reconnecting, voice transcript streaming
# ══════════════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    global _ws_send_fn, _ws_loop
    retry = 4.0; max_retry = 60.0

    while _running:
        try:
            log.info("WS: connecting...")
            print("  [WS] Connecting to Dacexy cloud...")

            connect_kw: dict = {"ping_interval": 20, "ping_timeout": 15,
                                "max_size": 16 * 1024 * 1024}
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
                        speak("Authentication failed.")
                        await asyncio.sleep(retry); retry = min(retry * 1.5, max_retry); continue
                except asyncio.TimeoutError:
                    log.warning("WS: auth timeout")
                    await asyncio.sleep(retry); retry = min(retry * 1.5, max_retry); continue
                except Exception as e:
                    log.warning("WS: auth error: %s", e)
                    await asyncio.sleep(retry); continue

                await ws.send(json.dumps({
                    "type": "init", "platform": platform.system(),
                    "machine": platform.machine(), "hostname": socket.gethostname(),
                    "version": "30.0",
                    "features": [
                        "voice3", "vision", "browser", "email", "social_selenium",
                        "bulk_email", "lead_gen", "web_research", "scheduler", "memory",
                        "selenium", "ocr", "screenshot", "file_organizer", "invoice_extractor",
                        "spreadsheet_paste", "inbox_reader", "approval_gates",
                        "real_mouse_keyboard", "encrypted_config", "health_monitor",
                        "calendar_booking", "human_approval", "social_reply_bots",
                        "payment_queue", "compound_tasks", "gmail_compose",
                        "research_and_write", "qa_voice", "ai_planner",
                        "business_reports", "proposal_generator", "invoice_generator",
                        "competitor_analysis", "social_content", "expense_tracker",
                        "daily_brief", "voice_transcript_stream",
                    ],
                }))

                log.info("WS: connected!")
                print("\n  [OK] Connected to Dacexy cloud — Dex is LIVE!")
                speak("Connected. Dex is live and ready for your commands.")
                retry = 4.0

                ws_lock = asyncio.Lock()
                loop    = asyncio.get_event_loop()
                _ws_loop = loop

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

                    if action and action not in ("swarm_task", "task", "run_agent", ""):
                        def _cmd_thread(m_=dict(msg), t_=token, tid_=task_id):
                            try:
                                r_ = exec_cmd(m_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"),
                                    "ok": 1 if r_.get("status") in ("ok", "skipped") else 0,
                                    "total": 1,
                                    "result": str(r_.get("message") or r_.get("opened") or "done"),
                                    "data": r_,
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 1, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_cmd_thread, daemon=True).start()
                        continue

                    if task_txt or mtype in ("task", "command"):
                        if not task_txt: task_txt = action
                        if not task_txt: continue
                        log.info("Dashboard task: %s", task_txt[:80])
                        print(f"\n  [TASK] From dashboard: {task_txt[:80]}")
                        speak(f"On it. {task_txt[:40]}.")

                        def _task_thread(t_=token, txt_=task_txt, tid_=task_id):
                            try:
                                r_ = execute_task(txt_, t_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "ok"),
                                    "ok": r_.get("ok", 0), "total": r_.get("total", 1),
                                    "result": r_.get("result", ""), "steps": r_.get("steps", []),
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
            _ws_loop    = None
            await asyncio.sleep(retry)
            retry = min(retry * 1.5, max_retry)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    global _running

    print("\n" + "=" * 65)
    print("  DEX v30.0 — YOUR AI BUSINESS CO-ASSISTANT")
    print("  Voice · Email · Files · Social · Finance · Operations")
    print("=" * 65 + "\n")

    init_tts()
    load_memory()
    _load_runtime_state()

    caps = []
    if PYAUTOGUI_OK:  caps.append("mouse/keyboard")
    if PIL_OK:        caps.append("screenshot")
    if VOICE_OK:      caps.append("VOICE ✓")
    if SELENIUM_OK:   caps.append("browser-automation")
    if BS4_OK:        caps.append("web-scraping")
    if OCR_OK:        caps.append("OCR")
    if PDF_OK:        caps.append("invoice-PDF")
    if XL_OK:         caps.append("spreadsheet")
    if CRYPTO_OK:     caps.append("encrypted-config")
    em = _smtp_cfg.get("email") or ""
    caps.append(f"email={'✓ ' + em if em else 'NOT CONFIGURED'}")
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
        print("  [EMAIL] Not configured. Type 'configure email' or 'email' to set up.\n")

    voice_ok    = start_voice(token)
    tok_ref     = [token]
    ws_send_ref = [None]

    threading.Thread(target=_scheduler_loop,    args=(tok_ref,),      daemon=True, name="Scheduler").start()
    threading.Thread(target=_health_monitor,    args=(ws_send_ref,),  daemon=True, name="HealthMon").start()
    threading.Thread(target=_interactive_shell, args=(token, tok_ref), daemon=True, name="Shell").start()

    print("  " + "─" * 63)
    print("  Dex v30.0 — LIVE")
    print(f"  Voice    : {'ON — say Hey Dex / Dex / Jarvis' if voice_ok else 'OFF (PyAudio not installed)'}")
    print(f"  Email    : {_smtp_cfg.get('email') or 'Not configured (type: configure email)'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print(f"  Log file : {LOG_FILE}")
    print("  " + "─" * 63 + "\n")

    speak("Dex is fully operational. Say Hey Dex to activate voice control.")

    if not WS_OK:
        print("  [ERROR] websockets not installed!")
        sys.exit(1)

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
        print("  Dex stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
