"""
DACEXY DESKTOP AGENT v16.0
World's best desktop AI agent - actually works.
"""
import subprocess, sys, os, platform

# ── AUTO-INSTALL ─────────────────────────────────────────────────────
PACKAGES = [
    "pyautogui", "pillow", "websockets", "requests",
    "speechrecognition", "pyttsx3", "numpy", "psutil",
    "pyperclip", "keyboard", "pygetwindow", "plyer",
]
for pkg in PACKAGES:
    imp = {"speechrecognition": "speech_recognition", "pillow": "PIL"}.get(pkg, pkg.replace("-","_"))
    try:
        __import__(imp)
    except ImportError:
        try:
            subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except Exception:
            pass

try:
    import pyaudio; PYAUDIO_OK = True
except Exception:
    PYAUDIO_OK = False
    try:
        subprocess.check_call([sys.executable,"-m","pip","install","PyAudio","-q"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        import pyaudio; PYAUDIO_OK = True
    except Exception:
        try:
            subprocess.check_call([sys.executable,"-m","pip","install","pipwin","-q"],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.check_call([sys.executable,"-m","pipwin","install","pyaudio","-q"],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            import pyaudio; PYAUDIO_OK = True
        except Exception:
            PYAUDIO_OK = False

# ── WINDOWS EVENT LOOP FIX ────────────────────────────────────────────
if platform.system() == "Windows":
    import asyncio as _a
    if hasattr(_a, "WindowsSelectorEventLoopPolicy"):
        _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())

# ── STDOUT UTF-8 FIX ──────────────────────────────────────────────────
if platform.system() == "Windows":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

# ── IMPORTS ───────────────────────────────────────────────────────────
import asyncio, base64, io, json, logging, threading, time
import webbrowser, re, datetime, ctypes, queue, smtplib
import urllib.parse, shutil, zipfile, hashlib, random, gc
from pathlib import Path
from typing import Optional
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pyautogui
import requests as req_lib
import websockets
from PIL import ImageGrab, Image
import pyttsx3
import pyperclip
import psutil

try: import winreg; WINREG_OK = True
except: WINREG_OK = False

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = PYAUDIO_OK
except:
    VOICE_AVAILABLE = False; sr = None

try: import pygetwindow as gw; WINDOW_OK = True
except: WINDOW_OK = False; gw = None

try: from plyer import notification; NOTIFY_OK = True
except: NOTIFY_OK = False

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# ── CONSTANTS ─────────────────────────────────────────────────────────
BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"
MEMORY_FILE  = Path.home() / ".dacexy_memory.json"
LOG_FILE     = Path.home() / "DacexyAgent" / "logs" / "startup.log"
VERSION      = "16.0"

# Wake words - short, easy to say
WAKE_WORDS = ["dacexy", "hey dacexy", "okay dacexy", "ok dacexy",
              "hey computer", "okay computer", "ok computer",
              "hey agent", "okay agent", "computer"]

KNOWN_SITES = {
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
}

KNOWN_APPS = {
    "chrome": "chrome.exe", "google chrome": "chrome.exe",
    "edge": "msedge.exe", "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe", "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe", "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "cmd": "cmd.exe", "command prompt": "cmd.exe",
    "terminal": "cmd.exe",
    "word": "winword.exe", "microsoft word": "winword.exe",
    "excel": "excel.exe", "microsoft excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "vlc": "vlc.exe",
    "zoom": "zoom.exe",
    "discord": "discord.exe",
    "spotify": "spotify.exe",
    "vscode": "code.exe", "visual studio code": "code.exe",
    "photoshop": "photoshop.exe",
}

BLOCKED_COMMANDS = [
    "rm -rf /","rm -rf ~","format c:","del /s /q c:\\windows",
    "rd /s /q c:\\","shutdown /s","shutdown /r","reg delete hklm",
    "dd if=/dev/zero","mkfs","deltree","bcdedit","cipher /w:c",
]

# ── GLOBAL STATE ──────────────────────────────────────────────────────
_memory_lock  = threading.Lock()
_config_lock  = threading.Lock()
_executor     = ThreadPoolExecutor(max_workers=6)
_agent_running = True
MEMORY = {
    "facts": [], "preferences": {},
    "task_history": deque(maxlen=100), "context": {}
}

# ── LOGGING ───────────────────────────────────────────────────────────
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a")
    ]
)
log = logging.getLogger("dacexy")

# ── TTS ───────────────────────────────────────────────────────────────
_tts = None
_tts_lock = threading.Lock()
_tts_q: queue.Queue = queue.Queue(maxsize=10)

def init_tts():
    global _tts
    try:
        _tts = pyttsx3.init()
        _tts.setProperty("rate", 160)
        _tts.setProperty("volume", 0.95)
        for v in (_tts.getProperty("voices") or []):
            if any(x in (v.name or "").lower() for x in ["zira","hazel","aria","female"]):
                _tts.setProperty("voice", v.id); break
        threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()
        log.info("TTS OK")
    except Exception as e:
        log.warning("TTS init: %s", e)

def _tts_worker():
    while _agent_running:
        try:
            text = _tts_q.get(timeout=1)
            if text is None: break
            try:
                with _tts_lock:
                    if _tts: _tts.say(str(text)[:300]); _tts.runAndWait()
            except Exception: pass
            finally: _tts_q.task_done()
        except queue.Empty: continue

def speak(text: str):
    if not text: return
    s = str(text)[:300]
    try: print(f"  [Dacexy] {s}"); sys.stdout.flush()
    except: pass
    log.info("SPEAK: %s", s)
    try: _tts_q.put_nowait(s)
    except queue.Full: pass

def notify(title: str, msg: str):
    try:
        if NOTIFY_OK: notification.notify(title=title, message=msg[:100], app_name="Dacexy", timeout=3)
    except: pass

# ── CONFIG & AUTH ────────────────────────────────────────────────────
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
        except Exception as e: log.warning("Config save: %s", e)

def get_token(): return load_config().get("access_token")
def save_token(t): cfg=load_config(); cfg["access_token"]=t; save_config(cfg)
def clear_token(): cfg=load_config(); cfg.pop("access_token",None); save_config(cfg)

def check_token_valid(token: str) -> bool:
    try:
        r = req_lib.get(f"{BACKEND_HTTP}/auth/me",
            headers={"Authorization": f"Bearer {token}"}, timeout=8)
        return r.status_code == 200
    except: return False

def setup_autostart():
    try:
        if not WINREG_OK: return
        bat = str(Path.home() / "DacexyAgent" / "install_dacexy_agent.bat")
        cmd = f'"{bat}"' if os.path.exists(bat) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DacexyAgent", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        log.info("Autostart registered")
    except Exception as e: log.warning("Autostart: %s", e)

def login() -> Optional[str]:
    print("\n" + "="*42)
    print("  Dacexy Agent v16.0 - Login")
    print("="*42)
    print("  Register at: dacexy.vercel.app\n")
    try:
        email = input("  Email   : ").strip()
        password = input("  Password: ").strip()
    except (EOFError, KeyboardInterrupt): return None
    if not email or "@" not in email: print("  [ERROR] Invalid email"); return None
    if not password or len(password) < 4: print("  [ERROR] Password too short"); return None
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
        else:
            try: d = r.json().get("detail", r.text)
            except: d = r.text[:100]
            print(f"  [ERROR] {d}")
    except Exception as e: print(f"  [ERROR] {e}")
    return None

# ── MEMORY ───────────────────────────────────────────────────────────
def load_memory():
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            with _memory_lock:
                MEMORY["facts"] = data.get("facts", [])
                MEMORY["preferences"] = data.get("preferences", {})
                MEMORY["context"] = data.get("context", {})
                MEMORY["task_history"] = deque(data.get("task_history", [])[-100:], maxlen=100)
    except Exception as e: log.warning("Memory load: %s", e)

def save_memory():
    try:
        with _memory_lock:
            data = {
                "facts": MEMORY["facts"][-200:],
                "preferences": MEMORY["preferences"],
                "context": MEMORY["context"],
                "task_history": list(MEMORY["task_history"])[-100:],
            }
        MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e: log.warning("Memory save: %s", e)

def remember(fact: str):
    if not fact: return
    with _memory_lock:
        if fact not in MEMORY["facts"]: MEMORY["facts"].append(fact)
    save_memory()

def get_memory_context() -> str:
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
        img = ImageGrab.grab()
        w, h = img.size
        if w > 1440: img = img.resize((1440, int(h*1440/w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning("Screenshot: %s", e); return None

# ── SMART TYPE ───────────────────────────────────────────────────────
def smart_type(text: str):
    text = str(text)[:3000]
    try:
        pyperclip.copy(text); time.sleep(0.06)
        pyautogui.hotkey("ctrl", "v"); time.sleep(0.1)
    except:
        try: pyautogui.write(text[:500], interval=0.02)
        except: pass

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

# ── PERMISSION SYSTEM ────────────────────────────────────────────────
PERMISSION_RULES = {
    "delete_files": {"triggers":[["delete","erase","wipe"],["file","folder","data"]],"warn":"This will delete files."},
    "banking":      {"triggers":[["bank","upi","transfer","gpay","paytm"],["any"]],"warn":"Accessing banking."},
    "email_send":   {"triggers":[["send email","compose email","email to"],["any"]],"warn":"Sending email."},
    "social_post":  {"triggers":[["post on","tweet","publish"],["facebook","instagram","twitter","linkedin"]],"warn":"Posting to social media."},
    "shutdown":     {"triggers":[["shutdown","restart","reboot"],["any"]],"warn":"Shutting down PC."},
}

def needs_permission(task: str) -> tuple:
    tl = task.lower()
    for ptype, rule in PERMISSION_RULES.items():
        kws, ctx = rule["triggers"]
        if any(k in tl for k in kws):
            if ctx == ["any"] or any(c in tl for c in ctx):
                return True, ptype
    return False, ""

def ask_permission(task: str, ptype: str) -> bool:
    rule = PERMISSION_RULES.get(ptype, {})
    print(f"\n  [PERMISSION REQUIRED] {rule.get('warn','')}")
    print(f'  Task: "{task[:80]}"')
    print("  Type YES to allow or NO to deny: ", end="", flush=True)
    try:
        r = input().strip().lower()
        granted = r in ["yes","y","allow","ok"]
        speak("Permission granted." if granted else "Cancelled.")
        return granted
    except: return False

# ── CORE COMMAND EXECUTOR ─────────────────────────────────────────────
def execute_command(cmd: dict, token: str = None) -> dict:
    if not isinstance(cmd, dict):
        return {"status": "error", "message": "Invalid command"}
    action = str(cmd.get("action", "")).lower().strip()
    if not action:
        return {"status": "error", "message": "No action"}

    # Security check
    task_str = str(cmd.get("text","") or cmd.get("url","") or cmd.get("command","") or action)
    if any(b in task_str.lower() for b in BLOCKED_COMMANDS):
        return {"status": "blocked", "message": "Blocked for safety"}

    log.info("CMD: %s", action)
    try:
        # ── SPEAK / NOTIFY ──────────────────────────
        if action == "speak":
            speak(cmd.get("text","")); return {"status":"ok"}
        elif action == "notify":
            notify(cmd.get("title","Dacexy"), cmd.get("text","")); return {"status":"ok"}

        # ── OPEN (handles all open variants) ─────────
        elif action in ("open","open_url","open_browser","launch","start","navigate"):
            url = (cmd.get("url","") or cmd.get("text","") or
                   cmd.get("app","") or cmd.get("name","")).strip()
            if not url: return {"status":"error","message":"Nothing to open"}
            # Check known sites
            ul = url.lower().replace("open ","").strip()
            for site, surl in KNOWN_SITES.items():
                if site in ul:
                    webbrowser.open(surl)
                    speak(f"Opening {site}")
                    return {"status":"ok","opened":surl}
            # Check known apps
            for app, exe in KNOWN_APPS.items():
                if app in ul:
                    subprocess.Popen(exe, shell=True)
                    speak(f"Opening {app}")
                    return {"status":"ok","opened":exe}
            # Raw URL
            if url.startswith("http"):
                webbrowser.open(url)
                return {"status":"ok","opened":url}
            # Try as URL with https
            if "." in url and " " not in url:
                webbrowser.open("https://"+url)
                return {"status":"ok","opened":url}
            # Try as app
            subprocess.Popen(url, shell=True)
            return {"status":"ok","opened":url}

        elif action == "open_app":
            app = cmd.get("app","").strip()
            al = app.lower()
            for name, exe in KNOWN_APPS.items():
                if name in al: subprocess.Popen(exe, shell=True); return {"status":"ok"}
            subprocess.Popen(app, shell=True); return {"status":"ok"}

        # ── MOUSE ────────────────────────────────────
        elif action == "click":
            x,y = int(cmd.get("x",0) or 0), int(cmd.get("y",0) or 0)
            if x==0 and y==0: return {"status":"skipped","reason":"no coordinates"}
            sw,sh = pyautogui.size()
            x,y = max(0,min(x,sw-1)), max(0,min(y,sh-1))
            pyautogui.click(x, y, button=cmd.get("button","left"))
            time.sleep(0.1); return {"status":"ok","at":f"({x},{y})"}
        elif action == "double_click":
            pyautogui.doubleClick(int(cmd.get("x",0)),int(cmd.get("y",0))); return {"status":"ok"}
        elif action == "right_click":
            pyautogui.rightClick(int(cmd.get("x",0)),int(cmd.get("y",0))); return {"status":"ok"}
        elif action == "move":
            pyautogui.moveTo(int(cmd.get("x",0)),int(cmd.get("y",0)),duration=0.15); return {"status":"ok"}
        elif action == "drag_to":
            pyautogui.moveTo(int(cmd.get("sx",0)),int(cmd.get("sy",0)))
            pyautogui.dragTo(int(cmd.get("ex",0)),int(cmd.get("ey",0)),duration=0.4,button="left")
            return {"status":"ok"}
        elif action == "scroll":
            x,y = int(cmd.get("x",0)),int(cmd.get("y",0))
            if x or y: pyautogui.moveTo(x,y)
            pyautogui.scroll(int(cmd.get("clicks",3))); return {"status":"ok"}
        elif action == "scroll_down":
            pyautogui.scroll(-int(cmd.get("amount",5))); return {"status":"ok"}
        elif action == "scroll_up":
            pyautogui.scroll(int(cmd.get("amount",5))); return {"status":"ok"}
        elif action == "get_mouse_pos":
            p = pyautogui.position(); return {"status":"ok","x":p.x,"y":p.y}

        # ── KEYBOARD ─────────────────────────────────
        elif action in ("type","type_text","write"):
            smart_type(cmd.get("text","")); return {"status":"ok"}
        elif action == "key":
            pyautogui.press(cmd.get("key","")); return {"status":"ok"}
        elif action == "hotkey":
            keys = cmd.get("keys",[])
            if isinstance(keys,str): keys = keys.split("+")
            if keys: pyautogui.hotkey(*keys[:4])
            return {"status":"ok"}
        elif action == "press_enter": pyautogui.press("enter"); return {"status":"ok"}
        elif action == "press_tab":   pyautogui.press("tab");   return {"status":"ok"}
        elif action == "press_escape":pyautogui.press("escape");return {"status":"ok"}
        elif action == "select_all":  pyautogui.hotkey("ctrl","a"); return {"status":"ok"}
        elif action == "copy":
            pyautogui.hotkey("ctrl","c"); time.sleep(0.1)
            return {"status":"ok","clipboard":pyperclip.paste()}
        elif action == "paste":  pyautogui.hotkey("ctrl","v"); return {"status":"ok"}
        elif action == "cut":    pyautogui.hotkey("ctrl","x"); return {"status":"ok"}
        elif action == "undo":   pyautogui.hotkey("ctrl","z"); return {"status":"ok"}
        elif action == "save":   pyautogui.hotkey("ctrl","s"); return {"status":"ok"}
        elif action == "get_clipboard": return {"status":"ok","text":pyperclip.paste()}
        elif action == "set_clipboard":
            pyperclip.copy(str(cmd.get("text",""))[:5000]); return {"status":"ok"}

        # ── SCREENSHOT / VISION ───────────────────────
        elif action == "screenshot":
            return {"status":"ok","screenshot":take_screenshot()}
        elif action in ("what_on_screen","describe_screen"):
            ss = take_screenshot(60)
            desc = "Screen captured"
            if ss and token:
                try:
                    r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
                        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
                        json={"messages":[{"role":"user","content":"Describe this screen in 2 sentences."}],"stream":False},
                        timeout=15)
                    if r.status_code==200:
                        desc = r.json().get("content") or r.json().get("response","Screen captured")
                except: pass
            speak(desc); return {"status":"ok","description":desc}

        # ── WINDOW ───────────────────────────────────
        elif action == "minimize_window": pyautogui.hotkey("win","d"); return {"status":"ok"}
        elif action == "maximize_window": pyautogui.hotkey("win","up"); return {"status":"ok"}
        elif action == "close_window":    pyautogui.hotkey("alt","f4"); return {"status":"ok"}
        elif action == "switch_window":   pyautogui.hotkey("alt","tab"); time.sleep(0.3); return {"status":"ok"}
        elif action == "get_active_window": return {"status":"ok","title":get_active_window()}
        elif action == "open_file_explorer": subprocess.Popen("explorer.exe",shell=True); return {"status":"ok"}
        elif action == "open_task_manager":  subprocess.Popen("taskmgr.exe",shell=True);  return {"status":"ok"}
        elif action == "open_settings":      subprocess.Popen("ms-settings:",shell=True); return {"status":"ok"}
        elif action == "open_notepad":
            txt = cmd.get("text","")
            if txt:
                tmp = Path.home()/"dacexy_note.txt"
                tmp.write_text(str(txt)[:50000],encoding="utf-8")
                subprocess.Popen(f'notepad.exe "{tmp}"',shell=True)
            else: subprocess.Popen("notepad.exe",shell=True)
            return {"status":"ok"}

        # ── VOLUME ───────────────────────────────────
        elif action == "volume_up":
            for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumeup")
            return {"status":"ok"}
        elif action == "volume_down":
            for _ in range(min(int(cmd.get("steps",5)),20)): pyautogui.press("volumedown")
            return {"status":"ok"}
        elif action == "mute": pyautogui.press("volumemute"); return {"status":"ok"}

        # ── FILES ────────────────────────────────────
        elif action == "write_file":
            p = Path(cmd.get("path",""))
            if not str(p).startswith(str(Path.home())):
                return {"status":"blocked","reason":"Outside home dir"}
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(str(cmd.get("content",""))[:100000],encoding="utf-8")
            return {"status":"ok"}
        elif action == "read_file":
            p = Path(cmd.get("path",""))
            if p.exists(): return {"status":"ok","content":p.read_text(encoding="utf-8",errors="ignore")[:5000]}
            return {"status":"error","message":"File not found"}
        elif action == "list_files":
            p = Path(cmd.get("path",str(Path.home())))
            try: return {"status":"ok","files":[f.name for f in p.iterdir()][:50]}
            except Exception as e: return {"status":"error","message":str(e)}
        elif action == "delete_file":
            p = Path(cmd.get("path",""))
            if p.exists(): p.unlink(); return {"status":"ok"}
            return {"status":"error","message":"Not found"}

        # ── SYSTEM ───────────────────────────────────
        elif action in ("get_system_info","system_info"):
            dp = "C:\\" if platform.system()=="Windows" else "/"
            info = {
                "cpu": psutil.cpu_percent(interval=0.5),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage(dp).percent,
                "active_window": get_active_window(),
                "platform": platform.system(),
            }
            speak(f"CPU {info['cpu']}%, RAM {info['ram']}%")
            return {"status":"ok","info":info}
        elif action == "get_time":
            t = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {t}"); return {"status":"ok","time":t}
        elif action == "get_date":
            d = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {d}"); return {"status":"ok","date":d}
        elif action == "run_command":
            c = cmd.get("command","")
            if any(b in c.lower() for b in BLOCKED_COMMANDS):
                return {"status":"blocked","reason":"Blocked"}
            try:
                r = subprocess.run(c,shell=True,capture_output=True,text=True,timeout=30)
                return {"status":"ok","stdout":r.stdout[:2000],"stderr":r.stderr[:500]}
            except subprocess.TimeoutExpired: return {"status":"error","message":"Timeout"}
        elif action == "kill_process":
            name = cmd.get("name","")
            safe = ["explorer","winlogon","csrss","svchost","system","lsass"]
            if any(p in name.lower() for p in safe): return {"status":"blocked"}
            killed=0
            for p in psutil.process_iter(["name"]):
                try:
                    if name.lower() in (p.info["name"] or "").lower():
                        p.kill(); killed+=1
                except: pass
            return {"status":"ok","killed":killed}
        elif action == "list_processes":
            procs = []
            for p in psutil.process_iter(["pid","name","cpu_percent"]):
                try: procs.append(p.info)
                except: pass
            return {"status":"ok","processes":procs[:30]}

        # ── SEARCH / BROWSE ──────────────────────────
        elif action == "search_web":
            q = str(cmd.get("query",""))[:200]
            if q: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
            return {"status":"ok"}
        elif action == "open_youtube":
            q = str(cmd.get("query",""))[:200]
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}" if q else "https://www.youtube.com"
            webbrowser.open(url); return {"status":"ok"}

        # ── EMAIL (opens gmail compose - no SMTP needed) ──
        elif action in ("send_email","gmail_send","compose_email"):
            to      = cmd.get("to","")
            subject = cmd.get("subject","")
            body    = cmd.get("body","") or cmd.get("text","")
            if not to: return {"status":"error","message":"No recipient"}
            url = (f"https://mail.google.com/mail/?view=cm"
                   f"&to={urllib.parse.quote(to)}"
                   f"&su={urllib.parse.quote(subject)}"
                   f"&body={urllib.parse.quote(body)}")
            webbrowser.open(url)
            speak(f"Opening Gmail compose to {to}")
            return {"status":"ok","note":"Opened Gmail compose"}

        # ── MEMORY ───────────────────────────────────
        elif action == "remember":
            remember(cmd.get("fact","") or cmd.get("text","")); return {"status":"ok"}
        elif action == "get_memory":
            return {"status":"ok","memory":get_memory_context()}
        elif action == "take_note":
            note = cmd.get("text","")
            if note: remember(f"Note: {note[:200]}"); speak("Saved.")
            return {"status":"ok"}

        # ── WAIT ─────────────────────────────────────
        elif action == "wait":
            time.sleep(min(float(cmd.get("seconds",1)),10)); return {"status":"ok"}
        elif action == "sleep":
            time.sleep(min(float(cmd.get("seconds",1)),10)); return {"status":"ok"}

        elif action == "ping": return {"status":"ok","pong":True}
        elif action == "health_check":
            return {"status":"ok","health":{"cpu":psutil.cpu_percent(),"ram":psutil.virtual_memory().percent}}

        else:
            # Unknown action — try to interpret as open command
            log.warning("Unknown action: %s — trying as open", action)
            return execute_command({"action":"open","text":action}, token)

    except Exception as e:
        log.error("CMD %s error: %s", action, e)
        return {"status":"error","message":str(e)}


# ── AI TASK EXECUTOR ─────────────────────────────────────────────────
def execute_task_with_ai(task: str, token: str) -> dict:
    """Send task to AI, get JSON commands, execute them on PC. Returns result dict."""
    if not task or not token:
        return {"status":"error","ok":0,"total":0,"result":"Missing task or token"}
    log.info("AI Task: %s", task)
    try:
        mem_ctx = get_memory_context()
        system_prompt = f"""You are Dacexy Desktop Agent controlling a Windows PC.
The user gives a task. Respond ONLY with a valid JSON array of commands. No explanation, no markdown.

AVAILABLE ACTIONS (use EXACTLY these names):
- open: {{"action":"open","url":"https://..."}} — open website or app
- open_app: {{"action":"open_app","app":"chrome.exe"}} — open application
- click: {{"action":"click","x":500,"y":300}} — click at coordinates (must have real x,y)
- type: {{"action":"type","text":"hello"}} — type text
- key: {{"action":"key","key":"enter"}} — press key
- hotkey: {{"action":"hotkey","keys":["ctrl","c"]}} — key combination
- scroll_down: {{"action":"scroll_down","amount":3}}
- scroll_up: {{"action":"scroll_up","amount":3}}
- screenshot: {{"action":"screenshot"}}
- search_web: {{"action":"search_web","query":"cats"}}
- open_youtube: {{"action":"open_youtube","query":"music"}}
- send_email: {{"action":"send_email","to":"x@gmail.com","subject":"Hi","body":"Hello"}}
- write_file: {{"action":"write_file","path":"C:/Users/.../file.txt","content":"text"}}
- read_file: {{"action":"read_file","path":"..."}}
- get_time: {{"action":"get_time"}}
- get_date: {{"action":"get_date"}}
- speak: {{"action":"speak","text":"Done!"}}
- wait: {{"action":"wait","seconds":2}}
- get_system_info: {{"action":"get_system_info"}}
- minimize_window / maximize_window / close_window
- volume_up / volume_down / mute
- copy / paste / select_all / save

RULES:
- To open YouTube: [{{"action":"open","url":"https://www.youtube.com"}}]
- To open Gmail and send email: [{{"action":"send_email","to":"EMAIL","subject":"SUBJECT","body":"BODY"}}]
- To search Google: [{{"action":"search_web","query":"QUERY"}}]
- NEVER use action "open_browser" — use "open" instead
- NEVER use click with x=0,y=0
- For email tasks WITHOUT SMTP configured, use send_email action which opens Gmail compose

User context:
{mem_ctx}

Return ONLY a JSON array like: [{{"action":"open","url":"https://youtube.com"}}]"""

        r = req_lib.post(f"{BACKEND_HTTP}/ai/chat",
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"},
            json={"messages":[
                {"role":"system","content":system_prompt},
                {"role":"user","content":f"Task: {task[:500]}"}
            ],"stream":False},
            timeout=30)

        if r.status_code != 200:
            return {"status":"error","ok":0,"total":0,"result":f"AI error HTTP {r.status_code}"}

        raw = (r.json().get("content") or r.json().get("response") or "").strip()
        if not raw:
            return {"status":"error","ok":0,"total":0,"result":"AI returned empty"}

        # Strip markdown fences
        raw = re.sub(r'^```(?:json)?\s*','',raw,flags=re.MULTILINE)
        raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE).strip()

        # Extract JSON array
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            # AI returned text, speak it
            speak(raw[:200])
            return {"status":"ok","ok":1,"total":1,"result":raw[:200]}

        try:
            commands = json.loads(match.group())
        except json.JSONDecodeError:
            speak("I understood but couldn't parse the steps.")
            return {"status":"error","ok":0,"total":0,"result":"JSON parse error"}

        if not isinstance(commands, list) or not commands:
            return {"status":"error","ok":0,"total":0,"result":"No commands"}

        ok_count = 0; total = len(commands)
        results_list = []

        for c in commands:
            if not isinstance(c, dict): continue
            # Flatten params if nested
            for k,v in c.get("params",{}).items():
                if k not in c: c[k] = v
            try:
                res = execute_command(c, token)
                ok_count += 1
                results_list.append(res)
                time.sleep(0.3)
                if res.get("status") == "error":
                    log.warning("Step failed: %s -> %s", c.get("action"), res.get("message"))
            except Exception as ce:
                log.error("Step error: %s", ce)
                results_list.append({"status":"error","message":str(ce)})

        with _memory_lock:
            MEMORY["task_history"].append(task[:100])
        save_memory()

        summary = f"Done {ok_count}/{total} steps for: {task[:60]}"
        log.info(summary)
        speak(f"Done! Completed {ok_count} out of {total} steps.")
        return {"status":"ok","ok":ok_count,"total":total,"result":summary,"steps":results_list}

    except req_lib.exceptions.Timeout:
        return {"status":"error","ok":0,"total":0,"result":"AI timeout"}
    except req_lib.exceptions.ConnectionError:
        return {"status":"error","ok":0,"total":0,"result":"No internet"}
    except Exception as e:
        log.error("Task error: %s", e)
        return {"status":"error","ok":0,"total":0,"result":str(e)}


# ── VOICE ENGINE ─────────────────────────────────────────────────────
_voice_active = False
_current_token = None
_voice_token_lock = threading.Lock()

def _voice_loop():
    global _voice_active, _current_token
    if not VOICE_AVAILABLE or not sr:
        log.warning("Voice disabled - PyAudio not available")
        print("  [WARN] Voice disabled. Install PyAudio.")
        return

    rec = sr.Recognizer()
    rec.energy_threshold = 400
    rec.dynamic_energy_threshold = True
    rec.pause_threshold = 0.7

    # Check mic
    try:
        mics = sr.Microphone.list_microphone_names()
        if not mics: print("  [WARN] No microphone found."); return
    except Exception as e: log.warning("Mic check: %s", e)

    print(f"\n  [MIC] Voice active! Say any of these wake words:")
    print(f"  --> 'Dacexy' / 'Hey Dacexy' / 'Computer' / 'Hey Computer'")
    speak("Voice ready. Say Dacexy or Computer to activate me.")
    errors = 0

    while _voice_active and _agent_running:
        try:
            with sr.Microphone() as src:
                try: rec.adjust_for_ambient_noise(src, duration=0.2)
                except: pass
                try:
                    audio = rec.listen(src, timeout=4, phrase_time_limit=5)
                    heard = rec.recognize_google(audio).lower().strip()
                    log.info("Heard: %s", heard)
                    errors = 0

                    # Check wake word
                    activated = any(w in heard for w in WAKE_WORDS)
                    if not activated: continue

                    print(f"\n  [WAKE] Activated! Listening for command...")
                    speak("Yes?")
                    time.sleep(0.3)

                    # Listen for command
                    with sr.Microphone() as csrc:
                        try: rec.adjust_for_ambient_noise(csrc, duration=0.15)
                        except: pass
                        try:
                            caudio = rec.listen(csrc, timeout=7, phrase_time_limit=20)
                            command = rec.recognize_google(caudio).strip()
                            print(f"  [CMD] {command}")
                            log.info("Voice command: %s", command)

                            if not command: continue

                            with _voice_token_lock: tok = _current_token
                            if not tok: speak("Please log in first."); continue

                            # Permission check
                            needs_p, ptype = needs_permission(command)
                            if needs_p and not ask_permission(command, ptype): continue

                            speak("On it!")

                            def _run(t, cmd_text):
                                try:
                                    result = execute_task_with_ai(cmd_text, t)
                                    if result.get("status") != "ok":
                                        speak(f"Sorry, {result.get('result','something went wrong.')[:80]}")
                                except Exception as ve:
                                    log.error("Voice task: %s", ve)
                                    speak("Sorry, something went wrong.")

                            threading.Thread(target=_run, args=(tok,command), daemon=True).start()

                        except sr.WaitTimeoutError: speak("Didn't hear a command.")
                        except sr.UnknownValueError: speak("Couldn't understand. Try again.")
                        except Exception as e: log.warning("Cmd recognition: %s", e)

                except sr.WaitTimeoutError: pass
                except sr.UnknownValueError: pass
                except sr.RequestError as e:
                    log.warning("SR API: %s", e); errors+=1; time.sleep(3)
                except Exception as e:
                    log.debug("Voice listen: %s", e); errors+=1; time.sleep(0.5)

        except OSError as e:
            log.warning("Mic error: %s", e); errors+=1; time.sleep(3)
        except Exception as e:
            log.warning("Voice loop: %s", e); errors+=1; time.sleep(2)

        if errors >= 10:
            log.warning("Too many voice errors - pausing 30s")
            speak("Voice temporarily unavailable. Retrying.")
            time.sleep(30); errors=0

def start_voice(token: str):
    global _voice_active, _current_token
    with _voice_token_lock: _current_token = token
    if not VOICE_AVAILABLE: return False
    _voice_active = True
    threading.Thread(target=_voice_loop, daemon=True, name="Voice").start()
    return True

def stop_voice():
    global _voice_active; _voice_active = False

def update_voice_token(token: str):
    global _current_token
    with _voice_token_lock: _current_token = token


# ── WEBSOCKET ────────────────────────────────────────────────────────
async def run_websocket(token: str):
    retry = 3.0; max_retry = 60.0

    while _agent_running:
        try:
            log.info("Connecting to backend...")
            print("  [WS] Connecting to Dacexy cloud...")

            # Version-safe connect
            kw = {"ping_interval":25,"ping_timeout":20,"max_size":10*1024*1024}
            try:
                ws_ver = int(str(getattr(websockets,"__version__","0")).split(".")[0])
                if ws_ver >= 14: kw["open_timeout"]=20
                else: kw["close_timeout"]=10; kw["extra_headers"]={"User-Agent":f"DacexyAgent/{VERSION}"}
            except: pass

            async with websockets.connect(BACKEND_WS, **kw) as ws:
                # Send auth
                await ws.send(json.dumps({
                    "token": token,
                    "type": "init",
                    "version": VERSION,
                    "platform": platform.system(),
                    "hostname": __import__("socket").gethostname(),
                    "features": ["voice","vision","email","browser","scheduler","memory"]
                }))

                # Wait for auth response
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    auth = json.loads(auth_raw)
                    if auth.get("type") == "error":
                        log.error("Auth failed: %s", auth.get("message"))
                        speak("Authentication failed.")
                        return
                except asyncio.TimeoutError:
                    log.error("Auth timeout"); await asyncio.sleep(retry); continue

                log.info("Connected to Dacexy backend!")
                print("  [OK] Connected to Dacexy cloud - ready!")
                speak("Connected. Ready for your commands.")
                retry = 3.0

                _ws_lock = asyncio.Lock()
                async def send(data):
                    async with _ws_lock:
                        try: await ws.send(json.dumps(data))
                        except: pass

                # Main loop
                while _agent_running:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=40)
                    except asyncio.TimeoutError:
                        try: await asyncio.wait_for(ws.send(json.dumps({"type":"ping"})), timeout=5)
                        except: break
                        continue

                    try: msg = json.loads(raw)
                    except: continue

                    mtype = msg.get("type","")

                    if mtype == "ping":
                        await send({"type":"pong","version":VERSION})

                    elif mtype in ("task","command") or "action" in msg or "task" in msg:
                        task_text = msg.get("task","") or msg.get("action","")
                        task_id   = str(msg.get("task_id",""))
                        action    = msg.get("action","")

                        if action and action != "swarm_task" and action != "task":
                            # Direct command from dashboard
                            log.info("Direct cmd: %s", action)
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                _executor, lambda: execute_command(msg, token))
                            await send({"type":"result","task_id":task_id,
                                       "status":result.get("status","ok"),
                                       "data":result,"ok":1,"total":1})
                        elif task_text:
                            log.info("Task: %s", task_text)
                            print(f"\n  [TASK] {task_text}")
                            speak(f"Working on: {task_text[:50]}")
                            loop = asyncio.get_event_loop()

                            def _run_task(t, task, tid):
                                try:
                                    needs_p, ptype = needs_permission(task)
                                    if needs_p and not ask_permission(task, ptype):
                                        asyncio.run_coroutine_threadsafe(
                                            send({"type":"task_result","task_id":tid,
                                                 "status":"denied","ok":0,"total":0,
                                                 "result":"Permission denied"}), loop)
                                        return
                                    result = execute_task_with_ai(task, t)
                                    asyncio.run_coroutine_threadsafe(
                                        send({"type":"task_result","task_id":tid,
                                             "status":result.get("status","ok"),
                                             "ok":result.get("ok",0),
                                             "total":result.get("total",1),
                                             "result":result.get("result",""),
                                             "steps":result.get("steps",[])}), loop)
                                except Exception as e:
                                    log.error("Task run: %s", e)
                                    asyncio.run_coroutine_threadsafe(
                                        send({"type":"task_result","task_id":tid,
                                             "status":"error","ok":0,"total":0,
                                             "result":str(e)}), loop)

                            threading.Thread(target=_run_task,
                                args=(token, task_text, task_id), daemon=True).start()

        except websockets.exceptions.ConnectionClosedOK:
            log.info("WS closed cleanly")
        except websockets.exceptions.ConnectionClosedError as e:
            log.warning("WS error: %s", e)
        except OSError as e:
            log.warning("Network: %s", e)
        except Exception as e:
            log.error("WS unexpected: %s", e)

        if _agent_running:
            log.info("Reconnecting in %.0fs...", retry)
            print(f"  [WS] Reconnecting in {int(retry)}s...")
            await asyncio.sleep(retry)
            retry = min(retry*1.5, max_retry)


# ── HEARTBEAT ────────────────────────────────────────────────────────
def heartbeat(token_holder: list):
    while _agent_running:
        time.sleep(300)
        try:
            tok = token_holder[0]
            if tok and not check_token_valid(tok):
                log.warning("Token expired")
                speak("Session expired. Please restart.")
            else:
                update_voice_token(tok)
        except Exception as e: log.warning("Heartbeat: %s", e)


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*50)
    print("  DACEXY DESKTOP AGENT v16.0")
    print("  The World's Best Desktop AI Agent")
    print("="*50 + "\n")

    init_tts()
    load_memory()

    # Auth
    token = get_token()
    if token:
        print("  Checking saved session...")
        try:
            if not check_token_valid(token):
                print("  Session expired. Logging in again.")
                clear_token(); token = None
            else:
                print("  [OK] Session valid")
        except: print("  Could not verify - continuing")

    if not token:
        for attempt in range(3):
            token = login()
            if token: break
            if attempt < 2: print(f"  Attempt {attempt+1}/3 failed.\n")
        if not token:
            print("\n  [ERROR] Could not authenticate. Exiting.")
            return

    # Setup
    try: setup_autostart()
    except: pass

    # Voice
    voice_ok = start_voice(token)
    if voice_ok:
        print(f"  [MIC] Voice active - say 'Dacexy' or 'Computer' to wake!")
    else:
        print("  [WARN] Voice disabled - PyAudio not available")

    # Heartbeat
    token_holder = [token]
    threading.Thread(target=heartbeat, args=(token_holder,), daemon=True).start()

    print("\n  " + "-"*46)
    print(f"  Agent running 24/7  |  Voice: {'ON' if voice_ok else 'OFF'}")
    print(f"  Wake words: 'Dacexy', 'Computer', 'Hey Computer'")
    print(f"  Control: dacexy.vercel.app/dashboard")
    print("  " + "-"*46 + "\n")

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
        speak("Goodbye!"); time.sleep(1)


if __name__ == "__main__":
    main()
