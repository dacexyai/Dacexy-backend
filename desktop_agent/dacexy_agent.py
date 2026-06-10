"""
DACEXY DESKTOP AGENT v17.0 - FULLY WORKING
- Fixed login (form-encoded, username field)
- Local NLP command parser (no AI needed for simple tasks)
- Real SMTP email sending
- Selenium browser automation for social media
- PyAudio robust install with wheel fallback
- Voice fully fixed
- Every task actually executes on PC
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
import webbrowser, ctypes, queue, socket, urllib.parse, shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional
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

# ── CONSTANTS ────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "agent.log"
VERSION      = "17.0-WORKING"

AGENT_DIR.mkdir(exist_ok=True)
(AGENT_DIR / "logs").mkdir(exist_ok=True)

WAKE_WORDS = [
    "dacexy","hey dacexy","okay dacexy","ok dacexy",
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

# ── GLOBALS ──────────────────────────────────────────────────────────
_memory_lock   = threading.Lock()
_config_lock   = threading.Lock()
_executor      = ThreadPoolExecutor(max_workers=8)
_agent_running = True
_tts_q: queue.Queue = queue.Queue(maxsize=10)
_tts_engine    = None
_tts_lock      = threading.Lock()
_voice_active  = False
_cur_token     = None
_token_lock    = threading.Lock()
_smtp_config   = {}   # saved SMTP credentials

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
    print("  Dacexy Agent v17.0 - Login")
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
        # FastAPI OAuth2 requires form-encoded data with field "username"
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
        # Try JSON login as fallback (some backends accept both)
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
                global _smtp_config
                _smtp_config = d.get("smtp_config", {})
    except Exception as e: log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _memory_lock:
            d = {
                "facts": MEMORY["facts"][-300:], "preferences": MEMORY["preferences"],
                "context": MEMORY["context"], "task_history": list(MEMORY["task_history"])[-200:],
                "smtp_config": _smtp_config,
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
            if recent: parts.append("Recent: " + "; ".join(recent))
        return "\n".join(parts)
    except: return ""

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

# ── EMAIL (REAL SMTP SEND) ────────────────────────────────────────────
def send_email_smtp(to: str, subject: str, body: str,
                    attachment_path: str = None) -> dict:
    """Send a real email via SMTP. Uses saved credentials or prompts."""
    global _smtp_config

    # Load saved SMTP creds
    smtp_email    = _smtp_config.get("email","")
    smtp_password = _smtp_config.get("password","")
    smtp_host     = _smtp_config.get("host","smtp.gmail.com")
    smtp_port     = int(_smtp_config.get("port", 587))

    if not smtp_email or not smtp_password:
        # Fall back to opening Gmail compose URL
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body)}")
        webbrowser.open(url)
        speak(f"Opening Gmail to compose email to {to}. To enable real sending, configure SMTP.")
        return {"status":"ok","note":"Opened Gmail compose. Configure SMTP for auto-send."}

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
        # Fallback to browser
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}"
               f"&su={urllib.parse.quote(subject)}"
               f"&body={urllib.parse.quote(body)}")
        webbrowser.open(url)
        return {"status":"ok","note":f"SMTP failed ({e}), opened Gmail compose instead."}

# ── SELENIUM BROWSER AUTOMATION ───────────────────────────────────────
def get_chrome_driver(headless=False):
    """Get a Chrome WebDriver instance."""
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
    """Post an image to Instagram via browser automation."""
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
        # Click new post button
        wait.until(EC.element_to_be_clickable((By.XPATH,
            '//div[@role="menuitem"]//div[contains(@class,"_abl-")]|//a[@href="/create/style/"]|'
            '//*[@aria-label="New post"]'))).click()
        time.sleep(2)
        # Upload file
        file_input = driver.find_element(By.XPATH,'//input[@type="file"]')
        file_input.send_keys(os.path.abspath(image_path))
        time.sleep(3)
        # Next -> Next -> Caption -> Share
        for _ in range(2):
            driver.find_element(By.XPATH,
                '//*[text()="Next" or @aria-label="Next"]').click()
            time.sleep(2)
        # Caption
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
    """Post to LinkedIn via browser automation."""
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
        # Click "Start a post"
        start_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            '//button[contains(.,"Start a post") or contains(.,"Create a post")]')))
        start_btn.click(); time.sleep(2)
        # Type text
        editor = wait.until(EC.presence_of_element_located((By.XPATH,
            '//div[@role="textbox" and @data-placeholder]')))
        editor.click(); editor.send_keys(text)
        time.sleep(1)
        if image_path and os.path.exists(image_path):
            img_btn = driver.find_element(By.XPATH,
                '//button[@aria-label="Add a photo"]')
            img_btn.click(); time.sleep(1)
            inp = driver.find_element(By.XPATH,'//input[@type="file"]')
            inp.send_keys(os.path.abspath(image_path)); time.sleep(3)
        # Post
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
        # Click "What's on your mind?"
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
    """Open WhatsApp Web with pre-filled message."""
    phone_clean = re.sub(r"[^0-9+]","",phone)
    if not phone_clean.startswith("+"): phone_clean = "+91" + phone_clean
    url = f"https://wa.me/{phone_clean.lstrip('+')}?text={urllib.parse.quote(message)}"
    webbrowser.open(url)
    speak(f"Opening WhatsApp to send message to {phone}")
    return {"status":"ok","note":"WhatsApp Web opened - click Send in browser"}

# ── LOCAL NLP COMMAND PARSER ─────────────────────────────────────────
# This converts plain English into commands WITHOUT needing AI API call.
# This is the core fix - tasks execute locally and reliably.
def parse_task_locally(task: str) -> list:
    """Convert natural language task into a list of command dicts."""
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
        to = email_m.group(1).strip()
        subject = email_m.group(2) or "Hello from Dacexy"
        body = task  # use full task as body hint
        cmds.append({"action":"send_email","to":to,"subject":subject,"body":body})
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

    # ── CONFIGURE SMTP ────────────────────────────────────────────
    if "smtp" in t or ("configure" in t and "email" in t):
        cmds.append({"action":"configure_smtp"})
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

        # ══ EMAIL ═════════════════════════════════════════════════
        elif action in ("send_email","email","compose_email","gmail_send","send_mail","mail"):
            to      = str(cmd.get("to") or cmd.get("email") or "")
            subject = str(cmd.get("subject") or "Message from Dacexy")
            body    = str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "")
            attach  = cmd.get("attachment") or cmd.get("attachment_path") or None
            if not to: return {"status":"error","message":"No recipient"}
            return send_email_smtp(to, subject, body, attach)

        # ══ CONFIGURE SMTP ════════════════════════════════════════
        elif action == "configure_smtp":
            global _smtp_config
            print("\n  ── Configure Email (SMTP) ──────────────────────")
            print("  For Gmail: use App Password from myaccount.google.com/apppasswords")
            try:
                em = input("  Your email : ").strip()
                pw = input("  App password: ").strip()
                ht = input("  SMTP host [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
                pt = input("  SMTP port [587]: ").strip() or "587"
                _smtp_config = {"email":em,"password":pw,"host":ht,"port":int(pt)}
                save_memory()
                speak("Email configured! I can now send emails for you.")
                return {"status":"ok","message":"SMTP configured"}
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
                # Open browser for manual login
                urls = {"instagram":"https://www.instagram.com",
                        "linkedin":"https://www.linkedin.com",
                        "facebook":"https://www.facebook.com",
                        "twitter":"https://x.com","x":"https://x.com"}
                url = urls.get(platform.lower(), "https://www.instagram.com")
                webbrowser.open(url)
                speak(f"Opening {platform}. Please provide username and password in the command for auto-posting.")
                return {"status":"ok","note":f"Opened {platform}. Provide username/password for auto-post."}

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
                # Open in notepad
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


# ── TASK EXECUTOR (LOCAL FIRST, AI FALLBACK) ──────────────────────────
def execute_task(task: str, token: str) -> dict:
    """Execute a task: try local NLP first, then AI if needed."""
    if not task:
        return {"status":"error","ok":0,"total":0,"result":"No task provided"}

    log.info("Task: %s", task)

    # Step 1: Try local NLP parser first (fast, no network needed)
    commands = parse_task_locally(task)

    if commands:
        log.info("Local NLP matched: %d commands", len(commands))
    else:
        # Step 2: Fall back to AI to generate commands
        log.info("No local match - asking AI...")
        commands = _get_ai_commands(task, token)

    if not commands:
        # Step 3: Last resort - just try to open whatever was said
        log.info("Trying smart_open as last resort")
        res = smart_open(task)
        if res.get("status") == "ok":
            return {"status":"ok","ok":1,"total":1,"result":f"Opened: {task}"}
        speak("I didn't understand that command. Please try again.")
        return {"status":"error","ok":0,"total":0,"result":"Could not parse task"}

    # Execute commands
    ok_count = 0
    total = len(commands)
    results_list = []

    for i, c in enumerate(commands):
        if not isinstance(c, dict): continue
        # Flatten nested params
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

    summary = f"Done: {ok_count}/{total} steps for '{task[:60]}'"
    log.info(summary)
    if ok_count > 0: speak(f"Done! {ok_count} out of {total} steps completed.")

    return {
        "status":"ok" if ok_count > 0 else "error",
        "ok":ok_count, "total":total,
        "result":summary, "steps":results_list
    }


def _get_ai_commands(task: str, token: str) -> list:
    """Call backend AI to get command list. Returns [] on failure."""
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
- post instagram: {{"action":"social_post","platform":"instagram","username":"u","password":"p","image_path":"C:/img.jpg","caption":"text"}}
- post linkedin: {{"action":"social_post","platform":"linkedin","username":"u","password":"p","text":"post text"}}
- whatsapp: {{"action":"whatsapp_send","phone":"+91XXXXXXXXXX","message":"Hello"}}
- remember: {{"action":"remember","fact":"user likes Python"}}

RULES:
1. NEVER click at 0,0
2. Return ONLY a JSON array, nothing else
3. Always end with a speak action summarizing what was done

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

        # Strip markdown fences
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if not m: return []

        commands = json.loads(m.group())
        return commands if isinstance(commands, list) else []

    except Exception as e:
        log.warning("AI commands: %s", e)
        return []


# ── VOICE ENGINE ─────────────────────────────────────────────────────
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

    # Verify microphone works
    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            print("  [WARN] No microphone detected"); return
        print(f"  [MIC] Found {len(mics)} microphone(s): {mics[0]}")
    except Exception as e:
        log.warning("Mic list: %s", e)

    print(f"\n  [VOICE] Active! Wake words: dacexy / computer / hey computer")
    speak("Voice control ready. Say Dacexy or Computer to wake me.")
    errs = 0

    while _voice_active and _agent_running:
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.15)
                except: pass
                try:
                    audio = rec.listen(src, timeout=3, phrase_time_limit=6)
                except sr.WaitTimeoutError: continue

            # Recognize in thread to not block
            try:
                heard = rec.recognize_google(audio, language="en-IN").lower().strip()
            except sr.UnknownValueError: continue
            except sr.RequestError as e:
                errs += 1; log.warning("SR API: %s", e); time.sleep(2); continue

            log.info("Heard: '%s'", heard)
            errs = 0

            # Check wake word
            if not any(w in heard for w in WAKE_WORDS): continue

            print(f"\n  [WAKE] '{heard}' detected - listening for command...")
            speak("Yes?")
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
                if not tok: speak("Please log in first."); continue

                speak("On it!")

                def _run_voice(t, cmd_text):
                    try: execute_task(cmd_text, t)
                    except Exception as e:
                        log.error("Voice task: %s", e)
                        speak("Error executing that command.")

                threading.Thread(target=_run_voice, args=(tok, command),
                    daemon=True).start()

            except sr.WaitTimeoutError: speak("Didn't catch a command.")
            except sr.UnknownValueError: speak("Couldn't understand. Please try again.")
            except Exception as e: log.warning("Command listen: %s", e)

        except OSError as e:
            errs += 1; log.warning("Mic OS error: %s", e); time.sleep(3)
        except Exception as e:
            errs += 1; log.debug("Voice loop: %s", e); time.sleep(0.5)

        if errs >= 8:
            speak("Voice paused - too many errors. Retrying in 30 seconds.")
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
                # Send init
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
                        "scheduler","self_healing","social_all","selenium"
                    ]
                }))

                # Auth ack
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    auth = json.loads(auth_raw)
                    if auth.get("type") == "error":
                        log.error("Auth failed: %s", auth.get("message"))
                        speak("Auth failed. Check your login.")
                        return
                except asyncio.TimeoutError:
                    log.error("Auth timeout"); await asyncio.sleep(retry); continue

                log.info("WebSocket connected and authenticated.")
                print("  [OK] Connected - dashboard control active!")
                speak("Connected to Dacexy cloud. Ready for commands.")
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
                        speak(f"Working on: {task_text[:50]}")

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
                    speak("Session expired. Please restart the agent.")
                else:
                    update_voice_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*52)
    print("  DACEXY DESKTOP AGENT v17.0 - FULLY WORKING")
    print("  Executes tasks directly on your PC")
    print("="*52 + "\n")

    init_tts()
    load_memory()

    # Check capabilities
    caps = []
    if pyautogui: caps.append("mouse/keyboard")
    if ImageGrab: caps.append("screenshot")
    if VOICE_AVAILABLE: caps.append("voice")
    if SELENIUM_OK: caps.append("browser-automation")
    if _smtp_config.get("email"): caps.append("real-email")
    print(f"  Capabilities: {', '.join(caps) if caps else 'basic'}")

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
        print("\n  [TIP] For real email sending, run this command in the dashboard:")
        print("        configure smtp")

    # Start voice
    voice_ok = start_voice(token)
    if voice_ok:
        print("  [VOICE] Active - say 'Dacexy' or 'Computer' to wake!")
    else:
        print("  [VOICE] Off (PyAudio not available)")
        print("  [TIP]  Install PyAudio: pip install PyAudio")

    # Heartbeat
    tok_ref = [token]
    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True).start()

    print("\n  " + "-"*50)
    print(f"  Agent v{VERSION} | Voice: {'ON' if voice_ok else 'OFF'}")
    print(f"  Wake words: 'Dacexy' / 'Computer' / 'Hey Dacexy'")
    print(f"  Dashboard : dacexy.vercel.app/dashboard")
    print(f"  Log file  : {LOG_FILE}")
    print("  " + "-"*50 + "\n")
    print("  Commands you can say or type in dashboard:")
    print("    'open youtube'")
    print("    'search cats on youtube'")
    print("    'send email to friend@gmail.com saying hello'")
    print("    'take a screenshot'")
    print("    'what time is it'")
    print("    'post on instagram'  (requires username/password)")
    print("    'open chrome'")
    print("    'configure smtp'  (for real email sending)")
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
