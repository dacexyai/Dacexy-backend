"""
DACEXY DESKTOP AGENT v15.0 ENTERPRISE
World's Most Powerful AI Desktop Agent
24/7 cloud-connected, voice-controlled, fully autonomous
"""

# ============================================================
# BLOCK 1 - WINDOWS FIXES (MUST BE FIRST)
# ============================================================
import sys
import os
import platform

if platform.system() == "Windows":
    import asyncio as _asyncio
    if hasattr(_asyncio, "WindowsSelectorEventLoopPolicy"):
        _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

if platform.system() == "Windows":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

# ============================================================
# BLOCK 2 - PATHS AND LOGGING
# ============================================================
from pathlib import Path
import datetime
import logging

_AGENT_DIR   = Path.home() / "DacexyAgent"
_LOG_DIR     = _AGENT_DIR / "logs"
_STARTUP_LOG = _LOG_DIR / "startup.log"
_AGENT_DIR.mkdir(exist_ok=True)
_LOG_DIR.mkdir(exist_ok=True)


def _safe_file_handler(path: Path) -> logging.Handler:
    for p in [path, path.with_suffix(".1.log"), Path.home() / "dacexy_startup.log"]:
        try:
            with open(str(p), "a", encoding="utf-8"):
                pass
            h = logging.FileHandler(str(p), encoding="utf-8", mode="a")
            return h
        except Exception:
            continue
    return logging.NullHandler()


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        _safe_file_handler(_STARTUP_LOG),
        _safe_file_handler(Path.home() / "dacexy_agent.log"),
    ]
)
log = logging.getLogger("dacexy")
log.info("=" * 60)
log.info("Dacexy Agent v15.0 ENTERPRISE starting: %s", datetime.datetime.now().isoformat())
log.info("Python: %s | Platform: %s", sys.version, platform.system())
log.info("=" * 60)

# ============================================================
# BLOCK 3 - AUTO-INSTALL DEPENDENCIES
# ============================================================
import subprocess

PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
    "pyperclip", "keyboard", "pygetwindow", "plyer",
    "selenium", "webdriver-manager", "pytesseract",
    "opencv-python", "schedule", "aiohttp", "aiofiles",
    "rich", "colorama", "python-docx", "openpyxl",
    "pandas", "cryptography", "packaging",
]


def _silent_install(pkg):
    special = {
        "speechrecognition": "speech_recognition", "pillow": "PIL",
        "opencv-python": "cv2", "webdriver-manager": "webdriver_manager",
        "python-docx": "docx",
    }
    imp = special.get(pkg.lower(), pkg.replace("-", "_"))
    try:
        __import__(imp)
    except ImportError:
        log.info("Installing %s...", pkg)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q", "--no-warn-script-location"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        except Exception as e:
            log.warning("Could not install %s: %s", pkg, e)


for _p in PACKAGES:
    _silent_install(_p)

try:
    import pyaudio
    PYAUDIO_OK = True
    log.info("PyAudio OK")
except Exception:
    PYAUDIO_OK = False
    log.warning("PyAudio not available - voice disabled")

# ============================================================
# BLOCK 4 - ALL IMPORTS
# ============================================================
import asyncio
import base64
import io
import json
import threading
import time
import webbrowser
import re
import ctypes
import queue
import smtplib
import socket
import hashlib
import traceback
import random
import zipfile
import csv
import shutil
import math
import gc

from typing import Optional, List, Dict, Any, Tuple, Callable
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import quote, urlparse
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from abc import ABC, abstractmethod

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.04
except Exception:
    class _Stub:
        FAILSAFE = False; PAUSE = 0.04
        def __getattr__(self, n): return lambda *a, **k: None
        def size(self): return (1920, 1080)
        def position(self): return (0, 0)
    pyautogui = _Stub()

try:
    import requests as req_lib
except Exception:
    req_lib = None

try:
    import websockets
except Exception:
    websockets = None

try:
    from PIL import ImageGrab, Image, ImageEnhance
except Exception:
    ImageGrab = Image = ImageEnhance = None

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
    VOICE_AVAILABLE = PYAUDIO_OK
except Exception:
    VOICE_AVAILABLE = False
    sr = None

try:
    import pygetwindow as gw
    WINDOW_OK = True
except Exception:
    WINDOW_OK = False
    gw = None

try:
    from plyer import notification
    NOTIFY_OK = True
except Exception:
    NOTIFY_OK = False

try:
    import cv2
    CV2_OK = True
except Exception:
    CV2_OK = False
    cv2 = None

try:
    import numpy as np
    NUMPY_OK = True
except Exception:
    NUMPY_OK = False
    np = None

try:
    import pytesseract
    TESSERACT_OK = True
    for _tp in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
    ]:
        if os.path.exists(_tp):
            pytesseract.pytesseract.tesseract_cmd = _tp
            break
except Exception:
    TESSERACT_OK = False
    pytesseract = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except Exception:
    SELENIUM_OK = False

try:
    import keyboard
    KEYBOARD_OK = True
except Exception:
    KEYBOARD_OK = False
    keyboard = None

try:
    import docx
    DOCX_OK = True
except Exception:
    DOCX_OK = False
    docx = None

try:
    import openpyxl
    OPENPYXL_OK = True
except Exception:
    OPENPYXL_OK = False
    openpyxl = None

log.info("All imports complete")

# ============================================================
# BLOCK 5 - CONSTANTS
# ============================================================
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE   = Path.home() / ".dacexy_agent.json"
MEMORY_FILE   = Path.home() / ".dacexy_memory.json"
AUDIT_FILE    = Path.home() / "dacexy_audit.log"
MACRO_FILE    = Path.home() / ".dacexy_macros.json"
CAMPAIGN_FILE = Path.home() / ".dacexy_campaigns.json"
SCHEDULE_FILE = Path.home() / ".dacexy_schedule.json"
SKILLS_FILE   = Path.home() / ".dacexy_skills.json"
PLUGINS_DIR   = Path.home() / ".dacexy_plugins"
COOKIES_DIR   = Path.home() / ".dacexy_cookies"
NOTES_DIR     = Path.home() / "DacexyNotes"
BACKUP_DIR    = Path.home() / "DacexyBackups"
RESEARCH_DIR  = Path.home() / "DacexyResearch"
VERSION       = "15.0 ENTERPRISE"
WAKE_WORDS    = ["hey dacexy", "dacexy", "assistant"]

for _d in [PLUGINS_DIR, COOKIES_DIR, NOTES_DIR, BACKUP_DIR, RESEARCH_DIR]:
    try:
        _d.mkdir(exist_ok=True)
    except Exception:
        pass

# ============================================================
# BLOCK 6 - GLOBAL STATE
# ============================================================
_memory_lock          = threading.Lock()
_config_lock          = threading.Lock()
_campaign_lock        = threading.Lock()
_agent_running        = True
_emergency_stop_event = threading.Event()
_executor             = ThreadPoolExecutor(max_workers=8)
_ws_connection        = None
_result_cache: Dict[str, Any] = {}

MEMORY = {
    "facts": [], "preferences": {}, "task_history": deque(maxlen=500),
    "context": {}, "user_profile": {}, "workflows": {}, "email_contacts": [],
    "social_accounts": {}, "automation_templates": {}, "scheduled_tasks": [],
    "success_patterns": [], "failure_patterns": [], "learned_skills": [],
    "optimization_hints": [], "conversation": deque(maxlen=100),
}

audit_log = logging.getLogger("dacexy.audit")
try:
    _ah = _safe_file_handler(AUDIT_FILE)
    _ah.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    audit_log.addHandler(_ah)
except Exception:
    pass

# ============================================================
# BLOCK 7 - DATA STRUCTURES
# ============================================================
class AgentStatus(Enum):
    IDLE = auto(); PLANNING = auto(); EXECUTING = auto()
    VERIFYING = auto(); RETRYING = auto(); PAUSED = auto()
    ERROR = auto(); STOPPED = auto()


@dataclass
class TaskStep:
    step_id: int; action: str; description: str
    params: Dict[str, Any] = field(default_factory=dict)
    action_type: str = ""; retry_count: int = 0
    max_retries: int = 3; timeout: int = 30
    verify: bool = True; completed: bool = False
    result: Any = None; error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class ExecutionContext:
    task_id: str; task_name: str
    steps: List[TaskStep] = field(default_factory=list)
    status: str = "pending"; start_time: float = field(default_factory=time.time)
    end_time: float = 0.0; total_steps: int = 0; done_steps: int = 0
    failed_steps: int = 0; screenshots: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    checkpoint: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    entry_id: str; category: str; content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    access_count: int = 0; importance: float = 1.0
    embedding: Optional[List[float]] = None


@dataclass
class EmailCampaignData:
    campaign_id: str; name: str; subject: str
    body_template: str; recipients: List[str]
    scheduled_at: Optional[str] = None; sent: int = 0
    failed: int = 0; opened: int = 0; clicked: int = 0
    bounced: int = 0; status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    html: bool = True; delay_sec: float = 1.0
    retry_queue: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class UIElement:
    label: str; x: int; y: int; width: int; height: int
    elem_type: str = "unknown"; confidence: float = 0.0
    text: str = ""; clickable: bool = True


@dataclass
class LearnedSkill:
    skill_id: str; name: str; description: str; steps: List[Dict]
    success_rate: float = 0.0; use_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    last_used: str = ""; tags: List[str] = field(default_factory=list)

# ============================================================
# BLOCK 8 - CONSOLE UTILITIES
# ============================================================
def _banner():
    lines = [
        "", "=" * 62,
        "  DACEXY v15.0 ENTERPRISE - AI Desktop Agent",
        "  Wake Words: Hey Dacexy / Dacexy / Assistant",
        f"  Log: {_STARTUP_LOG}", "=" * 62, "",
    ]
    for line in lines:
        try:
            print(line)
            sys.stdout.flush()
        except Exception:
            pass


def _print(prefix, m):
    try:
        print(f"  [{prefix}] {m}")
        sys.stdout.flush()
    except Exception:
        pass


def _ok(m):   _print("OK", m);   log.info("OK: %s", m)
def _err(m):  _print("ERROR", m); log.error("ERR: %s", m)
def _info(m): _print("INFO", m);  log.info("%s", m)
def _warn(m): _print("WARN", m);  log.warning("%s", m)
def _task(m): _print("TASK", m);  log.info("TASK: %s", m)


def generate_id(prefix: str = "") -> str:
    return f"{prefix}{hashlib.md5(f'{time.time()}{random.random()}'.encode()).hexdigest()[:10]}"


def mask_pii(text: str) -> str:
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]', str(text))
    text = re.sub(r'\b\d{10,12}\b', '[PHONE]', text)
    return text


def audit(action: str, detail: str = "", result: str = ""):
    try:
        audit_log.info("ACTION=%s | %s | RESULT=%s", action, mask_pii(str(detail)[:200]), result)
    except Exception:
        pass

# ============================================================
# BLOCK 9 - SAFE CONSOLE INPUT
# ============================================================
def _get_console_input(prompt: str = "") -> str:
    try:
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
    except Exception:
        pass
    if platform.system() == "Windows":
        try:
            with open("CONIN$", "r", encoding="utf-8", errors="replace") as con:
                return con.readline().rstrip("\n").rstrip("\r")
        except Exception:
            pass
    try:
        return input()
    except (EOFError, Exception):
        return ""

# ============================================================
# BLOCK 10 - TTS
# ============================================================
_tts = None
_tts_lock  = threading.Lock()
_tts_queue: queue.Queue = queue.Queue(maxsize=20)


def init_tts():
    global _tts
    if pyttsx3 is None:
        return
    try:
        _tts = pyttsx3.init()
        _tts.setProperty("rate", 162)
        _tts.setProperty("volume", 0.95)
        voices = _tts.getProperty("voices") or []
        for v in voices:
            if any(x in (v.name or "").lower() for x in ["zira", "hazel", "aria", "female"]):
                _tts.setProperty("voice", v.id)
                break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS initialized OK")
    except Exception as e:
        log.warning("TTS init failed: %s", e)
        _tts = None


def _tts_worker():
    while _agent_running:
        try:
            item = _tts_queue.get(timeout=1)
            if item is None:
                break
            text, _ = (item if isinstance(item, tuple) else (item, False))
            try:
                with _tts_lock:
                    if _tts:
                        _tts.say(str(text)[:400])
                        _tts.runAndWait()
            except Exception as e:
                log.debug("TTS speak: %s", e)
            finally:
                _tts_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            continue


def speak(text: str, priority: bool = False):
    if not text:
        return
    safe = str(text)[:400]
    try:
        print(f"  [Dacexy] {safe}")
        sys.stdout.flush()
    except Exception:
        pass
    log.info("SPEAK: %s", safe)
    try:
        if priority:
            while not _tts_queue.empty():
                try:
                    _tts_queue.get_nowait()
                except Exception:
                    break
        _tts_queue.put_nowait((safe, priority))
    except queue.Full:
        pass


def notify_desktop(title: str, message: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=message[:100], app_name="Dacexy", timeout=4)
    except Exception:
        pass

# ============================================================
# BLOCK 11 - CONFIG & AUTH
# ============================================================
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
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except Exception as e:
            log.warning("Config save: %s", e)


def get_token():   return load_config().get("access_token")
def save_token(t): cfg = load_config(); cfg["access_token"] = t; save_config(cfg)
def clear_token(): cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)
def get_smtp_config(): return load_config().get("smtp", {})
def save_smtp_config(s): cfg = load_config(); cfg["smtp"] = s; save_config(cfg)


def check_token_valid(token: str) -> bool:
    if not req_lib:
        return False
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
                        headers={"Authorization": f"Bearer {token}"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def check_internet() -> bool:
    if not req_lib:
        return False
    for url in ["https://www.google.com", "https://1.1.1.1"]:
        try:
            r = req_lib.get(url, timeout=5, verify=False)
            if r.status_code < 500:
                return True
        except Exception:
            continue
    return False


def setup_autostart():
    try:
        if not WINREG_OK:
            return
        bat_path = str(_AGENT_DIR / "install_dacexy_agent.bat")
        if os.path.exists(bat_path):
            cmd = f'"{bat_path}"'
        else:
            cmd = f'"{sys.executable}" "{Path(__file__).resolve()}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered")
    except Exception as e:
        log.warning("Autostart: %s", e)


def login() -> Optional[str]:
    print("\n" + "=" * 42)
    print("  Dacexy Agent v15.0 - Login")
    print("=" * 42)
    print("  Register free at: dacexy.vercel.app\n")
    sys.stdout.flush()
    email    = _get_console_input("  Email   : ").strip()
    password = _get_console_input("  Password: ").strip()
    print("")
    if not email or "@" not in email:
        _err("Invalid email address."); return None
    if not password or len(password) < 4:
        _err("Password too short."); return None
    if not req_lib:
        _err("requests library not installed."); return None
    _info("Connecting to Dacexy server...")
    try:
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
                         json={"email": email, "password": password},
                         headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                save_token(token)
                with _memory_lock:
                    MEMORY["user_profile"]["email"] = email
                    if f"User email: {email}" not in MEMORY["facts"]:
                        MEMORY["facts"].append(f"User email: {email}")
                _ok("Login successful!")
                audit("LOGIN", mask_pii(email), "SUCCESS")
                return token
        else:
            try:
                d = r.json().get("detail", r.text)
                if isinstance(d, list):
                    d = d[0].get("msg", str(d))
            except Exception:
                d = r.text[:200]
            _err(f"Login failed: {d}")
    except Exception as e:
        _err(f"Login error: {e}")
    return None


def login_loop() -> str:
    while True:
        token = login()
        if token:
            return token
        print("\n  Login failed. Press Enter to try again or Ctrl+C to exit.")
        sys.stdout.flush()
        try:
            _get_console_input("  > ")
        except KeyboardInterrupt:
            raise SystemExit(0)

# ============================================================
# BLOCK 12 - MEMORY SYSTEM
# ============================================================
class MemorySystem:
    def __init__(self):
        self._lock   = threading.Lock()
        self.entries: Dict[str, MemoryEntry] = {}
        self.skills:  Dict[str, LearnedSkill] = {}
        try:
            self.load()
        except Exception as e:
            log.warning("Memory load: %s", e)

    def store(self, content: str, category: str = "fact",
              metadata: Dict = None, importance: float = 1.0) -> str:
        eid   = generate_id("mem_")
        entry = MemoryEntry(entry_id=eid, category=category, content=content,
                            metadata=metadata or {}, importance=importance,
                            embedding=self._embed(content))
        with self._lock:
            self.entries[eid] = entry
            self._sync_legacy(category, content, metadata)
        try:
            self.save()
        except Exception:
            pass
        return eid

    def _sync_legacy(self, category, content, metadata):
        if category == "fact":
            if content not in MEMORY["facts"]:
                MEMORY["facts"].append(content)
        elif category == "preference":
            k = (metadata or {}).get("key", "pref")
            MEMORY["preferences"][k] = content
        elif category == "success":
            MEMORY["success_patterns"].append(content)
        elif category == "failure":
            MEMORY["failure_patterns"].append(content)

    def search(self, query: str, top_k: int = 5, category: str = None) -> List[MemoryEntry]:
        q_vec  = self._embed(query)
        scored = []
        with self._lock:
            for e in self.entries.values():
                if category and e.category != category:
                    continue
                s = self._cosine(q_vec, e.embedding or [])
                scored.append((s * e.importance, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_context(self, query: str = "") -> str:
        parts = []
        with self._lock:
            if MEMORY["facts"]:
                parts.append("Facts: " + "; ".join(MEMORY["facts"][-15:]))
            if MEMORY["preferences"]:
                parts.append("Preferences: " + str(MEMORY["preferences"]))
            if MEMORY["user_profile"]:
                parts.append("Profile: " + str(MEMORY["user_profile"]))
            recent = list(MEMORY["task_history"])[-10:]
            if recent:
                parts.append("Recent: " + "; ".join(recent))
            if MEMORY["success_patterns"]:
                parts.append("Known to work: " + "; ".join(MEMORY["success_patterns"][-5:]))
        if query:
            for e in self.search(query, top_k=3):
                parts.append(f"[{e.category}] {e.content[:80]}")
        return "\n".join(parts)

    def remember_success(self, task: str, method: str, dur: float = 0):
        self.store(f"SUCCESS: {task} via {method} in {dur:.1f}s", "success",
                   {"task": task, "method": method}, importance=1.5)

    def remember_failure(self, task: str, error: str):
        self.store(f"FAILURE: {task} err={error[:80]}", "failure",
                   {"task": task, "error": error}, importance=1.2)

    def add_conversation(self, role: str, text: str):
        with _memory_lock:
            MEMORY["conversation"].append({"role": role, "text": text,
                                           "time": datetime.datetime.now().isoformat()})

    def get_conversation(self, last_n: int = 20) -> List[Dict]:
        with _memory_lock:
            return list(MEMORY["conversation"])[-last_n:]

    def save_skill(self, name: str, steps: List[Dict],
                   description: str = "", tags: List[str] = None) -> str:
        sid   = generate_id("skill_")
        skill = LearnedSkill(skill_id=sid, name=name, description=description,
                             steps=steps, tags=tags or [])
        with self._lock:
            self.skills[sid] = skill
        self._save_skills()
        return sid

    def get_skill(self, name: str) -> Optional[LearnedSkill]:
        with self._lock:
            for s in self.skills.values():
                if s.name.lower() == name.lower():
                    s.use_count += 1
                    return s
        return None

    def list_skills(self) -> List[Dict]:
        with self._lock:
            return [{"name": s.name, "description": s.description,
                     "use_count": s.use_count} for s in self.skills.values()]

    def _embed(self, text: str, dim: int = 64) -> List[float]:
        vec = [0.0] * dim
        for i, ch in enumerate(str(text).lower()):
            vec[i % dim] += ord(ch) / 1000.0
        mag = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / mag for v in vec]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na  = math.sqrt(sum(x * x for x in a))
        nb  = math.sqrt(sum(x * x for x in b))
        return dot / ((na * nb) or 1.0)

    def load(self):
        try:
            if MEMORY_FILE.exists():
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                with _memory_lock:
                    MEMORY["facts"]            = data.get("facts", [])
                    MEMORY["preferences"]      = data.get("preferences", {})
                    MEMORY["user_profile"]     = data.get("user_profile", {})
                    MEMORY["workflows"]        = data.get("workflows", {})
                    MEMORY["email_contacts"]   = data.get("email_contacts", [])
                    MEMORY["success_patterns"] = data.get("success_patterns", [])
                    MEMORY["failure_patterns"] = data.get("failure_patterns", [])
                    MEMORY["learned_skills"]   = data.get("learned_skills", [])
                    history = data.get("task_history", [])
                    MEMORY["task_history"] = deque(history[-500:], maxlen=500)
                    for ed in data.get("entries", []):
                        try:
                            e = MemoryEntry(**ed)
                            self.entries[e.entry_id] = e
                        except Exception:
                            pass
            self._load_skills()
            log.info("Memory loaded: %d entries, %d skills", len(self.entries), len(self.skills))
        except Exception as e:
            log.warning("Memory load error: %s", e)

    def save(self):
        try:
            with _memory_lock:
                data = {
                    "facts":            MEMORY["facts"][-500:],
                    "preferences":      MEMORY["preferences"],
                    "user_profile":     MEMORY["user_profile"],
                    "workflows":        MEMORY["workflows"],
                    "email_contacts":   MEMORY["email_contacts"][-1000:],
                    "success_patterns": MEMORY["success_patterns"][-200:],
                    "failure_patterns": MEMORY["failure_patterns"][-200:],
                    "learned_skills":   MEMORY["learned_skills"][-100:],
                    "task_history":     list(MEMORY["task_history"])[-500:],
                    "entries": [asdict(e) for e in list(self.entries.values())[-300:]],
                }
            tmp = MEMORY_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(MEMORY_FILE)
        except Exception as e:
            log.warning("Memory save error: %s", e)

    def _save_skills(self):
        try:
            SKILLS_FILE.write_text(
                json.dumps({k: asdict(v) for k, v in self.skills.items()}, indent=2))
        except Exception:
            pass

    def _load_skills(self):
        try:
            if SKILLS_FILE.exists():
                for k, v in json.loads(SKILLS_FILE.read_text()).items():
                    try:
                        self.skills[k] = LearnedSkill(**v)
                    except Exception:
                        pass
        except Exception:
            pass


_mem_sys: Optional[MemorySystem] = None


def get_mem() -> MemorySystem:
    global _mem_sys
    if _mem_sys is None:
        _mem_sys = MemorySystem()
    return _mem_sys


def remember(fact: str, category: str = "fact"):
    try:
        get_mem().store(fact, category)
    except Exception:
        pass


def remember_preference(key: str, value: Any):
    try:
        get_mem().store(str(value), "preference", {"key": key})
        with _memory_lock:
            MEMORY["preferences"][key] = value
    except Exception:
        pass


def add_task_history(task: str):
    try:
        with _memory_lock:
            MEMORY["task_history"].append(
                f"{datetime.datetime.now().strftime('%H:%M')} - {task}")
    except Exception:
        pass


def get_memory_context(query: str = "") -> str:
    try:
        return get_mem().get_context(query)
    except Exception:
        return ""


def save_workflow(name: str, steps: List[dict]):
    try:
        with _memory_lock:
            MEMORY["workflows"][name] = {"steps": steps, "created": datetime.datetime.now().isoformat()}
        get_mem().save()
    except Exception:
        pass


def get_workflow(name: str) -> Optional[List[dict]]:
    with _memory_lock:
        wf = MEMORY["workflows"].get(name)
        return wf["steps"] if wf else None


def remember_contact(name: str, email: str = "", phone: str = ""):
    try:
        c = {"name": name, "email": email, "phone": phone,
             "added": datetime.datetime.now().isoformat()}
        with _memory_lock:
            if not any(x.get("email") == email for x in MEMORY["email_contacts"]):
                MEMORY["email_contacts"].append(c)
        get_mem().save()
    except Exception:
        pass

# ============================================================
# BLOCK 13 - VISION ENGINE
# ============================================================
class SuperVisionEngine:
    def __init__(self):
        self._lock        = threading.Lock()
        self._last_screen = None
        self._ui_elements: List[UIElement] = []
        self._monitoring  = False
        self._screen_hash = ""
        self._change_cbs: List[Callable] = []

    def capture(self, region=None, quality: int = 75) -> Optional[str]:
        try:
            img = self.capture_pil(region)
            if img is None:
                return None
            w, h = img.size
            if w > 1920:
                img = img.resize((1920, int(h * 1920 / w)), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            return base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            log.debug("Vision capture: %s", e)
            return None

    def capture_pil(self, region=None):
        try:
            if ImageGrab is None:
                return None
            img = (ImageGrab.grab(bbox=region) if region else ImageGrab.grab())
            with self._lock:
                self._last_screen = img
            return img
        except Exception as e:
            log.debug("capture_pil: %s", e)
            return None

    def get_screen_size(self) -> Tuple[int, int]:
        try:
            return pyautogui.size()
        except Exception:
            return (1920, 1080)

    def ocr(self, region=None) -> str:
        if not TESSERACT_OK:
            return ""
        try:
            img = self.capture_pil(region)
            if img is None:
                return ""
            if ImageEnhance:
                img = img.convert("L")
                img = ImageEnhance.Contrast(img).enhance(2.0)
            return pytesseract.image_to_string(img).strip()
        except Exception:
            return ""

    def ocr_fast(self, region=None) -> str:
        if not TESSERACT_OK:
            return ""
        try:
            img = self.capture_pil(region)
            if img is None:
                return ""
            return pytesseract.image_to_string(img, config="--psm 11").strip()
        except Exception:
            return ""

    def find_text(self, search: str, region=None) -> Optional[Tuple[int, int]]:
        if not TESSERACT_OK:
            return None
        try:
            img = self.capture_pil(region)
            if img is None:
                return None
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            for i, word in enumerate(data["text"]):
                if search.lower() in str(word).lower() and int(data["conf"][i]) > 25:
                    x = data["left"][i] + data["width"][i] // 2
                    y = data["top"][i]  + data["height"][i] // 2
                    if region:
                        x += region[0]; y += region[1]
                    return (x, y)
        except Exception:
            pass
        return None

    def detect_ui_elements(self, region=None) -> List[UIElement]:
        elements = []
        if not CV2_OK or not NUMPY_OK:
            return elements
        try:
            img = self.capture_pil(region)
            if img is None:
                return elements
            img_np  = np.array(img.convert("RGB"))
            gray    = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges   = cv2.Canny(blurred, 25, 100)
            kernel  = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area  = w * h
                ratio = w / h if h > 0 else 0
                if 300 < area < 150000 and 0.05 < ratio < 25:
                    et = ("button" if 18 < h < 55 and 30 < w < 400
                          else "input" if h < 35 and w > 80 else "unknown")
                    cx = (x + w // 2 + (region[0] if region else 0))
                    cy = (y + h // 2 + (region[1] if region else 0))
                    elements.append(UIElement(label=et, x=cx, y=cy, width=w,
                                              height=h, elem_type=et,
                                              confidence=min(1.0, area / 25000)))
            with self._lock:
                self._ui_elements = elements
        except Exception:
            pass
        return elements

    def detect_popups(self) -> bool:
        text = self.ocr_fast().lower()
        sigs = ["ok", "cancel", "yes", "no", "close", "error", "warning", "alert", "confirm"]
        return sum(1 for s in sigs if s in text) >= 2

    def detect_error_dialogs(self) -> Optional[str]:
        text = self.ocr_fast().lower()
        for e in ["error", "failed", "cannot", "invalid", "not found", "access denied"]:
            if e in text:
                return e
        return None

    def detect_loading(self) -> bool:
        text = self.ocr_fast().lower()
        return any(w in text for w in ["loading", "please wait", "processing", "connecting"])

    def wait_for_text(self, text: str, timeout: int = 30) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if text.lower() in self.ocr_fast().lower():
                return True
            time.sleep(0.8)
        return False

    def wait_loading_done(self, timeout: int = 60) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if not self.detect_loading():
                return True
            time.sleep(1.5)
        return True

    def get_screen_hash(self) -> str:
        try:
            img = self.capture_pil()
            if img is None:
                return ""
            small = img.resize((32, 32)).convert("L")
            return hashlib.md5(small.tobytes()).hexdigest()
        except Exception:
            return ""

    def has_screen_changed(self) -> bool:
        nh      = self.get_screen_hash()
        changed = nh != self._screen_hash
        self._screen_hash = nh
        return changed

    def track_application_state(self) -> Dict[str, Any]:
        return {"active_window": get_active_window(),
                "has_error": self.detect_error_dialogs(),
                "is_loading": self.detect_loading(),
                "has_popup": self.detect_popups(),
                "timestamp": datetime.datetime.now().isoformat()}

    def get_ai_description(self, token: str) -> str:
        ss = self.capture(quality=55)
        if not ss:
            return self.ocr_fast()[:300] or "Screen captured"
        try:
            if not req_lib:
                return self.ocr_fast()[:300]
            r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                             headers={"Authorization": f"Bearer {token}",
                                      "Content-Type": "application/json"},
                             json={"messages": [{"role": "user",
                                                 "content": "Describe this screen briefly."}],
                                   "stream": False},
                             timeout=20)
            if r.status_code == 200:
                return (r.json().get("content") or r.json().get("response", "") or "Screen captured")
        except Exception:
            pass
        return self.ocr_fast()[:300] or "Screen captured"

    def find_image_on_screen(self, template_path: str, threshold: float = 0.75) -> Optional[Tuple[int, int]]:
        if not CV2_OK or not NUMPY_OK:
            return None
        try:
            screen = self.capture_pil()
            if screen is None:
                return None
            sg   = cv2.cvtColor(np.array(screen.convert("RGB")), cv2.COLOR_RGB2GRAY)
            tmpl = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if tmpl is None:
                return None
            res = cv2.matchTemplate(sg, tmpl, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv >= threshold:
                th, tw = tmpl.shape
                return (ml[0] + tw // 2, ml[1] + th // 2)
        except Exception:
            pass
        return None

    def start_monitoring(self, interval: float = 2.0):
        if self._monitoring:
            return
        self._monitoring = True
        def _loop():
            while self._monitoring and _agent_running:
                try:
                    if self.has_screen_changed():
                        self.detect_ui_elements()
                        for cb in self._change_cbs:
                            try:
                                cb()
                            except Exception:
                                pass
                    time.sleep(interval)
                except Exception:
                    pass
        threading.Thread(target=_loop, daemon=True, name="VisionMonitor").start()


_vision_engine: Optional[SuperVisionEngine] = None


def get_vision() -> SuperVisionEngine:
    global _vision_engine
    if _vision_engine is None:
        _vision_engine = SuperVisionEngine()
    return _vision_engine


def get_active_window() -> str:
    try:
        if WINDOW_OK:
            w = gw.getActiveWindow()
            return w.title if w else ""
    except Exception:
        pass
    try:
        hwnd   = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf    = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""


def get_all_windows() -> List[str]:
    try:
        if WINDOW_OK:
            return [w.title for w in gw.getAllWindows() if w.title.strip()]
    except Exception:
        pass
    return []


def focus_window(title_kw: str) -> bool:
    try:
        if WINDOW_OK:
            wins = gw.getWindowsWithTitle(title_kw)
            if wins:
                wins[0].activate()
                time.sleep(0.3)
                return True
    except Exception:
        pass
    return False

# ============================================================
# BLOCK 14 - MOUSE & KEYBOARD
# ============================================================
def human_move(x: int, y: int, duration: float = None):
    try:
        if duration is None:
            cx, cy   = pyautogui.position()
            dist     = math.hypot(x - cx, y - cy)
            duration = max(0.07, min(0.50, dist / 2800))
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
    except Exception:
        pass


def human_click(x: int, y: int, button: str = "left", double: bool = False):
    try:
        jx = x + random.randint(-2, 2)
        jy = y + random.randint(-2, 2)
        human_move(jx, jy)
        time.sleep(random.uniform(0.04, 0.11))
        if double:
            pyautogui.doubleClick(jx, jy, button=button)
        else:
            pyautogui.click(jx, jy, button=button)
        time.sleep(random.uniform(0.04, 0.09))
        audit("CLICK", f"({x},{y})")
    except Exception as e:
        log.warning("human_click: %s", e)


def human_drag(x1, y1, x2, y2, duration: float = 0.5):
    try:
        human_move(x1, y1); time.sleep(0.1)
        pyautogui.mouseDown(); time.sleep(0.04)
        pyautogui.moveTo(x2, y2, duration=duration, tween=pyautogui.easeInOutQuad)
        time.sleep(0.04); pyautogui.mouseUp()
    except Exception:
        pass


def human_scroll(x: int, y: int, clicks: int, direction: str = "down"):
    try:
        human_move(x, y)
        sign = -1 if direction == "down" else 1
        pyautogui.scroll(sign * abs(clicks), x=x, y=y)
    except Exception:
        pass


def smart_type(text: str, clear_first: bool = False, human_speed: bool = False):
    text = str(text)[:5000]
    try:
        if clear_first:
            pyautogui.hotkey("ctrl", "a"); time.sleep(0.04)
            pyautogui.press("delete"); time.sleep(0.04)
        if human_speed and len(text) <= 100:
            for ch in text:
                pyautogui.typewrite(ch, interval=random.uniform(0.03, 0.08))
        else:
            if pyperclip:
                pyperclip.copy(text); time.sleep(0.05)
                pyautogui.hotkey("ctrl", "v"); time.sleep(0.08)
            else:
                pyautogui.write(text[:500], interval=0.02)
    except Exception as e:
        log.warning("smart_type: %s", e)


def press_key(key: str):
    try:
        pyautogui.press(key)
    except Exception:
        pass


def hotkey(*keys):
    try:
        pyautogui.hotkey(*keys)
    except Exception:
        pass


def get_clipboard() -> str:
    try:
        return pyperclip.paste() if pyperclip else ""
    except Exception:
        return ""


def set_clipboard(text: str):
    try:
        if pyperclip:
            pyperclip.copy(str(text))
    except Exception:
        pass

# ============================================================
# BLOCK 15 - APP MANAGEMENT
# ============================================================
def list_running_apps() -> List[Dict]:
    if not psutil:
        return []
    apps = []
    try:
        for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent"]):
            try:
                if proc.info["status"] == "running":
                    apps.append(proc.info)
            except Exception:
                continue
    except Exception:
        pass
    return apps


def kill_app(name: str) -> bool:
    if not psutil:
        return False
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            if name.lower() in (proc.info["name"] or "").lower():
                proc.kill()
                return True
    except Exception:
        pass
    return False


def open_app(app_name: str) -> bool:
    try:
        if platform.system() == "Windows":
            os.startfile(app_name)
        else:
            subprocess.Popen([app_name], shell=True)
        time.sleep(1.5)
        return True
    except Exception:
        try:
            subprocess.Popen(app_name, shell=True)
            time.sleep(1.5)
            return True
        except Exception as e:
            log.warning("open_app: %s", e)
            return False

# ============================================================
# BLOCK 16 - FILE ENGINE
# ============================================================
class FileEngine:
    SUPPORTED = {
        "text":    [".txt", ".md", ".py", ".js", ".html", ".css", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".log"],
        "data":    [".json", ".csv", ".tsv"],
        "docs":    [".docx", ".doc"],
        "sheet":   [".xlsx", ".xls"],
        "image":   [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"],
        "archive": [".zip", ".tar", ".gz", ".7z"],
    }

    def read(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        ext = p.suffix.lower()
        try:
            if ext in (self.SUPPORTED["text"] + self.SUPPORTED["data"]):
                return p.read_text(encoding="utf-8", errors="ignore")[:20000]
            elif ext == ".docx" and DOCX_OK:
                d = docx.Document(str(p))
                return "\n".join(x.text for x in d.paragraphs)[:10000]
            elif ext in (".xlsx", ".xls") and OPENPYXL_OK:
                wb   = openpyxl.load_workbook(str(p), data_only=True)
                rows = []
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        rows.append("\t".join(str(c or "") for c in row))
                return "\n".join(rows)[:10000]
            else:
                return p.read_bytes().hex()[:2000]
        except Exception as e:
            return f"Read error: {e}"

    def write(self, path: str, content: str, mode: str = "w") -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() == ".docx" and DOCX_OK:
                d = docx.Document()
                for para in content.split("\n"):
                    d.add_paragraph(para)
                d.save(str(p))
            else:
                with open(str(p), mode, encoding="utf-8") as f:
                    f.write(content)
            audit("WRITE_FILE", path, "OK")
            return True
        except Exception as e:
            log.warning("write_file: %s", e)
            return False

    def delete(self, path: str, safe: bool = True) -> bool:
        p = Path(path)
        if not p.exists():
            return False
        try:
            if safe:
                trash = Path.home() / ".dacexy_trash"
                trash.mkdir(exist_ok=True)
                dest  = trash / f"{p.name}_{int(time.time())}"
                p.rename(dest)
            else:
                if p.is_dir():
                    shutil.rmtree(str(p))
                else:
                    p.unlink()
            return True
        except Exception:
            return False

    def copy(self, src: str, dst: str) -> bool:
        try:
            shutil.copy2(src, dst); return True
        except Exception:
            return False

    def move(self, src: str, dst: str) -> bool:
        try:
            shutil.move(src, dst); return True
        except Exception:
            return False

    def search(self, keyword: str, folder: str = None, ext: str = None,
               content_search: bool = False) -> List[str]:
        results = []
        base = Path(folder) if folder else Path.home()
        pat  = f"**/*.{ext}" if ext else "**/*"
        try:
            for f in base.glob(pat):
                if not f.is_file():
                    continue
                if keyword.lower() in f.name.lower():
                    results.append(str(f))
                elif content_search:
                    try:
                        if keyword.lower() in f.read_text(encoding="utf-8", errors="ignore").lower():
                            results.append(str(f))
                    except Exception:
                        pass
                if len(results) >= 100:
                    break
        except Exception:
            pass
        return results

    def compress(self, paths: List[str], output: str) -> bool:
        try:
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in paths:
                    pp = Path(p)
                    if pp.is_file():
                        zf.write(str(pp), pp.name)
                    elif pp.is_dir():
                        for fp in pp.rglob("*"):
                            if fp.is_file():
                                zf.write(str(fp), str(fp.relative_to(pp.parent)))
            return True
        except Exception:
            return False

    def extract(self, zip_path: str, output_dir: str = None) -> bool:
        try:
            out = output_dir or str(Path(zip_path).parent)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(out)
            return True
        except Exception:
            return False

    def backup(self, source_dir: str, label: str = "") -> str:
        try:
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = (f"backup_{label}_{ts}.zip" if label else f"backup_{ts}.zip")
            dest = str(BACKUP_DIR / name)
            self.compress([source_dir], dest)
            return dest
        except Exception:
            return ""

    def organize_folder(self, folder: str) -> Dict[str, int]:
        moved = defaultdict(int)
        base  = Path(folder)
        tmap  = {ext: cat for cat, exts in self.SUPPORTED.items() for ext in exts}
        try:
            for f in base.iterdir():
                if not f.is_file():
                    continue
                cat = tmap.get(f.suffix.lower(), "other")
                dd  = base / cat
                dd.mkdir(exist_ok=True)
                f.rename(dd / f.name)
                moved[cat] += 1
        except Exception:
            pass
        return dict(moved)

    def list_files(self, folder: str = None, pattern: str = "*") -> List[str]:
        try:
            p = Path(folder) if folder else Path.home()
            return [str(f) for f in p.glob(pattern) if f.is_file()][:200]
        except Exception:
            return []

    def get_disk_usage(self) -> Dict[str, Any]:
        if not psutil:
            return {}
        try:
            u = psutil.disk_usage("/")
            return {"total_gb": round(u.total / 1e9, 2),
                    "used_gb":  round(u.used  / 1e9, 2),
                    "free_gb":  round(u.free  / 1e9, 2),
                    "percent":  u.percent}
        except Exception:
            return {}


_file_engine: Optional[FileEngine] = None


def get_file_engine() -> FileEngine:
    global _file_engine
    if _file_engine is None:
        _file_engine = FileEngine()
    return _file_engine

# ============================================================
# BLOCK 17 - EMAIL CAMPAIGN MANAGER
# ============================================================
class EmailCampaignManager:
    def __init__(self):
        self.smtp_config = get_smtp_config()
        self.smtp_pool:  List[Dict] = []
        self.campaigns:  Dict[str, EmailCampaignData] = {}
        try:
            self._load_campaigns()
        except Exception:
            pass
        threading.Thread(target=self._retry_worker, daemon=True, name="EmailRetry").start()

    def _load_campaigns(self):
        if CAMPAIGN_FILE.exists():
            raw = json.loads(CAMPAIGN_FILE.read_text(encoding="utf-8"))
            for cid, cdata in raw.items():
                try:
                    self.campaigns[cid] = EmailCampaignData(**cdata)
                except Exception:
                    pass

    def _save_campaigns(self):
        try:
            CAMPAIGN_FILE.write_text(
                json.dumps({cid: asdict(c) for cid, c in self.campaigns.items()}, indent=2))
        except Exception:
            pass

    def setup_gmail(self, email: str, app_password: str):
        cfg = {"host": "smtp.gmail.com", "port": 587, "email": email,
               "password": app_password, "use_tls": True}
        save_smtp_config(cfg)
        self.smtp_config = cfg
        self.smtp_pool.append(cfg)
        _ok(f"Gmail configured: {mask_pii(email)}")

    def setup_outlook(self, email: str, password: str):
        cfg = {"host": "smtp-mail.outlook.com", "port": 587, "email": email,
               "password": password, "use_tls": True}
        save_smtp_config(cfg)
        self.smtp_config = cfg
        _ok(f"Outlook configured: {mask_pii(email)}")

    def _get_smtp(self, idx: int = 0):
        pool = self.smtp_pool if self.smtp_pool else ([self.smtp_config] if self.smtp_config else [])
        if not pool:
            raise ValueError("SMTP not configured. Run: setup gmail <email> <app_password>")
        cfg = pool[idx % len(pool)]
        if cfg.get("use_tls"):
            s = smtplib.SMTP(cfg["host"], cfg["port"], timeout=30)
            s.ehlo(); s.starttls()
        else:
            s = smtplib.SMTP_SSL(cfg["host"], cfg.get("port", 465), timeout=30)
        s.login(cfg["email"], cfg["password"])
        return s, cfg

    def personalize(self, template: str, email: str, index: int = 0, extra: Dict = None) -> str:
        name  = email.split("@")[0].replace(".", " ").replace("_", " ").title()
        first = name.split()[0] if name.split() else name
        t = (template.replace("{name}", name).replace("{first}", first)
             .replace("{email}", email).replace("{index}", str(index + 1))
             .replace("{date}", datetime.date.today().strftime("%B %d, %Y")))
        if extra:
            for k, v in extra.items():
                t = t.replace(f"{{{k}}}", str(v))
        return t

    def create_campaign(self, name: str, subject: str, body_template: str,
                        recipients: List[str], html: bool = True,
                        delay_sec: float = 1.0, scheduled_at: str = None,
                        tags: List[str] = None) -> str:
        cid  = generate_id("camp_")
        camp = EmailCampaignData(campaign_id=cid, name=name, subject=subject,
                                 body_template=body_template,
                                 recipients=list(set(recipients)), html=html,
                                 delay_sec=delay_sec, scheduled_at=scheduled_at,
                                 tags=tags or [])
        with _campaign_lock:
            self.campaigns[cid] = camp
        self._save_campaigns()
        _ok(f"Campaign '{name}': {len(camp.recipients)} recipients")
        return cid

    def send_campaign(self, campaign_id: str, provider_index: int = 0) -> Dict[str, Any]:
        camp = self.campaigns.get(campaign_id)
        if not camp:
            return {"error": "Campaign not found"}
        camp.status = "running"
        self._save_campaigns()
        speak(f"Starting email campaign '{camp.name}' to {len(camp.recipients)} recipients.")
        sent = failed = bounced = 0
        start_t = time.time()
        try:
            server, cfg = self._get_smtp(provider_index)
            from_email  = cfg.get("email", "")
            for i, to in enumerate(camp.recipients):
                if _emergency_stop_event.is_set():
                    break
                try:
                    body = self.personalize(camp.body_template, to, i)
                    subj = self.personalize(camp.subject, to, i)
                    msg  = MIMEMultipart("alternative")
                    msg["Subject"] = subj; msg["From"] = from_email; msg["To"] = to
                    msg.attach(MIMEText(body, "html" if camp.html else "plain", "utf-8"))
                    server.sendmail(from_email, to, msg.as_string())
                    sent += 1; camp.sent = sent
                    _info(f"[{i+1}/{len(camp.recipients)}] -> {to}")
                    time.sleep(camp.delay_sec + random.uniform(0.1, 0.4))
                    if (i + 1) % 100 == 0:
                        try: server.quit()
                        except Exception: pass
                        server, cfg = self._get_smtp(provider_index)
                except smtplib.SMTPRecipientsRefused:
                    bounced += 1; failed += 1
                except Exception as e:
                    failed += 1
                    camp.retry_queue.append(to)
                    log.warning("Email failed %s: %s", to, e)
            try: server.quit()
            except Exception: pass
        except Exception as e:
            log.error("Campaign SMTP error: %s", e)
            failed = len(camp.recipients) - sent
        elapsed = time.time() - start_t
        camp.status = "complete"; camp.sent = sent; camp.failed = failed; camp.bounced = bounced
        self._save_campaigns()
        result = {"campaign": camp.name, "sent": sent, "failed": failed,
                  "bounced": bounced, "total": len(camp.recipients),
                  "rate": f"{100*sent//max(1,len(camp.recipients))}%",
                  "duration_min": round(elapsed / 60, 1)}
        speak(f"Campaign complete. {sent} sent.")
        audit("CAMPAIGN", camp.name, f"sent={sent} failed={failed}")
        return result

    def send_single(self, to: str, subject: str, body: str,
                    html: bool = False, attachment: str = None) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject; msg["From"] = self.smtp_config.get("email", ""); msg["To"] = to
            msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))
            if attachment and os.path.exists(attachment):
                with open(attachment, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition",
                                    f"attachment; filename={os.path.basename(attachment)}")
                    msg.attach(part)
            s, cfg = self._get_smtp()
            s.sendmail(cfg["email"], to, msg.as_string())
            s.quit()
            audit("SEND_EMAIL", mask_pii(to), "OK")
            return True
        except Exception as e:
            log.error("Single email: %s", e)
            return False

    def _retry_worker(self):
        while _agent_running:
            time.sleep(600)
            with _campaign_lock:
                camps = list(self.campaigns.values())
            for camp in camps:
                if camp.retry_queue and camp.status == "complete":
                    orig            = camp.recipients[:]
                    camp.recipients = list(camp.retry_queue)
                    camp.retry_queue = []
                    self.send_campaign(camp.campaign_id)
                    camp.recipients = orig

    def get_dashboard(self) -> Dict:
        clist  = [{"name": c.name, "sent": c.sent, "failed": c.failed,
                   "total": len(c.recipients), "status": c.status}
                  for c in self.campaigns.values()]
        t_sent = sum(c.get("sent", 0) for c in clist)
        t_rec  = sum(c.get("total", 0) for c in clist)
        return {"total_campaigns": len(clist), "total_recipients": t_rec,
                "total_sent": t_sent, "overall_rate": f"{100*t_sent//max(1,t_rec)}%",
                "campaigns": clist}

# ============================================================
# BLOCK 18 - ENTERPRISE BROWSER AGENT
# ============================================================
class EnterpriseBrowserAgent:
    WAIT = 15

    def __init__(self):
        self.driver = None; self.browser_type = "chrome"; self.headless = False

    def start(self, browser: str = "chrome", headless: bool = False, profile: str = None) -> bool:
        if not SELENIUM_OK:
            _err("Selenium not available."); return False
        self.browser_type = browser.lower(); self.headless = headless
        try:
            opts = ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-notifications")
            opts.add_argument("--start-maximized")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            opts.add_experimental_option("useAutomationExtension", False)
            if profile:
                opts.add_argument(f"--user-data-dir={profile}")
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
            try:
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
            except Exception:
                pass
            self.driver.implicitly_wait(4)
            _ok(f"Browser started: {browser}")
            return True
        except Exception as e:
            log.error("Browser start failed: %s", e); return False

    def stop(self):
        try:
            if self.driver:
                self.driver.quit(); self.driver = None
        except Exception:
            pass

    def _by(self, by: str):
        from selenium.webdriver.common.by import By as _B
        return {"css": _B.CSS_SELECTOR, "xpath": _B.XPATH, "id": _B.ID,
                "name": _B.NAME, "text": _B.LINK_TEXT, "class": _B.CLASS_NAME,
                "tag": _B.TAG_NAME}.get(by, _B.CSS_SELECTOR)

    def find(self, selector: str, by: str = "css", timeout: int = None):
        try:
            return WebDriverWait(self.driver, timeout or self.WAIT).until(
                EC.presence_of_element_located((self._by(by), selector)))
        except Exception:
            return None

    def find_and_click(self, selector: str, by: str = "css",
                       fallback_selectors: List[str] = None, js_fallback: bool = True) -> bool:
        sels = [(selector, by)] + [(s, "css") for s in (fallback_selectors or [])]
        for sel, b in sels:
            try:
                el = WebDriverWait(self.driver, self.WAIT).until(
                    EC.element_to_be_clickable((self._by(b), sel)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.15 + random.uniform(0, 0.2))
                try:
                    el.click()
                except Exception:
                    if js_fallback:
                        self.driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                continue
        return False

    def find_and_type(self, selector: str, text: str, by: str = "css",
                      clear: bool = True, human_speed: bool = True) -> bool:
        try:
            el = WebDriverWait(self.driver, self.WAIT).until(
                EC.presence_of_element_located((self._by(by), selector)))
            if clear:
                el.clear(); time.sleep(0.1)
            if human_speed and len(text) <= 80:
                for ch in text:
                    el.send_keys(ch); time.sleep(random.uniform(0.03, 0.10))
            else:
                el.send_keys(text)
            return True
        except Exception:
            return False

    def detect_captcha(self) -> bool:
        try:
            page = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            return any(s in page for s in ["captcha", "recaptcha", "i'm not a robot"])
        except Exception:
            return False

    def handle_captcha(self) -> bool:
        if self.detect_captcha():
            speak("CAPTCHA detected. Please solve it then press Enter.", priority=True)
            try:
                _get_console_input("  Press Enter after solving CAPTCHA... ")
            except Exception:
                time.sleep(30)
            return True
        return False

    def go_to(self, url: str, wait: float = 1.5):
        if not url.startswith("http"):
            url = "https://" + url
        try:
            self.driver.get(url)
            time.sleep(wait + random.uniform(0, 0.4))
        except Exception:
            pass

    def get_page_text(self) -> str:
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text[:8000]
        except Exception:
            return ""

    def execute_js(self, script: str, *args):
        try:
            return self.driver.execute_script(script, *args)
        except Exception:
            return None

    def extract_data(self, selector: str, by: str = "css") -> List[str]:
        try:
            els = self.driver.find_elements(self._by(by), selector)
            return [e.text for e in els if e.text.strip()]
        except Exception:
            return []

    def screenshot_b64(self) -> Optional[str]:
        try:
            return base64.b64encode(self.driver.get_screenshot_as_png()).decode()
        except Exception:
            return None

    def google_search(self, query: str) -> List[str]:
        try:
            self.go_to(f"https://www.google.com/search?q={quote(query)}")
            time.sleep(2)
            return [h.text for h in self.driver.find_elements(By.CSS_SELECTOR, "h3")
                    if h.text.strip()][:10]
        except Exception:
            return []

    def research_topic(self, topic: str, max_pages: int = 3) -> Dict:
        results  = self.google_search(topic)
        research = {"topic": topic, "sources": [], "results": results}
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, "div.g a")
            urls  = [e.get_attribute("href") for e in links
                     if e.get_attribute("href") and "google.com" not in (e.get_attribute("href") or "")][:max_pages]
            for url in urls:
                try:
                    self.execute_js(f"window.open('{url}','_blank');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(3)
                    research["sources"].append({"url": url, "text": self.get_page_text()[:300]})
                    self.driver.close()
                    if self.driver.window_handles:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                except Exception:
                    pass
        except Exception:
            pass
        try:
            fn = RESEARCH_DIR / f"research_{int(time.time())}.json"
            fn.write_text(json.dumps(research, indent=2))
        except Exception:
            pass
        return research

    def compose_gmail(self, to: str, subject: str, body: str) -> bool:
        """Open Gmail in browser and compose+send an email using Selenium."""
        try:
            if not self.driver:
                self.start("chrome")
            self.go_to("https://mail.google.com", wait=4)
            time.sleep(3)
            # Click Compose
            composed = False
            for sel in ["[gh='cm']", ".T-I.T-I-KE.L3", "[data-tooltip='Compose']",
                        "//div[contains(text(),'Compose')]"]:
                by = "xpath" if sel.startswith("//") else "css"
                if self.find_and_click(sel, by=by):
                    composed = True
                    break
            if not composed:
                _err("Could not find Compose button in Gmail")
                return False
            time.sleep(2)
            # To field
            for sel in ["[name='to']", ".agP.aFw input", "[aria-label='To']"]:
                if self.find_and_type(sel, to, clear=True):
                    break
            time.sleep(0.5)
            pyautogui.press("tab")
            time.sleep(0.5)
            # Subject field
            for sel in ["[name='subjectbox']", "[placeholder='Subject']", ".aoT"]:
                if self.find_and_type(sel, subject, clear=True):
                    break
            time.sleep(0.5)
            # Body field
            for sel in ["[aria-label='Message Body']", ".Am.Al.editable", "[role='textbox']"]:
                if self.find_and_type(sel, body, clear=False):
                    break
            time.sleep(0.5)
            # Send button
            for sel in ["[data-tooltip='Send']", "[aria-label='Send']",
                        ".T-I.J-J5-Ji.aoO.v7.T-I-atl.L3",
                        "//div[contains(@aria-label,'Send')]"]:
                by = "xpath" if sel.startswith("//") else "css"
                if self.find_and_click(sel, by=by):
                    time.sleep(2)
                    _ok(f"Email sent to {to}")
                    audit("GMAIL_SEND", mask_pii(to), "OK")
                    return True
            _err("Could not find Send button")
            return False
        except Exception as e:
            log.error("compose_gmail: %s", e)
            return False

    def whatsapp_bulk(self, contacts: List[str], message: str, delay: float = 3.5) -> Dict[str, Any]:
        if not self.driver and not self.start("chrome"):
            return {"error": "Browser not started"}
        speak(f"Starting WhatsApp to {len(contacts)} contacts.")
        self.go_to("https://web.whatsapp.com")
        speak("Scan QR if needed. Waiting up to 90 seconds.")
        time.sleep(5)
        loaded = False
        for _ in range(30):
            try:
                self.driver.find_element(By.XPATH, '//div[@data-testid="chat-list"]')
                loaded = True; break
            except Exception:
                time.sleep(3)
        if not loaded:
            return {"error": "WhatsApp Web not loaded"}
        sent = failed = 0
        for i, contact in enumerate(contacts):
            if _emergency_stop_event.is_set():
                break
            try:
                phone = re.sub(r'\D', '', contact)
                if phone:
                    self.go_to(f"https://web.whatsapp.com/send?phone={phone}&text={quote(message)}")
                    time.sleep(5)
                    btn = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="compose-btn-send"]')))
                    btn.click(); time.sleep(1)
                sent += 1
                _info(f"[{i+1}/{len(contacts)}] WA -> {contact}")
                time.sleep(delay + random.uniform(0.5, 1.5))
            except Exception as e:
                failed += 1
                log.warning("WA failed %s: %s", contact, e)
        speak(f"WhatsApp done. Sent {sent}/{len(contacts)}.")
        return {"sent": sent, "failed": failed, "total": len(contacts)}

    def twitter_post(self, username: str, password: str, text: str, media_path: str = None) -> bool:
        try:
            self.go_to("https://twitter.com/login", wait=3)
            self.find_and_type('input[autocomplete="username"]', username)
            time.sleep(0.6)
            self.find_and_click('//span[text()="Next"]', by="xpath")
            time.sleep(2)
            self.find_and_type('input[name="password"]', password)
            time.sleep(0.6)
            self.find_and_click('[data-testid="LoginForm_Login_Button"]')
            time.sleep(5); self.handle_captcha()
            self.find_and_click('[data-testid="tweetTextarea_0"]',
                                fallback_selectors=['[role="textbox"]'])
            time.sleep(0.8)
            self.find_and_type('[data-testid="tweetTextarea_0"]', text[:280])
            time.sleep(0.6)
            self.find_and_click('[data-testid="tweetButton"]')
            time.sleep(3); _ok("Tweet posted"); return True
        except Exception as e:
            log.error("Twitter: %s", e); return False

    def linkedin_post(self, username: str, password: str, text: str) -> bool:
        try:
            self.go_to("https://www.linkedin.com/login", wait=3)
            self.find_and_type("#username", username)
            self.find_and_type("#password", password)
            self.find_and_click('[type="submit"]')
            time.sleep(5); self.handle_captcha()
            tb = (self.find('//div[@role="textbox"]', by="xpath") or
                  self.find('[contenteditable="true"]'))
            if tb:
                tb.click(); time.sleep(0.3); tb.send_keys(text)
            self.find_and_click('//button[contains(text(),"Post")]', by="xpath")
            time.sleep(3); _ok("LinkedIn posted"); return True
        except Exception as e:
            log.error("LinkedIn: %s", e); return False

    def facebook_post(self, username: str, password: str, text: str, page_id: str = None) -> bool:
        try:
            self.go_to("https://www.facebook.com", wait=3)
            self.find_and_type("#email", username)
            self.find_and_type("#pass", password)
            self.find_and_click('[type="submit"]')
            time.sleep(5); self.handle_captcha()
            if page_id:
                self.go_to(f"https://www.facebook.com/{page_id}", wait=3)
            self.find_and_click('[placeholder*="What"]', fallback_selectors=['[role="textbox"]'])
            time.sleep(2.5)
            self.find_and_type('[role="textbox"]', text)
            time.sleep(1)
            self.find_and_click('[type="submit"]')
            time.sleep(3); _ok("Facebook posted"); return True
        except Exception as e:
            log.error("Facebook: %s", e); return False

    def instagram_post(self, username: str, password: str, image_path: str, caption: str) -> bool:
        try:
            self.go_to("https://www.instagram.com/accounts/login/", wait=4)
            self.find_and_type('[name="username"]', username)
            self.find_and_type('[name="password"]', password)
            self.find_and_click('[type="submit"]')
            time.sleep(7); self.handle_captcha()
            self.find_and_click('[aria-label="New post"]')
            time.sleep(2)
            fi = self.find('input[type="file"]')
            if fi and image_path:
                fi.send_keys(str(Path(image_path).resolve())); time.sleep(3)
            for _ in range(2):
                self.find_and_click('//button[text()="Next"]', by="xpath"); time.sleep(2)
            ce = self.find('//div[@aria-label="Write a caption..."]', by="xpath")
            if ce:
                ce.click(); ce.send_keys(caption)
            self.find_and_click('//button[text()="Share"]', by="xpath")
            time.sleep(5); _ok("Instagram posted"); return True
        except Exception as e:
            log.error("Instagram: %s", e); return False

    def youtube_upload(self, video_path: str, title: str, description: str, tags: List[str] = None) -> bool:
        try:
            self.go_to("https://studio.youtube.com", wait=3); self.handle_captcha()
            self.find_and_click('//ytcp-button[@id="create-icon"]', by="xpath"); time.sleep(1.5)
            self.find_and_click('//tp-yt-paper-item[@id="text-item-0"]', by="xpath"); time.sleep(2.5)
            fi = self.find('input#file-loader')
            if fi:
                fi.send_keys(str(Path(video_path).resolve())); time.sleep(6)
            te = self.find('#title-textarea')
            if te:
                te.click(); self.execute_js("arguments[0].innerHTML='';", te); te.send_keys(title)
            de = self.find('#description-textarea')
            if de:
                de.click(); de.send_keys(description)
            for _ in range(3):
                self.find_and_click('#next-button'); time.sleep(2)
            self.find_and_click('#done-button'); time.sleep(5)
            _ok("YouTube upload complete"); return True
        except Exception as e:
            log.error("YouTube: %s", e); return False

    def tiktok_post(self, video_path: str, caption: str) -> bool:
        try:
            self.go_to("https://www.tiktok.com/upload", wait=3); self.handle_captcha()
            fi = self.find('input[type="file"]')
            if fi:
                fi.send_keys(str(Path(video_path).resolve())); time.sleep(6)
            ce = self.find('//div[@contenteditable="true"]', by="xpath")
            if ce:
                ce.click(); self.execute_js("arguments[0].innerHTML='';", ce); ce.send_keys(caption)
            self.find_and_click('//button[text()="Post"]', by="xpath")
            time.sleep(5); _ok("TikTok posted"); return True
        except Exception as e:
            log.error("TikTok: %s", e); return False

# ============================================================
# BLOCK 19 - SECURITY
# ============================================================
PERMISSION_RULES = {
    "delete_files": {"triggers": [["delete", "erase", "wipe"], ["file", "folder", "data"]],
                     "icon": "[DELETE]", "label": "DELETE FILES", "warn": "This will permanently delete files."},
    "banking":      {"triggers": [["bank", "upi", "transfer", "gpay", "paytm"], ["any"]],
                     "icon": "[BANK]", "label": "BANKING", "warn": "Accessing financial services."},
    "payment":      {"triggers": [["pay", "purchase", "credit card", "cvv"], ["any"]],
                     "icon": "[PAY]", "label": "PAYMENT", "warn": "Making a payment."},
    "email_bulk":   {"triggers": [["bulk email", "mass email", "send email"], ["any"]],
                     "icon": "[EMAIL]", "label": "BULK EMAIL", "warn": "Sending bulk emails."},
    "social_post":  {"triggers": [["post on", "tweet", "publish"],
                                  ["facebook", "instagram", "twitter", "linkedin", "tiktok"]],
                     "icon": "[SOCIAL]", "label": "SOCIAL POST", "warn": "Posting to social media."},
    "whatsapp_bulk":{"triggers": [["whatsapp bulk", "bulk whatsapp"], ["any"]],
                     "icon": "[WA]", "label": "BULK WHATSAPP", "warn": "Sending bulk WhatsApp messages."},
    "shutdown":     {"triggers": [["shutdown", "restart", "reboot"], ["any"]],
                     "icon": "[POWER]", "label": "SHUTDOWN", "warn": "Shutting down computer."},
}

BLOCKED_COMMANDS = ["rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
                    "dd if=/dev/zero", "rd /s /q c:\\", "reg delete hklm"]


def emergency_stop():
    global _agent_running
    _emergency_stop_event.set()
    _agent_running = False
    speak("Emergency stop. All tasks halted.", priority=True)
    audit("EMERGENCY_STOP", "", "TRIGGERED")
    _info("EMERGENCY STOP ACTIVATED")


def needs_permission(task: str) -> Tuple[bool, str]:
    tl = task.lower()
    for ptype, rule in PERMISSION_RULES.items():
        kws, ctx = rule["triggers"]
        if any(k in tl for k in kws):
            if ctx == ["any"] or any(c in tl for c in ctx):
                return True, ptype
    return False, ""


def ask_permission(task: str, ptype: str) -> bool:
    rule  = PERMISSION_RULES.get(ptype, {})
    print(f"\n  {rule.get('icon','[!]')} PERMISSION REQUIRED: {rule.get('label','ACTION')}")
    print(f"  WARNING: {rule.get('warn','')}")
    print(f'  Task: "{task[:80]}"')
    sys.stdout.flush()
    speak(f"Permission needed: {rule.get('warn','')}")
    granted = _get_console_input("\n  Type YES to allow or NO to deny: ").strip().lower() in ["yes", "y"]
    speak("Permission granted." if granted else "Task cancelled.")
    audit("PERM", mask_pii(f"{ptype}: {task[:80]}"), "GRANTED" if granted else "DENIED")
    return granted


def is_blocked(cmd: str) -> bool:
    cl = cmd.lower()
    return any(b in cl for b in BLOCKED_COMMANDS)

# ============================================================
# BLOCK 20 - PLANNER AGENT  (FIXED: correct action names in prompt)
# ============================================================
class PlannerAgent:
    def __init__(self, token: str):
        self.token = token

    def run(self, task: Dict[str, Any]) -> List[Dict]:
        desc = task.get("task", "")
        log.info("Planner: %s", desc)
        try:
            if not req_lib:
                raise ValueError("no requests")
            ctx    = get_memory_context(desc)
            # FIX: strict action list so planner never returns unknown actions
            prompt = (
                "You are a desktop automation planner. Return ONLY a JSON array, no markdown, no explanation.\n"
                f"Task: {desc}\n"
                f"Context: {ctx[:300]}\n\n"
                "STRICT RULES:\n"
                "- To open a website/URL use action 'open_url' with field 'url'\n"
                "- To open an app use action 'open_app' with field 'app'\n"
                "- To click on screen use action 'click' with fields 'x' and 'y' (real pixel coordinates)\n"
                "- To type text use action 'type_text' with field 'text'\n"
                "- To send email via Gmail browser use action 'gmail_send' with fields 'to','subject','body'\n"
                "- To send email via SMTP use action 'send_email' with fields 'to','subject','body'\n"
                "- To use browser automation use action 'browser_go' with field 'url'\n"
                "- To click browser element use action 'browser_click' with field 'selector'\n"
                "- To type in browser use action 'browser_type' with fields 'selector','text'\n"
                "- To wait use action 'wait' with field 'seconds'\n"
                "- To speak use action 'speak' with field 'text'\n"
                "- To take screenshot use action 'screenshot'\n"
                "- NEVER use action 'open' - use 'open_url' or 'open_app' instead\n"
                "- NEVER use click with x=0,y=0 - only use click if you know real coordinates\n\n"
                'Return ONLY: [{"step":1,"action":"open_url","description":"...","params":{},"url":"https://..."}]'
            )
            r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                             headers={"Authorization": f"Bearer {self.token}",
                                      "Content-Type": "application/json"},
                             json={"messages": [{"role": "user", "content": prompt}], "stream": False},
                             timeout=35)
            if r.status_code == 200:
                content = (r.json().get("content", "") or r.json().get("response", ""))
                # strip markdown fences
                content = re.sub(r"```(?:json)?", "", content).strip().rstrip("`")
                m = re.search(r'\[.*\]', content, re.DOTALL)
                if m:
                    steps = json.loads(m.group())
                    # merge params into top level for executor compatibility
                    for s in steps:
                        for k, v in s.get("params", {}).items():
                            if k not in s:
                                s[k] = v
                    return steps
        except Exception as e:
            log.warning("Planning: %s", e)
        return [{"step": 1, "action": "speak", "description": desc, "text": f"I will do: {desc}", "params": {}}]


# ============================================================
# BLOCK 21 - AGENT SWARM
# ============================================================
class AgentSwarm:
    def __init__(self, token: str, browser: EnterpriseBrowserAgent, email_mgr: EmailCampaignManager):
        self.token     = token
        self.browser   = browser
        self.email_mgr = email_mgr
        self.planner   = PlannerAgent(token)
        self._bus: queue.Queue = queue.Queue()
        self._results: Dict[str, Any] = {}
        for i in range(4):
            threading.Thread(target=self._worker, daemon=True, name=f"Swarm-{i}").start()
        log.info("AgentSwarm initialized (4 workers)")

    def _worker(self):
        while _agent_running:
            try:
                tid, aname, task, handler = self._bus.get(timeout=1)
                try:
                    result = handler(task)
                    self._results[tid] = {"status": "ok", "result": result}
                except Exception as e:
                    self._results[tid] = {"status": "error", "error": str(e)}
                self._bus.task_done()
            except queue.Empty:
                continue

    def plan_and_execute(self, task_desc: str, command_executor: Callable) -> Dict[str, Any]:
        _task(f"Swarm planning: {task_desc}")
        steps   = self.planner.run({"task": task_desc})
        _task(f"Executing {len(steps)} steps...")
        results = []
        start_t = time.time()
        for step in steps:
            if _emergency_stop_event.is_set():
                break
            sn   = step.get("step", 0)
            desc = step.get("description", step.get("action", ""))
            _info(f"  Step {sn}: {desc}")
            for attempt in range(3):
                try:
                    r = command_executor(step)
                    results.append({"step": sn, "ok": True, "result": r})
                    get_mem().remember_success(desc, "swarm")
                    break
                except Exception as e:
                    if attempt == 2:
                        results.append({"step": sn, "ok": False, "error": str(e)})
                        get_mem().remember_failure(desc, str(e))
                    else:
                        time.sleep(1.5 * (attempt + 1))
        elapsed  = time.time() - start_t
        ok_count = sum(1 for r in results if r.get("ok"))
        if ok_count == len(steps) and len(steps) > 1:
            get_mem().save_skill(task_desc[:50], steps,
                                 f"Auto-learned: {task_desc[:100]}", ["auto-learned"])
        speak(f"Task done: {ok_count}/{len(steps)} steps succeeded.")
        return {"total": len(steps), "ok": ok_count, "elapsed_sec": round(elapsed, 1), "results": results}

# ============================================================
# BLOCK 22 - SELF-HEALING ENGINE
# ============================================================
class SelfHealingEngine:
    def __init__(self, command_executor: Callable):
        self.executor  = command_executor
        self._metrics: List[Dict] = []

    def get_health(self) -> Dict[str, Any]:
        if not psutil:
            return {"healthy": True, "cpu": 0, "ram": 0, "disk": 0}
        try:
            cpu  = psutil.cpu_percent(interval=0.3)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return {"cpu": cpu, "ram": ram.percent, "disk": disk.percent,
                    "ram_used_gb": round(ram.used / 1e9, 2),
                    "disk_free_gb": round(disk.free / 1e9, 2),
                    "healthy": (cpu < 92 and ram.percent < 92 and disk.percent < 96),
                    "timestamp": datetime.datetime.now().isoformat()}
        except Exception:
            return {"healthy": True}

    def _check(self):
        h = self.get_health()
        self._metrics.append(h)
        if len(self._metrics) > 50:
            self._metrics = self._metrics[-30:]
        if h.get("cpu", 0) > 92:
            _warn(f"High CPU: {h['cpu']}%")
        if h.get("ram", 0) > 92:
            _warn(f"High RAM: {h['ram']}% - clearing caches")
            _result_cache.clear(); gc.collect()
        if h.get("disk", 0) > 96:
            _warn("Low disk - cleaning trash")
            try:
                trash = Path.home() / ".dacexy_trash"
                if trash.exists():
                    shutil.rmtree(str(trash)); trash.mkdir()
            except Exception:
                pass

    def start(self):
        def _loop():
            while _agent_running:
                try:
                    self._check()
                except Exception:
                    pass
                time.sleep(60)
        threading.Thread(target=_loop, daemon=True, name="SelfHealing").start()

# ============================================================
# BLOCK 23 - AUTONOMOUS SCHEDULER
# ============================================================
class AutonomousScheduler:
    def __init__(self, command_executor: Callable):
        self.executor = command_executor
        self.jobs: List[Dict] = []
        self._load()

    def _load(self):
        try:
            if SCHEDULE_FILE.exists():
                self.jobs = json.loads(SCHEDULE_FILE.read_text())
        except Exception:
            pass

    def _save(self):
        try:
            SCHEDULE_FILE.write_text(json.dumps(self.jobs, indent=2))
        except Exception:
            pass

    def add_job(self, name: str, command: Dict, schedule_type: str,
                time_str: str = "", days: List[str] = None,
                repeat_every_minutes: int = 0) -> str:
        jid = generate_id("job_")
        self.jobs.append({"job_id": jid, "name": name, "command": command,
                          "type": schedule_type, "time": time_str, "days": days or [],
                          "repeat_every_minutes": repeat_every_minutes,
                          "created": datetime.datetime.now().isoformat(),
                          "last_run": "", "run_count": 0, "enabled": True})
        self._save()
        _ok(f"Job '{name}' scheduled ({schedule_type} {time_str})")
        return jid

    def remove_job(self, job_id: str):
        self.jobs = [j for j in self.jobs if j["job_id"] != job_id]
        self._save()

    def list_jobs(self) -> List[Dict]:
        return self.jobs

    def _should_run(self, job: Dict) -> bool:
        if not job.get("enabled"):
            return False
        now    = datetime.datetime.now()
        jtype  = job.get("type", "daily")
        jtime  = job.get("time", "")
        now_hm = now.strftime("%H:%M")
        last   = job.get("last_run", "")
        if last and last[:16] == now.strftime("%Y-%m-%dT%H:%M"):
            return False
        rmins = job.get("repeat_every_minutes", 0)
        if rmins > 0:
            if not last:
                return True
            try:
                last_dt  = datetime.datetime.fromisoformat(last)
                mins_ago = (now - last_dt).total_seconds() / 60
                return mins_ago >= rmins
            except Exception:
                return True
        if jtime and now_hm != jtime:
            return False
        if jtype == "daily":
            return True
        if jtype == "weekly":
            return now.strftime("%A").lower() in [d.lower() for d in job.get("days", [])]
        return False

    def _tick(self):
        for job in self.jobs:
            if self._should_run(job):
                _task(f"Scheduled job: {job['name']}")
                try:
                    self.executor(job["command"])
                    job["last_run"]  = datetime.datetime.now().isoformat()
                    job["run_count"] = job.get("run_count", 0) + 1
                    add_task_history(f"Job: {job['name']}")
                except Exception as e:
                    log.error("Job '%s': %s", job["name"], e)
        self._save()

    def start(self):
        def _loop():
            while _agent_running:
                try:
                    self._tick()
                except Exception:
                    pass
                time.sleep(30)
        threading.Thread(target=_loop, daemon=True, name="Scheduler").start()

# ============================================================
# BLOCK 24 - VOICE ASSISTANT 3.0
# ============================================================
class VoiceAssistant3:
    WAKE_WORDS = ["hey dacexy", "dacexy", "assistant"]

    def __init__(self, token: str, command_callback: Callable):
        self.token    = token
        self.callback = command_callback
        self.rec      = sr.Recognizer() if sr else None
        self.mic      = None
        self.running  = False
        self.paused   = False
        if VOICE_AVAILABLE and self.rec:
            try:
                self.rec.energy_threshold         = 2800
                self.rec.dynamic_energy_threshold = True
                self.rec.pause_threshold          = 0.75
                self.mic = sr.Microphone()
                with self.mic as src:
                    self.rec.adjust_for_ambient_noise(src, duration=1.5)
                log.info("Mic calibrated")
            except Exception as e:
                log.warning("Mic init: %s", e)
                self.mic = None

    def listen(self, timeout: int = 4, phrase_time: int = 15) -> Optional[str]:
        if not VOICE_AVAILABLE or not self.rec or not self.mic:
            return None
        try:
            with self.mic as src:
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=phrase_time)
            return self.rec.recognize_google(audio).lower().strip()
        except Exception:
            return None

    def route(self, text: str) -> Dict[str, Any]:
        t = text.lower().strip()
        if any(w in t for w in ["what time", "current time"]):
            return {"action": "get_time"}
        if any(w in t for w in ["what date", "today"]):
            return {"action": "get_date"}
        if "screenshot" in t:
            return {"action": "screenshot"}
        if t.startswith("open "):
            target = t[5:].strip()
            # smart routing: known sites go to browser, else open as app
            sites = {"youtube": "https://youtube.com", "gmail": "https://mail.google.com",
                     "google": "https://google.com", "facebook": "https://facebook.com",
                     "instagram": "https://instagram.com", "twitter": "https://twitter.com",
                     "whatsapp": "https://web.whatsapp.com", "linkedin": "https://linkedin.com",
                     "netflix": "https://netflix.com", "amazon": "https://amazon.in",
                     "flipkart": "https://flipkart.com", "github": "https://github.com"}
            for site, url in sites.items():
                if site in target:
                    return {"action": "open_url", "url": url}
            return {"action": "open_app", "app": target}
        if t.startswith("search for ") or t.startswith("google "):
            q = re.sub(r'^(search for|google)\s+', '', t).strip()
            return {"action": "search_web", "query": q}
        if any(w in t for w in ["stop", "emergency stop", "halt"]):
            return {"action": "emergency_stop"}
        if any(w in t for w in ["send email", "write email", "email to"]):
            return {"action": "swarm_task", "task": text}
        return {"action": "swarm_task", "task": text}

    def _voice_loop(self):
        _ok("Voice 3.0 active. Say 'Hey Dacexy' to activate.")
        speak("Dacexy Voice is ready.", priority=True)
        self.running = True
        fails = 0
        while self.running and _agent_running:
            try:
                if self.paused:
                    time.sleep(0.5); continue
                text = self.listen(timeout=4)
                if not text:
                    fails += 1
                    if fails > 30:
                        try:
                            with self.mic as src:
                                self.rec.adjust_for_ambient_noise(src, duration=0.5)
                            fails = 0
                        except Exception:
                            pass
                    continue
                fails = 0
                log.info("Voice heard: %s", text)
                if any(p in text for p in ["stop dacexy", "emergency stop"]):
                    emergency_stop()
                elif any(ww in text for ww in self.WAKE_WORDS):
                    speak("Yes, listening.", priority=True)
                    cmd_text = self.listen(timeout=8, phrase_time=25)
                    if cmd_text:
                        log.info("Voice command: %s", cmd_text)
                        try:
                            self.callback(self.route(cmd_text))
                        except Exception as e:
                            log.warning("Voice callback: %s", e)
                    else:
                        speak("Didn't catch that. Try again.")
            except Exception as e:
                log.debug("Voice loop: %s", e)
                time.sleep(1)

    def start(self):
        if not VOICE_AVAILABLE:
            _warn("Voice disabled - PyAudio/SpeechRecognition not available"); return
        threading.Thread(target=self._voice_loop, daemon=True, name="Voice3").start()

    def stop(self):   self.running = False
    def pause(self):  self.paused  = True
    def resume(self): self.paused  = False

# ============================================================
# BLOCK 25 - MACRO SYSTEM
# ============================================================
_macros: Dict[str, List[Dict]] = {}


def load_macros():
    global _macros
    try:
        if MACRO_FILE.exists():
            _macros = json.loads(MACRO_FILE.read_text())
    except Exception:
        pass


def save_macros():
    try:
        MACRO_FILE.write_text(json.dumps(_macros, indent=2))
    except Exception:
        pass


def create_macro(name: str, steps: List[Dict]):
    _macros[name] = steps; save_macros(); _ok(f"Macro '{name}' saved")


def run_macro(name: str, executor: Callable) -> bool:
    steps = _macros.get(name)
    if not steps:
        _err(f"Macro '{name}' not found"); return False
    for step in steps:
        try:
            executor(step)
        except Exception as e:
            log.warning("Macro step: %s", e)
    return True


def list_macros() -> List[str]:
    return list(_macros.keys())

# ============================================================
# BLOCK 26 - SYSTEM INFO
# ============================================================
def get_system_info() -> Dict[str, Any]:
    if not psutil:
        return {"error": "psutil not available"}
    try:
        cpu  = psutil.cpu_percent(interval=0.3)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net  = psutil.net_io_counters()
        batt = None
        try:
            b = psutil.sensors_battery()
            if b:
                batt = {"percent": b.percent, "plugged": b.power_plugged}
        except Exception:
            pass
        return {"cpu_percent":   cpu,
                "ram_used_gb":   round(ram.used  / 1e9, 2),
                "ram_total_gb":  round(ram.total / 1e9, 2),
                "ram_percent":   ram.percent,
                "disk_used_gb":  round(disk.used  / 1e9, 2),
                "disk_total_gb": round(disk.total / 1e9, 2),
                "disk_percent":  disk.percent,
                "net_sent_mb":   round(net.bytes_sent / 1e6, 2),
                "net_recv_mb":   round(net.bytes_recv / 1e6, 2),
                "battery":       batt,
                "platform":      platform.system(),
                "hostname":      socket.gethostname(),
                "python":        platform.python_version(),
                "uptime_hours":  round((time.time() - psutil.boot_time()) / 3600, 1)}
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# BLOCK 27 - MASTER COMMAND EXECUTOR  (FIXED: all action aliases)
# ============================================================
def execute_command(cmd: dict, token: str = None,
                    browser: EnterpriseBrowserAgent = None,
                    email_mgr: EmailCampaignManager = None,
                    swarm: AgentSwarm = None,
                    scheduler: AutonomousScheduler = None,
                    file_engine: FileEngine = None) -> dict:

    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Invalid command format"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action specified"}

    task_desc = (cmd.get("text", "") or cmd.get("task", "") or cmd.get("url", "") or action)
    if is_blocked(str(task_desc)):
        return {"status": "error", "message": "Command blocked for security"}

    needs_perm, ptype = needs_permission(str(task_desc))
    if needs_perm and not ask_permission(str(task_desc), ptype):
        return {"status": "denied", "message": "Permission denied"}

    audit("CMD", mask_pii(action))
    add_task_history(action[:80])

    fe = file_engine or get_file_engine()
    vi = get_vision()

    try:
        # ── SPEECH & NOTIFY ──────────────────────────────────────
        if action == "speak":
            speak(cmd.get("text", "")); return {"status": "ok"}
        elif action == "notify":
            notify_desktop(cmd.get("title", "Dacexy"), cmd.get("text", "")); return {"status": "ok"}

        # ── OPEN aliases (FIX: handle 'open', 'launch', 'start') ─
        elif action in ("open", "launch", "start"):
            target = (cmd.get("url", "") or cmd.get("app", "") or
                      cmd.get("text", "") or cmd.get("name", "")).strip()
            if not target:
                return {"status": "error", "message": "No target specified"}
            sites = {"youtube": "https://youtube.com", "gmail": "https://mail.google.com",
                     "google": "https://google.com", "facebook": "https://facebook.com",
                     "instagram": "https://instagram.com", "twitter": "https://twitter.com",
                     "whatsapp": "https://web.whatsapp.com", "linkedin": "https://linkedin.com",
                     "netflix": "https://netflix.com", "amazon": "https://amazon.in",
                     "flipkart": "https://flipkart.com", "github": "https://github.com",
                     "chrome": "chrome", "notepad": "notepad.exe", "calculator": "calc.exe",
                     "explorer": "explorer", "cmd": "cmd.exe", "terminal": "cmd.exe"}
            tl = target.lower()
            for name, dest in sites.items():
                if name in tl:
                    if dest.startswith("http"):
                        webbrowser.open(dest)
                        return {"status": "ok", "opened": dest}
                    else:
                        open_app(dest)
                        return {"status": "ok", "opened": dest}
            if target.startswith("http"):
                webbrowser.open(target)
                return {"status": "ok", "opened": target}
            open_app(target)
            return {"status": "ok", "opened": target}

        # ── MOUSE ────────────────────────────────────────────────
        elif action == "click":
            x = int(cmd.get("x", 0) or 0)
            y = int(cmd.get("y", 0) or 0)
            if x == 0 and y == 0:
                log.warning("click called with (0,0) - skipping")
                return {"status": "skipped", "reason": "no coordinates"}
            human_click(x, y, cmd.get("button", "left"))
            return {"status": "ok"}
        elif action == "right_click":
            human_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), "right"); return {"status": "ok"}
        elif action == "double_click":
            human_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), double=True); return {"status": "ok"}
        elif action == "move_mouse":
            human_move(int(cmd.get("x", 0)), int(cmd.get("y", 0))); return {"status": "ok"}
        elif action == "drag":
            human_drag(int(cmd.get("x1", 0)), int(cmd.get("y1", 0)),
                       int(cmd.get("x2", 0)), int(cmd.get("y2", 0))); return {"status": "ok"}
        elif action == "scroll":
            human_scroll(int(cmd.get("x", 960)), int(cmd.get("y", 540)),
                         int(cmd.get("clicks", 3)), cmd.get("direction", "down")); return {"status": "ok"}
        elif action == "get_mouse_pos":
            x, y = pyautogui.position(); return {"status": "ok", "x": x, "y": y}

        # ── KEYBOARD ─────────────────────────────────────────────
        elif action in ("type", "type_text", "write"):
            smart_type(cmd.get("text", ""), cmd.get("clear_first", False),
                       cmd.get("human_speed", False)); return {"status": "ok"}
        elif action == "press":
            press_key(cmd.get("key", "")); return {"status": "ok"}
        elif action == "hotkey":
            keys = cmd.get("keys", [])
            if isinstance(keys, list):
                hotkey(*keys)
            else:
                hotkey(*(keys.split("+")))
            return {"status": "ok"}
        elif action == "copy":
            hotkey("ctrl", "c"); return {"status": "ok", "clipboard": get_clipboard()}
        elif action == "paste":
            hotkey("ctrl", "v"); return {"status": "ok"}
        elif action == "get_clipboard":
            return {"status": "ok", "content": get_clipboard()}
        elif action == "set_clipboard":
            set_clipboard(cmd.get("text", "")); return {"status": "ok"}

        # ── VISION ───────────────────────────────────────────────
        elif action == "screenshot":
            return {"status": "ok", "screenshot": vi.capture()}
        elif action in ("what_on_screen", "describe_screen"):
            desc = (vi.get_ai_description(token) if token else vi.ocr())
            speak(desc); return {"status": "ok", "description": desc}
        elif action == "ocr_screen":
            return {"status": "ok", "text": vi.ocr(cmd.get("region"))}
        elif action == "ocr_fast":
            return {"status": "ok", "text": vi.ocr_fast()}
        elif action == "find_text_on_screen":
            pos = vi.find_text(cmd.get("text", ""))
            if pos:
                return {"status": "ok", "x": pos[0], "y": pos[1]}
            return {"status": "not_found"}
        elif action == "click_text":
            pos = vi.find_text(cmd.get("text", ""))
            if pos:
                human_click(pos[0], pos[1]); return {"status": "ok"}
            return {"status": "not_found"}
        elif action == "wait_for_text":
            found = vi.wait_for_text(cmd.get("text", ""), int(cmd.get("timeout", 30)))
            return {"status": "ok", "found": found}
        elif action == "detect_ui":
            return {"status": "ok", "elements": [asdict(e) for e in vi.detect_ui_elements()]}
        elif action == "detect_popups":
            return {"status": "ok", "popup": vi.detect_popups()}
        elif action == "detect_errors":
            return {"status": "ok", "error": vi.detect_error_dialogs()}
        elif action == "app_state":
            return {"status": "ok", "state": vi.track_application_state()}
        elif action == "start_vision_monitor":
            vi.start_monitoring(float(cmd.get("interval", 2.0))); return {"status": "ok"}

        # ── WINDOW / APP ─────────────────────────────────────────
        elif action == "focus_window":
            return {"status": "ok" if focus_window(cmd.get("title", "")) else "not_found"}
        elif action == "minimize_window":
            hotkey("win", "down"); return {"status": "ok"}
        elif action == "maximize_window":
            hotkey("win", "up"); return {"status": "ok"}
        elif action == "close_window":
            hotkey("alt", "F4"); return {"status": "ok"}
        elif action == "list_windows":
            return {"status": "ok", "windows": get_all_windows()}
        elif action == "get_active_window":
            return {"status": "ok", "title": get_active_window()}
        elif action == "open_app":
            return {"status": "ok" if open_app(cmd.get("app", "")) else "error"}
        elif action == "kill_app":
            return {"status": "ok" if kill_app(cmd.get("name", "")) else "not_found"}
        elif action == "list_apps":
            return {"status": "ok", "apps": [a["name"] for a in list_running_apps()[:30]]}
        elif action in ("open_browser", "open_url"):
            url = cmd.get("url", cmd.get("text", "https://google.com"))
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url); return {"status": "ok"}
        elif action == "open_notepad":
            open_app("notepad.exe"); return {"status": "ok"}
        elif action == "open_calculator":
            open_app("calc.exe"); return {"status": "ok"}
        elif action == "open_file_explorer":
            p = cmd.get("path", "")
            subprocess.Popen(["explorer", p] if p else ["explorer"]); return {"status": "ok"}
        elif action == "open_terminal":
            open_app("cmd.exe"); return {"status": "ok"}

        # ── FILES ────────────────────────────────────────────────
        elif action == "list_files":
            return {"status": "ok", "files": fe.list_files(cmd.get("folder"), cmd.get("pattern", "*"))}
        elif action == "read_file":
            return {"status": "ok", "content": fe.read(cmd.get("path", ""))}
        elif action == "write_file":
            return {"status": "ok" if fe.write(cmd.get("path", ""), cmd.get("content", "")) else "error"}
        elif action == "delete_file":
            return {"status": "ok" if fe.delete(cmd.get("path", ""), cmd.get("safe", True)) else "error"}
        elif action == "copy_file":
            return {"status": "ok" if fe.copy(cmd.get("src", ""), cmd.get("dst", "")) else "error"}
        elif action == "move_file":
            return {"status": "ok" if fe.move(cmd.get("src", ""), cmd.get("dst", "")) else "error"}
        elif action == "create_folder":
            try:
                Path(cmd.get("path", "")).mkdir(parents=True, exist_ok=True)
                return {"status": "ok"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        elif action == "search_files":
            return {"status": "ok", "files": fe.search(
                cmd.get("keyword", ""), cmd.get("folder"), cmd.get("ext"), cmd.get("content_search", False))}
        elif action == "compress_files":
            return {"status": "ok" if fe.compress(cmd.get("paths", []), cmd.get("output", "out.zip")) else "error"}
        elif action == "extract_zip":
            return {"status": "ok" if fe.extract(cmd.get("path", ""), cmd.get("output")) else "error"}
        elif action == "backup_folder":
            dest = fe.backup(cmd.get("folder", ""), cmd.get("label", ""))
            return {"status": "ok", "backup_path": dest}
        elif action == "organize_folder":
            return {"status": "ok", "result": fe.organize_folder(cmd.get("folder", ""))}
        elif action == "get_disk_usage":
            return {"status": "ok", "usage": fe.get_disk_usage()}

        # ── EMAIL ────────────────────────────────────────────────
        elif action == "setup_gmail":
            if email_mgr: email_mgr.setup_gmail(cmd.get("email", ""), cmd.get("app_password", ""))
            return {"status": "ok"}
        elif action == "setup_outlook":
            if email_mgr: email_mgr.setup_outlook(cmd.get("email", ""), cmd.get("password", ""))
            return {"status": "ok"}
        elif action in ("send_email", "email"):
            if email_mgr and email_mgr.smtp_config:
                ok = email_mgr.send_single(cmd.get("to", ""), cmd.get("subject", ""),
                                           cmd.get("body", ""), cmd.get("html", False),
                                           cmd.get("attachment"))
                speak(f"Email {'sent' if ok else 'failed'}.")
                return {"status": "ok" if ok else "error"}
            # fallback: open gmail in browser
            to      = cmd.get("to", "")
            subject = cmd.get("subject", "")
            body    = cmd.get("body", "")
            if to:
                url = f"https://mail.google.com/mail/?view=cm&to={quote(to)}&su={quote(subject)}&body={quote(body)}"
                webbrowser.open(url)
                speak(f"Opening Gmail to send email to {to}")
                return {"status": "ok", "note": "opened in browser"}
            return {"status": "error", "message": "No recipient specified"}
        elif action == "gmail_send":
            # Direct Gmail browser automation
            to      = cmd.get("to", "")
            subject = cmd.get("subject", "No Subject")
            body    = cmd.get("body", "")
            if not to:
                return {"status": "error", "message": "No recipient"}
            if browser and browser.driver:
                ok = browser.compose_gmail(to, subject, body)
                return {"status": "ok" if ok else "error"}
            else:
                # fallback: mailto URL
                url = f"https://mail.google.com/mail/?view=cm&to={quote(to)}&su={quote(subject)}&body={quote(body)}"
                webbrowser.open(url)
                speak(f"Opening Gmail compose to {to}")
                return {"status": "ok", "note": "opened compose in browser"}
        elif action == "create_campaign":
            if email_mgr:
                cid = email_mgr.create_campaign(
                    cmd.get("name", "Campaign"), cmd.get("subject", ""),
                    cmd.get("body", "Hello {name}!"), cmd.get("recipients", []),
                    cmd.get("html", True), float(cmd.get("delay", 1.0)),
                    cmd.get("scheduled_at"), cmd.get("tags", []))
                return {"status": "ok", "campaign_id": cid}
            return {"status": "error"}
        elif action == "send_campaign":
            if email_mgr:
                return {"status": "ok", "result": email_mgr.send_campaign(cmd.get("campaign_id", ""))}
            return {"status": "error"}
        elif action == "bulk_email":
            if email_mgr:
                recips = cmd.get("recipients", [])
                if isinstance(recips, str):
                    recips = [r.strip() for r in recips.split(",") if "@" in r]
                cid = email_mgr.create_campaign("bulk", cmd.get("subject", ""),
                                                cmd.get("body", "Hello {name}!"), recips,
                                                cmd.get("html", True), float(cmd.get("delay", 1.0)))
                return {"status": "ok", "result": email_mgr.send_campaign(cid)}
            return {"status": "error", "message": "Email not configured"}
        elif action == "email_dashboard":
            if email_mgr:
                return {"status": "ok", "dashboard": email_mgr.get_dashboard()}
            return {"status": "error"}

        # ── BROWSER ──────────────────────────────────────────────
        elif action == "browser_start":
            if not browser: browser = EnterpriseBrowserAgent()
            return {"status": "ok" if browser.start(
                cmd.get("browser", "chrome"), cmd.get("headless", False), cmd.get("profile")) else "error"}
        elif action == "browser_go":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start()
            browser.go_to(cmd.get("url", ""))
            return {"status": "ok"}
        elif action == "browser_click":
            if browser and browser.driver:
                return {"status": "ok" if browser.find_and_click(
                    cmd.get("selector", ""), cmd.get("by", "css"), cmd.get("fallbacks")) else "not_found"}
            return {"status": "error", "message": "Browser not started"}
        elif action == "browser_type":
            if browser and browser.driver:
                return {"status": "ok" if browser.find_and_type(
                    cmd.get("selector", ""), cmd.get("text", ""), cmd.get("by", "css")) else "error"}
            return {"status": "error"}
        elif action == "browser_extract":
            if browser and browser.driver:
                return {"status": "ok", "data": browser.extract_data(
                    cmd.get("selector", ""), cmd.get("by", "css"))}
            return {"status": "error"}
        elif action == "browser_js":
            if browser and browser.driver:
                return {"status": "ok", "result": str(browser.execute_js(cmd.get("script", "")))}
            return {"status": "error"}
        elif action == "browser_screenshot":
            if browser and browser.driver:
                return {"status": "ok", "screenshot": browser.screenshot_b64()}
            return {"status": "error"}
        elif action == "google_search":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start()
            return {"status": "ok", "results": browser.google_search(cmd.get("query", ""))}
        elif action == "research":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok", "result": browser.research_topic(
                cmd.get("topic", "") or cmd.get("query", ""), int(cmd.get("max_pages", 3)))}

        # ── SOCIAL MEDIA ─────────────────────────────────────────
        elif action == "whatsapp_bulk":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            contacts = cmd.get("contacts", [])
            if isinstance(contacts, str):
                contacts = [c.strip() for c in contacts.split(",") if c.strip()]
            return {"status": "ok", "result": browser.whatsapp_bulk(
                contacts, cmd.get("message", "Hello!"), float(cmd.get("delay", 3.5)))}
        elif action == "whatsapp_send":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok", "result": browser.whatsapp_bulk(
                [cmd.get("contact", "")], cmd.get("message", "Hello!"), 2.5)}
        elif action == "twitter_post":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.twitter_post(
                cmd.get("username", ""), cmd.get("password", ""),
                cmd.get("text", ""), cmd.get("media")) else "error"}
        elif action == "linkedin_post":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.linkedin_post(
                cmd.get("username", ""), cmd.get("password", ""), cmd.get("text", "")) else "error"}
        elif action == "facebook_post":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.facebook_post(
                cmd.get("username", ""), cmd.get("password", ""),
                cmd.get("text", ""), cmd.get("page_id")) else "error"}
        elif action == "instagram_post":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.instagram_post(
                cmd.get("username", ""), cmd.get("password", ""),
                cmd.get("image_path", ""), cmd.get("caption", "")) else "error"}
        elif action == "youtube_upload":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.youtube_upload(
                cmd.get("video_path", ""), cmd.get("title", ""),
                cmd.get("description", ""), cmd.get("tags", [])) else "error"}
        elif action == "tiktok_post":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            return {"status": "ok" if browser.tiktok_post(
                cmd.get("video_path", ""), cmd.get("caption", "")) else "error"}
        elif action == "post_all_social":
            if not browser: browser = EnterpriseBrowserAgent()
            if not browser.driver: browser.start("chrome")
            text  = cmd.get("text", "")
            creds = cmd.get("credentials", {})
            results = {}
            for p, cred in creds.items():
                if p == "twitter":
                    results["twitter"] = browser.twitter_post(cred["username"], cred["password"], text)
                if p == "linkedin":
                    results["linkedin"] = browser.linkedin_post(cred["username"], cred["password"], text)
                if p == "facebook":
                    results["facebook"] = browser.facebook_post(cred["username"], cred["password"], text)
            return {"status": "ok", "results": results}

        # ── AI SWARM ─────────────────────────────────────────────
        elif action == "swarm_task":
            if swarm:
                def _e(c):
                    return execute_command(c, token, browser, email_mgr, swarm, scheduler, fe)
                return {"status": "ok", "result": swarm.plan_and_execute(cmd.get("task", ""), _e)}
            return {"status": "error", "message": "Swarm not available"}

        # ── MEMORY ───────────────────────────────────────────────
        elif action == "remember":
            get_mem().store(cmd.get("fact", ""), cmd.get("category", "fact"),
                            importance=float(cmd.get("importance", 1.0))); return {"status": "ok"}
        elif action == "get_memory":
            return {"status": "ok", "memory": get_memory_context(cmd.get("query", ""))}
        elif action == "search_memory":
            results = get_mem().search(cmd.get("query", ""), int(cmd.get("top_k", 5)), cmd.get("category"))
            return {"status": "ok", "results": [asdict(e) for e in results]}
        elif action == "remember_preference":
            remember_preference(cmd.get("key", ""), cmd.get("value", "")); return {"status": "ok"}
        elif action == "save_workflow":
            save_workflow(cmd.get("name", ""), cmd.get("steps", [])); return {"status": "ok"}
        elif action == "run_workflow":
            steps = get_workflow(cmd.get("name", ""))
            if steps:
                for s in steps:
                    execute_command(s, token, browser, email_mgr, swarm, scheduler, fe)
                return {"status": "ok"}
            return {"status": "error", "message": "Workflow not found"}
        elif action == "remember_contact":
            remember_contact(cmd.get("name", ""), cmd.get("email", ""), cmd.get("phone", ""))
            return {"status": "ok"}
        elif action == "list_contacts":
            with _memory_lock: contacts = MEMORY["email_contacts"]
            return {"status": "ok", "contacts": contacts[:100]}
        elif action == "list_skills":
            return {"status": "ok", "skills": get_mem().list_skills()}
        elif action == "run_skill":
            skill = get_mem().get_skill(cmd.get("name", ""))
            if skill:
                def _e(c):
                    return execute_command(c, token, browser, email_mgr, swarm, scheduler, fe)
                for step in skill.steps:
                    try: _e(step)
                    except Exception as e: log.warning("Skill step: %s", e)
                return {"status": "ok"}
            return {"status": "error", "message": "Skill not found"}
        elif action == "save_skill":
            sid = get_mem().save_skill(cmd.get("name", ""), cmd.get("steps", []),
                                       cmd.get("description", ""), cmd.get("tags", []))
            return {"status": "ok", "skill_id": sid}

        # ── MACROS ───────────────────────────────────────────────
        elif action == "create_macro":
            create_macro(cmd.get("name", ""), cmd.get("steps", [])); return {"status": "ok"}
        elif action == "run_macro":
            def _e(c):
                return execute_command(c, token, browser, email_mgr, swarm, scheduler, fe)
            return {"status": "ok" if run_macro(cmd.get("name", ""), _e) else "error"}
        elif action == "list_macros":
            return {"status": "ok", "macros": list_macros()}

        # ── SCHEDULER ────────────────────────────────────────────
        elif action == "schedule_job":
            if scheduler:
                jid = scheduler.add_job(cmd.get("name", ""), cmd.get("command", {}),
                                        cmd.get("type", "daily"), cmd.get("time", ""),
                                        cmd.get("days", []), int(cmd.get("repeat_every_minutes", 0)))
                return {"status": "ok", "job_id": jid}
            return {"status": "error"}
        elif action == "list_jobs":
            if scheduler:
                return {"status": "ok", "jobs": scheduler.list_jobs()}
            return {"status": "error"}
        elif action == "remove_job":
            if scheduler: scheduler.remove_job(cmd.get("job_id", ""))
            return {"status": "ok"}

        # ── SYSTEM ───────────────────────────────────────────────
        elif action == "system_info":
            info = get_system_info()
            speak(f"CPU {info.get('cpu_percent','?')}%, RAM {info.get('ram_percent','?')}%")
            return {"status": "ok", "info": info}
        elif action == "check_internet":
            ok = check_internet()
            speak(f"Internet {'connected' if ok else 'not connected'}.")
            return {"status": "ok", "connected": ok}
        elif action == "get_time":
            t = datetime.datetime.now().strftime("%I:%M %p, %A %d %B %Y")
            speak(f"The time is {t}"); return {"status": "ok", "time": t}
        elif action == "get_date":
            d = datetime.date.today().strftime("%A, %B %d, %Y")
            speak(f"Today is {d}"); return {"status": "ok", "date": d}
        elif action == "lock_screen":
            if platform.system() == "Windows": ctypes.windll.user32.LockWorkStation()
            return {"status": "ok"}
        elif action == "run_command":
            raw = cmd.get("command", "")
            if is_blocked(raw):
                return {"status": "error", "message": "Blocked"}
            try:
                r = subprocess.run(raw, shell=True, capture_output=True, text=True, timeout=30)
                return {"status": "ok", "stdout": r.stdout[:2000], "stderr": r.stderr[:500]}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out"}
        elif action == "wait":
            time.sleep(float(cmd.get("seconds", 1))); return {"status": "ok"}
        elif action == "health_check":
            healer = SelfHealingEngine(lambda c: c)
            health = healer.get_health()
            speak(f"CPU {health.get('cpu',0):.0f}%, RAM {health.get('ram',0):.0f}%")
            return {"status": "ok", "health": health}
        elif action == "create_note":
            NOTES_DIR.mkdir(exist_ok=True)
            note = NOTES_DIR / f"note_{int(time.time())}.txt"
            fe.write(str(note), cmd.get("content", ""))
            speak("Note saved."); return {"status": "ok", "path": str(note)}
        elif action == "search_web":
            q = cmd.get("query", "")
            webbrowser.open(f"https://www.google.com/search?q={quote(q)}")
            return {"status": "ok"}
        elif action == "open_url":
            url = cmd.get("url", cmd.get("text", ""))
            if not url.startswith("http"): url = "https://" + url
            webbrowser.open(url); return {"status": "ok"}
        elif action == "emergency_stop":
            emergency_stop(); return {"status": "ok"}
        else:
            # last resort: try to open as URL or app
            if action.startswith("http"):
                webbrowser.open(action); return {"status": "ok"}
            log.warning("Unknown action: %s — attempting as swarm task", action)
            if swarm:
                def _e(c):
                    return execute_command(c, token, browser, email_mgr, swarm, scheduler, fe)
                task_str = cmd.get("task", "") or cmd.get("description", "") or action
                return {"status": "ok", "result": swarm.plan_and_execute(task_str, _e)}
            return {"status": "error", "message": f"Unknown action: {action}"}

    except Exception as e:
        log.error("CMD %s error: %s\n%s", action, e, traceback.format_exc())
        audit("CMD_ERROR", action, str(e)[:200])
        try:
            get_mem().remember_failure(action, str(e)[:100])
        except Exception:
            pass
        return {"status": "error", "message": str(e)}

# ============================================================
# BLOCK 28 - WEBSOCKET
# ============================================================
async def ws_recv_loop(ws, token, browser, email_mgr, swarm, scheduler):
    while _agent_running:
        try:
            raw   = await asyncio.wait_for(ws.recv(), timeout=30)
            msg   = json.loads(raw)
            mtype = msg.get("type", "")
            if mtype == "ping":
                await ws.send(json.dumps({"type": "pong", "version": VERSION}))
            elif mtype in ("command", "task"):
                cmd_data = msg.get("data", msg)
                _task(f"WS cmd: {cmd_data.get('action', cmd_data.get('task', ''))[:60]}")
                loop   = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    _executor,
                    lambda: execute_command(cmd_data, token, browser, email_mgr, swarm, scheduler))
                try:
                    await ws.send(json.dumps({"type": "result", "data": result}))
                except Exception:
                    pass
        except asyncio.TimeoutError:
            try:
                health = get_system_info()
                await ws.send(json.dumps({
                    "type": "heartbeat", "agent": "dacexy", "version": VERSION,
                    "health": health,
                    "features": ["voice3", "vision_super", "browser_enterprise",
                                 "email_enterprise", "whatsapp", "marketing",
                                 "memory_vector", "swarm", "hibernation",
                                 "scheduler", "self_healing", "file_engine",
                                 "social_all", "ocr", "multi_monitor"]}))
            except Exception:
                break
        except Exception as e:
            if "ConnectionClosed" in type(e).__name__:
                log.warning("WS connection closed"); break
            log.error("WS recv error: %s", e)
            await asyncio.sleep(1)


async def ws_connect_loop(token, browser, email_mgr, swarm, scheduler):
    retry_delay  = 2
    max_delay    = 120
    global _ws_connection

    while _agent_running:
        try:
            if websockets is None:
                await asyncio.sleep(30); continue

            if not check_internet():
                _warn("No internet - waiting 15s...")
                await asyncio.sleep(15); continue

            _info("Connecting to Dacexy backend...")

            connect_kwargs = {"ping_interval": 20, "ping_timeout": 15,
                              "max_size": 50 * 1024 * 1024}
            ws_major = int(str(getattr(websockets, "__version__", "0")).split(".")[0])
            if ws_major >= 14:
                connect_kwargs["open_timeout"] = 30
            else:
                connect_kwargs["close_timeout"] = 30

            async with websockets.connect(BACKEND_WS, **connect_kwargs) as ws:
                _ws_connection = ws
                retry_delay    = 2

                await ws.send(json.dumps({
                    "token":    token,
                    "type":     "init",
                    "version":  VERSION,
                    "platform": platform.system(),
                    "machine":  platform.machine(),
                    "hostname": socket.gethostname(),
                    "features": ["voice3", "vision_super", "browser_enterprise",
                                 "email_enterprise", "whatsapp", "marketing",
                                 "memory_vector", "swarm", "hibernation",
                                 "scheduler", "self_healing", "file_engine",
                                 "social_all", "ocr", "multi_monitor"],
                    "memory_context": get_memory_context()[:300]
                }))

                _ok("Connected to Dacexy backend")
                speak("Dacexy is online and ready.", priority=True)
                await ws_recv_loop(ws, token, browser, email_mgr, swarm, scheduler)

        except Exception as e:
            log.warning("WS connect error: %s", e)
        finally:
            _ws_connection = None

        if _agent_running:
            _warn(f"Reconnecting in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)

# ============================================================
# BLOCK 29 - HOTKEYS
# ============================================================
def register_hotkeys(voice: VoiceAssistant3 = None):
    if not KEYBOARD_OK:
        return
    try:
        keyboard.add_hotkey("ctrl+shift+d", lambda: speak("Dacexy running."))
        keyboard.add_hotkey("ctrl+shift+s", lambda: get_vision().capture())
        keyboard.add_hotkey("ctrl+shift+e", emergency_stop)
        keyboard.add_hotkey("ctrl+shift+m", lambda: speak(get_memory_context()[:200]))
        if voice:
            keyboard.add_hotkey("ctrl+shift+v",
                                lambda: voice.pause() if not voice.paused else voice.resume())
        _ok("Hotkeys: Ctrl+Shift+D/S/E/M/V")
    except Exception as e:
        log.warning("Hotkeys: %s", e)

# ============================================================
# BLOCK 30 - INTERACTIVE SHELL
# ============================================================
def print_menu():
    lines = [
        "", "=" * 60,
        "  DACEXY v15.0 ENTERPRISE - COMMAND CENTER",
        "=" * 60,
        "  [EMAIL]    bulk email / setup gmail <email> <pass>",
        "  [WA]       whatsapp bulk",
        "  [SOCIAL]   twitter / linkedin / facebook / instagram",
        "             youtube / tiktok / post all",
        "  [BROWSER]  browser <url> / google <query> / research <topic>",
        "  [VISION]   ocr / detect ui / screenshot",
        "  [DESKTOP]  click <x> <y> / type <text>",
        "  [FILES]    files / read <path> / backup <folder>",
        "  [MEMORY]   memory / skills / remember <fact>",
        "  [AI]       plan <task> / swarm <task>",
        "  [SCHEDULE] jobs",
        "  [SYSTEM]   sysinfo / health",
        "  [STOP]     stop / emergency stop",
        "  [HELP]     help / menu",
        "=" * 60, "",
    ]
    for line in lines:
        try:
            print(line); sys.stdout.flush()
        except Exception:
            pass


def interactive_shell(token, browser, email_mgr, swarm, scheduler):
    print_menu()
    def _exec(c):
        return execute_command(c, token, browser, email_mgr, swarm, scheduler)

    while _agent_running:
        try:
            inp = _get_console_input("  Dacexy> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!"); break
        except Exception as e:
            log.debug("Shell input: %s", e); time.sleep(0.5); continue
        if not inp:
            continue
        il = inp.lower()
        try:
            if il in ("stop", "exit", "quit", "bye"):
                speak("Goodbye!"); break
            elif il in ("help", "menu", "?"):
                print_menu()
            elif il in ("sysinfo", "health", "system info"):
                info = get_system_info()
                _info(f"CPU:{info.get('cpu_percent','?')}%"
                      f" RAM:{info.get('ram_percent','?')}%"
                      f" Disk:{info.get('disk_percent','?')}%")
            elif il == "memory":
                print(f"  Memory:\n{get_memory_context()}")
            elif il == "skills":
                skills = get_mem().list_skills()
                for s in skills:
                    print(f"  [SKILL] {s['name']} - used {s['use_count']}x")
                if not skills:
                    print("  No skills yet. They auto-learn from tasks.")
            elif il.startswith("remember "):
                remember(inp[9:]); speak("Remembered.")
            elif il in ("macros", "list macros"):
                print(f"  Macros: {list_macros() or 'None'}")
            elif il.startswith("run macro "):
                run_macro(inp[10:].strip(), _exec)
            elif il == "jobs":
                if scheduler:
                    for j in scheduler.list_jobs():
                        print(f"  [{j['type']}] {j['name']} @ {j['time']} - {j['run_count']}x")
            elif il.startswith("setup gmail "):
                parts = inp.split()
                if len(parts) >= 4 and email_mgr:
                    email_mgr.setup_gmail(parts[2], parts[3])
            elif il.startswith("bulk email"):
                if email_mgr:
                    emails_raw = _get_console_input("  Recipients (comma): ").strip()
                    subject    = _get_console_input("  Subject: ").strip()
                    body       = _get_console_input("  Body ({name} = name): ").strip()
                    delay_str  = _get_console_input("  Delay seconds [1]: ").strip()
                    delay      = float(delay_str or "1")
                    recips     = [e.strip() for e in emails_raw.split(",") if "@" in e]
                    cid        = email_mgr.create_campaign("cli", subject, body, recips, delay_sec=delay)
                    email_mgr.send_campaign(cid)
                else:
                    _err("Email not configured. Run: setup gmail <email> <app_password>")
            elif il.startswith("whatsapp"):
                cr       = _get_console_input("  Contacts (+phone, comma): ").strip()
                msg_text = _get_console_input("  Message: ").strip()
                contacts = [c.strip() for c in cr.split(",") if c.strip()]
                if not browser.driver: browser.start("chrome")
                browser.whatsapp_bulk(contacts, msg_text)
            elif il.startswith("twitter "):
                username = _get_console_input("  Username: ").strip()
                password = _get_console_input("  Password: ").strip()
                text     = _get_console_input("  Tweet (max 280): ").strip()
                if not browser.driver: browser.start("chrome")
                browser.twitter_post(username, password, text[:280])
            elif il.startswith("linkedin "):
                username = _get_console_input("  Email: ").strip()
                password = _get_console_input("  Password: ").strip()
                text     = _get_console_input("  Post text: ").strip()
                if not browser.driver: browser.start("chrome")
                browser.linkedin_post(username, password, text)
            elif il.startswith("instagram "):
                username = _get_console_input("  Username: ").strip()
                password = _get_console_input("  Password: ").strip()
                img      = _get_console_input("  Image path: ").strip()
                caption  = _get_console_input("  Caption: ").strip()
                if not browser.driver: browser.start("chrome")
                browser.instagram_post(username, password, img, caption)
            elif il.startswith("youtube "):
                video = _get_console_input("  Video path: ").strip()
                title = _get_console_input("  Title: ").strip()
                desc  = _get_console_input("  Description: ").strip()
                if not browser.driver: browser.start("chrome")
                browser.youtube_upload(video, title, desc)
            elif il.startswith("tiktok "):
                video   = _get_console_input("  Video path: ").strip()
                caption = _get_console_input("  Caption: ").strip()
                if not browser.driver: browser.start("chrome")
                browser.tiktok_post(video, caption)
            elif il.startswith("post all"):
                text  = _get_console_input("  Post text: ").strip()
                creds = {}
                for pn in ["twitter", "linkedin", "facebook"]:
                    yn = _get_console_input(f"  Include {pn}? (y/n): ").lower()
                    if yn == "y":
                        creds[pn] = {"username": _get_console_input(f"  {pn} user: ").strip(),
                                     "password": _get_console_input(f"  {pn} pass: ").strip()}
                if not browser.driver: browser.start("chrome")
                for pn, cred in creds.items():
                    if pn == "twitter": browser.twitter_post(cred["username"], cred["password"], text)
                    if pn == "linkedin": browser.linkedin_post(cred["username"], cred["password"], text)
                    if pn == "facebook": browser.facebook_post(cred["username"], cred["password"], text)
            elif il.startswith("browser "):
                url = inp[8:].strip()
                if not browser.driver: browser.start("chrome")
                browser.go_to(url)
            elif il.startswith("google "):
                q = inp[7:].strip()
                if not browser.driver: browser.start("chrome")
                for r in browser.google_search(q)[:5]:
                    print(f"  - {r}")
            elif il.startswith("research "):
                topic = inp[9:].strip()
                if not browser.driver: browser.start("chrome")
                result  = browser.research_topic(topic)
                _info(f"Research: {len(result.get('sources',[]))} sources found")
                for r in result.get("results", [])[:5]:
                    print(f"  - {r}")
            elif il == "screenshot":
                ss    = get_vision().capture()
                fname = Path.home() / f"dacexy_ss_{int(time.time())}.jpg"
                if ss:
                    fname.write_bytes(base64.b64decode(ss))
                    _ok(f"Saved: {fname}")
            elif il == "ocr":
                print(f"  Screen text:\n{get_vision().ocr()[:600]}")
            elif il == "detect ui":
                els = get_vision().detect_ui_elements()
                _info(f"{len(els)} UI elements detected")
            elif il.startswith("click "):
                try:
                    p = inp.split()
                    human_click(int(p[1]), int(p[2]))
                    _ok(f"Clicked ({p[1]},{p[2]})")
                except Exception:
                    _err("Usage: click <x> <y>")
            elif il.startswith("type "):
                smart_type(inp[5:])
            elif il.startswith("open "):
                target = inp[5:].strip()
                _exec({"action": "open", "text": target})
            elif il.startswith("plan "):
                task  = inp[5:]
                steps = swarm.planner.run({"task": task})
                _task(f"Plan ({len(steps)} steps):")
                for s in steps:
                    print(f"  {s.get('step')}. {s.get('description', s.get('action',''))}")
                yn = _get_console_input(f"\n  Execute {len(steps)} steps? (y/n): ").lower()
                if yn == "y":
                    swarm.plan_and_execute(task, _exec)
            elif il.startswith("swarm "):
                swarm.plan_and_execute(inp[6:].strip(), _exec)
            elif il.startswith("backup "):
                dest = get_file_engine().backup(inp[7:].strip())
                _ok(f"Backup: {dest}")
            elif il in ("stop all", "emergency stop", "halt"):
                emergency_stop()
            else:
                try:
                    cmd_json = json.loads(inp)
                    result   = _exec(cmd_json)
                    print(f"  Result: {result}")
                except json.JSONDecodeError:
                    _task(f"Processing: {inp}")
                    swarm.plan_and_execute(inp, _exec)
        except KeyboardInterrupt:
            print("\n  Interrupted. Type 'stop' to exit.")
        except Exception as e:
            log.error("Shell error: %s", e)
            _err(f"Error: {e}")

# ============================================================
# BLOCK 31 - MAIN
# ============================================================
async def main_async(token: str):
    log.info("main_async: initializing all subsystems")

    threading.Thread(target=init_tts, daemon=True, name="TTSInit").start()
    time.sleep(0.2)

    try: get_mem()
    except Exception as e: log.warning("Memory init: %s", e)

    try: load_macros()
    except Exception: pass

    try: get_vision().start_monitoring(interval=2.0)
    except Exception: pass

    try: setup_autostart()
    except Exception: pass

    browser   = EnterpriseBrowserAgent()
    email_mgr = EmailCampaignManager()
    swarm     = AgentSwarm(token, browser, email_mgr)

    def _exec(c):
        return execute_command(c, token, browser, email_mgr, swarm, None)

    scheduler = AutonomousScheduler(_exec)
    healer    = SelfHealingEngine(_exec)

    try: scheduler.start()
    except Exception: pass

    try: healer.start()
    except Exception: pass

    try: register_hotkeys()
    except Exception: pass

    voice = None
    try:
        def voice_cb(cmd: Dict):
            try: _exec(cmd)
            except Exception as ve: log.warning("Voice callback: %s", ve)
        voice = VoiceAssistant3(token, voice_cb)
        voice.start()
        register_hotkeys(voice)
    except Exception as e:
        log.warning("Voice start: %s", e)

    try:
        shell_t = threading.Thread(
            target=interactive_shell,
            args=(token, browser, email_mgr, swarm, scheduler),
            daemon=True, name="Shell")
        shell_t.start()
    except Exception as e:
        log.warning("Shell start: %s", e)

    log.info("Starting WebSocket connection loop...")
    try:
        await ws_connect_loop(token, browser, email_mgr, swarm, scheduler)
    except Exception as e:
        log.error("WS loop crashed: %s", e)
        while _agent_running:
            await asyncio.sleep(5)


def main():
    _banner()
    log.info("Dacexy Agent v%s starting", VERSION)

    token = None
    try:
        token = get_token()
        if token:
            _info("Checking saved session...")
            if not check_token_valid(token):
                _warn("Session expired. Please log in again.")
                clear_token()
                token = None
        if not token:
            token = login_loop()
    except SystemExit:
        print("\n  Goodbye!")
        return
    except Exception as e:
        log.error("Auth flow error: %s", e)
        _err(f"Auth error: {e}")
        try:
            _get_console_input("  Press Enter to try login again... ")
        except Exception:
            pass
        try:
            token = login_loop()
        except SystemExit:
            return
        except Exception:
            return

    log.info("Authenticated successfully")
    _ok(f"Dacexy v{VERSION} ready. Starting all systems...")
    audit("STARTUP", f"v{VERSION}", "OK")

    try:
        asyncio.run(main_async(token))
    except KeyboardInterrupt:
        print("\n\n  Dacexy stopped by user.")
    except Exception as e:
        log.error("Fatal error: %s\n%s", e, traceback.format_exc())
        print(f"\n  Fatal error: {e}")
        print(f"  Check log: {_STARTUP_LOG}")
        try:
            _get_console_input("  Press Enter to exit... ")
        except Exception:
            pass
    finally:
        try: get_mem().save()
        except Exception: pass
        try: save_macros()
        except Exception: pass
        audit("SHUTDOWN", f"v{VERSION}", "CLEAN")
        try: print("  State saved. Goodbye!")
        except Exception: pass


if __name__ == "__main__":
    main()
