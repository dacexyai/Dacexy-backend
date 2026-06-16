#!/usr/bin/env python3
"""
Dacexy Desktop Agent

A voice-first Windows desktop assistant with:
- speech output and microphone input
- browser and app launching
- desktop control helpers
- file, Excel, email-draft, report, reminder, and research tools
- optional LLM brain through OpenAI Responses API or local Ollama

Run:
    python desktop_agent.py
    python desktop_agent.py --text
    python desktop_agent.py --no-voice
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import getpass
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import textwrap
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    import pyttsx3
except Exception:  # pragma: no cover
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover
    sr = None

try:
    import pyautogui
except Exception:  # pragma: no cover
    pyautogui = None

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

try:
    import websockets
except Exception:  # pragma: no cover
    websockets = None

try:
    import pyperclip
except Exception:  # pragma: no cover
    pyperclip = None

try:
    from PIL import ImageGrab
except Exception:  # pragma: no cover
    ImageGrab = None

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None

try:
    from plyer import notification
except Exception:  # pragma: no cover
    notification = None


APP_NAME = "Dacexy"
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "agent_data"
MEMORY_FILE = DATA_DIR / "memory.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"
REPORTS_DIR = ROOT_DIR / "agent_reports"
SCREENSHOTS_DIR = ROOT_DIR / "agent_screenshots"
CAMPAIGNS_DIR = ROOT_DIR / "agent_campaigns"
OUTBOX_DIR = ROOT_DIR / "agent_outbox"
CREDENTIALS_FILE = DATA_DIR / "credentials.json"
DEFAULT_API_BASE = "https://dacexy-backend-v7ku.onrender.com/api/v1"
TOKEN_FILE = Path.home() / ".dacexy_agent.json"
AGENT_VERSION = "2.0.0-reel-cloud"


COMMON_SITES: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "email": "https://mail.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "slides": "https://slides.google.com",
    "chatgpt": "https://chatgpt.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "facebook": "https://www.facebook.com",
    "whatsapp": "https://web.whatsapp.com",
    "canva": "https://www.canva.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "shopify": "https://www.shopify.com/admin",
    "wordpress": "https://wordpress.com",
    "analytics": "https://analytics.google.com",
    "search console": "https://search.google.com/search-console",
    "google ads": "https://ads.google.com",
    "meta ads": "https://business.facebook.com/adsmanager",
}


COMMON_APPS: dict[str, list[str]] = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "cmd": ["cmd.exe"],
    "terminal": ["wt.exe"],
    "powershell": ["powershell.exe"],
    "explorer": ["explorer.exe"],
    "chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "outlook": ["outlook.exe"],
    "vscode": ["code.cmd"],
    "code": ["code.cmd"],
}


BUSINESS_SKILL_AREAS = {
    "founder": [
        "revenue tracking",
        "profit tracking",
        "investor updates",
        "board reports",
        "competitor monitoring",
        "market trends",
        "goal tracking",
        "risk monitoring",
        "churn tracking",
    ],
    "personal_assistant": [
        "travel planning",
        "meeting scheduling",
        "calendar prep",
        "reminders",
        "expense reporting",
        "document organization",
        "follow-up tracking",
    ],
    "email": [
        "priority detection",
        "categorization",
        "summarization",
        "draft generation",
        "follow-up reminders",
        "newsletter cleanup",
    ],
    "excel": [
        "data cleaning",
        "duplicate removal",
        "formula suggestions",
        "dashboard planning",
        "pivot-ready summaries",
        "trend analysis",
        "forecasting basics",
    ],
    "documents": [
        "proposal drafts",
        "contract outlines",
        "quotation drafts",
        "summaries",
        "formatting",
        "translation prompts",
    ],
    "marketing": [
        "market research",
        "audience research",
        "keyword research",
        "ad draft creation",
        "campaign reporting",
        "lead nurturing",
    ],
    "operations": [
        "inventory alerts",
        "purchase order drafts",
        "supplier comparison",
        "order tracking",
        "route planning",
        "staff scheduling",
    ],
}


def ensure_dirs() -> None:
    for path in (DATA_DIR, REPORTS_DIR, SCREENSHOTS_DIR, CAMPAIGNS_DIR, OUTBOX_DIR):
        path.mkdir(parents=True, exist_ok=True)


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_filename(name: str, suffix: str = ".md") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._ -]+", "", name).strip().replace(" ", "_")
    cleaned = cleaned[:80] or "agent_output"
    if not cleaned.lower().endswith(suffix.lower()):
        cleaned += suffix
    return cleaned


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def normalize_keys(keys: str | list[str]) -> list[str]:
    if isinstance(keys, list):
        return [str(k).lower().strip() for k in keys if str(k).strip()]
    pieces = re.split(r"[,+ ]+", keys)
    return [p.lower().strip() for p in pieces if p.strip()]


def save_access_token(token: str) -> None:
    token = token.strip()
    if not token:
        return
    current = load_json(TOKEN_FILE, {})
    current["access_token"] = token
    current["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    save_json(TOKEN_FILE, current)


def file_to_base64(path: str | Path, max_bytes: int = 5_000_000) -> str:
    file_path = Path(path)
    if not file_path.exists() or file_path.stat().st_size > max_bytes:
        return ""
    return base64.b64encode(file_path.read_bytes()).decode("ascii")


def installed_features() -> list[str]:
    features = [
        "desktop_control",
        "voice3",
        "browser_enterprise",
        "email_enterprise",
        "memory_vector",
        "scheduler",
        "self_healing",
        "plugins",
        "swarm10",
    ]
    if pyautogui or ImageGrab:
        features.append("vision_super")
    if gw:
        features.append("multi_monitor")
    if websockets:
        features.append("cloud_ws")
    if pd:
        features.append("excel")
    if BeautifulSoup:
        features.append("web_research")
    if pyperclip:
        features.append("clipboard")
    return sorted(set(features))


def host_metadata(settings: "Settings") -> dict[str, Any]:
    return {
        "type": "init",
        "version": AGENT_VERSION,
        "platform": f"{platform.system()} {platform.release()}",
        "hostname": socket.gethostname(),
        "features": installed_features(),
        "assistant_name": settings.assistant_name,
        "user": getpass.getuser(),
        "memory_context": "",
    }


@dataclass
class Settings:
    assistant_name: str = APP_NAME
    voice: bool = True
    microphone: bool = True
    safe_mode: bool = True
    wake_words: list[str] = field(default_factory=lambda: ["dacexy", "jarvis", "hey jarvis"])
    listen_timeout: int = 6
    phrase_time_limit: int = 12
    tts_rate: int = 178
    tts_volume: float = 1.0
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    cloud_enabled: bool = True
    api_base: str = DEFAULT_API_BASE
    ws_url: str = ""
    access_token: str = ""
    heartbeat_seconds: int = 30
    auto_reconnect: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        if load_dotenv:
            load_dotenv(ROOT_DIR / ".env")
            load_dotenv()
        stored = load_json(TOKEN_FILE, {})
        stored_token = str(stored.get("access_token") or stored.get("token") or "")
        return cls(
            assistant_name=os.getenv("ASSISTANT_NAME", APP_NAME),
            voice=os.getenv("VOICE_ENABLED", "true").lower() not in {"0", "false", "no"},
            microphone=os.getenv("MICROPHONE_ENABLED", "true").lower() not in {"0", "false", "no"},
            safe_mode=os.getenv("SAFE_MODE", "true").lower() not in {"0", "false", "no"},
            wake_words=[
                w.strip().lower()
                for w in os.getenv("WAKE_WORDS", "dacexy,jarvis,hey jarvis").split(",")
                if w.strip()
            ],
            listen_timeout=int(os.getenv("LISTEN_TIMEOUT", "6")),
            phrase_time_limit=int(os.getenv("PHRASE_TIME_LIMIT", "12")),
            tts_rate=int(os.getenv("TTS_RATE", "178")),
            tts_volume=float(os.getenv("TTS_VOLUME", "1.0")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            cloud_enabled=os.getenv("DACEXY_CLOUD_ENABLED", "true").lower() not in {"0", "false", "no"},
            api_base=os.getenv("DACEXY_API_BASE", DEFAULT_API_BASE).rstrip("/"),
            ws_url=os.getenv("DACEXY_WS_URL", ""),
            access_token=os.getenv("DACEXY_ACCESS_TOKEN", stored_token),
            heartbeat_seconds=int(os.getenv("DACEXY_HEARTBEAT_SECONDS", "30")),
            auto_reconnect=os.getenv("DACEXY_AUTO_RECONNECT", "true").lower() not in {"0", "false", "no"},
        )

    def resolved_ws_url(self) -> str:
        if self.ws_url:
            return self.ws_url
        base = self.api_base.rstrip("/")
        if base.startswith("https://"):
            base = "wss://" + base[len("https://") :]
        elif base.startswith("http://"):
            base = "ws://" + base[len("http://") :]
        return base + "/agent/desktop/ws"


class VoiceIO:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.recognizer = None
        if self.settings.voice and pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", self.settings.tts_rate)
                self.engine.setProperty("volume", self.settings.tts_volume)
            except Exception as exc:
                print(f"[voice] Text-to-speech unavailable: {exc}")
                self.engine = None
        if self.settings.microphone and sr:
            self.recognizer = sr.Recognizer()

    def say(self, text: str, *, speak: bool = True) -> None:
        text = str(text).strip()
        if not text:
            return
        print(f"\n{self.settings.assistant_name}: {text}")
        if speak and self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as exc:
                print(f"[voice] Speech failed: {exc}")

    def listen(self) -> str:
        if not self.recognizer or not sr:
            return input("\nYou: ").strip()
        try:
            with sr.Microphone() as source:
                print("\nListening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(
                    source,
                    timeout=self.settings.listen_timeout,
                    phrase_time_limit=self.settings.phrase_time_limit,
                )
            print("Recognizing...")
            return self.recognizer.recognize_google(audio).strip()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as exc:
            print(f"[voice] Microphone recognition failed: {exc}")
            return input("\nType command: ").strip()

    def confirm(self, prompt: str) -> bool:
        if not self.settings.safe_mode:
            return True
        self.say(prompt + " Say yes or type yes to confirm.", speak=True)
        answer = self.listen().lower().strip()
        return answer in {"yes", "y", "confirm", "do it", "ok", "okay"}


class Memory:
    def __init__(self) -> None:
        ensure_dirs()
        self.data = load_json(
            MEMORY_FILE,
            {"created_at": dt.datetime.now().isoformat(), "history": [], "notes": []},
        )

    def add_history(self, role: str, text: str) -> None:
        self.data.setdefault("history", []).append(
            {"time": dt.datetime.now().isoformat(timespec="seconds"), "role": role, "text": text}
        )
        self.data["history"] = self.data["history"][-80:]
        save_json(MEMORY_FILE, self.data)

    def recent_history(self, limit: int = 10) -> str:
        rows = self.data.get("history", [])[-limit:]
        return "\n".join(f"{row['role']}: {row['text']}" for row in rows if row.get("text"))


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._provider_cache = ""
        self._provider_checked_at = 0.0

    @property
    def provider(self) -> str:
        if self._provider_cache and time.monotonic() - self._provider_checked_at < 30:
            return self._provider_cache
        if self.settings.openai_api_key and requests:
            self._provider_cache = "openai"
            self._provider_checked_at = time.monotonic()
            return self._provider_cache
        if requests and self._ollama_is_available():
            self._provider_cache = "ollama"
            self._provider_checked_at = time.monotonic()
            return self._provider_cache
        self._provider_cache = "none"
        self._provider_checked_at = time.monotonic()
        return self._provider_cache

    def _ollama_is_available(self) -> bool:
        try:
            response = requests.get(f"{self.settings.ollama_url}/api/tags", timeout=1.5)
            return response.status_code == 200
        except Exception:
            return False

    def complete(self, system: str, user: str, *, temperature: float = 0.2, max_tokens: int = 1400) -> str:
        provider = self.provider
        if provider == "openai":
            return self._openai_complete(system, user, temperature=temperature, max_tokens=max_tokens)
        if provider == "ollama":
            return self._ollama_complete(system, user, temperature=temperature)
        return self._fallback_complete(user)

    def _openai_complete(self, system: str, user: str, *, temperature: float, max_tokens: int) -> str:
        if not requests:
            return self._fallback_complete(user)
        payload = {
            "model": self.settings.openai_model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if response.status_code >= 400:
                return f"I tried the AI brain, but the API returned {response.status_code}: {response.text[:250]}"
            data = response.json()
            if data.get("output_text"):
                return str(data["output_text"]).strip()
            chunks: list[str] = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    text = content.get("text") or content.get("output_text")
                    if text:
                        chunks.append(text)
            return "\n".join(chunks).strip() or "I did not receive a text answer from the AI brain."
        except Exception as exc:
            return f"I could not reach the AI brain: {exc}"

    def _ollama_complete(self, system: str, user: str, *, temperature: float) -> str:
        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = requests.post(f"{self.settings.ollama_url}/api/chat", json=payload, timeout=90)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "").strip()
        except Exception as exc:
            return f"I could not reach Ollama: {exc}"

    def _fallback_complete(self, user: str) -> str:
        return (
            "I can do desktop actions, open apps and websites, make reports, analyze Excel files, "
            "draft emails, set local reminders, and summarize files. For deeper conversation and "
            "autonomous planning, add OPENAI_API_KEY to .env or run Ollama locally. "
            f"You asked: {user}"
        )


@dataclass
class ToolResult:
    ok: bool
    message: str
    data: Any = None


class DesktopTools:
    def __init__(self, voice: VoiceIO, llm: LLMClient):
        self.voice = voice
        self.llm = llm

    def open_url(self, url: str) -> ToolResult:
        if not re.match(r"^https?://", url, flags=re.I):
            url = "https://" + url
        webbrowser.open(url)
        return ToolResult(True, f"Opened {url}")

    def open_site(self, name: str) -> ToolResult:
        key = name.strip().lower()
        url = COMMON_SITES.get(key)
        if not url:
            compact = key.replace(" ", "")
            for site_name, site_url in COMMON_SITES.items():
                if compact == site_name.replace(" ", "") or compact in site_name:
                    url = site_url
                    break
        if not url:
            return self.open_url(key)
        webbrowser.open(url)
        return ToolResult(True, f"Opened {name}")

    def web_search(self, query: str, *, engine: str = "google") -> ToolResult:
        query = query.strip()
        if not query:
            return ToolResult(False, "Tell me what to search for.")
        if engine == "youtube":
            url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
        else:
            url = "https://www.google.com/search?q=" + quote_plus(query)
        webbrowser.open(url)
        return ToolResult(True, f"Searching for {query}")

    def fetch_web_page(self, url: str) -> ToolResult:
        if not requests or not BeautifulSoup:
            return ToolResult(False, "Install requests and beautifulsoup4 to read web pages.")
        if not re.match(r"^https?://", url, flags=re.I):
            url = "https://" + url
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": f"{APP_NAME}/1.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            title = soup.title.get_text(" ", strip=True) if soup.title else url
            text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
            return ToolResult(True, title, text[:15000])
        except Exception as exc:
            return ToolResult(False, f"I could not read that page: {exc}")

    def launch_app(self, name: str) -> ToolResult:
        key = name.strip().lower()
        candidates = COMMON_APPS.get(key, [name])
        errors: list[str] = []
        for candidate in candidates:
            try:
                found = shutil.which(candidate) or candidate
                subprocess.Popen([found], shell=False)
                return ToolResult(True, f"Launched {name}")
            except Exception as exc:
                errors.append(str(exc))
        try:
            os.startfile(name)  # type: ignore[attr-defined]
            return ToolResult(True, f"Opened {name}")
        except Exception as exc:
            errors.append(str(exc))
        return ToolResult(False, f"I could not launch {name}. {' | '.join(errors[-2:])}")

    def open_folder(self, path: str) -> ToolResult:
        folder = self.resolve_path(path)
        if not folder.exists():
            return ToolResult(False, f"Folder not found: {folder}")
        os.startfile(str(folder))  # type: ignore[attr-defined]
        return ToolResult(True, f"Opened folder {folder}")

    def resolve_path(self, raw_path: str) -> Path:
        raw_path = raw_path.strip().strip('"').strip("'")
        raw_path = os.path.expandvars(os.path.expanduser(raw_path))
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    def screenshot(self, name: str = "") -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui to take screenshots.")
        filename = safe_filename(name or f"screenshot_{now_stamp()}", ".png")
        path = SCREENSHOTS_DIR / filename
        try:
            image = pyautogui.screenshot()
            image.save(path)
            return ToolResult(True, f"Screenshot saved to {path}", str(path))
        except Exception as exc:
            return ToolResult(False, f"Screenshot failed: {exc}")

    def ocr_screen(self, region: list[int] | None = None) -> ToolResult:
        screenshot = self.screenshot(f"ocr_screen_{now_stamp()}")
        if not screenshot.ok:
            return screenshot
        if not pytesseract:
            return ToolResult(
                False,
                "Screenshot captured, but OCR needs pytesseract and the Tesseract engine installed.",
                {"screenshot": screenshot.data},
            )
        try:
            from PIL import Image  # type: ignore

            image = Image.open(str(screenshot.data))
            if region and len(region) == 4:
                x1, y1, x2, y2 = [int(v) for v in region]
                image = image.crop((x1, y1, x2, y2))
            text = pytesseract.image_to_string(image).strip()
            out = REPORTS_DIR / safe_filename(f"ocr_{now_stamp()}", ".txt")
            out.write_text(text, encoding="utf-8")
            return ToolResult(True, f"OCR text saved to {out}\n\n{text[:1500]}", {"text": text, "path": str(out), "screenshot": screenshot.data})
        except Exception as exc:
            return ToolResult(False, f"OCR failed: {exc}", {"screenshot": screenshot.data})

    def notify(self, title: str, message: str) -> ToolResult:
        title = title or APP_NAME
        message = message or ""
        if notification:
            try:
                notification.notify(title=title, message=message[:250], timeout=5)
            except Exception:
                pass
        return ToolResult(True, f"{title}: {message}")

    def clipboard_set(self, text: str) -> ToolResult:
        if not pyperclip:
            return ToolResult(False, "Install pyperclip for clipboard support.")
        pyperclip.copy(text)
        return ToolResult(True, "Copied text to clipboard.")

    def clipboard_get(self) -> ToolResult:
        if not pyperclip:
            return ToolResult(False, "Install pyperclip for clipboard support.")
        return ToolResult(True, pyperclip.paste())

    def paste_text(self, text: str) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui to paste text.")
        if pyperclip:
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return ToolResult(True, "Pasted the text.")
        return self.type_text(text)

    def click(self, x: int | None = None, y: int | None = None, clicks: int = 1, button: str = "left") -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui for mouse control.")
        if x is None or y is None:
            pyautogui.click(clicks=clicks, button=button)
        else:
            pyautogui.click(int(x), int(y), clicks=int(clicks), button=button)
        return ToolResult(True, "Clicked.")

    def move_mouse(self, x: int, y: int, duration: float = 0.2) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui for mouse control.")
        pyautogui.moveTo(int(x), int(y), duration=float(duration))
        return ToolResult(True, f"Moved mouse to {x}, {y}.")

    def scroll(self, amount: int = -700) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui for scroll control.")
        pyautogui.scroll(int(amount))
        return ToolResult(True, f"Scrolled {amount}.")

    def list_windows(self) -> ToolResult:
        if not gw:
            return ToolResult(False, "Install pygetwindow to list windows.")
        windows = []
        for win in gw.getAllWindows():
            title = (win.title or "").strip()
            if title:
                windows.append({"title": title, "left": win.left, "top": win.top, "width": win.width, "height": win.height})
        lines = ["Open windows:"]
        for item in windows[:30]:
            lines.append(f"- {item['title']}")
        return ToolResult(True, "\n".join(lines), windows)

    def focus_window(self, keyword: str) -> ToolResult:
        if not gw:
            return ToolResult(False, "Install pygetwindow to focus windows.")
        keyword = keyword.lower().strip()
        for win in gw.getAllWindows():
            title = (win.title or "").lower()
            if keyword and keyword in title:
                try:
                    win.activate()
                    return ToolResult(True, f"Focused window: {win.title}")
                except Exception as exc:
                    return ToolResult(False, f"Could not focus that window: {exc}")
        return ToolResult(False, f"No open window matched: {keyword}")

    def type_text(self, text: str, interval: float = 0.01) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui to type into apps.")
        pyautogui.write(text, interval=interval)
        return ToolResult(True, "Typed the text.")

    def press(self, key: str) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui to press keys.")
        pyautogui.press(key)
        return ToolResult(True, f"Pressed {key}.")

    def hotkey(self, keys: str | list[str]) -> ToolResult:
        if not pyautogui:
            return ToolResult(False, "Install pyautogui to use hotkeys.")
        normalized = normalize_keys(keys)
        if not normalized:
            return ToolResult(False, "No hotkey keys were provided.")
        pyautogui.hotkey(*normalized)
        return ToolResult(True, "Pressed " + " + ".join(normalized))

    def system_status(self) -> ToolResult:
        if not psutil:
            return ToolResult(False, "Install psutil for system status.")
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home()))
        battery = psutil.sensors_battery()
        lines = [
            f"CPU: {cpu:.0f}%",
            f"Memory: {memory.percent:.0f}% used ({memory.used / 1e9:.1f} GB of {memory.total / 1e9:.1f} GB)",
            f"Disk: {disk.percent:.0f}% used ({disk.free / 1e9:.1f} GB free)",
        ]
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery"
            lines.append(f"Battery: {battery.percent:.0f}% {plugged}")
        return ToolResult(True, "\n".join(lines))

    def list_processes(self, limit: int = 10) -> ToolResult:
        if not psutil:
            return ToolResult(False, "Install psutil to inspect processes.")
        rows = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                rows.append(proc.info)
            except Exception:
                pass
        rows.sort(key=lambda row: (row.get("memory_percent") or 0), reverse=True)
        lines = ["Top processes by memory:"]
        for row in rows[:limit]:
            lines.append(
                f"{row.get('pid'):>6}  {row.get('name'):<28}  memory {row.get('memory_percent', 0):.1f}%"
            )
        return ToolResult(True, "\n".join(lines), rows[:limit])

    def read_file_text(self, path: str, max_chars: int = 20000) -> ToolResult:
        file_path = self.resolve_path(path)
        if not file_path.exists():
            return ToolResult(False, f"File not found: {file_path}")
        suffix = file_path.suffix.lower()
        try:
            if suffix in {".txt", ".md", ".py", ".json", ".csv", ".log", ".html", ".xml"}:
                return ToolResult(True, f"Read {file_path.name}", file_path.read_text(encoding="utf-8", errors="ignore")[:max_chars])
            if suffix in {".xlsx", ".xls"}:
                if not pd:
                    return ToolResult(False, "Install pandas and openpyxl to read Excel files.")
                frames = pd.read_excel(file_path, sheet_name=None)
                chunks = []
                for sheet, frame in frames.items():
                    chunks.append(f"Sheet: {sheet}\n{frame.head(80).to_string(index=False)}")
                return ToolResult(True, f"Read {file_path.name}", "\n\n".join(chunks)[:max_chars])
            if suffix == ".docx":
                try:
                    import docx  # type: ignore
                except Exception:
                    return ToolResult(False, "Install python-docx to read Word documents.")
                document = docx.Document(str(file_path))
                text = "\n".join(p.text for p in document.paragraphs)
                return ToolResult(True, f"Read {file_path.name}", text[:max_chars])
            if suffix == ".pdf":
                try:
                    import pypdf  # type: ignore
                except Exception:
                    return ToolResult(False, "Install pypdf to read PDF files.")
                reader = pypdf.PdfReader(str(file_path))
                text = "\n".join(page.extract_text() or "" for page in reader.pages[:20])
                return ToolResult(True, f"Read {file_path.name}", text[:max_chars])
            return ToolResult(False, f"I do not know how to read {suffix} files yet.")
        except Exception as exc:
            return ToolResult(False, f"File read failed: {exc}")

    def write_file_text(self, path: str, content: str, overwrite: bool = False) -> ToolResult:
        file_path = self.resolve_path(path)
        if file_path.exists() and not overwrite:
            return ToolResult(False, f"File already exists: {file_path}. Use overwrite=true to replace it.")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Wrote file {file_path}", str(file_path))
        except Exception as exc:
            return ToolResult(False, f"File write failed: {exc}")

    def organize_folder(self, folder: str = "", dry_run: bool = False) -> ToolResult:
        base = self.resolve_path(folder) if folder else Path.home() / "Desktop"
        if not base.exists() or not base.is_dir():
            return ToolResult(False, f"Folder not found: {base}")
        buckets = {
            "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"},
            "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".ppt", ".pptx"},
            "Spreadsheets": {".xls", ".xlsx", ".csv"},
            "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
            "Installers": {".exe", ".msi"},
            "Videos": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
            "Audio": {".mp3", ".wav", ".m4a", ".aac"},
            "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sql"},
        }
        moves = []
        for item in base.iterdir():
            if item.is_dir() or item.name.startswith("."):
                continue
            bucket = "Other"
            for name, exts in buckets.items():
                if item.suffix.lower() in exts:
                    bucket = name
                    break
            dest_dir = base / bucket
            dest = dest_dir / item.name
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{item.stem}_{counter}{item.suffix}"
                counter += 1
            moves.append((item, dest))
        if dry_run:
            lines = [f"Would organize {len(moves)} files in {base}:"]
            lines.extend(f"- {src.name} -> {dst.parent.name}/{dst.name}" for src, dst in moves[:80])
            return ToolResult(True, "\n".join(lines), [{"src": str(s), "dst": str(d)} for s, d in moves])
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        return ToolResult(True, f"Organized {len(moves)} files in {base}.", [{"src": str(s), "dst": str(d)} for s, d in moves])

    def create_campaign(
        self,
        name: str,
        subject: str,
        body: str,
        recipients: list[str] | None = None,
        html: bool = True,
        tags: list[str] | None = None,
        scheduled_at: str | None = None,
    ) -> ToolResult:
        campaign_id = str(uuid.uuid4())
        campaign = {
            "campaign_id": campaign_id,
            "name": name or f"Campaign {campaign_id[:8]}",
            "subject": subject,
            "body": body,
            "recipients": recipients or [],
            "html": html,
            "tags": tags or [],
            "scheduled_at": scheduled_at,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "status": "draft",
        }
        path = CAMPAIGNS_DIR / f"{campaign_id}.json"
        save_json(path, campaign)
        return ToolResult(True, f"Campaign draft created with {len(campaign['recipients'])} recipients: {campaign_id}", {"campaign_id": campaign_id, "path": str(path)})

    def send_campaign(self, campaign_id: str) -> ToolResult:
        path = CAMPAIGNS_DIR / f"{campaign_id}.json"
        campaign = load_json(path, None)
        if not campaign:
            return ToolResult(False, f"Campaign not found: {campaign_id}")
        campaign["status"] = "queued_needs_approval"
        campaign["queued_at"] = dt.datetime.now().isoformat(timespec="seconds")
        save_json(path, campaign)
        out = OUTBOX_DIR / f"campaign_{campaign_id}.md"
        out.write_text(
            f"# Campaign Ready For Approval\n\nSubject: {campaign.get('subject','')}\n"
            f"Recipients: {len(campaign.get('recipients', []))}\n\n{campaign.get('body','')}\n",
            encoding="utf-8",
        )
        return ToolResult(
            True,
            f"Campaign {campaign_id} is queued as a draft for approval. I did not mass-send it automatically.",
            {"campaign_id": campaign_id, "outbox": str(out)},
        )

    def whatsapp_bulk(self, contacts: list[str], message: str, delay: float = 3.5) -> ToolResult:
        job_id = str(uuid.uuid4())
        path = OUTBOX_DIR / f"whatsapp_bulk_{job_id}.md"
        path.write_text(
            "# WhatsApp Bulk Message Draft\n\n"
            f"Contacts: {len(contacts)}\nDelay: {delay}\n\nMessage:\n{message}\n\n"
            "This was saved as a draft. Review recipient consent and send manually or connect an approved WhatsApp Business workflow.\n",
            encoding="utf-8",
        )
        webbrowser.open("https://web.whatsapp.com")
        return ToolResult(True, f"WhatsApp draft saved to {path}. Opened WhatsApp Web for review.", {"job_id": job_id, "path": str(path)})

    def social_post_draft(self, platform_name: str, text: str = "", caption: str = "", media: str = "", **_: Any) -> ToolResult:
        platform_name = platform_name.lower().strip() or "social"
        post_text = caption or text
        out = OUTBOX_DIR / safe_filename(f"{platform_name}_post_{now_stamp()}", ".md")
        out.write_text(
            f"# {platform_name.title()} Post Draft\n\n"
            f"Media: {media}\n\n"
            f"{post_text}\n",
            encoding="utf-8",
        )
        url = COMMON_SITES.get(platform_name)
        if url:
            webbrowser.open(url)
        return ToolResult(True, f"{platform_name.title()} post draft saved to {out}. I opened the platform for review.", str(out))

    def health_check(self) -> ToolResult:
        status = self.system_status()
        health = {
            "ok": True,
            "version": AGENT_VERSION,
            "features": installed_features(),
            "time": dt.datetime.now().isoformat(timespec="seconds"),
            "brain": self.llm.provider,
            "voice": bool(self.voice.engine),
            "microphone": bool(self.voice.recognizer),
            "system": status.message if status.ok else status.message,
        }
        return ToolResult(True, "Health check complete.", health)

    def summarize_file(self, path: str) -> ToolResult:
        read = self.read_file_text(path)
        if not read.ok:
            return read
        if self.llm.provider == "none":
            summary = heuristic_summary(str(read.data))
        else:
            system = "You summarize documents for a busy founder. Be concise, specific, and action-oriented."
            user = (
                "Summarize this file. Return: key points, important numbers/dates, risks, and next actions.\n\n"
                + str(read.data)[:14000]
            )
            summary = self.llm.complete(system, user, temperature=0.1, max_tokens=1400)
        filename = safe_filename(f"summary_{Path(path).stem}_{now_stamp()}", ".md")
        out = REPORTS_DIR / filename
        out.write_text(f"# Summary: {Path(path).name}\n\n{summary}\n", encoding="utf-8")
        return ToolResult(True, f"Summary saved to {out}\n\n{summary}", str(out))

    def process_invoices(self, folder: str = "") -> ToolResult:
        base = self.resolve_path(folder) if folder else Path.home() / "Downloads"
        if not base.exists() or not base.is_dir():
            return ToolResult(False, f"Invoice folder not found: {base}")
        pdfs = list(base.glob("*.pdf"))[:50]
        if not pdfs:
            return ToolResult(False, f"No PDF invoices found in {base}")
        rows = []
        for pdf in pdfs:
            read = self.read_file_text(str(pdf), max_chars=12000)
            text = str(read.data or "") if read.ok else ""
            amounts = re.findall(r"(?:rs\.?|inr|\$|usd)?\s?\d[\d,]*(?:\.\d{1,2})?", text, flags=re.I)
            dates = re.findall(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text)
            vendor = ""
            for line in text.splitlines()[:20]:
                line = line.strip()
                if 3 < len(line) < 80 and not re.search(r"invoice|tax|date|total", line, flags=re.I):
                    vendor = line
                    break
            rows.append(
                {
                    "file": pdf.name,
                    "vendor_guess": vendor,
                    "dates": dates[:3],
                    "amounts": amounts[-5:],
                    "status": "needs_review",
                }
            )
        lines = ["# Invoice Processing Queue", "", f"Folder: {base}", f"PDFs scanned: {len(rows)}", ""]
        for idx, row in enumerate(rows, 1):
            lines.append(f"## {idx}. {row['file']}")
            lines.append(f"- Vendor guess: {row['vendor_guess'] or 'Unknown'}")
            lines.append(f"- Dates found: {', '.join(row['dates']) or 'None'}")
            lines.append(f"- Amounts found: {', '.join(row['amounts']) or 'None'}")
            lines.append("- Status: needs review before payment")
            lines.append("")
        lines.append("## Next Actions")
        lines.append("- Review each invoice, confirm vendor, amount, due date, GST/tax details, and approval owner.")
        lines.append("- Ask me to draft payment reminder emails or a vendor payment summary.")
        out = REPORTS_DIR / safe_filename(f"invoice_queue_{now_stamp()}", ".md")
        out.write_text("\n".join(lines), encoding="utf-8")
        return ToolResult(True, f"Invoice queue saved to {out}", {"path": str(out), "items": rows})

    def analyze_excel(self, path: str) -> ToolResult:
        if not pd:
            return ToolResult(False, "Install pandas and openpyxl to analyze Excel files.")
        file_path = self.resolve_path(path)
        if not file_path.exists():
            return ToolResult(False, f"File not found: {file_path}")
        try:
            frames = pd.read_excel(file_path, sheet_name=None)
            lines = [f"# Excel Analysis: {file_path.name}", ""]
            for sheet, frame in frames.items():
                lines.append(f"## Sheet: {sheet}")
                lines.append(f"Rows: {len(frame):,}")
                lines.append(f"Columns: {len(frame.columns):,}")
                lines.append("Columns: " + ", ".join(map(str, frame.columns[:30])))
                duplicate_count = int(frame.duplicated().sum())
                lines.append(f"Duplicate rows: {duplicate_count:,}")
                missing = frame.isna().sum().sort_values(ascending=False)
                missing = missing[missing > 0].head(10)
                if len(missing):
                    lines.append("Missing values:")
                    for col, count in missing.items():
                        lines.append(f"- {col}: {int(count):,}")
                numeric = frame.select_dtypes(include="number")
                if len(numeric.columns):
                    lines.append("Numeric summary:")
                    lines.append(numeric.describe().round(2).to_string())
                    money_cols = [
                        c
                        for c in numeric.columns
                        if any(word in str(c).lower() for word in ["revenue", "sales", "profit", "amount", "price", "total"])
                    ]
                    for col in money_cols[:8]:
                        lines.append(f"Total {col}: {numeric[col].sum():,.2f}")
                lines.append("")
            report = "\n".join(lines)
            out = REPORTS_DIR / safe_filename(f"excel_analysis_{file_path.stem}_{now_stamp()}", ".md")
            out.write_text(report, encoding="utf-8")
            return ToolResult(True, f"Excel analysis saved to {out}\n\n{report[:2500]}", str(out))
        except Exception as exc:
            return ToolResult(False, f"Excel analysis failed: {exc}")

    def clean_excel(self, path: str, output_path: str = "") -> ToolResult:
        if not pd:
            return ToolResult(False, "Install pandas and openpyxl to clean Excel files.")
        file_path = self.resolve_path(path)
        if not file_path.exists():
            return ToolResult(False, f"File not found: {file_path}")
        try:
            frames = pd.read_excel(file_path, sheet_name=None)
            cleaned: dict[str, Any] = {}
            report_lines = [f"# Cleaning Report: {file_path.name}", ""]
            for sheet, frame in frames.items():
                before = len(frame)
                frame = frame.drop_duplicates()
                after_dupes = len(frame)
                frame.columns = [str(c).strip() for c in frame.columns]
                for col in frame.select_dtypes(include="object").columns:
                    frame[col] = frame[col].astype(str).str.strip().replace({"nan": ""})
                cleaned[sheet] = frame
                report_lines.append(f"## {sheet}")
                report_lines.append(f"Rows before: {before:,}")
                report_lines.append(f"Rows after duplicate removal: {after_dupes:,}")
                report_lines.append(f"Removed duplicates: {before - after_dupes:,}")
                report_lines.append("")
            out = self.resolve_path(output_path) if output_path else file_path.with_name(file_path.stem + "_cleaned.xlsx")
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                for sheet, frame in cleaned.items():
                    frame.to_excel(writer, sheet_name=str(sheet)[:31], index=False)
            report = "\n".join(report_lines)
            report_path = REPORTS_DIR / safe_filename(f"cleaning_report_{file_path.stem}_{now_stamp()}", ".md")
            report_path.write_text(report, encoding="utf-8")
            return ToolResult(True, f"Cleaned Excel saved to {out}. Report saved to {report_path}", str(out))
        except Exception as exc:
            return ToolResult(False, f"Excel cleaning failed: {exc}")

    def draft_email(self, recipient: str = "", subject: str = "", points: str = "", tone: str = "professional") -> ToolResult:
        if self.llm.provider == "none":
            draft = fallback_email(recipient=recipient, subject=subject, points=points, tone=tone)
        else:
            system = "You write clear, useful business emails. Do not invent facts."
            user = f"Write a {tone} email.\nRecipient: {recipient}\nSubject: {subject}\nPoints:\n{points}"
            draft = self.llm.complete(system, user, temperature=0.3, max_tokens=1000)
        out = REPORTS_DIR / safe_filename(f"email_draft_{now_stamp()}", ".md")
        out.write_text(f"# Email Draft\n\nTo: {recipient}\nSubject: {subject}\n\n{draft}\n", encoding="utf-8")
        if recipient:
            mailto = f"mailto:{recipient}?subject={quote_plus(subject)}&body={quote_plus(draft)}"
            webbrowser.open(mailto)
        return ToolResult(True, f"Email draft saved to {out}\n\n{draft}", str(out))

    def create_report(self, title: str, instructions: str = "") -> ToolResult:
        title = title.strip() or "Business Report"
        if self.llm.provider == "none":
            report = fallback_report(title, instructions)
        else:
            system = (
                "You are a practical executive assistant. Create board-ready, founder-friendly reports. "
                "Use clear headings, numbers to request from the user if missing, assumptions, risks, and next actions."
            )
            user = f"Create a useful report titled: {title}\nInstructions/context:\n{instructions}"
            report = self.llm.complete(system, user, temperature=0.25, max_tokens=2200)
        out = REPORTS_DIR / safe_filename(f"{title}_{now_stamp()}", ".md")
        out.write_text(f"# {title}\n\n{report}\n", encoding="utf-8")
        return ToolResult(True, f"Report saved to {out}\n\n{report[:2500]}", str(out))

    def create_business_brief(self, topic: str, area: str = "founder") -> ToolResult:
        topic = topic.strip() or "my business"
        area = area.strip().lower() or "founder"
        skills = BUSINESS_SKILL_AREAS.get(area, BUSINESS_SKILL_AREAS["founder"])
        if self.llm.provider == "none":
            brief = fallback_business_brief(topic, area, skills)
        else:
            system = (
                "You are an AI chief of staff for a founder. Produce concrete operating plans, not vague advice. "
                "When data is missing, list exactly what data is needed."
            )
            user = (
                f"Business/topic: {topic}\n"
                f"Focus area: {area}\n"
                f"Relevant capabilities: {', '.join(skills)}\n\n"
                "Create a brief with: objective, current assumptions, exact tasks the agent can do now, "
                "data/access needed, automations to build, KPIs to track, and a 7-day execution plan."
            )
            brief = self.llm.complete(system, user, temperature=0.25, max_tokens=2400)
        out = REPORTS_DIR / safe_filename(f"{area}_brief_{topic}_{now_stamp()}", ".md")
        out.write_text(f"# {area.title()} Brief: {topic}\n\n{brief}\n", encoding="utf-8")
        return ToolResult(True, f"Brief saved to {out}\n\n{brief[:2500]}", str(out))

    def summarize_text(self, text: str) -> ToolResult:
        if self.llm.provider == "none":
            summary = heuristic_summary(text)
        else:
            system = "Summarize business text for a busy user. Extract actions, names, dates, numbers, and risks."
            summary = self.llm.complete(system, text[:16000], temperature=0.1, max_tokens=1200)
        return ToolResult(True, summary)

    def categorize_email_text(self, text: str) -> ToolResult:
        lowered = text.lower()
        categories = []
        rules = {
            "urgent": ["urgent", "asap", "immediately", "today", "deadline", "overdue"],
            "lead": ["pricing", "quote", "demo", "interested", "proposal", "buy", "purchase"],
            "finance": ["invoice", "payment", "receipt", "gst", "tax", "refund", "billing"],
            "support": ["issue", "problem", "not working", "complaint", "bug", "help"],
            "newsletter": ["unsubscribe", "newsletter", "weekly digest", "promotion"],
            "meeting": ["meeting", "calendar", "schedule", "call", "zoom", "teams"],
        }
        for category, words in rules.items():
            if any(word in lowered for word in words):
                categories.append(category)
        if not categories:
            categories = ["general"]
        if self.llm.provider == "none":
            summary = (
                f"Categories detected: {', '.join(categories)}\n\n"
                + heuristic_summary(text, title="Email Summary")
            )
        else:
            summary = self.llm.complete(
                "Classify and summarize this email. Be concise.",
                f"Categories detected: {', '.join(categories)}\n\nEmail:\n{text[:10000]}",
                temperature=0.1,
                max_tokens=800,
            )
        return ToolResult(True, summary, categories)

    def add_reminder(self, text: str, due_text: str) -> ToolResult:
        due = parse_due_time(due_text)
        if not due:
            return ToolResult(False, "I could not understand the reminder time. Try 'in 10 minutes' or '2026-06-16 18:30'.")
        reminders = load_json(REMINDERS_FILE, [])
        reminders.append(
            {
                "id": now_stamp(),
                "text": text.strip(),
                "due": due.isoformat(timespec="seconds"),
                "done": False,
            }
        )
        save_json(REMINDERS_FILE, reminders)
        return ToolResult(True, f"Reminder set for {due.strftime('%Y-%m-%d %H:%M')}: {text}")

    def list_reminders(self) -> ToolResult:
        reminders = load_json(REMINDERS_FILE, [])
        pending = [r for r in reminders if not r.get("done")]
        if not pending:
            return ToolResult(True, "No pending reminders.")
        lines = ["Pending reminders:"]
        for item in pending[:20]:
            lines.append(f"- {item.get('due')}: {item.get('text')}")
        return ToolResult(True, "\n".join(lines), pending)


def parse_due_time(text: str) -> dt.datetime | None:
    text = text.strip().lower()
    now = dt.datetime.now()
    match = re.search(r"in\s+(\d+)\s*(minute|minutes|min|hour|hours|day|days)", text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("min"):
            return now + dt.timedelta(minutes=amount)
        if unit.startswith("hour"):
            return now + dt.timedelta(hours=amount)
        return now + dt.timedelta(days=amount)
    if text.startswith("tomorrow"):
        base = now + dt.timedelta(days=1)
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or "0")
            ampm = time_match.group(3)
            if ampm == "pm" and hour < 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
            return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return base.replace(hour=9, minute=0, second=0, microsecond=0)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return dt.datetime.strptime(text, fmt)
        except Exception:
            pass
    return None


def split_points(text: str, limit: int = 6) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []
    pieces = re.split(r"(?:;|\n|\. )", cleaned)
    points = [p.strip(" .-") for p in pieces if p.strip(" .-")]
    return points[:limit]


def heuristic_summary(text: str, title: str = "Summary") -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return f"## {title}\n\nNo readable text was found."

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
    first_sentences = sentences[:4]
    important = []
    action_words = ["need", "must", "should", "follow", "call", "send", "pay", "deadline", "urgent", "risk", "issue"]
    for sentence in sentences:
        lower = sentence.lower()
        has_number = bool(re.search(r"\d", sentence))
        has_action = any(word in lower for word in action_words)
        if has_number or has_action:
            important.append(sentence)
        if len(important) >= 8:
            break

    dates = re.findall(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        text,
        flags=re.I,
    )
    money = re.findall(r"(?:rs\.?|inr|\$|usd)?\s?\d[\d,]*(?:\.\d+)?\s?(?:crore|lakh|k|m|million|billion)?", text, flags=re.I)

    lines = [f"## {title}", ""]
    lines.append("### Key Points")
    for sentence in (first_sentences or sentences[:3])[:5]:
        lines.append(f"- {sentence}")
    if important:
        lines.append("")
        lines.append("### Numbers, Risks, Or Actions Detected")
        for sentence in important:
            lines.append(f"- {sentence}")
    if dates or money:
        lines.append("")
        lines.append("### Extracted Signals")
        if dates:
            lines.append("- Dates: " + ", ".join(dict.fromkeys(dates[:12])))
        if money:
            lines.append("- Numbers/money: " + ", ".join(dict.fromkeys(money[:12])))
    lines.append("")
    lines.append("### Suggested Next Actions")
    lines.append("- Confirm the important numbers and deadlines.")
    lines.append("- Turn each action item into an owner plus due date.")
    lines.append("- Ask me to draft the reply, report, checklist, or follow-up message.")
    return "\n".join(lines)


def fallback_email(recipient: str, subject: str, points: str, tone: str = "professional") -> str:
    bullets = split_points(points)
    greeting = "Hi"
    if recipient:
        name = recipient.split("@", 1)[0].split(".")[0].replace("_", " ").title()
        greeting = f"Hi {name}"
    body_lines = [
        f"Subject: {subject or 'Following up'}",
        "",
        f"{greeting},",
        "",
    ]
    if bullets:
        body_lines.append("I wanted to reach out regarding the following points:")
        body_lines.append("")
        for point in bullets:
            body_lines.append(f"- {point}")
    else:
        body_lines.append(f"I wanted to follow up regarding {subject or 'our discussion'}.")
    body_lines.extend(
        [
            "",
            "Please let me know your thoughts and the best next step.",
            "",
            "Best regards,",
            "[Your Name]",
        ]
    )
    if tone.lower() in {"friendly", "warm"}:
        body_lines[-4] = "Would love to hear your thoughts when you get a moment."
    return "\n".join(body_lines)


def fallback_report(title: str, instructions: str) -> str:
    points = split_points(instructions, limit=8)
    lines = [
        "## Executive Summary",
        f"This report is a working draft for: {title}. It is ready for you to fill with live company data.",
        "",
        "## Context Captured",
    ]
    if points:
        for point in points:
            lines.append(f"- {point}")
    else:
        lines.append("- No detailed context was provided yet.")
    lines.extend(
        [
            "",
            "## KPIs To Track",
            "- Revenue: daily, weekly, monthly, and by channel.",
            "- Gross profit and net profit.",
            "- Cash in, cash out, and runway.",
            "- Leads, conversion rate, repeat purchase rate, and churn.",
            "- Top products, top customers, and highest-cost operations.",
            "",
            "## Data Needed",
            "- Sales/export file from CRM, POS, marketplace, or payment gateway.",
            "- Expense file or accounting export.",
            "- Customer list with acquisition date, last order date, and total spend.",
            "- Marketing spend by channel.",
            "- Team or vendor task status if productivity tracking is needed.",
            "",
            "## Risks And Watch Items",
            "- Missing or inconsistent data can hide profit leaks.",
            "- Revenue without margin can create false confidence.",
            "- Manual follow-ups can cause lost leads, late payments, and customer churn.",
            "",
            "## Next 7 Days",
            "- Day 1: Collect revenue, expense, lead, and customer files.",
            "- Day 2: Clean duplicates and standardize columns.",
            "- Day 3: Build KPI summary for revenue, profit, churn, and open follow-ups.",
            "- Day 4: Identify top risks and delayed actions.",
            "- Day 5: Draft investor, board, or management update.",
            "- Day 6: Create repeatable reminders and report templates.",
            "- Day 7: Review results and decide automations to connect next.",
        ]
    )
    return "\n".join(lines)


def fallback_business_brief(topic: str, area: str, skills: list[str]) -> str:
    lines = [
        "## Objective",
        f"Build an operating assistant workflow for: {topic}.",
        "",
        "## Focus Area",
        area.replace("_", " ").title(),
        "",
        "## Tasks The Agent Can Do Now",
    ]
    for skill in skills:
        lines.append(f"- Prepare, analyze, or draft work for {skill}.")
    lines.extend(
        [
            "",
            "## Access Or Data Needed",
            "- Relevant Excel/CSV exports.",
            "- Website, Gmail, Calendar, CRM, accounting, or marketplace access opened by the user.",
            "- Clear approval before sending, submitting, purchasing, deleting, or booking anything.",
            "",
            "## Automations To Build Next",
            "- Daily KPI report from your business data.",
            "- Priority inbox summary with follow-up reminders.",
            "- Weekly competitor and market trend research brief.",
            "- Revenue, profit, churn, inventory, and cash-flow monitoring.",
            "- Draft generation for emails, proposals, reports, and meeting notes.",
            "",
            "## KPIs",
            "- Revenue, profit, cash flow, conversion rate, churn, customer support backlog, and open follow-ups.",
            "",
            "## 7-Day Execution Plan",
            "- Day 1: Connect or export the most important data source.",
            "- Day 2: Clean the data and remove duplicates.",
            "- Day 3: Create the first KPI report.",
            "- Day 4: Add email and follow-up workflow.",
            "- Day 5: Add competitor or market research workflow.",
            "- Day 6: Add reminders and recurring review checklist.",
            "- Day 7: Review accuracy and decide what can safely run autonomously.",
        ]
    )
    return "\n".join(lines)


class ReminderWatcher(threading.Thread):
    def __init__(self, voice: VoiceIO):
        super().__init__(daemon=True)
        self.voice = voice
        self.running = True

    def run(self) -> None:
        while self.running:
            try:
                reminders = load_json(REMINDERS_FILE, [])
                changed = False
                now = dt.datetime.now()
                for reminder in reminders:
                    if reminder.get("done"):
                        continue
                    due_text = reminder.get("due")
                    if not due_text:
                        continue
                    due = dt.datetime.fromisoformat(due_text)
                    if due <= now:
                        reminder["done"] = True
                        changed = True
                        self.voice.say(f"Reminder: {reminder.get('text')}")
                if changed:
                    save_json(REMINDERS_FILE, reminders)
            except Exception:
                pass
            time.sleep(15)


class CommandRouter:
    def __init__(self, tools: DesktopTools, voice: VoiceIO):
        self.tools = tools
        self.voice = voice

    def route(self, command: str) -> ToolResult | None:
        original = command.strip()
        text = original.lower().strip()
        if not text:
            return ToolResult(False, "I did not catch that.")

        if text in {"help", "what can you do", "show commands", "commands"}:
            return ToolResult(True, capabilities_text())

        if text in {"status", "system status", "how is my pc", "pc status"}:
            return self.tools.system_status()

        if text in {"volume up", "increase volume"}:
            return self.tools.press("volumeup")

        if text in {"volume down", "decrease volume"}:
            return self.tools.press("volumedown")

        if text in {"mute", "mute volume"}:
            return self.tools.press("volumemute")

        if text in {"health", "health check", "agent health"}:
            return self.tools.health_check()

        if text in {"skills", "list skills", "agent skills"}:
            return ToolResult(True, capabilities_text(), installed_features())

        match = re.match(r"^(set|save)\s+(cloud\s+)?token\s+(.+)$", original, flags=re.I | re.S)
        if match:
            save_access_token(match.group(3).strip())
            return ToolResult(True, f"Cloud token saved to {TOKEN_FILE}. Restart the agent or run with --cloud to connect.")

        if "list reminders" in text or "show reminders" in text:
            return self.tools.list_reminders()

        if "screenshot" in text or "screen shot" in text:
            name = re.sub(r".*screen\s*shot|.*screenshot", "", original, flags=re.I).strip()
            return self.tools.screenshot(name)

        if text in {"ocr screen", "read screen", "scan screen"}:
            return self.tools.ocr_screen()

        if text in {"list windows", "show windows", "open windows"}:
            return self.tools.list_windows()

        match = re.match(r"^(focus|switch to)\s+(.+)$", original, flags=re.I)
        if match:
            return self.tools.focus_window(match.group(2))

        if "organize my desktop" in text or "organise my desktop" in text:
            if self.voice.confirm("This will move desktop files into folders by type."):
                return self.tools.organize_folder(str(Path.home() / "Desktop"))
            return ToolResult(False, "Desktop organization cancelled.")

        match = re.match(r"^(organize|organise)\s+folder\s+(.+)$", original, flags=re.I)
        if match:
            if self.voice.confirm("This will move files into folders by type."):
                return self.tools.organize_folder(match.group(2))
            return ToolResult(False, "Folder organization cancelled.")

        match = re.match(r"^(copy|clipboard)\s+(.+)$", original, flags=re.I | re.S)
        if match:
            return self.tools.clipboard_set(match.group(2))

        match = re.match(r"^paste\s+(.+)$", original, flags=re.I | re.S)
        if match:
            if self.voice.confirm("This will paste into the focused app."):
                return self.tools.paste_text(match.group(1))
            return ToolResult(False, "Paste cancelled.")

        match = re.match(r"^(open|go to|launch website)\s+(.+)$", text)
        if match:
            target = match.group(2).strip()
            if "." in target and " " not in target:
                return self.tools.open_url(target)
            return self.tools.open_site(target)

        match = re.match(r"^(launch|start|run)\s+(.+)$", text)
        if match:
            return self.tools.launch_app(match.group(2))

        match = re.match(r"^(search|google|look up|find)\s+(.+)$", text)
        if match:
            return self.tools.web_search(match.group(2), engine="google")

        match = re.match(r"^(youtube search|search youtube for|find on youtube)\s+(.+)$", text)
        if match:
            return self.tools.web_search(match.group(2), engine="youtube")

        match = re.match(r"^(type|write)\s+(.+)$", original, flags=re.I | re.S)
        if match:
            if self.voice.confirm("This will type into the currently focused app."):
                return self.tools.type_text(match.group(2))
            return ToolResult(False, "Typing cancelled.")

        match = re.match(r"^(press)\s+(.+)$", text)
        if match:
            return self.tools.press(match.group(2).strip())

        match = re.match(r"^(hotkey|shortcut)\s+(.+)$", original, flags=re.I)
        if match:
            if self.voice.confirm("This will press a keyboard shortcut in the focused app."):
                return self.tools.hotkey(match.group(2))
            return ToolResult(False, "Hotkey cancelled.")

        match = re.match(r"^remind me to\s+(.+?)\s+(in .+|tomorrow.*|\d{4}-\d{2}-\d{2}.+)$", text)
        if match:
            return self.tools.add_reminder(match.group(1), match.group(2))

        file_path = extract_path(original)
        if file_path and any(word in text for word in ["summarize file", "summarise file", "summarize document", "summarise document"]):
            return self.tools.summarize_file(file_path)

        if file_path and any(word in text for word in ["analyze excel", "analyse excel", "excel analysis"]):
            return self.tools.analyze_excel(file_path)

        if file_path and any(word in text for word in ["clean excel", "remove duplicates"]):
            return self.tools.clean_excel(file_path)

        match = re.match(r"^(draft|write)\s+(an\s+)?email\s*(.*)$", original, flags=re.I | re.S)
        if match:
            rest = match.group(3).strip()
            recipient = find_email(rest)
            subject = find_subject(rest) or "Following up"
            points = find_email_body(rest) or clean_email_command(rest, recipient, subject)
            return self.tools.draft_email(recipient=recipient, subject=subject, points=points)

        if text.startswith("create report") or text.startswith("make report") or text.startswith("prepare report"):
            title = re.sub(r"^(create|make|prepare)\s+report\s*(on|about|for)?", "", original, flags=re.I).strip()
            return self.tools.create_report(title or "Business Report", original)

        if any(word in text for word in ["business plan", "founder brief", "investor update", "board report"]):
            return self.tools.create_business_brief(original, area="founder")

        if any(word in text for word in ["marketing plan", "competitor research", "market research", "keyword research"]):
            return self.tools.create_business_brief(original, area="marketing")

        if any(word in text for word in ["email automation", "clean my inbox", "inbox cleanup"]):
            return self.tools.create_business_brief(original, area="email")

        if any(word in text for word in ["excel automation", "spreadsheet", "dashboard"]):
            return self.tools.create_business_brief(original, area="excel")

        if any(word in text for word in ["book flight", "book hotel", "travel plan"]):
            self.tools.web_search(original, engine="google")
            return self.tools.create_business_brief(original, area="personal_assistant")

        if "process invoices" in text or "pending payments" in text:
            folder = extract_folder(original)
            return self.tools.process_invoices(folder)

        if "approve payment" in text:
            return ToolResult(True, "I can prepare a payment approval note, but I will not approve or submit payments automatically. Tell me the invoice/payment details and I will draft the approval.")

        if "reply to my whatsapp" in text or "whatsapp messages" in text:
            webbrowser.open("https://web.whatsapp.com")
            return ToolResult(True, "Opened WhatsApp Web. I can draft replies, but I need you to review before sending.")

        return None


def extract_path(text: str) -> str:
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', text)
    if quoted:
        return quoted.group(1) or quoted.group(2)
    match = re.search(r"([A-Za-z]:\\[^<>|?*\n\r]+?\.(?:xlsx|xls|csv|txt|md|docx|pdf|json))", text, flags=re.I)
    return match.group(1).strip() if match else ""


def extract_folder(text: str) -> str:
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', text)
    if quoted:
        return quoted.group(1) or quoted.group(2)
    match = re.search(r"([A-Za-z]:\\[^<>|?*\n\r]+)", text, flags=re.I)
    return match.group(1).strip() if match else ""


def find_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0) if match else ""


def find_after_label(text: str, label: str) -> str:
    match = re.search(label + r"\s*[:=-]\s*(.+?)(?:\n|$)", text, flags=re.I)
    return match.group(1).strip() if match else ""


def find_subject(text: str) -> str:
    match = re.search(
        r"subject\s*[:=-]\s*(.+?)(?=\s+(?:body|message|points)\s*[:=-]|\s+saying\s+|\n|$)",
        text,
        flags=re.I | re.S,
    )
    return match.group(1).strip(" .") if match else ""


def find_email_body(text: str) -> str:
    match = re.search(r"(?:body|message|points)\s*[:=-]\s*(.+)$", text, flags=re.I | re.S)
    if match:
        return match.group(1).strip()
    match = re.search(r"\bsaying\s+(.+)$", text, flags=re.I | re.S)
    return match.group(1).strip() if match else ""


def clean_email_command(text: str, recipient: str, subject: str) -> str:
    cleaned = text
    if recipient:
        cleaned = re.sub(r"\bto\s+" + re.escape(recipient), "", cleaned, flags=re.I)
        cleaned = cleaned.replace(recipient, "")
    if subject:
        cleaned = re.sub(r"subject\s*[:=-]\s*" + re.escape(subject), "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if cleaned.lower() in {"", "to", "email"}:
        return f"Following up regarding {subject or 'our discussion'}."
    return cleaned


def capabilities_text() -> str:
    return textwrap.dedent(
        f"""
        I can help with:
        - Voice conversation: listen, answer, and speak back.
        - Cloud dashboard mode: connect to your Dacexy backend over WebSocket and execute dashboard tasks.
        - Browser tasks: open sites, search Google or YouTube, open Gmail, Calendar, Drive, Ads, Analytics, and more.
        - Windows tasks: launch apps, take screenshots, OCR the screen, type/paste text, click, scroll, press keys, manage windows, and use hotkeys after confirmation.
        - CEO work: create founder briefs, investor updates, board report drafts, KPI plans, competitor research plans.
        - Email work: summarize pasted emails, draft replies, detect priority/lead/finance/support style emails.
        - Excel work: analyze workbooks, remove duplicates, clean text cells, and create cleaning reports.
        - Campaign/social work: create email campaign drafts, WhatsApp drafts, and social post drafts for review.
        - Documents: summarize txt, md, csv, Excel, docx, and PDF files when dependencies are installed.
        - Personal assistant work: reminders, travel planning checklists, meeting prep, follow-up lists.

        Example commands:
        - Open Gmail
        - Search competitor analysis for cloud kitchen in Delhi
        - Analyze Excel "C:\\path\\sales.xlsx"
        - Clean Excel "C:\\path\\leads.xlsx"
        - Draft email to rahul@example.com subject: Partnership proposal
        - Create report on monthly revenue tracking for my company
        - Remind me to call investor in 20 minutes
        - Take screenshot
        - Set cloud token YOUR_DASHBOARD_TOKEN
        - Organize my desktop
        - List windows
        """
    ).strip()


class CloudBridge(threading.Thread):
    def __init__(self, settings: Settings, agent: "Agent"):
        super().__init__(daemon=True)
        self.settings = settings
        self.agent = agent
        self.running = True
        self.connected = False

    def run(self) -> None:
        if not self.settings.cloud_enabled:
            return
        if not websockets:
            self.agent.voice.say("Cloud dashboard bridge disabled: install websockets.", speak=False)
            return
        if not self.settings.access_token:
            self.agent.voice.say(
                f"Cloud dashboard bridge is ready but no token is saved. Use: set cloud token YOUR_TOKEN",
                speak=False,
            )
            return
        try:
            asyncio.run(self._run_forever())
        except Exception as exc:
            self.agent.voice.say(f"Cloud bridge stopped: {exc}", speak=False)

    async def _run_forever(self) -> None:
        while self.running:
            try:
                await self._connect_once()
            except Exception as exc:
                self.connected = False
                self.agent.voice.say(f"Cloud disconnected: {exc}", speak=False)
            if not self.settings.auto_reconnect:
                break
            await asyncio.sleep(5)

    async def _connect_once(self) -> None:
        url = self.settings.resolved_ws_url()
        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=10_000_000) as ws:
            await ws.send(json.dumps({"token": self.settings.access_token}))
            first = await asyncio.wait_for(ws.recv(), timeout=20)
            first_msg = json.loads(first)
            if first_msg.get("type") == "error":
                raise RuntimeError(first_msg.get("message", "Cloud authentication failed."))
            await ws.send(json.dumps(host_metadata(self.settings)))
            self.connected = True
            self.agent.voice.say("Cloud dashboard connected.", speak=False)
            heartbeat = asyncio.create_task(self._heartbeat(ws))
            try:
                async for raw in ws:
                    await self._handle_ws_message(ws, raw)
            finally:
                heartbeat.cancel()
                self.connected = False

    async def _heartbeat(self, ws: Any) -> None:
        while self.running:
            await asyncio.sleep(max(10, self.settings.heartbeat_seconds))
            try:
                health = self.agent.tools.health_check().data
                await ws.send(json.dumps({"type": "heartbeat", "health": health, "version": AGENT_VERSION}))
            except Exception:
                return

    async def _handle_ws_message(self, ws: Any, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            return
        msg_type = msg.get("type", "")
        if msg_type == "ping":
            await ws.send(json.dumps({"type": "pong"}))
            return
        result = self.agent.execute_cloud_action(msg)
        payload = self._result_payload(msg, result)
        await ws.send(json.dumps(payload, ensure_ascii=True))

    def _result_payload(self, msg: dict[str, Any], result: ToolResult) -> dict[str, Any]:
        action = msg.get("action") or msg.get("type") or "command"
        task_id = msg.get("task_id", "")
        result_type = "task_result" if task_id or msg.get("type") == "task" else "result"
        payload: dict[str, Any] = {
            "type": result_type,
            "task_id": task_id,
            "action": action,
            "status": "completed" if result.ok else "failed",
            "ok": 1 if result.ok else 0,
            "total": 1,
            "message": result.message,
            "result": result.data if result.data is not None else result.message,
            "version": AGENT_VERSION,
            "time": dt.datetime.now().isoformat(timespec="seconds"),
        }
        if action == "screenshot" and result.ok and result.data:
            payload["screenshot_path"] = str(result.data)
            payload["screenshot"] = file_to_base64(result.data)
        if action == "ocr_screen":
            payload["type"] = "ocr_result"
            data = result.data if isinstance(result.data, dict) else {}
            payload["text"] = data.get("text", "")
            payload["screenshot"] = file_to_base64(data.get("screenshot", ""))
        if action == "health_check":
            payload["type"] = "health_result"
            payload["health"] = result.data
        if action == "get_memory":
            payload["type"] = "memory_result"
            payload["memory"] = result.message
        if action == "list_skills":
            payload["type"] = "skill_result"
            payload["skills"] = result.data or []
        return payload


class Agent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.voice = VoiceIO(settings)
        self.memory = Memory()
        self.llm = LLMClient(settings)
        self.tools = DesktopTools(self.voice, self.llm)
        self.router = CommandRouter(self.tools, self.voice)
        self.reminder_watcher = ReminderWatcher(self.voice)
        self.cloud_bridge = CloudBridge(settings, self)

    def start(self) -> None:
        ensure_dirs()
        self.reminder_watcher.start()
        self.cloud_bridge.start()
        provider = self.llm.provider
        brain = provider if provider != "none" else "rule-based mode"
        self.voice.say(
            f"{self.settings.assistant_name} online. Brain: {brain}. Say a command, or type it here."
        )
        self.voice.say("Say help to see what I can do.", speak=False)
        while True:
            try:
                command = self.voice.listen()
                if not command:
                    continue
                print(f"\nYou: {command}")
                cleaned = self.strip_wake_word(command)
                if cleaned.lower() in {"exit", "quit", "stop", "shutdown", "bye"}:
                    self.voice.say("Going offline.")
                    break
                self.handle(cleaned)
            except KeyboardInterrupt:
                self.voice.say("Going offline.")
                break
            except Exception as exc:
                self.voice.say(f"I hit an error: {exc}")

    def strip_wake_word(self, command: str) -> str:
        text = command.strip()
        lowered = text.lower()
        for wake in sorted(self.settings.wake_words, key=len, reverse=True):
            if lowered.startswith(wake):
                return text[len(wake) :].lstrip(" ,:")
        return text

    def handle(self, command: str) -> None:
        self.memory.add_history("user", command)
        result = self.execute_text_command(command)
        self.memory.add_history("assistant", result.message)
        self.voice.say(result.message)

    def execute_text_command(self, command: str) -> ToolResult:
        result = self.router.route(command)
        if result is None:
            result = self.try_llm_plan(command)
        if result is None:
            result = self.converse(command)
        return result

    def execute_cloud_action(self, msg: dict[str, Any]) -> ToolResult:
        action = str(msg.get("action") or msg.get("type") or "").strip()
        if action in {"task", "swarm_task", "command", "speak"}:
            command = str(msg.get("task") or msg.get("command") or msg.get("query") or msg.get("context") or "").strip()
            if not command:
                return ToolResult(False, "No task text was provided.")
            self.memory.add_history("cloud_user", command)
            result = self.execute_text_command(command)
            self.memory.add_history("assistant", result.message)
            return result
        if action == "screenshot":
            return self.tools.screenshot(str(msg.get("name") or "cloud_screenshot"))
        if action == "ocr_screen":
            return self.tools.ocr_screen(msg.get("region"))
        if action == "health_check":
            return self.tools.health_check()
        if action == "get_memory":
            return ToolResult(True, self.memory.recent_history(30))
        if action == "list_skills":
            return ToolResult(True, "Skills listed.", installed_features())
        return self.dispatch_cloud_tool(action, msg)

    def dispatch_cloud_tool(self, action: str, msg: dict[str, Any]) -> ToolResult:
        try:
            if action in {"open", "open_site"}:
                return self.tools.open_site(str(msg.get("app") or msg.get("url") or msg.get("query") or ""))
            if action == "open_url":
                return self.tools.open_url(str(msg.get("url") or msg.get("query") or ""))
            if action in {"launch", "launch_app", "start_app"}:
                return self.tools.launch_app(str(msg.get("app") or msg.get("name") or msg.get("command") or ""))
            if action in {"search", "web_search"}:
                return self.tools.web_search(str(msg.get("query") or msg.get("task") or ""), engine=str(msg.get("engine") or "google"))
            if action in {"click", "mouse_click"}:
                return self.tools.click(msg.get("x"), msg.get("y"), int(msg.get("clicks") or 1), str(msg.get("button") or "left"))
            if action == "move":
                return self.tools.move_mouse(int(msg.get("x") or 0), int(msg.get("y") or 0), float(msg.get("duration") or 0.2))
            if action == "scroll":
                amount = int(msg.get("amount") or (-700 if msg.get("direction", "down") == "down" else 700))
                return self.tools.scroll(amount)
            if action == "type":
                return self.tools.paste_text(str(msg.get("text") or ""))
            if action == "press":
                return self.tools.press(str(msg.get("key") or ""))
            if action == "hotkey":
                return self.tools.hotkey(msg.get("keys") or "")
            if action == "read_file":
                return self.tools.read_file_text(str(msg.get("path") or ""))
            if action == "write_file":
                return self.tools.write_file_text(str(msg.get("path") or ""), str(msg.get("content") or ""), overwrite=bool(msg.get("overwrite") or False))
            if action == "summarize_file":
                return self.tools.summarize_file(str(msg.get("path") or ""))
            if action in {"analyze_excel", "excel_analysis"}:
                return self.tools.analyze_excel(str(msg.get("path") or ""))
            if action == "clean_excel":
                return self.tools.clean_excel(str(msg.get("path") or ""), str(msg.get("output") or ""))
            if action in {"organize_desktop", "organize_folder"}:
                folder = str(msg.get("folder") or msg.get("path") or (Path.home() / "Desktop"))
                return self.tools.organize_folder(folder, dry_run=bool(msg.get("dry_run") or False))
            if action in {"process_invoices", "pending_payments"}:
                return self.tools.process_invoices(str(msg.get("folder") or msg.get("path") or ""))
            if action == "create_report":
                return self.tools.create_report(str(msg.get("title") or msg.get("name") or "Business Report"), str(msg.get("content") or msg.get("task") or ""))
            if action == "draft_email":
                return self.tools.draft_email(str(msg.get("email") or ""), str(msg.get("subject") or ""), str(msg.get("body") or msg.get("message") or ""), "professional")
            if action == "create_campaign":
                return self.tools.create_campaign(
                    str(msg.get("name") or "Campaign"),
                    str(msg.get("subject") or ""),
                    str(msg.get("body") or ""),
                    msg.get("recipients") or [],
                    bool(msg.get("html") if msg.get("html") is not None else True),
                    msg.get("tags") or [],
                    msg.get("scheduled_at"),
                )
            if action == "send_campaign":
                return self.tools.send_campaign(str(msg.get("campaign_id") or ""))
            if action == "whatsapp_bulk":
                return self.tools.whatsapp_bulk(msg.get("contacts") or [], str(msg.get("message") or ""), float(msg.get("delay") or 3.5))
            if action in {"twitter_post", "linkedin_post", "facebook_post", "instagram_post", "youtube_upload", "tiktok_post", "post_all_social"}:
                platform_name = action.replace("_post", "").replace("_upload", "")
                return self.tools.social_post_draft(platform_name, text=str(msg.get("text") or ""), caption=str(msg.get("caption") or ""), media=str(msg.get("image_path") or msg.get("video_path") or msg.get("media") or ""))
            if action == "system_info":
                return self.tools.system_status()
            if action == "list_windows":
                return self.tools.list_windows()
            if action == "focus_window":
                return self.tools.focus_window(str(msg.get("keyword") or msg.get("title") or ""))
        except Exception as exc:
            return ToolResult(False, f"Cloud action {action} failed: {exc}")
        return ToolResult(False, f"Unsupported cloud action: {action}")

    def converse(self, command: str) -> ToolResult:
        system = (
            f"You are {self.settings.assistant_name}, a practical Jarvis-style desktop assistant. "
            "Be concise, direct, and useful. If the user asks for a task that requires credentials, payment, "
            "legal/medical/financial decisions, deletion, or external account access, explain what you can prepare "
            "and what needs user confirmation. Do not claim that you performed desktop actions unless a tool did it."
        )
        user = f"Recent conversation:\n{self.memory.recent_history()}\n\nUser command:\n{command}"
        answer = self.llm.complete(system, user, temperature=0.35, max_tokens=1200)
        return ToolResult(True, answer)

    def try_llm_plan(self, command: str) -> ToolResult | None:
        if self.llm.provider == "none":
            return None
        system = (
            f"You are the planner for {self.settings.assistant_name}, a Windows desktop agent. "
            "Return only JSON. Choose zero or more safe tool actions. Do not invent files or credentials. "
            "For payments, bookings, deleting data, sending emails, or private account actions, prepare drafts/checklists only. "
            "Schema: {\"speak\":\"short response\", \"actions\":[{\"tool\":\"tool_name\", \"args\":{}}]}.\n"
            "Available tools:\n"
            "- open_site {name}\n"
            "- open_url {url}\n"
            "- web_search {query, engine}\n"
            "- launch_app {name}\n"
            "- screenshot {name}\n"
            "- ocr_screen {}\n"
            "- paste_text {text}\n"
            "- list_windows {}\n"
            "- focus_window {keyword}\n"
            "- system_status {}\n"
            "- summarize_file {path}\n"
            "- analyze_excel {path}\n"
            "- clean_excel {path}\n"
            "- organize_folder {folder, dry_run}\n"
            "- process_invoices {folder}\n"
            "- draft_email {recipient, subject, points, tone}\n"
            "- create_report {title, instructions}\n"
            "- create_business_brief {topic, area}\n"
            "- add_reminder {text, due_text}\n"
            "- list_reminders {}\n"
        )
        user = f"Recent conversation:\n{self.memory.recent_history()}\n\nUser command:\n{command}"
        raw = self.llm.complete(system, user, temperature=0.0, max_tokens=1200)
        plan = extract_json_object(raw)
        if not plan:
            return None
        actions = plan.get("actions") or []
        if not isinstance(actions, list):
            return None
        messages = []
        speak = str(plan.get("speak") or "").strip()
        if speak:
            messages.append(speak)
        for action in actions[:6]:
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool") or "").strip()
            args = action.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            result = self.dispatch(tool, args)
            messages.append(result.message)
        if not messages:
            return None
        return ToolResult(True, "\n".join(messages))

    def dispatch(self, tool: str, args: dict[str, Any]) -> ToolResult:
        mapping: dict[str, Callable[..., ToolResult]] = {
            "open_site": self.tools.open_site,
            "open_url": self.tools.open_url,
            "web_search": self.tools.web_search,
            "launch_app": self.tools.launch_app,
            "screenshot": self.tools.screenshot,
            "ocr_screen": self.tools.ocr_screen,
            "paste_text": self.tools.paste_text,
            "list_windows": self.tools.list_windows,
            "focus_window": self.tools.focus_window,
            "system_status": self.tools.system_status,
            "summarize_file": self.tools.summarize_file,
            "analyze_excel": self.tools.analyze_excel,
            "clean_excel": self.tools.clean_excel,
            "organize_folder": self.tools.organize_folder,
            "process_invoices": self.tools.process_invoices,
            "draft_email": self.tools.draft_email,
            "create_report": self.tools.create_report,
            "create_business_brief": self.tools.create_business_brief,
            "add_reminder": self.tools.add_reminder,
            "list_reminders": self.tools.list_reminders,
        }
        func = mapping.get(tool)
        if not func:
            return ToolResult(False, f"I do not have a tool named {tool}.")
        try:
            return func(**args)
        except TypeError:
            return ToolResult(False, f"The tool {tool} received the wrong arguments: {args}")
        except Exception as exc:
            return ToolResult(False, f"The tool {tool} failed: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dacexy Jarvis-style desktop agent")
    parser.add_argument("--text", action="store_true", help="Use keyboard input instead of microphone.")
    parser.add_argument("--no-voice", action="store_true", help="Print responses without speaking.")
    parser.add_argument("--unsafe", action="store_true", help="Disable confirmation prompts for typing/hotkeys.")
    parser.add_argument("--no-cloud", action="store_true", help="Do not connect to the Dacexy cloud dashboard.")
    parser.add_argument("--token", help="Save/use a Dacexy dashboard access token for the cloud bridge.")
    parser.add_argument("--command", help="Run one command and exit.")
    args = parser.parse_args()

    settings = Settings.from_env()
    if args.text:
        settings.microphone = False
    if args.no_voice:
        settings.voice = False
    if args.unsafe:
        settings.safe_mode = False
    if args.no_cloud:
        settings.cloud_enabled = False
    if args.token:
        settings.access_token = args.token.strip()
        save_access_token(settings.access_token)

    agent = Agent(settings)
    if args.command:
        agent.handle(args.command)
        return 0
    agent.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
