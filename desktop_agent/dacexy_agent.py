"""
Dacexy Desktop Agent v2.0
=========================
Double-click to run. Auto-installs everything needed.
Connects your computer to Dacexy AI.

HOW TO USE:
1. Double-click this file (or run: python dacexy_agent.py)
2. Enter your Dacexy email and password when prompted
3. Go to dacexy.vercel.app/chat and start giving commands!
"""
import subprocess, sys

# Auto-install dependencies before anything else
for pkg in ["pyautogui", "pillow", "websockets", "requests"]:
    try:
        __import__(pkg.replace("-","_"))
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable,"-m","pip","install",pkg,"-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

import asyncio, base64, io, json, logging, os, platform, threading, time, webbrowser
from pathlib import Path

import pyautogui, requests, websockets
from PIL import ImageGrab

BACKEND_WS   = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE  = Path.home() / ".dacexy_agent.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / "dacexy_agent.log", encoding="utf-8")
    ]
)
log = logging.getLogger("dacexy")
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

def load_config():
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_token():
    return load_config().get("access_token")

def save_token(token):
    cfg = load_config(); cfg["access_token"] = token; save_config(cfg)

def clear_token():
    cfg = load_config(); cfg.pop("access_token", None); save_config(cfg)

def login():
    print("\n" + "="*52)
    print("   Dacexy Desktop Agent — Login")
    print("="*52)
    email    = input("  Email   : ").strip()
    password = input("  Password: ").strip()
    print()
    try:
        r = requests.post(
            f"{BACKEND_HTTP}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        if r.status_code == 200:
            token = r.json().get("access_token","")
            if token:
                save_token(token)
                print("  ✅  Login successful! Credentials saved.")
                return token
            print("  ❌  No token received.")
        else:
            d = r.json().get("detail", r.text)
            if isinstance(d, list): d = d[0].get("msg", str(d))
            print(f"  ❌  Login failed: {d}")
    except requests.exceptions.ConnectionError:
        print("  ❌  Cannot connect. Check your internet.")
    except Exception as e:
        print(f"  ❌  Error: {e}")
    return None

def take_screenshot():
    try:
        img = ImageGrab.grab()
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return None

BLOCKED = ["rm -rf /","rm -rf ~","format c:","del /s /q c:\\",
           "shutdown","reboot","mkfs","dd if=/dev/zero","sudo rm"]

def execute_command(cmd: dict) -> dict:
    action = cmd.get("action","").lower()
    try:
        if action == "screenshot":
            return {"status":"ok","screenshot": take_screenshot()}

        elif action == "click":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.click(x,y,button=cmd.get("button","left"))
            return {"status":"ok","action":f"clicked ({x},{y})"}

        elif action == "double_click":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.doubleClick(x,y)
            return {"status":"ok","action":f"double-clicked ({x},{y})"}

        elif action == "right_click":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.rightClick(x,y)
            return {"status":"ok","action":f"right-clicked ({x},{y})"}

        elif action == "type":
            text = cmd.get("text","")
            pyautogui.typewrite(text, interval=0.04)
            return {"status":"ok","action":f"typed {len(text)} chars"}

        elif action == "key":
            pyautogui.press(cmd.get("key",""))
            return {"status":"ok","action":f"pressed {cmd.get('key','')}"}

        elif action == "hotkey":
            keys = cmd.get("keys",[])
            if keys: pyautogui.hotkey(*keys)
            return {"status":"ok","action":f"hotkey {'+'.join(keys)}"}

        elif action == "scroll":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.scroll(int(cmd.get("clicks",3)), x=x, y=y)
            return {"status":"ok","action":"scrolled"}

        elif action == "move":
            x,y = int(cmd.get("x",0)), int(cmd.get("y",0))
            pyautogui.moveTo(x,y, duration=float(cmd.get("duration",0.3)))
            return {"status":"ok","action":f"moved to ({x},{y})"}

        elif action == "open_url":
            url = cmd.get("url","")
            webbrowser.open(url)
            return {"status":"ok","action":f"opened {url}"}

        elif action == "open_app":
            app = cmd.get("app","")
            s = platform.system()
            if s == "Windows": os.startfile(app)
            elif s == "Darwin": subprocess.Popen(["open","-a",app])
            else: subprocess.Popen([app])
            return {"status":"ok","action":f"opened {app}"}

        elif action == "run_shell":
            command = cmd.get("command","")
            for b in BLOCKED:
                if b.lower() in command.lower():
                    return {"status":"error","message":f"Blocked: {b}"}
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"status":"ok","stdout":r.stdout[:3000],"stderr":r.stderr[:500],"code":r.returncode}

        elif action == "get_screen_size":
            sz = pyautogui.size()
            return {"status":"ok","width":sz.width,"height":sz.height}

        elif action == "get_system_info":
            sz = pyautogui.size()
            return {"status":"ok","os":platform.system(),"os_version":platform.version(),
                    "machine":platform.machine(),"hostname":platform.node(),
                    "screen_width":sz.width,"screen_height":sz.height,"agent_version":"2.0"}

        else:
            return {"status":"error","message":f"Unknown action: {action}"}

    except pyautogui.FailSafeException:
        return {"status":"error","message":"Failsafe triggered"}
    except Exception as e:
        log.error(f"Command error [{action}]: {e}")
        return {"status":"error","message":str(e)}

async def agent_loop(token: str):
    retry_delay = 5
    failures = 0
    while True:
        try:
            log.info("Connecting to Dacexy...")
            async with websockets.connect(BACKEND_WS, ping_interval=20, ping_timeout=30) as ws:
                # Send token as first message for authentication
                await ws.send(json.dumps({"token": token}))

                # Wait for auth confirmation
                resp = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(resp)

                if data.get("type") == "error":
                    print(f"\n  ❌  Auth failed: {data.get('message')}")
                    print("  Session expired. Please re-login.\n")
                    clear_token()
                    return

                print("\n" + "="*52)
                print("  ✅  DACEXY AGENT IS ACTIVE!")
                print("  Your computer is connected to Dacexy AI.")
                print("  Visit dacexy.vercel.app/chat to send commands.")
                print("  Press Ctrl+C to stop.")
                print("="*52 + "\n")

                retry_delay = 5
                failures = 0

                # Send system info
                info = execute_command({"action":"get_system_info"})
                await ws.send(json.dumps({"type":"system_info","data":info}))

                # Command loop
                async for raw in ws:
                    try:
                        cmd = json.loads(raw)
                        mtype = cmd.get("type","")

                        if mtype == "ping":
                            await ws.send(json.dumps({"type":"pong"})); continue

                        if mtype == "command" or "action" in cmd:
                            action = cmd.get("action","unknown")
                            log.info(f"▶ Executing: {action}")

                            # Screenshot before
                            if action not in ["screenshot","get_system_info","get_screen_size"]:
                                ss = take_screenshot()
                                if ss: await ws.send(json.dumps({"type":"screenshot_before","data":ss}))

                            # Execute command
                            result = execute_command(cmd)
                            await ws.send(json.dumps({"type":"result","action":action,"data":result}))

                            # Screenshot after
                            if action not in ["get_system_info","get_screen_size"]:
                                await asyncio.sleep(0.5)
                                ss = take_screenshot()
                                if ss: await ws.send(json.dumps({"type":"screenshot_after","data":ss}))

                    except json.JSONDecodeError:
                        log.warning("Bad JSON from server")
                    except Exception as e:
                        log.error(f"Loop error: {e}")
                        await ws.send(json.dumps({"type":"error","message":str(e)}))

        except websockets.exceptions.ConnectionClosedOK:
            log.info("Connection closed normally.")
        except Exception as e:
            log.error(f"Connection error: {e}")

        failures += 1
        wait = min(retry_delay * (2 ** min(failures, 5)), 120)
        print(f"  ⚠  Disconnected. Reconnecting in {wait}s...")
        await asyncio.sleep(wait)

def run_with_tray(token: str):
    try:
        import pystray
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (64,64), "#7c3aed")
        d = ImageDraw.Draw(img)
        d.ellipse([4,4,60,60], fill="#6d28d9")
        d.text((22,18), "D", fill="white")

        def open_dacexy(icon, item): webbrowser.open("https://dacexy.vercel.app/chat")
        def quit_agent(icon, item): icon.stop(); os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open Dacexy Chat", open_dacexy, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Agent", quit_agent),
        )
        icon = pystray.Icon("Dacexy Agent", img, "Dacexy Agent — Active", menu)

        t = threading.Thread(target=lambda: asyncio.run(agent_loop(token)), daemon=True)
        t.start()
        icon.run()

    except ImportError:
        asyncio.run(agent_loop(token))

def main():
    print("\n" + "="*52)
    print("  🤖  Dacexy Desktop Agent v2.0")
    print("  AI-powered computer automation")
    print("="*52 + "\n")

    token = get_token()
    if not token:
        print("  First time — please login to Dacexy\n")
        token = login()
        if not token:
            print("\n  ❌  Login failed.")
            input("  Press Enter to exit...")
            sys.exit(1)
    else:
        print("  ✅  Saved credentials found. Starting...")

    print("  Connecting to Dacexy servers...\n")
    try:
        run_with_tray(token)
    except KeyboardInterrupt:
        print("\n\n  👋  Agent stopped.")

if __name__ == "__main__":
    main()
                
