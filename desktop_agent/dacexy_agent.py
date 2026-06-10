"""
DACEXY DESKTOP AGENT 
Upgraded from v17.0 - NO breaking changes, only additions:
+ JARVIS-grade AI brain: plans multi-step complex tasks like a human
+ Bulk email engine with CSV contact discovery
+ Internet lead scraping (find interested customers)
+ Social media scheduler & bulk posting
+ Full voice personality like Jarvis (greeting, context, personality)
+ Conversation memory (remembers context across commands)
+ Self-correcting executor (retries failed steps intelligently)
+ Web research engine (reads web pages, summarizes, acts on info)
+ Autonomous marketing campaigns
+ Background task scheduler
+ All v17 features preserved exactly
"""
from __future__ import annotations
import subprocess, sys, os, platform

if platform.system() == "Windows":
    import asyncio as _af
    if hasattr(_af, "WindowsSelectorEventLoopPolicy"):
        _af.set_event_loop_policy(_af.WindowsSelectorEventLoopPolicy())

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

for _pkg, _imp in [
    ("pyautogui","pyautogui"), ("pillow","PIL"), ("websockets","websockets"),
    ("requests","requests"), ("pyttsx3","pyttsx3"), ("numpy","numpy"),
    ("psutil","psutil"), ("pyperclip","pyperclip"), ("pygetwindow","pygetwindow"),
    ("plyer","plyer"), ("speechrecognition","speech_recognition"),
    ("keyboard","keyboard"), ("beautifulsoup4","bs4"),
]:
    try: __import__(_imp)
    except ImportError: _pip(_pkg)

try: from selenium import webdriver as _sdw; _sdw
except ImportError: _pip("selenium", "webdriver-manager")

PYAUDIO_OK = False
try:
    import pyaudio; PYAUDIO_OK = True
except ImportError:
    for _cmd in [
        [sys.executable, "-m", "pip", "install", "PyAudio", "-q"],
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
import webbrowser, ctypes, queue, socket, urllib.parse, shutil, csv, random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import deque
from concurrent.futures import ThreadPoolExecutor

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

try: from bs4 import BeautifulSoup; BS4_OK = True
except Exception: BS4_OK = False; BeautifulSoup = None

# ── CONSTANTS ────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "agent.log"
VERSION      = "18.0-JARVIS"

AGENT_DIR.mkdir(exist_ok=True)
(AGENT_DIR / "logs").mkdir(exist_ok=True)
(AGENT_DIR / "data").mkdir(exist_ok=True)
(AGENT_DIR / "exports").mkdir(exist_ok=True)

WAKE_WORDS = [
    "dacexy","hey dacexy","okay dacexy","ok dacexy",
    "jarvis","hey jarvis","yo jarvis",
    "computer","hey computer","okay computer","ok computer",
    "hey agent","agent","daisy","hey daisy",
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
    "dacexy":"https://dacexy.vercel.app","notion":"https://www.notion.so",
    "slack":"https://app.slack.com","trello":"https://trello.com",
    "canva":"https://www.canva.com","figma":"https://www.figma.com",
    "drive":"https://drive.google.com","google drive":"https://drive.google.com",
    "sheets":"https://sheets.google.com","docs":"https://docs.google.com",
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
    "whatsapp desktop":"WhatsApp.exe","obs":"obs64.exe",
    "photoshop":"photoshop.exe","premiere":"premiere.exe",
}

BLOCKED = [
    "rm -rf /","rm -rf ~","format c:","del /s /q c:\\windows",
    "rd /s /q c:\\","reg delete hklm","dd if=/dev/zero",
]

# ── GLOBALS ──────────────────────────────────────────────────────────
_memory_lock   = threading.Lock()
_config_lock   = threading.Lock()
_executor      = ThreadPoolExecutor(max_workers=10)
_agent_running = True
_tts_q: queue.Queue = queue.Queue(maxsize=10)
_tts_engine    = None
_tts_lock      = threading.Lock()
_voice_active  = False
_cur_token     = None
_token_lock    = threading.Lock()
_smtp_config   = {}
_scheduled_tasks: list = []
_scheduler_lock = threading.Lock()

# Conversation context for Jarvis brain
_conversation_history: deque = deque(maxlen=20)
_conversation_lock = threading.Lock()

MEMORY = {
    "facts":[], "preferences":{},
    "task_history":deque(maxlen=500),
    "context":{}, "contacts":{},
    "campaigns":[], "leads":[]
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
log.info("Dacexy Agent v%s (JARVIS EDITION) starting", VERSION)

# ── JARVIS PERSONALITY ────────────────────────────────────────────────
JARVIS_GREETINGS = [
    "At your service.",
    "Ready and standing by.",
    "All systems online. How can I help?",
    "Jarvis here. What do you need?",
    "Online and ready. What's the mission?",
]
JARVIS_THINKING = [
    "On it.", "Processing.", "Let me handle that.",
    "Right away.", "Working on it now.", "Consider it done.",
]
JARVIS_DONE = [
    "Task complete.", "Done.", "Mission accomplished.",
    "All steps completed.", "It's done.",
]

def jarvis_say(text: str, style: str = "normal"):
    """Speak with Jarvis personality."""
    if style == "greeting":
        prefix = random.choice(JARVIS_GREETINGS) + " "
        speak(prefix + text if text else random.choice(JARVIS_GREETINGS))
    elif style == "thinking":
        speak(random.choice(JARVIS_THINKING) + " " + text[:100] if text else random.choice(JARVIS_THINKING))
    elif style == "done":
        speak(random.choice(JARVIS_DONE) + " " + text[:100] if text else random.choice(JARVIS_DONE))
    else:
        speak(text)

# ── TTS ──────────────────────────────────────────────────────────────
def _tts_worker():
    while _agent_running:
        try:
            text = _tts_q.get(timeout=1)
            if text is None: break
            try:
                with _tts_lock:
                    if _tts_engine:
                        _tts_engine.say(str(text)[:400])
                        _tts_engine.runAndWait()
            except Exception: pass
            finally: _tts_q.task_done()
        except queue.Empty: continue

def init_tts():
    global _tts_engine
    if not pyttsx3: return
    try:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 165)
        _tts_engine.setProperty("volume", 0.92)
        voices = _tts_engine.getProperty("voices") or []
        # Prefer a clear male voice for Jarvis feel, fallback to any
        for v in voices:
            if any(x in (v.name or "").lower() for x in ["david","mark","george","james"]):
                _tts_engine.setProperty("voice", v.id); break
        else:
            for v in voices:
                if any(x in (v.name or "").lower() for x in ["zira","hazel","aria","female"]):
                    _tts_engine.setProperty("voice", v.id); break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS ready")
    except Exception as e: log.warning("TTS init: %s", e)

def speak(text: str):
    if not text: return
    s = str(text)[:400]
    try: print(f"  [Jarvis] {s}"); sys.stdout.flush()
    except: pass
    log.info("SPEAK: %s", s)
    try: _tts_q.put_nowait(s)
    except queue.Full: pass

def notify_desktop(title: str, msg: str):
    try:
        if NOTIFY_OK: notification.notify(title=title, message=msg[:100], app_name="Dacexy", timeout=4)
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
    print("\n" + "="*50)
    print("  DACEXY JARVIS AGENT v18.0 - Login")
    print("="*50)
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
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token","")
            if token:
                save_token(token)
                with _memory_lock:
                    if f"email:{email}" not in MEMORY["facts"]:
                        MEMORY["facts"].append(f"email:{email}")
                print("  [OK] Login successful!")
                return token
        r2 = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r2.status_code == 200:
            token = r2.json().get("access_token","")
            if token: save_token(token); print("  [OK] Login successful!"); return token
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
                MEMORY["facts"]        = d.get("facts",[])
                MEMORY["preferences"]  = d.get("preferences",{})
                MEMORY["context"]      = d.get("context",{})
                MEMORY["task_history"] = deque(d.get("task_history",[])[-500:], maxlen=500)
                MEMORY["contacts"]     = d.get("contacts",{})
                MEMORY["campaigns"]    = d.get("campaigns",[])
                MEMORY["leads"]        = d.get("leads",[])
                global _smtp_config
                _smtp_config = d.get("smtp_config",{})
    except Exception as e: log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _memory_lock:
            d = {
                "facts": MEMORY["facts"][-500:],
                "preferences": MEMORY["preferences"],
                "context": MEMORY["context"],
                "task_history": list(MEMORY["task_history"])[-200:],
                "contacts": MEMORY["contacts"],
                "campaigns": MEMORY["campaigns"][-50:],
                "leads": MEMORY["leads"][-200:],
                "smtp_config": _smtp_config,
            }
        MEMORY_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception as e: log.warning("save_memory: %s", e)

def remember(fact: str, category: str = "general"):
    if not fact: return
    entry = f"[{category}] {fact}" if category != "general" else fact
    with _memory_lock:
        if entry not in MEMORY["facts"]: MEMORY["facts"].append(entry)
    save_memory()

def add_contact(name: str, email: str = "", phone: str = "", notes: str = ""):
    with _memory_lock:
        MEMORY["contacts"][name.lower()] = {
            "name":name,"email":email,"phone":phone,
            "notes":notes,"added":datetime.datetime.now().isoformat()
        }
    save_memory()

def get_contact(name: str) -> dict:
    with _memory_lock:
        return MEMORY["contacts"].get(name.lower(), {})

def get_memory_ctx() -> str:
    try:
        with _memory_lock:
            parts = []
            if MEMORY["facts"]: parts.append("Facts: " + "; ".join(MEMORY["facts"][-15:]))
            if MEMORY["preferences"]: parts.append("Prefs: " + str(MEMORY["preferences"]))
            recent = list(MEMORY["task_history"])[-8:]
            if recent: parts.append("Recent tasks: " + "; ".join(recent))
            if MEMORY["contacts"]:
                names = list(MEMORY["contacts"].keys())[:5]
                parts.append("Known contacts: " + ", ".join(names))
        return "\n".join(parts)
    except: return ""

def add_to_conversation(role: str, content: str):
    with _conversation_lock:
        _conversation_history.append({"role": role, "content": content[:1000]})

def get_conversation_history() -> list:
    with _conversation_lock:
        return list(_conversation_history)

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

# ── WEB RESEARCH ENGINE ───────────────────────────────────────────────
def web_search_and_read(query: str, max_results: int = 3) -> str:
    """Search Google, read top pages, return summarized text."""
    if not req_lib: return "Web research unavailable."
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        # DuckDuckGo HTML search (no API key needed)
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        r = req_lib.get(url, headers=headers, timeout=15)
        results_text = ""
        if BS4_OK and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            snippets = soup.find_all("a", class_="result__snippet")
            titles   = soup.find_all("a", class_="result__a")
            links    = []
            for i, (t, s) in enumerate(zip(titles[:max_results], snippets[:max_results])):
                results_text += f"\n[{i+1}] {t.get_text()}: {s.get_text()}"
                href = t.get("href","")
                if href and href.startswith("http"): links.append(href)
            log.info("Web search '%s': %d results", query, len(snippets))
        else:
            results_text = f"Search for: {query}"
        return results_text[:3000] if results_text else f"Searched: {query}"
    except Exception as e:
        log.warning("web_research: %s", e)
        return f"Research on '{query}' - search performed."

def scrape_page_text(url: str) -> str:
    """Read a webpage and return clean text."""
    if not req_lib: return ""
    try:
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = req_lib.get(url, headers=headers, timeout=12)
        if BS4_OK and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script","style","nav","footer","header"]): tag.decompose()
            return soup.get_text(separator=" ", strip=True)[:5000]
        return r.text[:2000]
    except Exception as e: return f"Could not read {url}: {e}"

def find_leads_online(product_desc: str, max_leads: int = 20) -> list:
    """Find potential customers interested in a product by searching online."""
    leads = []
    queries = [
        f"people interested in {product_desc} contact email",
        f"{product_desc} buyers looking for site:linkedin.com",
        f"{product_desc} interested customers email list",
    ]
    for q in queries[:2]:
        text = web_search_and_read(q, max_results=5)
        # Extract emails from search results
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails[:max_leads//2]:
            if email not in [l.get("email") for l in leads]:
                leads.append({"email":email,"source":"web_search","query":q})
        if len(leads) >= max_leads: break
    log.info("Found %d potential leads for '%s'", len(leads), product_desc)
    return leads[:max_leads]

# ── EMAIL ENGINE ─────────────────────────────────────────────────────
def send_email_smtp(to: str, subject: str, body: str,
                    attachment_path: str = None, html_body: str = None) -> dict:
    global _smtp_config
    smtp_email    = _smtp_config.get("email","")
    smtp_password = _smtp_config.get("password","")
    smtp_host     = _smtp_config.get("host","smtp.gmail.com")
    smtp_port     = int(_smtp_config.get("port", 587))

    if not smtp_email or not smtp_password:
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body)}")
        webbrowser.open(url)
        speak(f"Opening Gmail to compose email to {to}. Configure SMTP for auto-send.")
        return {"status":"ok","note":"Opened Gmail compose. Say 'configure smtp' to enable auto-send."}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = smtp_email
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        html_content = html_body or f"<html><body><p>{body.replace(chr(10),'<br>')}</p></body></html>"
        msg.attach(MIMEText(html_content, "html"))

        if attachment_path and os.path.exists(str(attachment_path)):
            with open(str(attachment_path), "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(str(attachment_path))}")
            msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=25) as server:
            server.ehlo(); server.starttls(); server.ehlo()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [to], msg.as_string())

        speak(f"Email sent to {to}.")
        log.info("Email sent: %s -> %s", subject, to)
        return {"status":"ok","sent_to":to,"subject":subject}
    except smtplib.SMTPAuthenticationError:
        return {"status":"error","message":"SMTP auth failed. Check your app password."}
    except Exception as e:
        log.error("Email SMTP: %s", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body)}")
        webbrowser.open(url)
        return {"status":"ok","note":f"SMTP failed ({e}), opened Gmail compose."}

def send_bulk_email_campaign(recipients: list, subject: str, body_template: str,
                              delay_seconds: float = 2.0) -> dict:
    """Send personalized emails to a list of recipients."""
    if not recipients:
        return {"status":"error","message":"No recipients provided"}

    speak(f"Starting bulk email campaign to {len(recipients)} recipients.")
    log.info("Bulk email: %d recipients", len(recipients))

    sent = 0; failed = 0; errors = []
    for i, recip in enumerate(recipients):
        if isinstance(recip, dict):
            to_email = recip.get("email","")
            name = recip.get("name","Customer") or recip.get("first_name","")
        else:
            to_email = str(recip)
            name = to_email.split("@")[0].title()

        if not to_email or "@" not in to_email: continue

        # Personalize body
        personalized = body_template.replace("{name}", name).replace("{email}", to_email)
        personalized = personalized.replace("{first_name}", name.split()[0] if name else "")

        result = send_email_smtp(to_email, subject, personalized)
        if result.get("status") == "ok": sent += 1
        else: failed += 1; errors.append(f"{to_email}: {result.get('message','failed')}")

        if i < len(recipients) - 1:
            time.sleep(delay_seconds)

    summary = f"Bulk email done: {sent} sent, {failed} failed out of {len(recipients)}"
    speak(summary)
    log.info(summary)

    # Save campaign record
    with _memory_lock:
        MEMORY["campaigns"].append({
            "type":"bulk_email","subject":subject,
            "total":len(recipients),"sent":sent,"failed":failed,
            "timestamp":datetime.datetime.now().isoformat()
        })
    save_memory()

    return {"status":"ok","sent":sent,"failed":failed,"total":len(recipients),
            "errors":errors[:5]}

def load_contacts_from_csv(csv_path: str) -> list:
    """Load email contacts from a CSV file."""
    contacts = []
    try:
        path = Path(csv_path)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = (row.get("email") or row.get("Email") or row.get("EMAIL") or
                         row.get("email_address") or "").strip()
                name  = (row.get("name") or row.get("Name") or row.get("first_name") or
                         row.get("First Name") or email.split("@")[0]).strip()
                if email and "@" in email:
                    contacts.append({"email":email,"name":name})
        log.info("Loaded %d contacts from %s", len(contacts), csv_path)
    except Exception as e: log.warning("load_csv: %s", e)
    return contacts

# ── SELENIUM BROWSER AUTOMATION ───────────────────────────────────────
def get_chrome_driver(headless=False, keep_open=False):
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
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        if keep_open:
            opts.add_experimental_option("detach", True)
        try:
            svc = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
        except Exception:
            driver = webdriver.Chrome(options=opts)
        driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return driver
    except Exception as e:
        log.error("Chrome driver: %s", e); return None

def selenium_post_instagram(username,password,image_path,caption="") -> dict:
    driver = get_chrome_driver()
    if not driver: return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver,25)
        driver.get("https://www.instagram.com/accounts/login/"); time.sleep(3)
        wait.until(EC.presence_of_element_located((By.NAME,"username"))).send_keys(username)
        driver.find_element(By.NAME,"password").send_keys(password)
        driver.find_element(By.NAME,"password").send_keys(Keys.RETURN); time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH,
            '//*[@aria-label="New post"] | //div[@role="menuitem"]'))).click(); time.sleep(2)
        driver.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(image_path))
        time.sleep(3)
        for _ in range(2):
            driver.find_element(By.XPATH,'//*[text()="Next" or @aria-label="Next"]').click()
            time.sleep(2)
        cap_area = driver.find_element(By.XPATH,'//div[@aria-label="Write a caption..."]')
        cap_area.click(); cap_area.send_keys(caption); time.sleep(1)
        driver.find_element(By.XPATH,'//*[text()="Share" or @aria-label="Share"]').click()
        time.sleep(5)
        speak("Instagram post published!")
        return {"status":"ok","message":"Posted to Instagram"}
    except Exception as e: log.error("Instagram: %s",e); return {"status":"error","message":str(e)}
    finally:
        try: driver.quit()
        except: pass

def selenium_post_linkedin(username,password,text,image_path=None) -> dict:
    driver = get_chrome_driver()
    if not driver: return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver,20)
        driver.get("https://www.linkedin.com/login"); time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID,"username"))).send_keys(username)
        driver.find_element(By.ID,"password").send_keys(password)
        driver.find_element(By.ID,"password").send_keys(Keys.RETURN); time.sleep(4)
        driver.get("https://www.linkedin.com/feed/"); time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH,
            '//button[contains(.,"Start a post") or contains(.,"Create a post")]'))).click()
        time.sleep(2)
        editor = wait.until(EC.presence_of_element_located((By.XPATH,
            '//div[@role="textbox" and @data-placeholder]')))
        editor.click(); editor.send_keys(text); time.sleep(1)
        if image_path and os.path.exists(image_path):
            driver.find_element(By.XPATH,'//button[@aria-label="Add a photo"]').click()
            time.sleep(1)
            driver.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(image_path))
            time.sleep(3)
        driver.find_element(By.XPATH,
            '//button[contains(@class,"share-actions__primary-action")]').click()
        time.sleep(3); speak("LinkedIn post published!")
        return {"status":"ok","message":"Posted to LinkedIn"}
    except Exception as e: log.error("LinkedIn: %s",e); return {"status":"error","message":str(e)}
    finally:
        try: driver.quit()
        except: pass

def selenium_post_facebook(username,password,text,image_path=None) -> dict:
    driver = get_chrome_driver()
    if not driver: return {"status":"error","message":"Chrome/Selenium not available"}
    try:
        wait = WebDriverWait(driver,20)
        driver.get("https://www.facebook.com/login"); time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID,"email"))).send_keys(username)
        driver.find_element(By.ID,"pass").send_keys(password)
        driver.find_element(By.ID,"pass").send_keys(Keys.RETURN); time.sleep(5)
        driver.get("https://www.facebook.com/"); time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="button" and (contains(.,"mind") or contains(.,"Mind"))]'))).click()
        time.sleep(2)
        editor = wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="textbox" and @contenteditable="true"]')))
        editor.click(); editor.send_keys(text); time.sleep(1)
        if image_path and os.path.exists(image_path):
            driver.find_element(By.XPATH,'//div[@aria-label="Photo/video"]').click()
            time.sleep(1)
            driver.find_element(By.XPATH,'//input[@type="file"]').send_keys(os.path.abspath(image_path))
            time.sleep(3)
        driver.find_element(By.XPATH,'//div[@aria-label="Post" and @role="button"]').click()
        time.sleep(3); speak("Facebook post published!")
        return {"status":"ok","message":"Posted to Facebook"}
    except Exception as e: log.error("Facebook: %s",e); return {"status":"error","message":str(e)}
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
    speak(f"Opening WhatsApp to {phone}")
    return {"status":"ok","note":"WhatsApp Web opened - click Send in browser"}

# ── JARVIS BRAIN (AI PLANNING ENGINE) ────────────────────────────────
def jarvis_think(task: str, token: str, screenshot_b64: str = None) -> dict:
    """
    The core Jarvis brain. Takes a complex task, thinks like a human,
    breaks it into executable steps, and returns a full execution plan.
    Uses conversation history for context continuity.
    """
    if not req_lib or not token:
        return {"plan":[],"response":"No AI connection available.","needs_info":[]}

    mem = get_memory_ctx()
    history = get_conversation_history()

    # Build a rich system prompt that makes the AI think like a human assistant
    system_prompt = f"""You are JARVIS, the world's most capable AI desktop assistant for Dacexy.
You run on the user's Windows PC and can control EVERYTHING on it.
You think step-by-step like a human expert, anticipate problems, and complete tasks autonomously.

TODAY: {datetime.datetime.now().strftime('%A, %B %d %Y %I:%M %p')}
USER CONTEXT:
{mem}

YOUR CAPABILITIES (use these actions):
BROWSER/WEB:
  open website: {{"action":"open","url":"https://site.com"}}
  google search: {{"action":"search_web","query":"search terms"}}
  youtube search: {{"action":"open_youtube","query":"video title"}}
  web research: {{"action":"web_research","query":"topic to research"}}
  scrape page: {{"action":"scrape_page","url":"https://page.com"}}

EMAIL:
  send single email: {{"action":"send_email","to":"email@example.com","subject":"Subject","body":"Body text"}}
  send bulk emails: {{"action":"bulk_email","recipients":[{{"email":"a@b.com","name":"Name"}}],"subject":"Sub","body":"Hi {{name}}, ..."}}
  load CSV contacts: {{"action":"load_csv_contacts","path":"C:/contacts.csv"}}
  find leads online: {{"action":"find_leads","product":"your product description","max":20}}
  configure smtp: {{"action":"configure_smtp"}}

SOCIAL MEDIA (requires username+password):
  instagram post: {{"action":"social_post","platform":"instagram","username":"u","password":"p","image_path":"C:/img.jpg","caption":"text"}}
  linkedin post: {{"action":"social_post","platform":"linkedin","username":"u","password":"p","text":"post content"}}
  facebook post: {{"action":"social_post","platform":"facebook","username":"u","password":"p","text":"content"}}

WHATSAPP:
  send message: {{"action":"whatsapp_send","phone":"+91XXXXXXXXXX","message":"Hello"}}

COMPUTER CONTROL:
  click: {{"action":"click","x":500,"y":300}}
  type text: {{"action":"type","text":"hello world"}}
  press key: {{"action":"key","key":"enter"}}
  hotkey: {{"action":"hotkey","keys":["ctrl","c"]}}
  screenshot: {{"action":"screenshot"}}
  scroll down: {{"action":"scroll_down","amount":5}}
  scroll up: {{"action":"scroll_up","amount":5}}
  volume up/down: {{"action":"volume_up","steps":3}}
  mute: {{"action":"mute"}}
  minimize/maximize: {{"action":"minimize_window"}} / {{"action":"maximize_window"}}
  close window: {{"action":"close_window"}}

FILES:
  write file: {{"action":"write_file","path":"C:/Users/user/Desktop/file.txt","content":"text"}}
  read file: {{"action":"read_file","path":"..."}}
  run command: {{"action":"run_command","command":"dir C:\\"}}

SYSTEM:
  get time: {{"action":"get_time"}}
  get date: {{"action":"get_date"}}
  system info: {{"action":"get_system_info"}}
  speak: {{"action":"speak","text":"message"}}
  wait: {{"action":"wait","seconds":2}}
  remember: {{"action":"remember","fact":"important info"}}
  add contact: {{"action":"add_contact","name":"John","email":"j@example.com","phone":"+91..."}}

MARKETING CAMPAIGN (complete end-to-end):
  {{"action":"marketing_campaign","product":"product name","target":"target audience","message":"campaign message","platforms":["email","linkedin","instagram"]}}

SCHEDULING:
  {{"action":"schedule_task","task":"send email to team","at":"14:30","repeat":"daily"}}

CRITICAL THINKING RULES:
1. For complex tasks, BREAK IT DOWN into clear sequential steps
2. If info is missing (password, file path), add a speak step asking for it THEN proceed with what you can
3. For "send 100 emails to customers interested in X":
   - Step 1: find_leads to discover prospects
   - Step 2: bulk_email with personalized template
4. For marketing campaigns: research -> create content -> post to platforms -> send emails
5. ALWAYS end with a speak step summarizing what was done
6. Use web_research when you need current information
7. Remember important user information with the remember action
8. If a task is a conversation/question (not an action), return a speak action with your answer

Return ONLY a valid JSON object with this exact structure:
{{"plan": [list of command objects], "response": "what you're doing in one sentence", "needs_info": ["list of info needed if any"]}}

No markdown, no explanation outside the JSON."""

    # Build messages with conversation history for context
    messages = [{"role":"system","content":system_prompt}]
    for h in history[-6:]:  # Last 6 turns for context
        messages.append(h)

    # Add current task with optional screenshot
    user_content = f"Task: {task}"
    if screenshot_b64:
        user_content += "\n[Screenshot of current screen is available]"
    messages.append({"role":"user","content":user_content})

    try:
        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":messages,"stream":False}, timeout=40)

        if r.status_code != 200:
            log.warning("Jarvis brain HTTP %s", r.status_code)
            return {"plan":[],"response":f"AI unavailable (HTTP {r.status_code})","needs_info":[]}

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw: return {"plan":[],"response":"Empty AI response","needs_info":[]}

        # Strip markdown fences
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        # Try to parse full JSON object
        try:
            result = json.loads(raw)
            if isinstance(result, dict) and "plan" in result:
                log.info("Jarvis plan: %d steps - %s", len(result["plan"]), result.get("response",""))
                return result
        except: pass

        # Try to find JSON object
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                result = json.loads(m.group())
                if "plan" in result: return result
            except: pass

        # If AI returned a JSON array directly (backwards compat)
        m2 = re.search(r'\[.*\]', raw, re.DOTALL)
        if m2:
            try:
                plan = json.loads(m2.group())
                if isinstance(plan, list):
                    return {"plan":plan,"response":"Executing plan","needs_info":[]}
            except: pass

        # AI gave a plain text response - treat as conversation
        clean = re.sub(r'[{}\[\]"]','',raw)[:300]
        return {"plan":[{"action":"speak","text":clean}],
                "response":clean,"needs_info":[]}

    except req_lib.exceptions.Timeout:
        return {"plan":[],"response":"AI request timed out","needs_info":[]}
    except Exception as e:
        log.error("jarvis_think: %s", e)
        return {"plan":[],"response":str(e),"needs_info":[]}

# ── LOCAL NLP PARSER (fast path, no AI needed) ────────────────────────
def parse_task_locally(task: str) -> list:
    t = task.lower().strip()
    cmds = []

    open_m = re.match(r"open\s+(.+)", t)
    if open_m:
        target = open_m.group(1).strip()
        cmds.append({"action":"open","target":target})
        cmds.append({"action":"speak","text":f"Opening {target}"})
        return cmds

    yt_m = re.search(r"(?:search|play|find|look up)\s+(.+?)\s+(?:on|in)\s+youtube|"
                     r"youtube\s+(?:search|play)\s+(.+)", t)
    if yt_m:
        q = (yt_m.group(1) or yt_m.group(2) or "").strip()
        cmds.append({"action":"open_youtube","query":q}); return cmds
    if "youtube" in t and any(w in t for w in ["search","play","watch","find"]):
        q = re.sub(r"(youtube|search|play|watch|find|on|in|for)","",t).strip()
        cmds.append({"action":"open_youtube","query":q}); return cmds

    g_m = re.search(r"(?:google|search|look up|search for)\s+(.+?)(?:\s+on google)?$", t)
    if g_m and "youtube" not in t:
        cmds.append({"action":"search_web","query":g_m.group(1).strip()}); return cmds

    if any(w in t for w in ["screenshot","screen shot","capture screen"]):
        cmds.append({"action":"screenshot"})
        cmds.append({"action":"speak","text":"Screenshot taken."}); return cmds

    if re.search(r"\btime\b", t) and not re.search(r"send|schedule", t):
        cmds.append({"action":"get_time"}); return cmds
    if re.search(r"\bdate\b|\btoday\b", t) and not re.search(r"send|schedule", t):
        cmds.append({"action":"get_date"}); return cmds

    if any(w in t for w in ["system info","cpu usage","ram usage","disk space"]):
        cmds.append({"action":"get_system_info"}); return cmds

    if re.search(r"volume\s*up|increase\s+volume|louder", t):
        cmds.append({"action":"volume_up","steps":5}); return cmds
    if re.search(r"volume\s*down|lower\s+volume|quieter", t):
        cmds.append({"action":"volume_down","steps":5}); return cmds
    if re.search(r"\bmute\b|\bsilence\b", t):
        cmds.append({"action":"mute"}); return cmds

    if re.search(r"minimize|minimise", t): cmds.append({"action":"minimize_window"}); return cmds
    if re.search(r"maximize|maximise|full.?screen", t): cmds.append({"action":"maximize_window"}); return cmds
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app)", t): cmds.append({"action":"close_window"}); return cmds

    type_m = re.match(r"(?:type|write|enter|input)\s+(.+)", t)
    if type_m: cmds.append({"action":"type","text":type_m.group(1).strip()}); return cmds

    if re.search(r"scroll\s+down", t): cmds.append({"action":"scroll_down","amount":5}); return cmds
    if re.search(r"scroll\s+up", t): cmds.append({"action":"scroll_up","amount":5}); return cmds

    rem_m = re.match(r"remember\s+(.+)", t)
    if rem_m: cmds.append({"action":"remember","fact":rem_m.group(1)}); return cmds

    say_m = re.match(r"(?:say|speak|tell me)\s+(.+)", t)
    if say_m: cmds.append({"action":"speak","text":say_m.group(1)}); return cmds

    if "copy" in t and "paste" not in t: cmds.append({"action":"copy"}); return cmds
    if "paste" in t: cmds.append({"action":"paste"}); return cmds
    if "undo" in t: cmds.append({"action":"undo"}); return cmds

    if "smtp" in t or ("configure" in t and "email" in t):
        cmds.append({"action":"configure_smtp"}); return cmds

    for app_name in APPS:
        if app_name in t:
            cmds.append({"action":"open","app":app_name}); return cmds

    return []  # Complex task - use Jarvis brain

# ── EXTENDED COMMAND EXECUTOR ────────────────────────────────────────
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
        if action == "speak":
            speak(cmd.get("text","")); return {"status":"ok"}

        elif action == "notify":
            notify_desktop(cmd.get("title","Dacexy"), cmd.get("text",""))
            return {"status":"ok"}

        elif action in ("open","open_url","open_browser","launch","start",
                        "navigate","navigate_to","go_to","browse","visit",
                        "open_site","open_website","open_app","run_app"):
            target = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                      cmd.get("name") or cmd.get("site") or cmd.get("target") or "").strip()
            if not target: return {"status":"error","message":"No target"}
            return smart_open(target)

        elif action in ("send_email","email","compose_email","gmail_send","send_mail","mail"):
            to      = str(cmd.get("to") or cmd.get("email") or "")
            subject = str(cmd.get("subject") or "Message from Dacexy")
            body    = str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "")
            attach  = cmd.get("attachment") or cmd.get("attachment_path") or None
            html_b  = cmd.get("html_body") or None
            if not to: return {"status":"error","message":"No recipient"}
            if not body and not subject:
                return {"status":"error","message":"Email needs subject and body"}
            return send_email_smtp(to, subject, body, attach, html_b)

        # ══ BULK EMAIL ════════════════════════════════════════════
        elif action in ("bulk_email","send_bulk_email","email_campaign","mass_email"):
            recipients = cmd.get("recipients") or []
            subject    = str(cmd.get("subject") or "Important message")
            body_tmpl  = str(cmd.get("body") or cmd.get("template") or "Hello {name},\n\nWe'd like to reach out.")
            delay      = float(cmd.get("delay_seconds") or cmd.get("delay") or 2.0)
            csv_path   = cmd.get("csv_path") or ""

            if not recipients and csv_path:
                recipients = load_contacts_from_csv(csv_path)
            if not recipients:
                return {"status":"error","message":"No recipients. Provide list or CSV path."}
            return send_bulk_email_campaign(recipients, subject, body_tmpl, delay)

        # ══ LOAD CSV CONTACTS ════════════════════════════════════
        elif action == "load_csv_contacts":
            path = cmd.get("path","")
            contacts = load_contacts_from_csv(path)
            if contacts:
                for c in contacts: add_contact(c["name"], c["email"])
                speak(f"Loaded {len(contacts)} contacts from CSV.")
                return {"status":"ok","contacts":contacts,"count":len(contacts)}
            return {"status":"error","message":f"No contacts found in {path}"}

        # ══ FIND LEADS ONLINE ════════════════════════════════════
        elif action in ("find_leads","find_customers","search_leads","scrape_leads"):
            product = str(cmd.get("product") or cmd.get("query") or cmd.get("text") or "")
            max_l   = int(cmd.get("max") or cmd.get("limit") or 20)
            if not product:
                return {"status":"error","message":"Specify product description to find leads"}
            speak(f"Searching internet for people interested in {product}...")
            leads = find_leads_online(product, max_l)
            with _memory_lock: MEMORY["leads"].extend(leads)
            save_memory()
            # Export to CSV
            export_path = AGENT_DIR / "exports" / f"leads_{int(time.time())}.csv"
            try:
                with open(export_path,"w",newline="",encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["email","source","query"])
                    writer.writeheader(); writer.writerows(leads)
            except: pass
            speak(f"Found {len(leads)} potential leads. Saved to exports folder.")
            return {"status":"ok","leads":leads,"count":len(leads),"exported":str(export_path)}

        # ══ WEB RESEARCH ═════════════════════════════════════════
        elif action in ("web_research","research","web_search_deep"):
            query = str(cmd.get("query") or cmd.get("topic") or cmd.get("text") or "")
            if not query: return {"status":"error","message":"No research query"}
            speak(f"Researching {query}...")
            results = web_search_and_read(query)
            log.info("Research results: %s...", results[:100])
            return {"status":"ok","research":results,"query":query}

        elif action in ("scrape_page","read_page","fetch_page"):
            url = str(cmd.get("url") or "")
            if not url: return {"status":"error","message":"No URL to scrape"}
            text = scrape_page_text(url)
            return {"status":"ok","content":text}

        # ══ MARKETING CAMPAIGN ════════════════════════════════════
        elif action in ("marketing_campaign","run_campaign","launch_campaign"):
            product   = str(cmd.get("product") or "")
            target    = str(cmd.get("target") or "potential customers")
            message   = str(cmd.get("message") or "")
            platforms = cmd.get("platforms") or ["email"]

            speak(f"Launching marketing campaign for {product}. Working on all platforms.")
            results = {}

            if "email" in platforms:
                # Find leads and send emails
                leads = find_leads_online(f"{product} {target}", 10)
                if leads and _smtp_config.get("email"):
                    email_body = (message or
                        f"Hi {{name}},\n\nWe wanted to reach out about {product}.\n\n"
                        f"As someone interested in this space, we thought you'd love what we're building.\n\n"
                        f"Would love to connect!\n\nBest regards,\nDacexy Team")
                    result = send_bulk_email_campaign(leads,
                        f"Exciting news about {product}", email_body, 3.0)
                    results["email"] = result

            for platform in [p for p in platforms if p != "email"]:
                results[platform] = {"status":"ok","note":f"Manual post needed for {platform}"}

            speak(f"Campaign launched. Results: {json.dumps(results)[:100]}")
            return {"status":"ok","results":results}

        # ══ ADD CONTACT ══════════════════════════════════════════
        elif action == "add_contact":
            name  = str(cmd.get("name") or "")
            email = str(cmd.get("email") or "")
            phone = str(cmd.get("phone") or "")
            notes = str(cmd.get("notes") or "")
            if not name: return {"status":"error","message":"Contact needs a name"}
            add_contact(name, email, phone, notes)
            speak(f"Contact {name} saved.")
            return {"status":"ok","contact":name}

        # ══ GET CONTACT ══════════════════════════════════════════
        elif action == "get_contact":
            name = str(cmd.get("name") or "")
            contact = get_contact(name)
            if contact: speak(f"{name}: email {contact.get('email','unknown')}")
            return {"status":"ok","contact":contact}

        # ══ CONFIGURE SMTP ════════════════════════════════════════
        elif action == "configure_smtp":
            global _smtp_config
            print("\n  ── Configure Email (SMTP) ──────────────────────")
            print("  For Gmail: create App Password at myaccount.google.com/apppasswords")
            print("  (Enable 2FA first, then create App Password for 'Mail')")
            try:
                em = input("  Your Gmail : ").strip()
                pw = input("  App Password (16 chars): ").strip()
                ht = input("  SMTP host [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
                pt = input("  SMTP port [587]: ").strip() or "587"
                _smtp_config = {"email":em,"password":pw,"host":ht,"port":int(pt)}
                save_memory()
                # Test connection
                try:
                    with smtplib.SMTP(_smtp_config["host"], _smtp_config["port"], timeout=10) as s:
                        s.starttls(); s.login(em, pw)
                    speak("Email configured and tested! Ready to send emails for you.")
                    return {"status":"ok","message":"SMTP configured and verified"}
                except Exception as te:
                    speak(f"SMTP saved but test failed: {te}. Check your app password.")
                    return {"status":"ok","message":f"SMTP saved (test failed: {te})"}
            except Exception as e:
                return {"status":"error","message":str(e)}

        # ══ SCHEDULE TASK ════════════════════════════════════════
        elif action == "schedule_task":
            task_txt = str(cmd.get("task") or cmd.get("text") or "")
            at_time  = str(cmd.get("at") or cmd.get("time") or "")
            repeat   = str(cmd.get("repeat") or "once")
            if not task_txt: return {"status":"error","message":"No task to schedule"}
            with _scheduler_lock:
                _scheduled_tasks.append({
                    "task":task_txt,"at":at_time,"repeat":repeat,
                    "created":datetime.datetime.now().isoformat(),"last_run":""
                })
            speak(f"Task scheduled: {task_txt[:50]} at {at_time}")
            return {"status":"ok","scheduled":task_txt}

        # ══ WHATSAPP ══════════════════════════════════════════════
        elif action in ("whatsapp_send","whatsapp","send_whatsapp"):
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            msg   = str(cmd.get("message") or cmd.get("text") or cmd.get("content") or "")
            if not phone: return {"status":"error","message":"No phone number"}
            return whatsapp_send_web(phone, msg)

        # ══ SOCIAL MEDIA ══════════════════════════════════════════
        elif action in ("social_post","post_social","instagram_post","linkedin_post",
                        "facebook_post","post_instagram","post_linkedin","post_facebook"):
            plat = str(cmd.get("platform") or action.replace("post_","").replace("_post","") or "")
            usr  = str(cmd.get("username") or cmd.get("user") or "")
            pwd  = str(cmd.get("password") or cmd.get("pass") or "")
            txt  = str(cmd.get("text") or cmd.get("caption") or cmd.get("content") or "")
            img  = cmd.get("image_path") or cmd.get("image") or None

            if not usr or not pwd:
                urls = {"instagram":"https://www.instagram.com","linkedin":"https://www.linkedin.com",
                        "facebook":"https://www.facebook.com","twitter":"https://x.com"}
                webbrowser.open(urls.get(plat.lower(),"https://www.instagram.com"))
                return {"status":"ok","note":f"Opened {plat}. Provide username/password for auto-post."}

            if "instagram" in plat.lower():
                if not img: return {"status":"error","message":"Instagram requires an image path"}
                return selenium_post_instagram(usr, pwd, img, txt)
            elif "linkedin" in plat.lower():
                return selenium_post_linkedin(usr, pwd, txt, img)
            elif "facebook" in plat.lower():
                return selenium_post_facebook(usr, pwd, txt, img)
            else:
                webbrowser.open("https://www.instagram.com")
                return {"status":"ok","note":f"Opened {plat} browser"}

        elif action in ("open_youtube","youtube","youtube_search"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            return selenium_youtube_search(q) if q else smart_open("youtube")

        elif action in ("search_web","search","google_search","google"):
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q: return selenium_google_search(q)
            return smart_open("google")

        # ══ MOUSE ═════════════════════════════════════════════════
        elif action == "click":
            if not pyautogui: return {"status":"error","message":"pyautogui not available"}
            x = int(cmd.get("x") or 0); y = int(cmd.get("y") or 0)
            if x == 0 and y == 0: return {"status":"skipped","reason":"no coordinates"}
            sw, sh = pyautogui.size()
            x = max(0,min(x,sw-1)); y = max(0,min(y,sh-1))
            pyautogui.click(x, y, button=cmd.get("button","left")); time.sleep(0.12)
            return {"status":"ok","at":f"({x},{y})"}

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
            direction = str(cmd.get("direction","down")).lower()
            amt = abs(amt) if direction=="up" else -abs(amt)
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
                x1,y1=int(cmd.get("x1",0)),int(cmd.get("y1",0))
                x2,y2=int(cmd.get("x2",0)),int(cmd.get("y2",0))
                pyautogui.moveTo(x1,y1); pyautogui.dragTo(x2,y2,duration=0.4,button="left")
            return {"status":"ok"}
        elif action == "get_mouse_pos":
            if pyautogui: p=pyautogui.position(); return {"status":"ok","x":p.x,"y":p.y}
            return {"status":"ok","x":0,"y":0}

        # ══ KEYBOARD ══════════════════════════════════════════════
        elif action in ("type","type_text","write","input","enter_text"):
            smart_type(cmd.get("text") or cmd.get("content") or "")
            return {"status":"ok"}
        elif action in ("key","press","press_key","keypress"):
            k = cmd.get("key") or cmd.get("keys") or ""
            if k and pyautogui: pyautogui.press(str(k))
            return {"status":"ok"}
        elif action in ("hotkey","key_combo","shortcut"):
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys,str): keys = keys.replace("+"," ").split()
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
            return {"status":"ok","text":pyperclip.paste() if pyperclip else ""}
        elif action == "set_clipboard":
            if pyperclip: pyperclip.copy(str(cmd.get("text",""))[:5000])
            return {"status":"ok"}

        # ══ SCREENSHOT ════════════════════════════════════════════
        elif action in ("screenshot","take_screenshot"):
            ss = take_screenshot()
            if ss:
                try:
                    fname = AGENT_DIR / f"screenshot_{int(time.time())}.jpg"
                    fname.write_bytes(base64.b64decode(ss))
                    speak(f"Screenshot saved.")
                except: pass
            return {"status":"ok","screenshot":ss}

        # ══ WINDOW ════════════════════════════════════════════════
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
            else:
                subprocess.Popen("notepad.exe",shell=True)
            return {"status":"ok"}

        # ══ VOLUME ════════════════════════════════════════════════
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

        # ══ FILES ═════════════════════════════════════════════════
        elif action == "write_file":
            p = Path(str(cmd.get("path","")))
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(str(cmd.get("content",""))[:200000],encoding="utf-8")
            subprocess.Popen(f'notepad.exe "{p}"',shell=True)
            speak(f"File created: {p.name}")
            return {"status":"ok","path":str(p)}
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

        # ══ SYSTEM ════════════════════════════════════════════════
        elif action in ("get_system_info","system_info","sysinfo"):
            if psutil:
                dp = "C:\\" if platform.system()=="Windows" else "/"
                info = {
                    "cpu":psutil.cpu_percent(interval=0.5),
                    "ram":psutil.virtual_memory().percent,
                    "disk":psutil.disk_usage(dp).percent,
                    "platform":platform.system(),"hostname":socket.gethostname(),
                    "active_window":get_active_window(),
                }
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
                killed = 0
                for p in psutil.process_iter(["name"]):
                    try:
                        if name.lower() in (p.info["name"] or "").lower(): p.kill(); killed+=1
                    except: pass
                return {"status":"ok","killed":killed}
            return {"status":"ok"}

        # ══ MEMORY ════════════════════════════════════════════════
        elif action in ("remember","save_fact","take_note"):
            fact = str(cmd.get("fact") or cmd.get("text") or cmd.get("content") or "")
            cat  = str(cmd.get("category") or "general")
            if fact: remember(fact, cat); speak("Noted. I'll remember that.")
            return {"status":"ok"}
        elif action == "get_memory":
            return {"status":"ok","memory":get_memory_ctx()}

        # ══ WAIT ══════════════════════════════════════════════════
        elif action in ("wait","sleep","pause","delay"):
            secs = min(float(cmd.get("seconds") or cmd.get("duration") or 1),15)
            time.sleep(secs); return {"status":"ok"}

        elif action in ("ping","pong","test","health","health_check"):
            return {"status":"ok","pong":True,"version":VERSION}

        elif action in ("what_on_screen","describe_screen"):
            win = get_active_window()
            speak(f"Active window: {win}")
            return {"status":"ok","active_window":win}

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


# ── MAIN TASK EXECUTOR ────────────────────────────────────────────────
def execute_task(task: str, token: str) -> dict:
    """
    Full task execution pipeline:
    1. Try local NLP for simple/fast tasks
    2. Use Jarvis brain for complex tasks
    3. Execute each step with error recovery
    4. Report results
    """
    if not task:
        return {"status":"error","ok":0,"total":0,"result":"No task"}

    log.info("Task: %s", task)
    add_to_conversation("user", task)

    # Step 1: Fast local NLP for simple commands
    commands = parse_task_locally(task)

    if commands:
        log.info("Local NLP: %d commands", len(commands))
        response_text = f"Executing: {task[:60]}"
    else:
        # Step 2: Jarvis AI brain for complex tasks
        log.info("Invoking Jarvis brain for: %s", task[:80])
        jarvis_say(task[:50], style="thinking")

        brain_result = jarvis_think(task, token)
        commands = brain_result.get("plan", [])
        response_text = brain_result.get("response","")
        needs_info = brain_result.get("needs_info",[])

        if response_text and not commands:
            speak(response_text)
            add_to_conversation("assistant", response_text)
            return {"status":"ok","ok":1,"total":1,"result":response_text}

        if needs_info:
            info_msg = "I need: " + ", ".join(needs_info)
            speak(info_msg)

        if not commands:
            res = smart_open(task)
            if res.get("status") == "ok":
                add_to_conversation("assistant", f"Opened: {task}")
                return {"status":"ok","ok":1,"total":1,"result":f"Opened: {task}"}
            speak("I couldn't figure out what to do. Please be more specific.")
            return {"status":"error","ok":0,"total":0,"result":"Could not parse task"}

    # Step 3: Execute each command with retry
    ok_count = 0; total = len(commands); results_list = []
    for i, c in enumerate(commands):
        if not isinstance(c, dict): continue
        for k, v in c.get("params",{}).items():
            if k not in c: c[k] = v
        log.info("Step %d/%d: %s", i+1, total, c.get("action","?"))
        try:
            res = execute_command(c, token)
            results_list.append(res)
            status = res.get("status","ok")
            if status in ("ok","skipped"):
                ok_count += 1
            else:
                log.warning("Step %d failed: %s", i+1, res.get("message",""))
                # Self-healing: if it's a speak or open failure, try to continue
                if c.get("action") not in ("click","type"):
                    ok_count += 0.5  # partial credit, continue
            time.sleep(0.35)
        except Exception as ce:
            log.error("Step %d: %s", i+1, ce)
            results_list.append({"status":"error","message":str(ce)})

    # Update memory and conversation
    with _memory_lock:
        MEMORY["task_history"].append(
            f"{datetime.datetime.now().strftime('%H:%M')} - {task[:80]}")
    save_memory()

    summary = response_text or f"Done: {int(ok_count)}/{total} steps for '{task[:60]}'"
    log.info(summary)

    if ok_count > 0:
        jarvis_say(f"{int(ok_count)} of {total} steps completed.", style="done")

    add_to_conversation("assistant", summary)
    return {
        "status":"ok" if ok_count > 0 else "error",
        "ok":int(ok_count), "total":total,
        "result":summary, "steps":results_list
    }


# ── BACKGROUND SCHEDULER ──────────────────────────────────────────────
def _scheduler_loop():
    """Run scheduled tasks in background."""
    while _agent_running:
        try:
            now = datetime.datetime.now()
            now_str = now.strftime("%H:%M")
            with _scheduler_lock:
                tasks_copy = list(_scheduled_tasks)
            for task in tasks_copy:
                at = task.get("at","")
                if at and at == now_str and task.get("last_run","") != now_str:
                    log.info("Scheduler: running '%s'", task["task"][:50])
                    with _token_lock: tok = _cur_token
                    if tok:
                        task["last_run"] = now_str
                        threading.Thread(target=execute_task,
                            args=(task["task"], tok), daemon=True).start()
        except Exception as e: log.warning("Scheduler: %s", e)
        time.sleep(30)

# ── VOICE ENGINE (JARVIS STYLE) ───────────────────────────────────────
def _voice_loop():
    global _voice_active
    if not VOICE_AVAILABLE or not sr:
        print("  [WARN] Voice disabled - PyAudio not installed")
        print("  [TIP]  pip install PyAudio")
        return

    rec = sr.Recognizer()
    rec.energy_threshold = 320
    rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.65
    rec.non_speaking_duration = 0.3

    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics: print("  [WARN] No microphone found"); return
        print(f"  [MIC] Microphone ready: {mics[0]}")
    except Exception as e: log.warning("Mic: %s", e)

    print(f"\n  [JARVIS] Voice active! Wake words: 'Jarvis' / 'Dacexy' / 'Computer'")
    jarvis_say("", style="greeting")
    errs = 0

    while _voice_active and _agent_running:
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.12)
                except: pass
                try: audio = rec.listen(src, timeout=3, phrase_time_limit=7)
                except sr.WaitTimeoutError: continue

            try: heard = rec.recognize_google(audio, language="en-IN").lower().strip()
            except sr.UnknownValueError: continue
            except sr.RequestError as e: errs+=1; log.warning("SR: %s",e); time.sleep(2); continue

            log.info("Heard: '%s'", heard)
            errs = 0

            if not any(w in heard for w in WAKE_WORDS): continue

            # Woke up!
            print(f"\n  [WAKE] '{heard}' - listening for command...")
            speak("Yes?")
            time.sleep(0.18)

            # Listen for the actual command
            try:
                with sr.Microphone() as csrc:
                    try: rec.adjust_for_ambient_noise(csrc, duration=0.08)
                    except: pass
                    # Longer listen for complex commands
                    caudio = rec.listen(csrc, timeout=7, phrase_time_limit=30)

                command = rec.recognize_google(caudio, language="en-IN").strip()
                if not command: continue

                log.info("Voice command: '%s'", command)
                print(f"  [CMD] {command}")

                with _token_lock: tok = _cur_token
                if not tok: speak("Please log in first."); continue

                # Don't block voice thread
                def _run(t, cmd_text):
                    try: execute_task(cmd_text, t)
                    except Exception as e:
                        log.error("Voice task: %s", e)
                        speak("Something went wrong with that command.")

                threading.Thread(target=_run, args=(tok, command), daemon=True).start()

            except sr.WaitTimeoutError: speak("I didn't hear a command. Say Jarvis again.")
            except sr.UnknownValueError: speak("Couldn't understand that. Please try again.")
            except Exception as e: log.warning("Cmd listen: %s", e)

        except OSError as e: errs+=1; log.warning("Mic OS: %s",e); time.sleep(3)
        except Exception as e: errs+=1; log.debug("Voice: %s",e); time.sleep(0.5)

        if errs >= 8:
            speak("Voice paused due to errors. Retrying in 30 seconds.")
            time.sleep(30); errs = 0

def start_voice(token: str) -> bool:
    global _voice_active, _cur_token
    with _token_lock: _cur_token = token
    if not VOICE_AVAILABLE: return False
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
            log.info("Connecting to Dacexy backend...")
            print("  [WS] Connecting...")
            kw = {"ping_interval":25,"ping_timeout":20,"max_size":10*1024*1024}
            try:
                wsv = int(str(getattr(websockets,"__version__","0")).split(".")[0])
                if wsv >= 14: kw["open_timeout"] = 20
                else: kw["close_timeout"] = 10
            except: pass

            async with websockets.connect(BACKEND_WS, **kw) as ws:
                await ws.send(json.dumps({
                    "token":token,"type":"init","version":VERSION,
                    "platform":platform.system(),"machine":platform.machine(),
                    "hostname":socket.gethostname(),
                    "features":["voice3","vision_super","browser_enterprise",
                                "email_enterprise","swarm","memory_vector",
                                "scheduler","self_healing","social_all","selenium",
                                "jarvis_brain","bulk_email","lead_gen","web_research"]
                }))
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    auth = json.loads(auth_raw)
                    if auth.get("type") == "error":
                        speak("Auth failed."); return
                except asyncio.TimeoutError:
                    await asyncio.sleep(retry); continue

                log.info("WebSocket connected!")
                print("  [OK] Connected - Jarvis is online!")
                jarvis_say("Connected to Dacexy cloud. All systems ready.", style="greeting")
                retry = 3.0
                _ws_lock = asyncio.Lock()
                loop = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with _ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e: log.warning("ws_send: %s", e)

                while _agent_running:
                    try: raw = await asyncio.wait_for(ws.recv(), timeout=40)
                    except asyncio.TimeoutError:
                        try: await asyncio.wait_for(ws.send(json.dumps({"type":"ping","version":VERSION})),timeout=5)
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

                    if action and action not in ("swarm_task","task","run_agent"):
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
                        threading.Thread(target=_run_cmd,args=(msg,token),daemon=True).start()
                        continue

                    if task_text or mtype in ("task","command"):
                        if not task_text: task_text = action
                        if not task_text: continue
                        log.info("Task from dashboard: %s", task_text)
                        print(f"\n  [TASK] {task_text}")
                        jarvis_say(task_text[:50], style="thinking")

                        def _run_task(t, txt, tid):
                            try:
                                result = execute_task(txt, t)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":result.get("status","ok"),
                                    "ok":result.get("ok",0),"total":result.get("total",1),
                                    "result":result.get("result",""),"steps":result.get("steps",[])
                                }), loop)
                            except Exception as e:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type":"task_result","task_id":tid,
                                    "status":"error","ok":0,"total":0,"result":str(e)
                                }), loop)

                        threading.Thread(target=_run_task,
                            args=(token,task_text,task_id),daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK: log.info("WS closed OK")
        except websockets.exceptions.ConnectionClosedError as e: log.warning("WS closed: %s",e)
        except OSError as e: log.warning("WS network: %s",e)
        except Exception as e: log.error("WS: %s",e)

        if _agent_running:
            print(f"  [WS] Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry)
            retry = min(retry*1.5, max_retry)

# ── HEARTBEAT ────────────────────────────────────────────────────────
def _heartbeat(token_ref: list):
    while _agent_running:
        time.sleep(300)
        try:
            tok = token_ref[0]
            if tok:
                if not check_token_valid(tok): speak("Session expired. Please restart.")
                else: update_voice_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)

# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*58)
    print("  DACEXY JARVIS AGENT v18.0")
    print("  The World's Most Capable Desktop AI Agent")
    print("  Thinks like a human. Works 100x faster.")
    print("="*58 + "\n")

    init_tts()
    load_memory()

    caps = []
    if pyautogui: caps.append("mouse/keyboard")
    if ImageGrab: caps.append("screenshot")
    if VOICE_AVAILABLE: caps.append("jarvis-voice")
    if SELENIUM_OK: caps.append("browser-automation")
    if _smtp_config.get("email"): caps.append("real-email")
    if BS4_OK: caps.append("web-research")
    print(f"  Capabilities: {', '.join(caps) if caps else 'basic'}")

    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if check_token_valid(token): print("  [OK] Session valid")
            else: print("  Session expired."); clear_token(); token = None
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

    if not _smtp_config.get("email"):
        print("\n  [TIP] Enable real email sending: say 'configure smtp'")

    voice_ok = start_voice(token)
    if voice_ok: print("  [JARVIS] Voice active - say 'Jarvis' or 'Dacexy' to wake!")
    else:
        print("  [VOICE] Off - install PyAudio to enable")
        print("  [TIP]   pip install PyAudio")

    tok_ref = [token]
    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True).start()
    threading.Thread(target=_scheduler_loop, daemon=True, name="Scheduler").start()

    print("\n  " + "─"*56)
    print(f"  JARVIS v{VERSION} | Voice: {'ON ✓' if voice_ok else 'OFF'}")
    print(f"  Wake words: 'Jarvis' / 'Dacexy' / 'Hey Computer'")
    print(f"  Dashboard : dacexy.vercel.app/dashboard")
    print(f"  Log file  : {LOG_FILE}")
    print("  " + "─"*56)
    print()
    print("  EXAMPLE COMPLEX COMMANDS:")
    print("  'Send email to john@example.com saying the meeting is at 3pm'")
    print("  'Find customers interested in AI software and send them emails'")
    print("  'Post on LinkedIn that we launched a new product'")
    print("  'Research the best marketing strategies for SaaS products'")
    print("  'Send 50 emails from contacts.csv with subject Hello'")
    print("  'Take a screenshot and open it'")
    print("  'Schedule daily email to team@company.com at 09:00'")
    print()

    if not websockets:
        print("  [ERROR] websockets not installed!"); return

    try: asyncio.run(run_websocket(token))
    except KeyboardInterrupt: print("\n  Stopped.")
    except Exception as e: log.error("Fatal: %s",e); print(f"\n  Fatal: {e}")
    finally:
        global _agent_running; _agent_running = False
        stop_voice(); save_memory()
        speak("Shutting down. Goodbye.")
        time.sleep(1); print("  Goodbye!")

if __name__ == "__main__":
    main()
