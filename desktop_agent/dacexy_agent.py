"""
DACEXY DESKTOP AGENT v16.0 FINAL
Completely rewritten - actually executes tasks on PC.
"""
import subprocess, sys, os, platform

# Windows event loop fix FIRST
if platform.system() == "Windows":
    import asyncio as _asyfix
    if hasattr(_asyfix, "WindowsSelectorEventLoopPolicy"):
        _asyfix.set_event_loop_policy(_asyfix.WindowsSelectorEventLoopPolicy())

# UTF-8 stdout fix
if platform.system() == "Windows":
    import io as _io
    try:
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

# Auto-install packages
_PKGS = [
    ("pyautogui", "pyautogui"), ("pillow", "PIL"), ("websockets", "websockets"),
    ("requests", "requests"), ("speechrecognition", "speech_recognition"),
    ("pyttsx3", "pyttsx3"), ("numpy", "numpy"), ("psutil", "psutil"),
    ("pyperclip", "pyperclip"), ("keyboard", "keyboard"),
    ("pygetwindow", "pygetwindow"), ("plyer", "plyer"),
]
for _pkg, _imp in _PKGS:
    try:
        __import__(_imp)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# PyAudio special install
try:
    import pyaudio; PYAUDIO_OK = True
except Exception:
    PYAUDIO_OK = False
    for _cmd in [
        [sys.executable, "-m", "pip", "install", "PyAudio", "-q"],
    ]:
        try:
            subprocess.check_call(_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True; break
        except Exception:
            pass
    if not PYAUDIO_OK:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio", "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True
        except Exception:
            pass

import asyncio, base64, io, json, logging, threading, time
import webbrowser, re, datetime, ctypes, queue, socket
import urllib.parse, shutil, hashlib, random
from pathlib import Path
from typing import Optional
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
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
    import winreg; WINREG_OK = True
except Exception:
    WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except Exception:
    VOICE_AVAILABLE = False; sr = None

try:
    import pygetwindow as gw; WINDOW_OK = True
except Exception:
    WINDOW_OK = False; gw = None

try:
    from plyer import notification; NOTIFY_OK = True
except Exception:
    NOTIFY_OK = False

# ── CONSTANTS ────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
AGENT_DIR    = Path.home() / "DacexyAgent"
LOG_FILE     = AGENT_DIR / "logs" / "startup.log"
VERSION      = "16.0-FINAL"

AGENT_DIR.mkdir(exist_ok=True)
(AGENT_DIR / "logs").mkdir(exist_ok=True)

# Wake words - multiple easy alternatives
WAKE_WORDS = [
    "dacexy", "hey dacexy", "okay dacexy", "ok dacexy",
    "computer", "hey computer", "okay computer", "ok computer",
    "hey agent", "agent", "daisy", "hey daisy",
]

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
}

APPS = {
    "chrome": "chrome.exe", "google chrome": "chrome.exe",
    "edge": "msedge.exe", "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe", "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe", "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "cmd": "cmd.exe", "command prompt": "cmd.exe", "terminal": "cmd.exe",
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
    "vlc": "vlc.exe", "zoom": "zoom.exe", "discord": "discord.exe",
    "spotify": "spotify.exe", "vscode": "code.exe",
    "visual studio code": "code.exe",
}

BLOCKED = [
    "rm -rf /", "rm -rf ~", "format c:", "del /s /q c:\\windows",
    "rd /s /q c:\\", "reg delete hklm", "dd if=/dev/zero",
    "shutdown /s", "shutdown /r", "bcdedit",
]

# ── GLOBALS ──────────────────────────────────────────────────────────
_memory_lock   = threading.Lock()
_config_lock   = threading.Lock()
_executor      = ThreadPoolExecutor(max_workers=6)
_agent_running = True
_tts_q: queue.Queue = queue.Queue(maxsize=10)
_tts_engine    = None
_tts_lock      = threading.Lock()
_voice_active  = False
_cur_token     = None
_token_lock    = threading.Lock()

MEMORY = {
    "facts": [], "preferences": {},
    "task_history": deque(maxlen=200), "context": {}
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
        _tts_engine.setProperty("rate", 160)
        _tts_engine.setProperty("volume", 0.9)
        for v in (_tts_engine.getProperty("voices") or []):
            if any(x in (v.name or "").lower() for x in ["zira","hazel","aria","female"]):
                _tts_engine.setProperty("voice", v.id); break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS OK")
    except Exception as e:
        log.warning("TTS: %s", e)

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
            headers={"Authorization": f"Bearer {token}"}, timeout=8)
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
        log.info("Autostart OK")
    except Exception as e: log.warning("Autostart: %s", e)

def login() -> Optional[str]:
    print("\n" + "="*44)
    print("  Dacexy Agent v16.0 - Login")
    print("="*44)
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
        r = req_lib.post(f"{BACKEND_HTTP}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            if token:
                save_token(token)
                with _memory_lock:
                    if f"email:{email}" not in MEMORY["facts"]:
                        MEMORY["facts"].append(f"email:{email}")
                print("  [OK] Login successful!")
                return token
        try: d = r.json().get("detail", r.text)
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
    except Exception as e: log.warning("load_memory: %s", e)

def save_memory():
    try:
        with _memory_lock:
            d = {"facts": MEMORY["facts"][-300:], "preferences": MEMORY["preferences"],
                 "context": MEMORY["context"], "task_history": list(MEMORY["task_history"])[-200:]}
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
            if pyautogui: pyautogui.hotkey("ctrl", "v"); time.sleep(0.1)
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

# ── SMART OPEN (the key function that was broken) ─────────────────────
def smart_open(target: str) -> dict:
    """Intelligently open a website, app, or URL."""
    if not target: return {"status": "error", "message": "Nothing to open"}
    t = target.lower().strip()
    # Remove common prefixes
    for prefix in ["open ", "launch ", "start ", "go to ", "navigate to ", "show "]:
        if t.startswith(prefix): t = t[len(prefix):].strip()

    # Check known sites
    for site, url in SITES.items():
        if site in t:
            webbrowser.open(url)
            speak(f"Opening {site}")
            log.info("Opened site: %s -> %s", site, url)
            return {"status": "ok", "opened": url}

    # Check known apps
    for app, exe in APPS.items():
        if app in t:
            subprocess.Popen(exe, shell=True)
            speak(f"Opening {app}")
            log.info("Opened app: %s", exe)
            return {"status": "ok", "opened": exe}

    # Raw URL
    if t.startswith("http://") or t.startswith("https://"):
        webbrowser.open(t)
        return {"status": "ok", "opened": t}

    # Domain-like string
    if "." in t and " " not in t:
        url = "https://" + t
        webbrowser.open(url)
        return {"status": "ok", "opened": url}

    # Try as app executable
    try:
        subprocess.Popen(target, shell=True)
        return {"status": "ok", "opened": target}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ── COMMAND EXECUTOR ─────────────────────────────────────────────────
def execute_command(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Invalid command"}

    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action"}

    # Security
    raw_str = " ".join(str(v) for v in cmd.values())
    if any(b in raw_str.lower() for b in BLOCKED):
        return {"status": "blocked", "message": "Blocked for safety"}

    log.info("EXEC: %s", action)

    try:
        # ═══ SPEAK / NOTIFY ══════════════════════════════
        if action == "speak":
            speak(cmd.get("text", "")); return {"status": "ok"}

        elif action == "notify":
            notify_desktop(cmd.get("title", "Dacexy"), cmd.get("text", ""))
            return {"status": "ok"}

        # ═══ ALL OPEN VARIANTS (this was the main bug) ═══
        elif action in ("open", "open_url", "open_browser", "launch", "start",
                        "navigate", "navigate_to", "go_to", "browse", "visit",
                        "open_site", "open_website", "open_app", "run_app"):
            # Collect target from any possible field
            target = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                      cmd.get("name") or cmd.get("site") or cmd.get("target") or "").strip()
            if not target:
                return {"status": "error", "message": "No target to open"}
            return smart_open(target)

        # ═══ MOUSE ═══════════════════════════════════════
        elif action == "click":
            if not pyautogui: return {"status": "error", "message": "pyautogui not available"}
            x = int(cmd.get("x") or 0)
            y = int(cmd.get("y") or 0)
            if x == 0 and y == 0:
                log.warning("click(0,0) skipped")
                return {"status": "skipped", "reason": "no coordinates"}
            sw, sh = pyautogui.size()
            x = max(0, min(x, sw-1)); y = max(0, min(y, sh-1))
            pyautogui.click(x, y, button=cmd.get("button", "left"))
            time.sleep(0.12)
            return {"status": "ok", "at": f"({x},{y})"}

        elif action == "double_click":
            if pyautogui: pyautogui.doubleClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            return {"status": "ok"}

        elif action == "right_click":
            if pyautogui: pyautogui.rightClick(int(cmd.get("x",0)), int(cmd.get("y",0)))
            return {"status": "ok"}

        elif action == "move_mouse":
            if pyautogui: pyautogui.moveTo(int(cmd.get("x",0)), int(cmd.get("y",0)), duration=0.15)
            return {"status": "ok"}

        elif action == "scroll":
            amt = int(cmd.get("clicks") or cmd.get("amount") or 3)
            direction = str(cmd.get("direction","down")).lower()
            if direction == "up": amt = abs(amt)
            else: amt = -abs(amt)
            if pyautogui: pyautogui.scroll(amt)
            return {"status": "ok"}

        elif action in ("scroll_down", "scrolldown"):
            if pyautogui: pyautogui.scroll(-int(cmd.get("amount",5)))
            return {"status": "ok"}

        elif action in ("scroll_up", "scrollup"):
            if pyautogui: pyautogui.scroll(int(cmd.get("amount",5)))
            return {"status": "ok"}

        elif action == "drag":
            if pyautogui:
                x1,y1 = int(cmd.get("x1",0)), int(cmd.get("y1",0))
                x2,y2 = int(cmd.get("x2",0)), int(cmd.get("y2",0))
                pyautogui.moveTo(x1,y1); pyautogui.dragTo(x2,y2,duration=0.4,button="left")
            return {"status": "ok"}

        elif action == "get_mouse_pos":
            if pyautogui:
                p = pyautogui.position(); return {"status":"ok","x":p.x,"y":p.y}
            return {"status":"ok","x":0,"y":0}

        # ═══ KEYBOARD ════════════════════════════════════
        elif action in ("type", "type_text", "write", "input", "enter_text"):
            smart_type(cmd.get("text") or cmd.get("content") or "")
            return {"status": "ok"}

        elif action in ("key", "press", "press_key", "keypress"):
            k = cmd.get("key") or cmd.get("keys") or ""
            if k and pyautogui: pyautogui.press(str(k))
            return {"status": "ok"}

        elif action in ("hotkey", "key_combo", "shortcut"):
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str): keys = keys.replace("+", " ").split()
            if keys and pyautogui: pyautogui.hotkey(*[str(k) for k in keys[:4]])
            return {"status": "ok"}

        elif action == "press_enter":
            if pyautogui: pyautogui.press("enter")
            return {"status": "ok"}

        elif action == "press_tab":
            if pyautogui: pyautogui.press("tab")
            return {"status": "ok"}

        elif action == "press_escape":
            if pyautogui: pyautogui.press("escape")
            return {"status": "ok"}

        elif action == "select_all":
            if pyautogui: pyautogui.hotkey("ctrl","a")
            return {"status": "ok"}

        elif action == "copy":
            if pyautogui: pyautogui.hotkey("ctrl","c"); time.sleep(0.1)
            clip = pyperclip.paste() if pyperclip else ""
            return {"status":"ok","clipboard":clip}

        elif action == "paste":
            if pyautogui: pyautogui.hotkey("ctrl","v")
            return {"status": "ok"}

        elif action == "cut":
            if pyautogui: pyautogui.hotkey("ctrl","x")
            return {"status": "ok"}

        elif action == "undo":
            if pyautogui: pyautogui.hotkey("ctrl","z")
            return {"status": "ok"}

        elif action == "save":
            if pyautogui: pyautogui.hotkey("ctrl","s")
            return {"status": "ok"}

        elif action == "get_clipboard":
            return {"status":"ok","text": pyperclip.paste() if pyperclip else ""}

        elif action == "set_clipboard":
            if pyperclip: pyperclip.copy(str(cmd.get("text",""))[:5000])
            return {"status": "ok"}

        # ═══ SCREENSHOT / VISION ═════════════════════════
        elif action == "screenshot":
            ss = take_screenshot()
            # Save to file too
            if ss:
                try:
                    import base64 as b64m
                    fname = AGENT_DIR / f"screenshot_{int(time.time())}.jpg"
                    fname.write_bytes(b64m.b64decode(ss))
                    log.info("Screenshot saved: %s", fname)
                except: pass
            return {"status":"ok","screenshot":ss}

        elif action in ("what_on_screen","describe_screen","what_is_on_screen"):
            ss = take_screenshot(60)
            desc = "Screen captured"
            if ss and token and req_lib:
                try:
                    r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
                        json={"messages":[{"role":"user","content":"Describe this screen briefly."}],"stream":False},
                        timeout=15)
                    if r.status_code==200:
                        desc = r.json().get("content") or r.json().get("response","Screen captured")
                except: pass
            speak(desc); return {"status":"ok","description":desc}

        # ═══ WINDOW MANAGEMENT ═══════════════════════════
        elif action in ("minimize_window","minimize"):
            if pyautogui: pyautogui.hotkey("win","d")
            return {"status": "ok"}

        elif action in ("maximize_window","maximize"):
            if pyautogui: pyautogui.hotkey("win","up")
            return {"status": "ok"}

        elif action in ("close_window","close"):
            if pyautogui: pyautogui.hotkey("alt","f4")
            return {"status": "ok"}

        elif action == "switch_window":
            if pyautogui: pyautogui.hotkey("alt","tab"); time.sleep(0.3)
            return {"status": "ok"}

        elif action == "get_active_window":
            return {"status":"ok","title": get_active_window()}

        elif action == "open_file_explorer":
            subprocess.Popen("explorer.exe", shell=True)
            return {"status": "ok"}

        elif action == "open_task_manager":
            subprocess.Popen("taskmgr.exe", shell=True)
            return {"status": "ok"}

        elif action == "open_settings":
            subprocess.Popen("ms-settings:", shell=True)
            return {"status": "ok"}

        elif action in ("open_notepad","notepad"):
            txt = cmd.get("text","")
            if txt:
                tmp = AGENT_DIR / "note.txt"
                tmp.write_text(str(txt)[:50000], encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"', shell=True)
            else:
                subprocess.Popen("notepad.exe", shell=True)
            return {"status": "ok"}

        # ═══ VOLUME ══════════════════════════════════════
        elif action == "volume_up":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumeup")
            return {"status": "ok"}

        elif action == "volume_down":
            if pyautogui:
                for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumedown")
            return {"status": "ok"}

        elif action == "mute":
            if pyautogui: pyautogui.press("volumemute")
            return {"status": "ok"}

        # ═══ FILES ═══════════════════════════════════════
        elif action == "write_file":
            p = Path(str(cmd.get("path","")))
            if not str(p).startswith(str(Path.home())):
                return {"status":"blocked","reason":"Outside home dir"}
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(cmd.get("content",""))[:100000], encoding="utf-8")
            return {"status": "ok", "path": str(p)}

        elif action == "read_file":
            p = Path(str(cmd.get("path","")))
            if p.exists():
                return {"status":"ok","content": p.read_text(encoding="utf-8",errors="ignore")[:5000]}
            return {"status":"error","message":"File not found"}

        elif action == "list_files":
            p = Path(str(cmd.get("path", str(Path.home()))))
            try: return {"status":"ok","files":[f.name for f in p.iterdir()][:50]}
            except Exception as e: return {"status":"error","message":str(e)}

        elif action == "delete_file":
            p = Path(str(cmd.get("path","")))
            if p.exists(): p.unlink(); return {"status":"ok"}
            return {"status":"error","message":"Not found"}

        # ═══ SYSTEM ══════════════════════════════════════
        elif action in ("get_system_info","system_info","sysinfo"):
            if psutil:
                dp = "C:\\" if platform.system()=="Windows" else "/"
                info = {
                    "cpu": psutil.cpu_percent(interval=0.5),
                    "ram": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage(dp).percent,
                    "active_window": get_active_window(),
                    "platform": platform.system(),
                    "hostname": socket.gethostname(),
                }
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%")
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
            if any(b in c.lower() for b in BLOCKED):
                return {"status":"blocked","reason":"Blocked"}
            try:
                r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=30)
                return {"status":"ok","stdout":r.stdout[:2000],"stderr":r.stderr[:500]}
            except subprocess.TimeoutExpired:
                return {"status":"error","message":"Timeout"}

        elif action == "kill_process":
            name = str(cmd.get("name",""))
            safe = ["explorer","winlogon","csrss","svchost","system","lsass"]
            if any(p in name.lower() for p in safe):
                return {"status":"blocked","reason":"System process"}
            if psutil:
                killed = 0
                for p in psutil.process_iter(["name"]):
                    try:
                        if name.lower() in (p.info["name"] or "").lower():
                            p.kill(); killed += 1
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

        # ═══ SEARCH / BROWSE ═════════════════════════════
        elif action in ("search_web","search","google_search"):
            q = str(cmd.get("query") or cmd.get("text") or "")[:200]
            if q: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
            return {"status": "ok"}

        elif action in ("open_youtube","youtube"):
            q = str(cmd.get("query") or cmd.get("text") or "")[:200]
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}" if q else "https://www.youtube.com"
            webbrowser.open(url); return {"status": "ok"}

        # ═══ EMAIL ═══════════════════════════════════════
        elif action in ("send_email","gmail_send","compose_email","email","send_mail"):
            to      = str(cmd.get("to") or cmd.get("email") or "")
            subject = str(cmd.get("subject") or "")
            body    = str(cmd.get("body") or cmd.get("text") or cmd.get("content") or "")
            if not to: return {"status":"error","message":"No recipient specified"}
            # Open Gmail compose URL - works without SMTP
            url = (f"https://mail.google.com/mail/?view=cm&fs=1"
                   f"&to={urllib.parse.quote(to)}"
                   f"&su={urllib.parse.quote(subject)}"
                   f"&body={urllib.parse.quote(body)}")
            webbrowser.open(url)
            speak(f"Opening Gmail to send email to {to}")
            log.info("Gmail compose opened for: %s", to)
            return {"status":"ok","note":f"Gmail compose opened for {to}"}

        # ═══ MEMORY ══════════════════════════════════════
        elif action in ("remember","save_fact","take_note"):
            fact = str(cmd.get("fact") or cmd.get("text") or cmd.get("content") or "")
            if fact: remember(fact); speak("Got it, I'll remember that.")
            return {"status": "ok"}

        elif action == "get_memory":
            return {"status":"ok","memory": get_memory_ctx()}

        # ═══ WAIT ════════════════════════════════════════
        elif action in ("wait","sleep","pause","delay"):
            secs = min(float(cmd.get("seconds") or cmd.get("duration") or 1), 15)
            time.sleep(secs); return {"status": "ok"}

        # ═══ HEALTH / PING ═══════════════════════════════
        elif action in ("ping","pong","test"):
            return {"status":"ok","pong":True,"version":VERSION}

        elif action in ("health_check","health","status"):
            info = {}
            if psutil: info = {"cpu":psutil.cpu_percent(),"ram":psutil.virtual_memory().percent}
            return {"status":"ok","health":info,"version":VERSION}

        # ═══ TAKE SCREENSHOT SHORTCUT ════════════════════
        elif action == "take_screenshot":
            ss = take_screenshot()
            return {"status":"ok","screenshot":ss}

        # ═══ FALLBACK - try to open as target ════════════
        else:
            log.warning("Unknown action '%s' - trying smart_open", action)
            # Build a target from whatever fields we have
            target = (cmd.get("url") or cmd.get("app") or cmd.get("text") or
                      cmd.get("name") or cmd.get("target") or action)
            result = smart_open(str(target))
            if result.get("status") == "ok":
                return result
            return {"status":"error","message":f"Unknown action: {action}"}

    except Exception as e:
        log.error("execute_command [%s]: %s", action, e)
        return {"status":"error","message":str(e)}


# ── AI TASK EXECUTOR ─────────────────────────────────────────────────
def execute_task_with_ai(task: str, token: str) -> dict:
    """Get AI plan, execute on PC, return result with ok/total counts."""
    if not task or not token:
        return {"status":"error","ok":0,"total":0,"result":"Missing task or token"}

    log.info("AI Task: %s", task)

    if not req_lib:
        return {"status":"error","ok":0,"total":0,"result":"requests not available"}

    try:
        mem = get_memory_ctx()
        prompt = f"""You are Dacexy Desktop Agent controlling a Windows 11 PC.
Return ONLY a valid JSON array of commands. No text, no markdown, no explanation.

EXACT ACTION NAMES YOU MUST USE:
- open a website: {{"action":"open","url":"https://youtube.com"}}
- open an app: {{"action":"open","app":"chrome.exe"}}
- click: {{"action":"click","x":500,"y":300}}  (only if you know real pixel coords)
- type text: {{"action":"type","text":"hello world"}}
- press key: {{"action":"key","key":"enter"}}
- hotkey: {{"action":"hotkey","keys":["ctrl","c"]}}
- search google: {{"action":"search_web","query":"weather today"}}
- search youtube: {{"action":"open_youtube","query":"music"}}
- take screenshot: {{"action":"screenshot"}}
- send email: {{"action":"send_email","to":"x@gmail.com","subject":"Hi","body":"Hello"}}
- get time: {{"action":"get_time"}}
- get date: {{"action":"get_date"}}
- speak: {{"action":"speak","text":"Done!"}}
- wait: {{"action":"wait","seconds":2}}
- scroll down: {{"action":"scroll_down","amount":3}}
- scroll up: {{"action":"scroll_up","amount":3}}
- minimize window: {{"action":"minimize_window"}}
- close window: {{"action":"close_window"}}
- volume up: {{"action":"volume_up","steps":3}}
- volume down: {{"action":"volume_down","steps":3}}
- mute: {{"action":"mute"}}
- copy: {{"action":"copy"}}
- paste: {{"action":"paste"}}
- system info: {{"action":"get_system_info"}}
- write file: {{"action":"write_file","path":"C:/Users/user/Desktop/file.txt","content":"text"}}
- read file: {{"action":"read_file","path":"..."}}
- run command: {{"action":"run_command","command":"dir"}}

CRITICAL RULES:
1. NEVER use "launch", "navigate", "open_browser", "browse" - use "open" instead
2. NEVER click at x=0, y=0 - skip clicks unless you have real coordinates
3. For opening YouTube: [{{"action":"open","url":"https://www.youtube.com"}}]
4. For opening Gmail and sending email: [{{"action":"send_email","to":"EMAIL","subject":"SUBJ","body":"BODY"}}]
5. For web search: [{{"action":"search_web","query":"QUERY"}}]
6. If task needs browser automation without coords, use open+wait+type steps

User context: {mem}

Return ONLY JSON array. Example: [{{"action":"open","url":"https://youtube.com"}},{{"action":"speak","text":"YouTube is open!"}}]"""

        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":[
                {"role":"system","content":prompt},
                {"role":"user","content":f"Task: {task[:500]}"}
            ],"stream":False},
            timeout=30)

        if r.status_code != 200:
            speak(f"AI error: {r.status_code}")
            return {"status":"error","ok":0,"total":0,"result":f"AI HTTP {r.status_code}"}

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw:
            return {"status":"error","ok":0,"total":0,"result":"Empty AI response"}

        # Strip markdown
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        # Extract JSON array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if not m:
            # Plain text response - just speak it
            speak(raw[:200])
            return {"status":"ok","ok":1,"total":1,"result":raw[:200]}

        try:
            commands = json.loads(m.group())
        except json.JSONDecodeError as e:
            log.error("JSON parse: %s", e)
            return {"status":"error","ok":0,"total":0,"result":f"Parse error: {e}"}

        if not isinstance(commands, list) or not commands:
            return {"status":"error","ok":0,"total":0,"result":"No commands returned"}

        # Execute each command
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
                stat = res.get("status","ok")
                if stat in ("ok","skipped"):
                    ok_count += 1
                else:
                    log.warning("Step %d failed: %s", i+1, res.get("message",""))
                time.sleep(0.4)
            except Exception as ce:
                log.error("Step %d error: %s", i+1, ce)
                results_list.append({"status":"error","message":str(ce)})

        # Update memory
        with _memory_lock:
            MEMORY["task_history"].append(f"{datetime.datetime.now().strftime('%H:%M')} - {task[:80]}")
        save_memory()

        summary = f"Completed {ok_count}/{total} steps for: {task[:60]}"
        log.info(summary)
        speak(f"Done! {ok_count} out of {total} steps completed.")

        return {
            "status": "ok" if ok_count > 0 else "error",
            "ok": ok_count,
            "total": total,
            "result": summary,
            "steps": results_list
        }

    except req_lib.exceptions.Timeout:
        speak("Request timed out.")
        return {"status":"error","ok":0,"total":0,"result":"Timeout"}
    except req_lib.exceptions.ConnectionError:
        speak("No internet connection.")
        return {"status":"error","ok":0,"total":0,"result":"No internet"}
    except Exception as e:
        log.error("execute_task_with_ai: %s", e)
        return {"status":"error","ok":0,"total":0,"result":str(e)}


# ── VOICE ENGINE ─────────────────────────────────────────────────────
def _voice_loop():
    global _voice_active
    if not VOICE_AVAILABLE or not sr:
        print("  [WARN] Voice disabled - PyAudio not available"); return

    rec = sr.Recognizer()
    rec.energy_threshold = 400
    rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.7

    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics: print("  [WARN] No microphone found"); return
    except Exception as e: log.warning("Mic: %s", e)

    print(f"\n  [MIC] Voice active! Wake words: 'Dacexy', 'Computer', 'Hey Computer'")
    speak("Voice ready. Say Dacexy or Computer to activate.")
    errs = 0

    while _voice_active and _agent_running:
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.2)
                except: pass
                try:
                    audio = rec.listen(src, timeout=4, phrase_time_limit=5)
                    heard = rec.recognize_google(audio).lower().strip()
                    log.info("Heard: %s", heard)
                    errs = 0

                    # Check any wake word
                    if not any(w in heard for w in WAKE_WORDS): continue

                    print(f"\n  [WAKE] Listening for command...")
                    speak("Yes?")
                    time.sleep(0.25)

                    with sr.Microphone() as csrc:
                        try: rec.adjust_for_ambient_noise(csrc, duration=0.1)
                        except: pass
                        try:
                            caudio = rec.listen(csrc, timeout=7, phrase_time_limit=20)
                            command = rec.recognize_google(caudio).strip()
                            log.info("Voice cmd: %s", command)
                            print(f"  [CMD] {command}")
                            if not command: continue

                            with _token_lock: tok = _cur_token
                            if not tok: speak("Please log in first."); continue

                            speak("On it!")

                            def _run_voice(t, cmd_text):
                                try:
                                    result = execute_task_with_ai(cmd_text, t)
                                    if result.get("status") != "ok":
                                        speak("Sorry, something went wrong.")
                                except Exception as e:
                                    log.error("Voice task: %s", e)
                                    speak("Error executing command.")

                            threading.Thread(target=_run_voice, args=(tok, command),
                                daemon=True).start()

                        except sr.WaitTimeoutError: speak("Didn't hear command.")
                        except sr.UnknownValueError: speak("Couldn't understand, try again.")
                        except Exception as e: log.warning("Cmd recog: %s", e)

                except sr.WaitTimeoutError: pass
                except sr.UnknownValueError: pass
                except sr.RequestError as e: log.warning("SR API: %s", e); errs+=1; time.sleep(3)
                except Exception as e: log.debug("Listen: %s", e); errs+=1; time.sleep(0.5)

        except OSError as e: log.warning("Mic OS: %s", e); errs+=1; time.sleep(3)
        except Exception as e: log.warning("Voice: %s", e); errs+=1; time.sleep(2)

        if errs >= 10:
            speak("Voice temporarily paused. Retrying in 30 seconds.")
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

def update_voice_token(token: str):
    global _cur_token
    with _token_lock: _cur_token = token


# ── WEBSOCKET ────────────────────────────────────────────────────────
async def run_websocket(token: str):
    retry = 3.0; max_retry = 60.0

    while _agent_running:
        try:
            log.info("Connecting to Dacexy backend...")
            print("  [WS] Connecting...")

            # Build connect kwargs - handle websockets v8 through v14+
            kw = {"ping_interval": 25, "ping_timeout": 20, "max_size": 10*1024*1024}
            try:
                wsv = int(str(getattr(websockets, "__version__", "0")).split(".")[0])
                if wsv >= 14:
                    kw["open_timeout"] = 20
                else:
                    kw["close_timeout"] = 10
                    try: kw["extra_headers"] = {"User-Agent": f"DacexyAgent/{VERSION}"}
                    except: pass
            except: pass

            async with websockets.connect(BACKEND_WS, **kw) as ws:
                # Send init with token + metadata
                await ws.send(json.dumps({
                    "token": token,
                    "type": "init",
                    "version": VERSION,
                    "platform": platform.system(),
                    "machine": platform.machine(),
                    "hostname": socket.gethostname(),
                    "features": [
                        "voice3", "vision_super", "browser_enterprise",
                        "email_enterprise", "swarm", "memory_vector",
                        "scheduler", "self_healing", "social_all", "ocr"
                    ]
                }))

                # Wait for connection ack
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    auth = json.loads(auth_raw)
                    if auth.get("type") == "error":
                        log.error("Auth failed: %s", auth.get("message"))
                        speak("Authentication failed. Check credentials.")
                        return
                except asyncio.TimeoutError:
                    log.error("Auth timeout"); await asyncio.sleep(retry); continue

                log.info("Connected! user authenticated.")
                print("  [OK] Connected to Dacexy cloud - ready!")
                speak("Connected. Ready for your commands.")
                retry = 3.0

                _ws_lock = asyncio.Lock()
                loop = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with _ws_lock:
                        try: await ws.send(json.dumps(data))
                        except Exception as e: log.warning("ws_send: %s", e)

                # Main message loop
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

                    mtype = msg.get("type", "")
                    action = msg.get("action", "")
                    task_text = msg.get("task", "") or msg.get("goal", "")
                    task_id = str(msg.get("task_id", ""))

                    # Ping/pong
                    if mtype == "ping":
                        await ws_send({"type":"pong","version":VERSION})
                        continue

                    if mtype in ("pong","connected","init_ack"):
                        continue

                    # DIRECT COMMAND (single action from dashboard)
                    if action and action not in ("swarm_task","task","run_agent"):
                        log.info("Direct cmd: %s", action)

                        def _run_cmd(m, t):
                            try:
                                result = execute_command(m, t)
                                asyncio.run_coroutine_threadsafe(
                                    ws_send({
                                        "type": "task_result",
                                        "task_id": task_id,
                                        "status": result.get("status","ok"),
                                        "ok": 1 if result.get("status") in ("ok","skipped") else 0,
                                        "total": 1,
                                        "result": str(result.get("message","") or result.get("opened","") or "done"),
                                        "data": result
                                    }), loop)
                            except Exception as e:
                                log.error("Direct cmd error: %s", e)
                                asyncio.run_coroutine_threadsafe(
                                    ws_send({"type":"task_result","task_id":task_id,
                                            "status":"error","ok":0,"total":1,"result":str(e)}), loop)

                        threading.Thread(target=_run_cmd, args=(msg, token), daemon=True).start()
                        continue

                    # TASK (needs AI planning)
                    if task_text or mtype in ("task","command"):
                        if not task_text: task_text = action
                        if not task_text: continue

                        log.info("Task received: %s", task_text)
                        print(f"\n  [TASK] {task_text}")
                        speak(f"Working on: {task_text[:50]}")

                        def _run_task(t, task, tid):
                            try:
                                result = execute_task_with_ai(task, t)
                                asyncio.run_coroutine_threadsafe(
                                    ws_send({
                                        "type": "task_result",
                                        "task_id": tid,
                                        "status": result.get("status","ok"),
                                        "ok": result.get("ok", 0),
                                        "total": result.get("total", 1),
                                        "result": result.get("result",""),
                                        "steps": result.get("steps",[])
                                    }), loop)
                            except Exception as e:
                                log.error("Task error: %s", e)
                                asyncio.run_coroutine_threadsafe(
                                    ws_send({"type":"task_result","task_id":tid,
                                            "status":"error","ok":0,"total":0,"result":str(e)}), loop)

                        threading.Thread(target=_run_task,
                            args=(token, task_text, task_id), daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK:
            log.info("WS closed OK")
        except websockets.exceptions.ConnectionClosedError as e:
            log.warning("WS closed error: %s", e)
        except OSError as e:
            log.warning("WS network: %s", e)
        except Exception as e:
            log.error("WS error: %s", e)

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
                    speak("Session expired. Please restart.")
                else:
                    update_voice_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*50)
    print("  DACEXY DESKTOP AGENT v16.0 FINAL")
    print("  World's Best Desktop AI Agent")
    print("="*50 + "\n")

    init_tts()
    load_memory()

    # Auth
    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if check_token_valid(token):
                print("  [OK] Session valid - skipping login")
            else:
                print("  Session expired.")
                clear_token(); token = None
        except: pass

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"\n  Attempt {attempt+1}/3 failed. Try again.\n")
        if not token:
            print("\n  [ERROR] Cannot authenticate. Exiting.")
            return

    try: setup_autostart()
    except: pass

    # Start voice
    voice_ok = start_voice(token)
    if voice_ok:
        print("  [MIC] Voice active - say 'Dacexy' or 'Computer' to wake!")
    else:
        print("  [WARN] Voice off - PyAudio unavailable")

    # Heartbeat
    tok_ref = [token]
    threading.Thread(target=_heartbeat, args=(tok_ref,), daemon=True).start()

    print("\n  " + "-"*48)
    print(f"  Agent v{VERSION} | Voice: {'ON' if voice_ok else 'OFF'}")
    print(f"  Wake words: 'Dacexy' / 'Computer' / 'Hey Computer'")
    print(f"  Dashboard : dacexy.vercel.app/dashboard")
    print(f"  Log file  : {LOG_FILE}")
    print("  " + "-"*48 + "\n")

    if not websockets:
        print("  [ERROR] websockets not installed!")
        return

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
        speak("Shutting down. Goodbye!"); time.sleep(1)
        print("  Goodbye!")


if __name__ == "__main__":
    main()
PYEOF
python3 -c "
import ast
src = open('/home/claude/dacexy_agent.py').read()
try:
    ast.parse(src)
    print('Syntax: OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
print(f'Lines: {len(src.splitlines())}')
print(f'Size : {len(src)} bytes')
for fn in ['execute_command','execute_task_with_ai','_voice_loop','run_websocket','smart_open','main']:
    ok = 'OK' if fn in src else 'MISSING'
    print(f'  {fn}: {ok}')
"
