"""
Dacexy Desktop Agent
Double-click to run. Connects to Dacexy AI and controls your computer.
Requirements: pip install pyautogui pillow websockets requests
"""
import asyncio
import base64
import io
import json
import logging
import os
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Auto-install dependencies
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

for pkg in ["pyautogui", "pillow", "websockets", "requests"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        print(f"Installing {pkg}...")
        install(pkg)

import pyautogui
import requests
import websockets
from PIL import ImageGrab

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dacexy-agent")

BACKEND_WS = "wss://dacexy-backend-v7ku.onrender.com/api/v1/agent/desktop/ws"
BACKEND_HTTP = "https://dacexy-backend-v7ku.onrender.com/api/v1"
CONFIG_FILE = Path.home() / ".dacexy_agent.json"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# ─── Config ───────────────────────────────────────────────────────────────────

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def get_token():
    cfg = load_config()
    return cfg.get("access_token")

def save_token(token):
    cfg = load_config()
    cfg["access_token"] = token
    save_config(cfg)

# ─── Login ────────────────────────────────────────────────────────────────────

def login():
    print("\n" + "="*50)
    print("  Dacexy Desktop Agent — Login")
    print("="*50)
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    try:
        r = requests.post(f"{BACKEND_HTTP}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30)
        if r.status_code == 200:
            token = r.json().get("access_token")
            save_token(token)
            print("✅ Logged in successfully!")
            return token
        else:
            print(f"❌ Login failed: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

# ─── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot():
    try:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        log.error(f"Screenshot failed: {e}")
        return None

# ─── Execute command ──────────────────────────────────────────────────────────

def execute_command(cmd: dict) -> str:
    action = cmd.get("action", "")
    try:
        if action == "screenshot":
            data = take_screenshot()
            return json.dumps({"status": "ok", "screenshot": data})

        elif action == "click":
            x, y = cmd.get("x", 0), cmd.get("y", 0)
            pyautogui.click(x, y)
            return json.dumps({"status": "ok", "action": f"clicked ({x},{y})"})

        elif action == "type":
            text = cmd.get("text", "")
            pyautogui.typewrite(text, interval=0.03)
            return json.dumps({"status": "ok", "action": f"typed: {text[:30]}"})

        elif action == "key":
            key = cmd.get("key", "")
            pyautogui.press(key)
            return json.dumps({"status": "ok", "action": f"pressed: {key}"})

        elif action == "hotkey":
            keys = cmd.get("keys", [])
            pyautogui.hotkey(*keys)
            return json.dumps({"status": "ok", "action": f"hotkey: {'+'.join(keys)}"})

        elif action == "scroll":
            x, y = cmd.get("x", 0), cmd.get("y", 0)
            clicks = cmd.get("clicks", 3)
            pyautogui.scroll(clicks, x=x, y=y)
            return json.dumps({"status": "ok", "action": f"scrolled {clicks}"})

        elif action == "move":
            x, y = cmd.get("x", 0), cmd.get("y", 0)
            pyautogui.moveTo(x, y, duration=0.3)
            return json.dumps({"status": "ok", "action": f"moved to ({x},{y})"})

        elif action == "open_url":
            url = cmd.get("url", "")
            webbrowser.open(url)
            return json.dumps({"status": "ok", "action": f"opened {url}"})

        elif action == "run_shell":
            command = cmd.get("command", "")
            # Safety check — only allow safe commands
            blocked = ["rm -rf", "format", "del /", "shutdown", "reboot", "mkfs"]
            if any(b in command.lower() for b in blocked):
                return json.dumps({"status": "error", "message": "Command blocked for safety"})
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return json.dumps({"status": "ok", "stdout": result.stdout[:2000], "stderr": result.stderr[:500]})

        elif action == "get_screen_size":
            size = pyautogui.size()
            return json.dumps({"status": "ok", "width": size.width, "height": size.height})

        elif action == "get_system_info":
            return json.dumps({
                "status": "ok",
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "python": sys.version,
                "screen": {"width": pyautogui.size().width, "height": pyautogui.size().height}
            })

        else:
            return json.dumps({"status": "error", "message": f"Unknown action: {action}"})

    except Exception as e:
        log.error(f"Command error: {e}")
        return json.dumps({"status": "error", "message": str(e)})

# ─── WebSocket loop ───────────────────────────────────────────────────────────

async def run_agent(token: str):
    log.info("Connecting to Dacexy backend...")
    headers = {"Authorization": f"Bearer {token}"}
    retry_delay = 5

    while True:
        try:
            async with websockets.connect(BACKEND_WS, extra_headers=headers, ping_interval=30) as ws:
                log.info("✅ Connected to Dacexy! Agent is running.")
                print("\n" + "="*50)
                print("  ✅ Dacexy Agent is ACTIVE")
                print("  Go to dacexy.vercel.app and give commands!")
                print("  Press Ctrl+C to stop")
                print("="*50 + "\n")
                retry_delay = 5

                # Send initial system info
                info = execute_command({"action": "get_system_info"})
                await ws.send(json.dumps({"type": "system_info", "data": json.loads(info)}))

                async for message in ws:
                    try:
                        cmd = json.loads(message)
                        log.info(f"Received command: {cmd.get('action', 'unknown')}")

                        # Take screenshot before executing
                        if cmd.get("action") not in ["screenshot", "get_system_info", "get_screen_size"]:
                            screenshot = take_screenshot()
                            if screenshot:
                                await ws.send(json.dumps({"type": "screenshot_before", "data": screenshot}))

                        result = execute_command(cmd)
                        await ws.send(json.dumps({"type": "result", "data": json.loads(result)}))

                        # Take screenshot after executing
                        time.sleep(0.5)
                        screenshot = take_screenshot()
                        if screenshot:
                            await ws.send(json.dumps({"type": "screenshot_after", "data": screenshot}))

                    except json.JSONDecodeError:
                        log.error("Invalid JSON received")
                    except Exception as e:
                        log.error(f"Error processing command: {e}")
                        await ws.send(json.dumps({"type": "error", "message": str(e)}))

        except websockets.exceptions.ConnectionClosed:
            log.warning(f"Connection closed. Reconnecting in {retry_delay}s...")
        except Exception as e:
            log.error(f"Connection error: {e}. Retrying in {retry_delay}s...")

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)

# ─── System tray icon (optional) ─────────────────────────────────────────────

def try_systray(token):
    try:
        import pystray
        from PIL import Image, ImageDraw

        def create_icon():
            img = Image.new("RGB", (64, 64), "#7c3aed")
            d = ImageDraw.Draw(img)
            d.text((20, 20), "D", fill="white")
            return img

        def on_quit(icon, item):
            icon.stop()
            os._exit(0)

        def open_dashboard(icon, item):
            webbrowser.open("https://dacexy.vercel.app/chat")

        menu = pystray.Menu(
            pystray.MenuItem("Open Dacexy", open_dashboard),
            pystray.MenuItem("Quit Agent", on_quit)
        )
        icon = pystray.Icon("Dacexy Agent", create_icon(), "Dacexy Agent", menu)

        # Run WebSocket in background thread
        def run_ws():
            asyncio.run(run_agent(token))

        t = threading.Thread(target=run_ws, daemon=True)
        t.start()
        icon.run()

    except ImportError:
        # No systray, just run normally
        asyncio.run(run_agent(token))

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*50)
    print("  🤖 Dacexy Desktop Agent")
    print("  AI that controls your computer")
    print("="*50)

    token = get_token()
    if not token:
        print("\nFirst time setup — please login to Dacexy")
        token = login()
        if not token:
            print("❌ Could not login. Exiting.")
            input("Press Enter to exit...")
            return

    print(f"\n✅ Token found. Starting agent...")
    try:
        try_systray(token)
    except KeyboardInterrupt:
        print("\n👋 Agent stopped.")

if __name__ == "__main__":
    main()
