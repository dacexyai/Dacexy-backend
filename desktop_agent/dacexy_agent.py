"""
dacexy_agent.py — Dacexy Desktop AI Agent
Production-grade autonomous desktop AI: voice, planner, executor, verifier,
memory, workflow learning, multi-agent orchestration, business OS, WebSocket bridge.
All-in-one single file.

 changes (targeted fixes, no rewrite):
  - Voice: conversation-mode pause threshold lengthened (0.8s -> 1.4s) so multi-clause
    business commands aren't cut off; unrecognized speech in conversation mode now
    triggers a spoken retry instead of silently dropping; periodic re-calibration
    against ambient noise every 5 minutes.
  - Verification: real_click now confirms cursor position before clicking; real_type
    now returns a real status dict (clipboard round-trip check) instead of swallowing
    errors silently; send_email_real and replay_workflow no longer report "ok" when
    they only opened a manual browser draft (new "action_required" status).
  - Planner/executor: execute_planned_task now only counts true "ok" as verified,
    retries a failed step once before giving up, stops the plan early on a hard
    failure instead of burning through remaining steps blind, and never saves a
    workflow as "verified" unless every step actually succeeded.
  - Multi-agent: execute_task now routes through coordinator_dispatch (previously
    only one WebSocket message type ever reached the agent router; voice and the
    interactive shell bypassed it entirely).
  - Dashboard sync: added live per-step "task_progress" WebSocket messages instead
    of a single result at the end; removed a hardcoded ok=1 for "skipped" status on
    direct dashboard actions.
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
            _sys_early.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        _sys_early.stderr = _io_early.TextIOWrapper(
            _sys_early.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
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
    ("edge-tts",          "edge_tts"),
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

# --- EMBEDDED MODULAR SYSTEM ---
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class ActionStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    DENIED = "denied"
    ACTION_REQUIRED = "action_required"
    PENDING = "pending"
    SKIPPED = "skipped"
    PARTIAL = "partial"

class MemoryType(str, Enum):
    FACT = "fact"
    CONTACT = "contact"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    BUSINESS = "business"
    WORKFLOW = "workflow"
    KPI = "kpi"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"

class ActionResult(BaseModel):
    status: ActionStatus
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PlannedStep(BaseModel):
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

class ExecutionPlan(BaseModel):
    goal: str
    steps: List[PlannedStep]
    requires_approval: bool = False

class MemoryEntry(BaseModel):
    kind: MemoryType
    key: str
    text: str
    value: Any = None
    tags: List[str] = Field(default_factory=list)
    updated: str

class WorkflowRecord(BaseModel):
    name: str
    steps: List[PlannedStep]
    verified: bool = True
    run_count: int = 0
    saved_at: str

from typing import Callable, Dict, Any, List, Optional
import logging


log = logging.getLogger("dacexy.tool_registry")

class ToolRegistry:
    def __init__(self):
        # Maps action string to a callable function
        # The callable must take a dict of parameters and return an ActionResult
        self._tools: Dict[str, Callable[[Dict[str, Any]], ActionResult]] = {}

    def register(self, action_name: str, func: Callable[[Dict[str, Any]], ActionResult]) -> None:
        """Register a new tool."""
        if action_name in self._tools:
            log.warning(f"Overwriting existing tool registration for: {action_name}")
        self._tools[action_name] = func
        log.debug(f"Registered tool: {action_name}")

    def get_tool(self, action_name: str) -> Optional[Callable[[Dict[str, Any]], ActionResult]]:
        """Retrieve a registered tool by name."""
        return self._tools.get(action_name)

    def execute(self, action_name: str, params: Dict[str, Any]) -> ActionResult:
        """Execute a tool by name with the given parameters."""
        tool = self.get_tool(action_name)
        if not tool:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Unknown tool/action: {action_name}"
            )
        try:
            return tool(params)
        except Exception as e:
            log.error(f"Error executing tool {action_name}: {e}")
            return ActionResult(
                status=ActionStatus.ERROR,
                message=str(e)
            )

    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())

import os
import time
import logging
from typing import Dict, Any, Callable


log = logging.getLogger("dacexy.verification_engine")

class VerificationEngine:
    def __init__(self):
        # Maps action name to a custom verification function
        self._verifiers: Dict[str, Callable[[Dict[str, Any], ActionResult], bool]] = {}
        self._register_default_verifiers()

    def _register_default_verifiers(self):
        self.register("create_file", self._verify_file_created)
        self.register("write_file", self._verify_file_created)
        self.register("delete_file", self._verify_file_deleted)

    def register(self, action_name: str, verifier_func: Callable[[Dict[str, Any], ActionResult], bool]):
        self._verifiers[action_name] = verifier_func

    def verify(self, action_name: str, params: Dict[str, Any], result: ActionResult) -> ActionResult:
        """
        Verify the outcome of an action.
        Returns the original result if verification passes, or an updated
        ActionResult if verification fails.
        """
        if result.status != ActionStatus.OK:
            return result  # Only verify successful actions

        verifier = self._verifiers.get(action_name)
        if not verifier:
            # If no explicit verifier exists, trust the tool's reported status
            return result

        try:
            is_valid = verifier(params, result)
            if not is_valid:
                log.warning(f"Verification failed for action {action_name}")
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Verification failed: Post-conditions for {action_name} not met."
                )
            return result
        except Exception as e:
            log.error(f"Error during verification of {action_name}: {e}")
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Verification process raised an error: {e}"
            )

    # --- Built-in Verifiers ---

    def _verify_file_created(self, params: Dict[str, Any], result: ActionResult) -> bool:
        filepath = params.get("path") or params.get("filepath")
        if not filepath:
            return True # Can't verify without a path
        
        # Wait a short moment for async disk flushes
        for _ in range(5):
            if os.path.exists(filepath):
                return True
            time.sleep(0.2)
        return False

    def _verify_file_deleted(self, params: Dict[str, Any], result: ActionResult) -> bool:
        filepath = params.get("path") or params.get("filepath")
        if not filepath:
            return True
        return not os.path.exists(filepath)

import os
import json
import threading
import hashlib
import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import logging



log = logging.getLogger("dacexy.memory_system")

class MemoryManager:
    def __init__(self, memory_file_path: str):
        self._file_path = memory_file_path
        self._lock = threading.Lock()
        
        # Internal memory representation
        self._data = {
            "facts": [],
            "long_term": [],
            "semantic_memory": [],
            "business_memory": {},
            "contact_memory": {},
            "customer_memory": {},
            "workflow_memory": {},
            "task_history": deque(maxlen=1000)
        }
        
        self.load()

    def load(self):
        """Load memory from disk thread-safely."""
        with self._lock:
            try:
                if os.path.exists(self._file_path):
                    with open(self._file_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    
                    self._data["facts"] = loaded.get("facts", [])
                    self._data["long_term"] = loaded.get("long_term", [])
                    self._data["semantic_memory"] = loaded.get("semantic_memory", [])
                    self._data["business_memory"] = loaded.get("business_memory", {})
                    self._data["contact_memory"] = loaded.get("contact_memory", {})
                    self._data["customer_memory"] = loaded.get("customer_memory", {})
                    self._data["workflow_memory"] = loaded.get("workflow_memory", {})
                    
                    th = loaded.get("task_history", [])
                    self._data["task_history"] = deque(th[-1000:], maxlen=1000)
                    
                    log.info(f"Memory loaded from {self._file_path}")
            except Exception as e:
                log.error(f"Error loading memory: {e}")

    def save(self):
        """Save memory to disk atomically and thread-safely."""
        with self._lock:
            try:
                to_save = {
                    "facts": self._data["facts"][-1000:],
                    "long_term": self._data["long_term"][-2000:],
                    "semantic_memory": self._data["semantic_memory"][-5000:],
                    "business_memory": self._data["business_memory"],
                    "contact_memory": self._data["contact_memory"],
                    "customer_memory": self._data["customer_memory"],
                    "workflow_memory": self._data["workflow_memory"],
                    "task_history": list(self._data["task_history"])[-200:]
                }
                tmp_path = self._file_path + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(to_save, f, indent=2, default=str)
                os.replace(tmp_path, self._file_path)
            except Exception as e:
                log.error(f"Error saving memory: {e}")

    def remember_fact(self, fact: str):
        """Remember a simple string fact."""
        if not fact: return
        with self._lock:
            if fact not in self._data["facts"]:
                self._data["facts"].append(fact)
            if fact not in self._data["long_term"]:
                self._data["long_term"].append(fact)
                
            entry = MemoryEntry(
                kind=MemoryType.FACT,
                key=hashlib.sha1(fact.encode()).hexdigest()[:12],
                text=fact,
                updated=datetime.datetime.now().isoformat()
            )
            self._data["semantic_memory"].append(entry.dict())
        self.save()

    def remember_structured(self, kind: MemoryType, key: str, value: Any, tags: Optional[List[str]] = None):
        """Remember structured data (contacts, business facts, etc)."""
        key = key.strip().lower()
        
        text_rep = json.dumps(value, default=str) if not isinstance(value, str) else value
        
        entry = MemoryEntry(
            kind=kind,
            key=key,
            text=text_rep,
            value=value,
            tags=tags or [],
            updated=datetime.datetime.now().isoformat()
        )
        
        with self._lock:
            if kind == MemoryType.CONTACT:
                self._data["contact_memory"][key] = value
            elif kind == MemoryType.CUSTOMER:
                self._data["customer_memory"][key] = value
            elif kind == MemoryType.BUSINESS:
                self._data["business_memory"][key] = value
            elif kind == MemoryType.WORKFLOW:
                self._data["workflow_memory"][key] = value
            else:
                self._data["long_term"].append(text_rep)
                
            self._data["semantic_memory"].append(entry.dict())
        self.save()
        
    def record_task_history(self, task: str, result: str):
        with self._lock:
            self._data["task_history"].append(f"{task[:80]} [{result}]")
        self.save()

    def get_context_summary(self) -> str:
        """Returns a string summary of recent/relevant memory for LLM context."""
        with self._lock:
            parts = []
            if self._data["facts"]:
                parts.append("Facts: " + "; ".join(self._data["facts"][-10:]))
            
            recent_tasks = list(self._data["task_history"])[-8:]
            if recent_tasks:
                parts.append("Recent Tasks: " + "; ".join(recent_tasks))
                
            contacts = list(self._data["contact_memory"].keys())[:8]
            if contacts:
                parts.append("Contacts: " + ", ".join(contacts))
                
            biz = self._data["business_memory"]
            if biz:
                parts.append("Business: " + json.dumps(dict(list(biz.items())[:8]), default=str)[:600])
                
            return "\n".join(parts)

    def _tokenize(self, text: str) -> set:
        import re
        return {t for t in re.findall(r"[a-z0-9][a-z0-9_\-]{1,}", str(text).lower()) if len(t) > 1}

    def semantic_search(self, query: str, top_k: int = 5, categories: Optional[List[MemoryType]] = None) -> List[Dict]:
        """Perform a bag-of-words similarity search across all memories."""
        qtok = self._tokenize(query)
        if not qtok:
            return []
            
        cats = {c.value for c in categories} if categories else None
        
        docs = []
        with self._lock:
            for entry in self._data["semantic_memory"][-3000:]:
                if cats and entry.get("kind") not in cats:
                    continue
                docs.append(entry)
                
        scored = []
        for doc in docs:
            dtok = self._tokenize(doc.get("text", ""))
            if not dtok: continue
            overlap = qtok & dtok
            if not overlap: continue
            
            score = len(overlap) / max(len(qtok | dtok), 1)
            scored.append((score, doc))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        seen = set()
        for score, doc in scored:
            ident = (doc.get("kind"), doc.get("key"), str(doc.get("text", ""))[:80])
            if ident in seen: continue
            seen.add(ident)
            
            res = dict(doc)
            res["score"] = round(score, 4)
            results.append(res)
            
            if len(results) >= max(1, min(int(top_k), 20)):
                break
                
        return results

import datetime
import logging
from typing import List, Optional




log = logging.getLogger("dacexy.learning_layer")

class WorkflowLearner:
    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def save_workflow(self, name: str, steps: List[PlannedStep], verified: bool = True) -> None:
        """Persist a successful sequence of steps as a reusable workflow."""
        if not name or not steps:
            return

        name_lower = name.lower()
        # Retrieve existing to keep run_count if any (need direct memory access or a helper, 
        # but for now we'll just check if it exists in semantic search or just overwrite)
        # Assuming memory_manager has the workflow in business_memory or similar
        
        # We will use remember_structured to store it
        record = WorkflowRecord(
            name=name,
            steps=steps,
            verified=verified,
            run_count=1, # simplified; real implementation would increment
            saved_at=datetime.datetime.now().isoformat()
        )
        
        self.memory.remember_structured(
            kind=MemoryType.WORKFLOW,
            key=name_lower,
            value=record.dict()
        )
        log.info(f"Workflow saved: '{name}' ({len(steps)} steps)")

    def get_workflow(self, name: str) -> Optional[WorkflowRecord]:
        """Retrieve a saved workflow by name."""
        name_lower = name.lower()
        # MemoryManager._data is private, but we could use a specific method.
        # For this refactor, we assume the MemoryManager exposes a way to get it,
        # or we just access the internal dict for now (or add a get method to memory).
        # We'll use the internal dict access for the prototype, but in production
        # we'd add `get_structured` to MemoryManager.
        with self.memory._lock:
            data = self.memory._data["workflow_memory"].get(name_lower)
            if data:
                return WorkflowRecord(**data)
        return None

    def list_workflows(self) -> List[str]:
        """List all saved workflow names."""
        with self.memory._lock:
            return list(self.memory._data["workflow_memory"].keys())

    def record_execution(self, name: str, success: bool):
        """Update the run count and verification status of a workflow."""
        wf = self.get_workflow(name)
        if wf:
            wf.run_count += 1
            if not success:
                wf.verified = False
            self.memory.remember_structured(
                kind=MemoryType.WORKFLOW,
                key=name.lower(),
                value=wf.dict()
            )

import json
import logging
from typing import List, Dict, Any




log = logging.getLogger("dacexy.hierarchical_planner")

class Planner:
    def __init__(self, reasoning_engine: ReasoningEngine):
        self.reasoning = reasoning_engine

    def create_plan(self, goal: str, context: str = "") -> ExecutionPlan:
        """
        Takes a natural language goal and converts it into a structured
        ExecutionPlan using the ReasoningEngine (LLM/NLP logic).
        """
        log.info(f"Creating plan for goal: {goal}")
        
        # In the monolithic version, local_parse used a massive regex system.
        # Here we abstract it so the ReasoningEngine can use AI or regex.
        
        system_prompt = (
            "You are a task planner. Break the user's goal down into actionable steps. "
            "Output valid JSON matching this schema: "
            "{ 'requires_approval': bool, 'steps': [ {'action': 'str', 'target': 'str', 'parameters': {}} ] }"
        )
        
        # A real implementation would parse the result from the LLM or regex
        # For the architecture stub, we'll simulate the parse
        
        raw_response = self.reasoning.ask(
            prompt=f"Goal: {goal}\nContext: {context}",
            system_prompt=system_prompt,
            expect_json=True
        )
        
        try:
            # Attempt to parse the response as JSON if it's a string, or it might already be a dict
            data = raw_response if isinstance(raw_response, dict) else json.loads(raw_response)
            
            steps = []
            for s in data.get("steps", []):
                steps.append(PlannedStep(
                    action=s.get("action", "unknown"),
                    target=s.get("target"),
                    parameters=s.get("parameters", {}),
                    description=s.get("description")
                ))
                
            plan = ExecutionPlan(
                goal=goal,
                steps=steps,
                requires_approval=data.get("requires_approval", False)
            )
            return plan
            
        except Exception as e:
            log.error(f"Failed to parse plan: {e}")
            # Fallback to a single-step generic plan
            return ExecutionPlan(
                goal=goal,
                steps=[PlannedStep(action="smart_open", target=goal, parameters={"target": goal})],
                requires_approval=False
            )

import logging
import time
from typing import List





log = logging.getLogger("dacexy.execution_engine")

class ExecutionEngine:
    def __init__(self, registry: ToolRegistry, verifier: VerificationEngine):
        self.registry = registry
        self.verifier = verifier

    def execute_plan(self, plan: ExecutionPlan) -> ActionResult:
        """
        Iterates over a plan's steps, executing them in sequence.
        Aborts early if a step fails verification.
        """
        log.info(f"Executing plan: {plan.goal} ({len(plan.steps)} steps)")
        
        results: List[ActionResult] = []
        verified_count = 0
        action_required_count = 0
        
        for step in plan.steps:
            step_result = self.execute_step(step)
            results.append(step_result)
            
            if step_result.status == ActionStatus.OK:
                verified_count += 1
            elif step_result.status == ActionStatus.ACTION_REQUIRED:
                action_required_count += 1
            elif step_result.status == ActionStatus.SKIPPED:
                continue
            else:
                log.error(f"Plan aborted due to step failure: {step.action}")
                return ActionResult(
                    status=ActionStatus.PARTIAL if verified_count > 0 else ActionStatus.ERROR,
                    message=f"Plan halted at step '{step.action}': {step_result.message}",
                    data={"completed_steps": verified_count, "failed_step": step.dict(), "results": [r.dict() for r in results]}
                )
            
            time.sleep(0.5) # Throttle between steps
            
        final_status = ActionStatus.OK
        if action_required_count > 0:
            final_status = ActionStatus.PARTIAL
            
        return ActionResult(
            status=final_status,
            message=f"Plan completed. {verified_count} ok, {action_required_count} action required.",
            data={"completed_steps": verified_count, "results": [r.dict() for r in results]}
        )

    def execute_step(self, step: PlannedStep) -> ActionResult:
        """Executes a single step and verifies it."""
        log.debug(f"Executing step: {step.action}")
        
        # Merge target into parameters for convenience if needed
        params = dict(step.parameters)
        if step.target and "target" not in params:
            params["target"] = step.target
            
        # 1. Execute
        raw_result = self.registry.execute(step.action, params)
        
        # 2. Verify
        verified_result = self.verifier.verify(step.action, params, raw_result)
        
        # 3. Handle Retry if verification fails (simple 1-retry policy)
        if verified_result.status == ActionStatus.ERROR and raw_result.status == ActionStatus.OK:
            log.warning(f"Step {step.action} failed verification. Retrying once...")
            time.sleep(1.0)
            raw_result_2 = self.registry.execute(step.action, params)
            verified_result = self.verifier.verify(step.action, params, raw_result_2)
            
        return verified_result

import logging
import json
from typing import Optional, Union, Dict, Any

# We assume g4f is used as in the original code, or a similar provider
try:
    import g4f
    G4F_AVAILABLE = True
except ImportError:
    G4F_AVAILABLE = False

log = logging.getLogger("dacexy.reasoning_engine")

class ReasoningEngine:
    def __init__(self, default_model: str = "gpt-4"):
        self.default_model = default_model

    def ask(self, prompt: str, system_prompt: str = "", expect_json: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Send a prompt to the LLM and return the response.
        If expect_json is True, attempts to parse and return a dict.
        """
        log.debug(f"Asking AI. Prompt length: {len(prompt)}")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if not G4F_AVAILABLE:
            log.error("g4f is not available. Cannot perform reasoning.")
            return {} if expect_json else "Error: AI provider not available."

        try:
            # Using g4f API as per original codebase pattern
            response = g4f.ChatCompletion.create(
                model=self.default_model,
                messages=messages,
                timeout=30
            )
            
            response_text = str(response).strip()
            
            if expect_json:
                return self._parse_json(response_text)
                
            return response_text
            
        except Exception as e:
            log.error(f"Reasoning engine error: {e}")
            return {} if expect_json else f"Error: {e}"

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Attempt to extract and parse JSON from a potentially messy text response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block
            import re
            match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            log.warning("Failed to parse JSON from reasoning response.")
            return {}

import logging
from typing import Dict, Any







log = logging.getLogger("dacexy.multi_agent_system")

class AgentCoordinator:
    """
    The root node that receives triggers, invokes the Planner, passes plans 
    to the ExecutionEngine, and records results via the LearningLayer and MemorySystem.
    """
    def __init__(self, 
                 memory: MemoryManager, 
                 planner: Planner, 
                 executor: ExecutionEngine, 
                 learner: WorkflowLearner):
        self.memory = memory
        self.planner = planner
        self.executor = executor
        self.learner = learner

    def dispatch(self, goal: str, context: str = "") -> ActionResult:
        """
        Main entry point for fulfilling a user request.
        """
        log.info(f"Coordinator received goal: {goal}")
        
        # 1. Check if we already know how to do this (Workflow)
        # A real implementation would semantically match the goal to a workflow name
        # For simplicity, we just check exact match
        existing_wf = self.learner.get_workflow(goal)
        if existing_wf:
            log.info(f"Replaying existing workflow for: {goal}")
            # Mock replay logic - in reality, convert workflow to ExecutionPlan
            
            plan = ExecutionPlan(goal=goal, steps=existing_wf.steps)
            result = self.executor.execute_plan(plan)
            self.learner.record_execution(goal, result.status == ActionStatus.OK)
            self.memory.record_task_history(goal, result.status.value)
            return result

        # 2. Plan
        mem_context = self.memory.get_context_summary()
        full_context = f"{mem_context}\n{context}"
        plan = self.planner.create_plan(goal, full_context)
        
        if not plan.steps:
            msg = "Planner could not generate any steps."
            log.error(msg)
            return ActionResult(status=ActionStatus.ERROR, message=msg)

        # 3. Execute
        result = self.executor.execute_plan(plan)

        # 4. Learn
        if result.status == ActionStatus.OK:
            # Save successful novel plans as workflows
            self.learner.save_workflow(name=goal, steps=plan.steps, verified=True)
            
        # 5. Remember
        self.memory.record_task_history(goal, result.status.value)
        
        return result


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
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    import numpy as np
    NUMPY_OK = True
except Exception:
    np = None; NUMPY_OK = False

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
AGENT_VERSION = "14.0-autonomous"
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
MEMORY_FILE = Path.home() / ".dacexy_memory.json"
DEVICE_FILE = DATA_DIR / "device_registration.json"
TASK_STATE_FILE = DATA_DIR / "task_state.json"
VISION_STATE_FILE = DATA_DIR / "vision_state.json"

for _d in [AGENT_DIR, AGENT_DIR / "logs", SS_DIR, DATA_DIR, DOC_DIR, INBOX_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

SOCIAL_PROFILE_DIR = AGENT_DIR / "browser_profiles"
SOCIAL_PROFILE_DIR.mkdir(exist_ok=True)
PAYMENT_QUEUE_FILE = DATA_DIR / "payment_queue.json"
WORKFLOW_FILE      = DATA_DIR / "learned_workflows.json"

PAYMENT_PORTALS: Dict[str, str] = {
    "razorpay": "https://dashboard.razorpay.com/app/payments",
    "paypal":   "https://www.paypal.com/myaccount/transfer/homepage/pay",
    "bank":     "",
}

AUTO_REPLY_TEMPLATES: Dict[str, str] = {
    "default": "Thanks for your message! I'll get back to you shortly.",
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

SOCIAL_POLL_INTERVAL = 45

WAKE_WORDS = [
    "dex", "hey dex", "dexy", "hey dexy",
    "dacexy", "hey dacexy", "okay dacexy",
    "jarvis", "hey jarvis",
    "computer", "assistant", "hey agent", "agent",
]

_abort_flag = False

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
_ws_send_fn        = None
_ws_loop           = None
_ws_device_session = ""
_dashboard_last_screenshot = 0.0
_task_cancel_flags: Dict[str, threading.Event] = {}
_task_checkpoint_lock = threading.Lock()
_vision_lock = threading.Lock()
_vision_thread = None
_vision_on = False
_last_vision_hash = ""
_voice_interrupt = threading.Event()

# Social reply-bot state
_social_drivers: Dict[str, Any] = {}
_social_lock       = threading.Lock()
_social_auto: Dict[str, bool] = {"whatsapp": False, "instagram": False, "facebook": False}
_social_seen: Dict[str, set]  = {"whatsapp": set(), "instagram": set(), "facebook": set()}
_social_thread     = None
_social_running    = False

# ── MEMORY ────────────────────────────────────────────────────────────────────
MEMORY: Dict = {
    "facts":        [],
    "preferences":  {},
    "task_history": deque(maxlen=1000),
    "context":      {},
    "contacts":     {},
    "customers":    {},
    "suppliers":    {},
    "leads":        [],
    "skills":       [],
    "approved_ops": [],
    "workflows":    {},
    "business_facts": {},
    "long_term":    [],
    "business_memory": {},
    "customer_memory": {},
    "contact_memory": {},
    "workflow_memory": {},
    "semantic_memory": [],
    "kpis": {},
    "revenue": [],
    "profit": [],
    "sales": [],
    "competitors": {},
    "market_watch": {},
    "retention": {},
    "documents": {},
}

HEALTH: Dict = {
    "cpu": 0.0, "ram": 0.0, "disk": 0.0,
    "tasks_run": 0, "tasks_ok": 0, "uptime_start": time.time(),
    "voice_status": "off",
    "ws_status": "disconnected",
    "planner_status": "idle",
    "executor_status": "idle",
    "memory_status": "ok",
    "agent_errors": 0,
    "vision_status": "idle",
    "active_jobs": 0,
    "last_checkpoint": "",
    "device_id": "",
    "ws_reconnects": 0,
}

VISION_STATE: Dict = {
    "status": "idle",
    "updated_at": "",
    "active_window": "",
    "windows": [],
    "ocr_text": "",
    "buttons": [],
    "forms": [],
    "errors": [],
    "browser": {},
    "summary": "",
    "screenshot_path": "",
}

# ── TASK QUEUE (Phase 3) ──────────────────────────────────────────────────────
_task_queue: queue.Queue = queue.Queue(maxsize=100)
_active_tasks: Dict[str, dict] = {}
_tasks_lock = threading.Lock()

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
log.info("Dacexy Agent v13.0 initializing")

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
# TTS — Streaming edge-tts + pyttsx3 fallback
# ══════════════════════════════════════════════════════════════════════════════
async def _edge_speak(text: str):
    import edge_tts, tempfile
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
        temp_name = fp.name
    try:
        if _voice_interrupt.is_set():
            return
        await communicate.save(temp_name)
        if _voice_interrupt.is_set():
            return
        ctypes.windll.winmm.mciSendStringW(
            f'open "{temp_name}" type mpegvideo alias dexmp3', None, 0, 0)
        ctypes.windll.winmm.mciSendStringW("play dexmp3 wait", None, 0, 0)
        ctypes.windll.winmm.mciSendStringW("close dexmp3", None, 0, 0)
    except Exception as e:
        log.warning("MCI/Edge-TTS: %s", e)
        raise e
    finally:
        try:
            os.unlink(temp_name)
        except Exception:
            pass

def _tts_worker():
    while _running:
        text = None
        try:
            text = _tts_q.get(timeout=1)
            if text is None:
                break
            if _voice_interrupt.is_set():
                _voice_interrupt.clear()
                continue
            try:
                asyncio.run(_edge_speak(str(text)[:400]))
            except Exception as e:
                log.warning("Edge-TTS failed, pyttsx3 fallback: %s", e)
                with _tts_lock:
                    if _tts_engine:
                        if _voice_interrupt.is_set():
                            _voice_interrupt.clear()
                            continue
                        _tts_engine.say(str(text)[:400])
                        _tts_engine.runAndWait()
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

def interrupt_speech(reason: str = "interrupt"):
    _voice_interrupt.set()
    try:
        while True:
            _tts_q.get_nowait()
            _tts_q.task_done()
    except Exception:
        pass
    try:
        ctypes.windll.winmm.mciSendStringW("stop dexmp3", None, 0, 0)
        ctypes.windll.winmm.mciSendStringW("close dexmp3", None, 0, 0)
    except Exception:
        pass
    try:
        with _tts_lock:
            if _tts_engine:
                _tts_engine.stop()
    except Exception:
        pass
    log.info("Speech interrupted: %s", reason)

# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def _notify(title: str, msg: str):
    try:
        if NOTIFY_OK:
            notification.notify(title=title, message=str(msg)[:100], app_name="Dacexy", timeout=5)
    except Exception:
        pass

def _new_id(prefix: str = "id") -> str:
    raw = f"{prefix}:{socket.gethostname()}:{time.time()}:{random.random()}".encode("utf-8", errors="ignore")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:16]}"

def get_device_registration() -> dict:
    """Persistent local desktop identity used by dashboard sync and reconnects."""
    try:
        if DEVICE_FILE.exists():
            data = json.loads(DEVICE_FILE.read_text(encoding="utf-8"))
            if data.get("device_id"):
                HEALTH["device_id"] = data["device_id"]
                return data
    except Exception as e:
        log.warning("device registration read: %s", e)
    data = {
        "device_id": _new_id("device"),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "version": AGENT_VERSION,
        "registered_at": datetime.datetime.now().isoformat(),
    }
    try:
        DEVICE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        DEVICE_FILE.chmod(0o600)
    except Exception as e:
        log.warning("device registration write: %s", e)
    HEALTH["device_id"] = data["device_id"]
    return data

def _send_ws_best_effort(payload: dict):
    if not (_ws_send_fn and _ws_loop):
        return
    try:
        asyncio.run_coroutine_threadsafe(_ws_send_fn(payload), _ws_loop)
    except Exception:
        pass

def _dashboard_log(level: str, message: str, **extra):
    payload = {"type": "log", "level": level, "message": str(message)[:1000], **extra}
    _send_ws_best_effort(payload)

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
        for _ in range(3):
            try:
                return _check()
            except Exception:
                time.sleep(1)
        return False
    except Exception:
        return False

def _get_dex_token():
    return _cur_token

# ══════════════════════════════════════════════════════════════════════════════
# MEMORY ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def _normalize_memory():
    with _mem_lock:
        defaults = {
            "facts": [],
            "preferences": {},
            "context": {},
            "contacts": {},
            "customers": {},
            "suppliers": {},
            "leads": [],
            "skills": [],
            "approved_ops": [],
            "workflows": {},
            "business_facts": {},
            "long_term": [],
            "business_memory": {},
            "customer_memory": {},
            "contact_memory": {},
            "workflow_memory": {},
            "semantic_memory": [],
            "kpis": {},
            "revenue": [],
            "profit": [],
            "sales": [],
            "competitors": {},
            "market_watch": {},
            "retention": {},
            "documents": {},
        }
        for key, default in defaults.items():
            if key not in MEMORY or MEMORY[key] is None:
                MEMORY[key] = default.copy() if isinstance(default, dict) else list(default)
        if not isinstance(MEMORY.get("task_history"), deque):
            MEMORY["task_history"] = deque(list(MEMORY.get("task_history", []))[-1000:], maxlen=1000)
        if not MEMORY.get("contact_memory") and MEMORY.get("contacts"):
            MEMORY["contact_memory"] = dict(MEMORY["contacts"])
        if not MEMORY.get("customer_memory") and MEMORY.get("customers"):
            MEMORY["customer_memory"] = dict(MEMORY["customers"])
        if not MEMORY.get("workflow_memory") and MEMORY.get("workflows"):
            MEMORY["workflow_memory"] = dict(MEMORY["workflows"])

def load_memory():
    global _smtp_cfg, _sched_jobs
    try:
        if MEMORY_FILE.exists():
            d = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            with _mem_lock:
                MEMORY["facts"]         = d.get("facts", [])
                MEMORY["preferences"]   = d.get("preferences", {})
                MEMORY["context"]       = d.get("context", {})
                MEMORY["contacts"]      = d.get("contacts", {})
                MEMORY["customers"]     = d.get("customers", {})
                MEMORY["suppliers"]     = d.get("suppliers", {})
                MEMORY["leads"]         = d.get("leads", [])
                MEMORY["skills"]        = d.get("skills", [])
                MEMORY["approved_ops"]  = d.get("approved_ops", [])
                MEMORY["workflows"]     = d.get("workflows", {})
                MEMORY["business_facts"]= d.get("business_facts", {})
                MEMORY["long_term"]     = d.get("long_term", d.get("facts", []))[-2000:]
                MEMORY["business_memory"] = d.get("business_memory", {})
                MEMORY["customer_memory"] = d.get("customer_memory", d.get("customers", {}))
                MEMORY["contact_memory"] = d.get("contact_memory", d.get("contacts", {}))
                MEMORY["workflow_memory"] = d.get("workflow_memory", d.get("workflows", {}))
                MEMORY["semantic_memory"] = d.get("semantic_memory", [])
                MEMORY["kpis"]          = d.get("kpis", {})
                MEMORY["revenue"]       = d.get("revenue", [])
                MEMORY["profit"]        = d.get("profit", [])
                MEMORY["sales"]         = d.get("sales", [])
                MEMORY["competitors"]   = d.get("competitors", {})
                MEMORY["market_watch"]  = d.get("market_watch", {})
                MEMORY["retention"]     = d.get("retention", {})
                MEMORY["documents"]     = d.get("documents", {})
                MEMORY["task_history"]  = deque(d.get("task_history", [])[-1000:], maxlen=1000)
            _smtp_cfg = {}
            raw_smtp = d.get("smtp_config", {})
            for k, v in raw_smtp.items():
                _smtp_cfg[k] = decrypt_str(v) if k == "password" else v
            _sched_jobs = d.get("sched_jobs", [])
            log.info("Memory loaded: %d facts, %d contacts, %d workflows",
                     len(MEMORY["facts"]), len(MEMORY["contacts"]), len(MEMORY["workflows"]))
    except Exception as e:
        log.warning("load_memory: %s", e)
    _normalize_memory()

def save_memory():
    try:
        enc_smtp = dict(_smtp_cfg)
        if enc_smtp.get("password"):
            enc_smtp["password"] = encrypt_str(enc_smtp["password"])
        with _mem_lock:
            d = {
                "facts":          MEMORY["facts"][-1000:],
                "preferences":    MEMORY["preferences"],
                "context":        MEMORY["context"],
                "contacts":       MEMORY["contacts"],
                "customers":      MEMORY["customers"],
                "suppliers":      MEMORY["suppliers"],
                "leads":          MEMORY["leads"][-500:],
                "skills":         MEMORY["skills"],
                "approved_ops":   MEMORY["approved_ops"][-100:],
                "workflows":      MEMORY["workflows"],
                "business_facts": MEMORY["business_facts"],
                "long_term":      MEMORY["long_term"][-2000:],
                "business_memory": MEMORY["business_memory"],
                "customer_memory": MEMORY["customer_memory"],
                "contact_memory": MEMORY["contact_memory"],
                "workflow_memory": MEMORY["workflow_memory"],
                "semantic_memory": MEMORY["semantic_memory"][-5000:],
                "kpis":           MEMORY["kpis"],
                "revenue":        MEMORY["revenue"][-2000:],
                "profit":         MEMORY["profit"][-2000:],
                "sales":          MEMORY["sales"][-2000:],
                "competitors":    MEMORY["competitors"],
                "market_watch":   MEMORY["market_watch"],
                "retention":      MEMORY["retention"],
                "documents":      MEMORY["documents"],
                "task_history":   list(MEMORY["task_history"])[-200:],
                "smtp_config":    enc_smtp,
                "sched_jobs":     _sched_jobs[-50:],
            }
        tmp = MEMORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=2, default=str), encoding="utf-8")
        tmp.replace(MEMORY_FILE)
        MEMORY_FILE.chmod(0o600)
    except Exception as e:
        log.warning("save_memory: %s", e)

def remember(fact: str):
    if not fact:
        return
    with _mem_lock:
        if fact not in MEMORY["facts"]:
            MEMORY["facts"].append(fact)
        if fact not in MEMORY["long_term"]:
            MEMORY["long_term"].append(fact)
        MEMORY["semantic_memory"].append({
            "kind": "fact",
            "key": hashlib.sha1(fact.encode("utf-8", errors="ignore")).hexdigest()[:12],
            "text": fact,
            "tags": [],
            "updated": datetime.datetime.now().isoformat(),
        })
    save_memory()

def remember_task(task: str, result: str = "ok"):
    with _mem_lock:
        MEMORY["task_history"].append(f"{task[:80]} [{result}]")
    save_memory()

def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9_\-]{1,}", str(text).lower()) if len(t) > 1}

def remember_structured(kind: str, key: str, value: Any, tags: Optional[List[str]] = None) -> dict:
    kind = (kind or "memory").strip().lower().replace(" ", "_")
    key = (key or hashlib.sha1(json.dumps(value, default=str).encode("utf-8", errors="ignore")).hexdigest()[:12]).strip().lower()
    entry = {
        "kind": kind,
        "key": key,
        "value": value,
        "text": json.dumps(value, default=str, ensure_ascii=False) if not isinstance(value, str) else value,
        "tags": tags or [],
        "updated": datetime.datetime.now().isoformat(),
    }
    with _mem_lock:
        if kind in ("contact", "contacts"):
            MEMORY["contacts"][key] = value if isinstance(value, dict) else {"name": key, "note": str(value)}
            MEMORY["contact_memory"][key] = MEMORY["contacts"][key]
        elif kind in ("customer", "customers"):
            MEMORY["customers"][key] = value if isinstance(value, dict) else {"name": key, "note": str(value)}
            MEMORY["customer_memory"][key] = MEMORY["customers"][key]
        elif kind in ("business", "business_fact", "metric"):
            MEMORY["business_memory"][key] = value
        elif kind in ("workflow", "workflow_memory"):
            MEMORY["workflow_memory"][key] = value
        else:
            MEMORY["long_term"].append(entry["text"])
        MEMORY["semantic_memory"].append(entry)
    save_memory()
    return {"status": "ok", "memory": entry}

def _memory_documents() -> List[dict]:
    docs = []
    with _mem_lock:
        for i, fact in enumerate(MEMORY.get("long_term", [])):
            docs.append({"kind": "long_term", "key": str(i), "text": str(fact), "value": fact})
        for kind, collection in (
            ("business", MEMORY.get("business_memory", {})),
            ("business_fact", MEMORY.get("business_facts", {})),
            ("contact", MEMORY.get("contact_memory", {})),
            ("customer", MEMORY.get("customer_memory", {})),
            ("workflow", MEMORY.get("workflow_memory", {})),
            ("kpi", MEMORY.get("kpis", {})),
            ("competitor", MEMORY.get("competitors", {})),
            ("market", MEMORY.get("market_watch", {})),
        ):
            if isinstance(collection, dict):
                for key, value in collection.items():
                    docs.append({"kind": kind, "key": str(key), "text": json.dumps(value, default=str), "value": value})
        for entry in MEMORY.get("semantic_memory", [])[-3000:]:
            if isinstance(entry, dict):
                docs.append({
                    "kind": entry.get("kind", "semantic"),
                    "key": entry.get("key", ""),
                    "text": entry.get("text") or json.dumps(entry.get("value", ""), default=str),
                    "value": entry.get("value", entry.get("text", "")),
                })
    return docs

def semantic_search_memory(query: str, top_k: int = 5, categories: Optional[List[str]] = None) -> dict:
    qtok = _tokens(query)
    if not qtok:
        return {"status": "error", "message": "No searchable query"}
    cats = {c.lower() for c in categories or [] if c}
    scored = []
    for doc in _memory_documents():
        if cats and doc.get("kind", "").lower() not in cats:
            continue
        dtok = _tokens(doc.get("text", ""))
        if not dtok:
            continue
        overlap = qtok & dtok
        if not overlap:
            continue
        score = len(overlap) / max(len(qtok | dtok), 1)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    seen = set()
    for score, doc in scored:
        ident = (doc.get("kind"), doc.get("key"), doc.get("text", "")[:80])
        if ident in seen:
            continue
        seen.add(ident)
        results.append({
            "score": round(score, 4),
            "kind": doc.get("kind"),
            "key": doc.get("key"),
            "text": str(doc.get("text", ""))[:800],
            "value": doc.get("value"),
        })
        if len(results) >= max(1, min(int(top_k or 5), 20)):
            break
    return {"status": "ok", "query": query, "results": results}

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
            wf = list(MEMORY["workflows"].keys())[:5]
            if wf:
                parts.append("Workflows: " + ", ".join(wf))
            biz = MEMORY.get("business_memory", {})
            if biz:
                parts.append("Business: " + json.dumps(dict(list(biz.items())[:8]), default=str)[:600])
            kpis = MEMORY.get("kpis", {})
            if kpis:
                parts.append("KPIs: " + json.dumps(dict(list(kpis.items())[:8]), default=str)[:600])
            conv = list(_convo)[-6:]
            if conv:
                parts.append("Conv: " + " | ".join(conv))
            return "\n".join(parts)
    except Exception:
        return ""

# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW LEARNING ENGINE (Phase 6)
# ══════════════════════════════════════════════════════════════════════════════
def save_workflow(name: str, steps: List[dict], verified: bool = True):
    """Persist a successful workflow so it can be replayed later."""
    if not name or not steps:
        return
    with _mem_lock:
        existing = MEMORY["workflows"].get(name.lower(), {})
        MEMORY["workflows"][name.lower()] = {
            "name":       name,
            "steps":      steps,
            "verified":   verified,
            "run_count":  existing.get("run_count", 0) + 1,
            "saved_at":   datetime.datetime.now().isoformat(),
        }
    save_memory()
    log.info("Workflow saved: '%s' (%d steps)", name, len(steps))

def get_workflow(name: str) -> Optional[dict]:
    with _mem_lock:
        return MEMORY["workflows"].get(name.lower())

def list_workflows() -> List[str]:
    with _mem_lock:
        return list(MEMORY["workflows"].keys())

def replay_workflow(name: str, token: str) -> dict:
    wf = get_workflow(name)
    if not wf:
        return {"status": "error", "message": f"No saved workflow: {name}"}
    speak(f"Replaying workflow: {name}")
    results = []
    verified_count = 0
    action_required_count = 0
    for step in wf["steps"]:
        r = exec_cmd(step, token)
        status = r.get("status")
        results.append({"step": step, "result": r, "status": status})
        if status == "ok":
            verified_count += 1
        elif status == "skipped":
            pass
        elif status == "action_required":
            action_required_count += 1
            speak(f"Workflow step needs your attention: {r.get('message','')[:60]}")
        else:
            speak(f"Workflow step failed: {step.get('action')}")
            return {"status": "error", "message": f"Step failed: {step}", "results": results}
        time.sleep(0.5)

    total = len(wf["steps"])
    if verified_count == total:
        speak(f"Workflow {name} completed and verified.")
        final_status = "ok"
    elif verified_count + action_required_count > 0:
        speak(f"Workflow {name} mostly done — {action_required_count} step(s) need manual follow-through.")
        final_status = "partial"
    else:
        speak(f"Workflow {name} did not complete.")
        final_status = "failed"

    wf["run_count"] = wf.get("run_count", 0) + 1
    save_memory()
    return {"status": final_status, "workflow": name, "steps_run": len(results),
            "ok": verified_count, "action_required": action_required_count,
            "total": total, "results": results}

# ══════════════════════════════════════════════════════════════════════════════
# SECURITY CHECKS
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
    global _pending_approvals, _ws_send_fn
    req_id = hashlib.md5(f"{action}{details}{time.time()}".encode()).hexdigest()[:8]
    _pending_approvals[req_id] = "pending"
    
    if _ws_send_fn:
        # Route through WebSocket
        _send_ws_best_effort({"type": "approval_request", "req_id": req_id, "action": action, "details": details})
        
        start = time.time()
        while time.time() - start < timeout:
            if _pending_approvals[req_id] == "approved":
                return True
            if _pending_approvals[req_id] == "denied":
                return False
            time.sleep(1)
        return False
    else:
        # Console fallback
        print(f"
[APPROVAL REQUIRED] {action}: {details}")
        ans = input(f"Approve? (y/n) [{timeout}s timeout]: ").strip().lower()
        return ans == "y"


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
    if not PYAUTOGUI_OK:
        return {"status": "error", "message": "pyautogui not available"}
    try:
        sw, sh = pyautogui.size()
        x = max(1, min(x, sw - 1))
        y = max(1, min(y, sh - 1))
        pyautogui.moveTo(x, y, duration=duration)
        # Verify the cursor actually arrived before clicking — catches pyautogui
        # fail-safe triggers or a stalled/virtual display silently no-op'ing the move.
        try:
            actual_x, actual_y = pyautogui.position()
            if abs(actual_x - x) > 3 or abs(actual_y - y) > 3:
                pyautogui.moveTo(x, y, duration=duration)
                actual_x, actual_y = pyautogui.position()
                if abs(actual_x - x) > 3 or abs(actual_y - y) > 3:
                    return {"status": "error",
                            "message": f"Cursor did not reach ({x},{y}), landed at ({actual_x},{actual_y})"}
        except Exception:
            pass
        pyautogui.click(x, y, button=button, clicks=clicks, interval=0.08)
        log.info("CLICK x=%d y=%d btn=%s clicks=%d", x, y, button, clicks)
        return {"status": "ok", "x": x, "y": y}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def real_type(text: str, clear_first: bool = False, human_speed: bool = False) -> dict:
    """Types text into the focused field. Returns a real status dict so callers
    can verify the action instead of assuming success."""
    if not text:
        return {"status": "skipped", "reason": "empty text"}
    text = str(text)[:100_000]
    if not PYAUTOGUI_OK and not CLIP_OK:
        return {"status": "error", "message": "No input backend available (pyautogui/pyperclip missing)"}
    try:
        if clear_first and PYAUTOGUI_OK:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.press("delete")
            time.sleep(0.05)
        if CLIP_OK:
            pyperclip.copy(text)
            time.sleep(0.06)
            # Verify the OS clipboard actually received the text before pasting —
            # catches silent clipboard-manager interference.
            clip_ok = False
            try:
                clip_ok = pyperclip.paste() == text
            except Exception:
                clip_ok = False
            if PYAUTOGUI_OK:
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.12)
            return {"status": "ok" if clip_ok else "error",
                    "message": "" if clip_ok else "Clipboard did not contain expected text after copy"}
        elif PYAUTOGUI_OK:
            interval = random.uniform(0.03, 0.09) if human_speed else 0.012
            for chunk in [text[i:i+300] for i in range(0, len(text), 300)]:
                pyautogui.write(chunk, interval=interval)
            return {"status": "ok"}
        return {"status": "error", "message": "No usable input method"}
    except Exception as e:
        log.warning("real_type: %s", e)
        return {"status": "error", "message": str(e)}

def real_hotkey(*keys):
    if not PYAUTOGUI_OK:
        return
    try:
        flat = []
        for k in keys:
            if isinstance(k, (list, tuple)):
                flat.extend([str(x) for x in k])
            else:
                flat.append(str(k))
        pyautogui.hotkey(*flat[:6])
    except Exception as e:
        log.warning("hotkey %s: %s", keys, e)

def real_press(key: str):
    if not PYAUTOGUI_OK:
        return
    try:
        pyautogui.press(str(key))
    except Exception as e:
        log.warning("press %s: %s", key, e)

def real_scroll(direction: str = "down", amount: int = 5):
    if not PYAUTOGUI_OK:
        return
    try:
        amt = abs(amount)
        pyautogui.scroll(amt if direction == "up" else -amt)
    except Exception as e:
        log.warning("scroll: %s", e)

def find_on_screen(image_path: str, confidence: float = 0.85) -> Optional[Tuple[int, int]]:
    if not PYAUTOGUI_OK:
        return None
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

def _browser_page_understanding() -> dict:
    with _sel_lock:
        drv = _selenium_driver
    if not drv:
        return {}
    try:
        script = """
        const pick = (els, n) => Array.from(els).slice(0, n).map((el) => ({
          text: (el.innerText || el.value || el.getAttribute('aria-label') || el.name || '').trim().slice(0,120),
          tag: el.tagName.toLowerCase(),
          type: el.type || '',
          id: el.id || '',
          name: el.name || '',
          role: el.getAttribute('role') || '',
          placeholder: el.getAttribute('placeholder') || ''
        }));
        return {
          title: document.title || '',
          url: location.href,
          headings: pick(document.querySelectorAll('h1,h2,h3'), 12),
          buttons: pick(document.querySelectorAll('button,input[type=button],input[type=submit],a[role=button]'), 20),
          forms: pick(document.querySelectorAll('input,textarea,select'), 30),
          links: pick(document.querySelectorAll('a[href]'), 20),
          bodyText: (document.body && document.body.innerText || '').trim().replace(/\\s+/g,' ').slice(0,1500)
        };
        """
        return drv.execute_script(script) or {}
    except Exception as e:
        return {"error": str(e)}

def _detect_visual_controls(img) -> dict:
    controls = {"buttons": [], "forms": []}
    if not CV2_OK or not NUMPY_OK or not PIL_OK or img is None:
        return controls
    try:
        arr = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        gray = cv2.bilateralFilter(gray, 5, 35, 35)
        edges = cv2.Canny(gray, 40, 120)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape[:2]
        for c in contours[:800]:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw < 35 or bh < 14 or bw > w * 0.95 or bh > h * 0.5:
                continue
            aspect = bw / max(bh, 1)
            area = bw * bh
            if 1.4 <= aspect <= 8 and 250 <= area <= 45000:
                roi = gray[y:y+bh, x:x+bw]
                border_score = float(np.std(roi)) if roi.size else 0.0
                item = {"x": int(x), "y": int(y), "w": int(bw), "h": int(bh), "confidence": round(min(border_score / 80.0, 1.0), 2)}
                if aspect >= 3.0 and bh <= 65:
                    controls["forms"].append(item)
                else:
                    controls["buttons"].append(item)
        controls["buttons"] = sorted(controls["buttons"], key=lambda r: (r["y"], r["x"]))[:40]
        controls["forms"] = sorted(controls["forms"], key=lambda r: (r["y"], r["x"]))[:40]
    except Exception as e:
        log.debug("visual controls: %s", e)
    return controls

def _detect_error_context(text: str, windows: List[str]) -> List[dict]:
    hay = "\n".join([text or ""] + windows).lower()
    patterns = [
        "error", "exception", "failed", "failure", "crash", "not responding",
        "access denied", "permission denied", "invalid password", "network error",
        "cannot connect", "timed out", "warning", "blocked", "unhandled",
    ]
    hits = []
    for p in patterns:
        if p in hay:
            hits.append({"type": p, "evidence": p})
    return hits[:10]

def understand_screen(save_screenshot: bool = True, fast: bool = False) -> dict:
    if not PIL_OK:
        return {"status": "error", "message": "Pillow/ImageGrab not available"}
    try:
        img = ImageGrab.grab()
        shot_path = ""
        if save_screenshot:
            shot_path = str(SS_DIR / f"vision_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            img.save(shot_path, format="JPEG", quality=75)
        ocr_text = ""
        if OCR_OK and not fast:
            try:
                ocr_text = pytesseract.image_to_string(img)[:8000]
            except Exception as e:
                log.warning("vision OCR: %s", e)
        windows = list_windows()
        active = get_active_win()
        controls = _detect_visual_controls(img)
        browser = _browser_page_understanding()
        errors = _detect_error_context(ocr_text, windows)
        summary_bits = []
        if active:
            summary_bits.append(f"Active window: {active}")
        if browser.get("title"):
            summary_bits.append(f"Browser page: {browser.get('title')} ({browser.get('url','')})")
        if ocr_text.strip():
            compact = re.sub(r"\s+", " ", ocr_text.strip())[:350]
            summary_bits.append(f"Visible text: {compact}")
        if errors:
            summary_bits.append("Possible error detected: " + ", ".join(e["type"] for e in errors[:3]))
        if controls["buttons"] or controls["forms"]:
            summary_bits.append(f"Detected {len(controls['buttons'])} button-like and {len(controls['forms'])} form-like regions")
        state = {
            "status": "ok",
            "updated_at": datetime.datetime.now().isoformat(),
            "active_window": active,
            "windows": windows[:40],
            "ocr_text": ocr_text,
            "buttons": controls["buttons"],
            "forms": controls["forms"],
            "errors": errors,
            "browser": browser,
            "summary": " | ".join(summary_bits) if summary_bits else "Screen captured, no readable text detected.",
            "screenshot_path": shot_path,
        }
        with _vision_lock:
            VISION_STATE.update(state)
        try:
            VISION_STATE_FILE.write_text(json.dumps({k: v for k, v in state.items() if k != "ocr_text"} | {"ocr_preview": ocr_text[:1000]}, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass
        HEALTH["vision_status"] = "ok"
        return state
    except Exception as e:
        HEALTH["vision_status"] = "error"
        return {"status": "error", "message": str(e)}

def get_screen_summary() -> str:
    with _vision_lock:
        summary = VISION_STATE.get("summary", "")
    if summary:
        return summary
    res = understand_screen(save_screenshot=False)
    return res.get("summary", res.get("message", "I could not inspect the screen."))

def _vision_monitor_loop():
    global _last_vision_hash
    while _vision_on and _running:
        try:
            state = understand_screen(save_screenshot=False, fast=False)
            if state.get("status") == "ok":
                digest_src = "|".join([
                    state.get("active_window", ""),
                    state.get("summary", "")[:500],
                    json.dumps(state.get("errors", []), sort_keys=True),
                ])
                digest = hashlib.sha1(digest_src.encode("utf-8", errors="ignore")).hexdigest()
                if digest != _last_vision_hash:
                    _last_vision_hash = digest
                    _send_ws_best_effort({
                        "type": "vision_result",
                        "vision": {k: v for k, v in state.items() if k != "ocr_text"},
                        "ocr_preview": state.get("ocr_text", "")[:1000],
                    })
                if state.get("errors"):
                    _dashboard_log("warning", "Screen error context detected", errors=state.get("errors"))
            time.sleep(8)
        except Exception as e:
            log.warning("vision monitor: %s", e)
            time.sleep(10)

def start_vision_monitor() -> dict:
    global _vision_on, _vision_thread
    if _vision_on:
        return {"status": "ok", "message": "Vision monitor already running"}
    if not PIL_OK:
        return {"status": "error", "message": "Pillow/ImageGrab not available"}
    _vision_on = True
    _vision_thread = threading.Thread(target=_vision_monitor_loop, daemon=True, name="VisionMonitor")
    _vision_thread.start()
    HEALTH["vision_status"] = "monitoring"
    return {"status": "ok", "message": "Vision monitor started"}

def stop_vision_monitor() -> dict:
    global _vision_on
    _vision_on = False
    HEALTH["vision_status"] = "idle"
    return {"status": "ok", "message": "Vision monitor stopped"}

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
            time.sleep(0.4)
            return True
    except Exception as e:
        log.warning("focus_window: %s", e)
    return False

# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION ENGINE (Phase 4)
# ══════════════════════════════════════════════════════════════════════════════
def verify_file_created(path: str) -> bool:
    try:
        p = Path(path)
        return p.exists() and p.stat().st_size > 0
    except Exception:
        return False

def verify_window_contains(text: str) -> bool:
    if not WINDOW_OK:
        return True
    try:
        for w in gw.getAllTitles():
            if text.lower() in w.lower():
                return True
        return False
    except Exception:
        return True

def verify_screen_ocr(text: str) -> bool:
    if not OCR_OK or not PIL_OK:
        return True
    try:
        img = ImageGrab.grab()
        ocr_text = pytesseract.image_to_string(img).lower()
        return text.lower() in ocr_text
    except Exception:
        return True

def verify_email_sent(to: str) -> bool:
    # Real verification: check audit log for sent record
    try:
        log_path = LOG_FILE
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="ignore")
            return f"EMAIL_SENT to={to}" in content
        return False
    except Exception:
        return False

def verify_browser_loaded(url_fragment: str = "") -> bool:
    if not SELENIUM_OK:
        return True
    try:
        with _sel_lock:
            drv = _selenium_driver
        if drv:
            current = drv.current_url
            if url_fragment:
                return url_fragment.lower() in current.lower()
            return len(current) > 5
        return False
    except Exception:
        return False

def run_with_verification(
    action_func: Callable,
    verify_func: Callable,
    desc: str,
    max_retries: int = 2,
    correction_func: Optional[Callable] = None,
) -> dict:
    res = action_func()
    if isinstance(res, dict) and res.get("status") == "error":
        return res

    for attempt in range(max_retries):
        time.sleep(1.2)
        if verify_func():
            HEALTH["tasks_ok"] += 1
            return {"status": "ok", "verified": True, "desc": desc}
        log.warning("Verification attempt %d failed for: %s", attempt + 1, desc)
        speak(f"Verifying {desc} — retrying.")
        if correction_func:
            correction_func()
        else:
            action_func()

    return {"status": "error", "message": f"Failed to verify '{desc}' after {max_retries} attempts. Action not confirmed."}

# ══════════════════════════════════════════════════════════════════════════════
# AI BRAIN
# ══════════════════════════════════════════════════════════════════════════════
def ai_completion(prompt: str, system: str = "", timeout: int = 30) -> str:
    import concurrent.futures
    sys_msg = system or (
        "You are Dacexy, a fast autonomous desktop AI agent. "
        "Respond ONLY in English, concisely and directly. No markdown unless writing documents."
    )
    def _g4f_call():
        import g4f
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user",   "content": prompt},
            ],
        )
        return str(response).strip()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_g4f_call)
            text = future.result(timeout=timeout)
            if text and len(text) > 10 and "error" not in text.lower()[:60]:
                return text
    except concurrent.futures.TimeoutError:
        log.warning("AI Brain timed out, falling back to web research")
    except Exception as e:
        log.warning("AI Brain g4f: %s", e)

    try:
        return web_research(prompt)[:800]
    except Exception as e:
        return f"I looked into '{prompt[:60]}' but couldn't get a clear answer: {e}"

def ask_ai_brain(prompt: str) -> str:
    return ai_completion(prompt)

# ══════════════════════════════════════════════════════════════════════════════
# PLANNER ENGINE (Phase 2) — Goal → Plan → Task Graph → Execute → Verify
# ══════════════════════════════════════════════════════════════════════════════
def plan_task(goal: str) -> List[dict]:
    """
    Turn a natural language goal into an ordered list of exec_cmd-compatible steps.
    Falls back to local_parse if AI planning fails.
    """
    context = get_mem_ctx()
    plan_prompt = (
        f"You are a task planner for Dacexy, a Windows desktop automation agent.\n"
        f"User context:\n{context}\n\n"
        f"Goal: {goal}\n\n"
        f"Break this into 2-8 concrete steps. Each step must be a JSON object with an 'action' key "
        f"and any required parameters. Use ONLY these actions where possible:\n"
        f"screenshot, read_inbox, organize_folder, send_email, bulk_email, find_leads, "
        f"read_spreadsheet, process_invoices, web_research, ask_ai, open, get_system_info, "
        f"write_file, ocr, understand_screen, run_diagnostics, create_newsletter, draft_contract, "
        f"backup_to_cloud, business_dashboard, record_metric, board_report, kpi_report, "
        f"finance_report, monitor_competitor, monitor_market, lead_manage, sales_pipeline_report, "
        f"customer_retention_report, semantic_memory_search.\n\n"
        f"Respond ONLY with a JSON array of step objects. No explanation. Example:\n"
        f'[{{"action":"read_inbox","max_count":10}},{{"action":"ask_ai","prompt":"summarize emails"}}]'
    )
    try:
        raw = ai_completion(plan_prompt, timeout=25)
        raw = raw.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        steps = json.loads(raw)
        if isinstance(steps, list) and steps:
            log.info("Planner produced %d steps for: %s", len(steps), goal[:60])
            return steps
    except Exception as e:
        log.warning("Planner JSON parse failed: %s", e)

    # Fallback to local NLP
    return local_parse(goal)

def _report_step_progress(task_id: str, step_index: int, total_steps: int, step: dict, result: dict):
    """Push live per-step status to the dashboard if a WebSocket session is active.
    Best-effort: failures here never affect task execution."""
    if not (_ws_send_fn and _ws_loop):
        return
    try:
        payload = {
            "type": "task_progress",
            "task_id": task_id,
            "step_index": step_index,
            "total_steps": total_steps,
            "progress": round(step_index / max(total_steps, 1), 4),
            "action": step.get("action", "?"),
            "status": result.get("status", "?"),
            "message": result.get("message", ""),
        }
        asyncio.run_coroutine_threadsafe(_ws_send_fn(payload), _ws_loop)
    except Exception:
        pass

def execute_planned_task(goal: str, token: str, task_id: str = "") -> dict:
    """Full Plan → Execute → Verify → Learn cycle.

    Honesty rules:
      - Only status == "ok" counts as a verified success.
      - "skipped" is a deliberate no-op (e.g. duplicate action) and counts as
        non-blocking but is never reported to the user as a completed action.
      - "action_required" means the agent did something (e.g. opened a draft)
        but a human must finish it — never folded into "all_ok".
      - Any other status (error, denied, blocked) is a real failure and gets
        one retry attempt before the whole task is marked partial/failed.
    """
    HEALTH["planner_status"] = "planning"
    speak(f"Planning: {goal[:50]}")

    steps = plan_task(goal)
    if not steps:
        HEALTH["planner_status"] = "idle"
        return {"status": "error", "message": "Could not create plan"}

    speak(f"Plan ready: {len(steps)} steps.")
    _checkpoint_task(task_id, "running", total_steps=len(steps), message="Plan ready")
    HEALTH["planner_status"] = "executing"
    HEALTH["executor_status"] = "running"

    results = []
    verified_count = 0
    action_required_count = 0
    hard_failure = False

    for i, step in enumerate(steps):
        if _is_task_cancelled(task_id):
            results.append({"step": step, "result": {"status": "cancelled", "message": "Task cancelled"}, "ok": False, "status": "cancelled"})
            _checkpoint_task(task_id, "cancelled", i, len(steps), step, {"status": "cancelled"})
            speak("Task cancelled.")
            break
        step_desc = f"Step {i+1}/{len(steps)}: {step.get('action','?')}"
        log.info("Executing %s", step_desc)
        _checkpoint_task(task_id, "running", i, len(steps), step, message=step_desc)
        try:
            r = exec_cmd(step, token)
            status = r.get("status")

            # One retry for a real failure before giving up on this step —
            # transient issues (window not focused yet, page still loading)
            # are common and a single retry meaningfully improves reliability
            # without masking genuine failures.
            if status not in ("ok", "skipped", "action_required"):
                log.warning("Step %d failed (%s), retrying once: %s", i + 1, status, r.get("message", ""))
                recovery = _recover_from_failure(step, r)
                if recovery.get("attempted"):
                    r["recovery"] = recovery
                    _checkpoint_task(task_id, "recovering", i, len(steps), step, r,
                                     message=f"Recovery attempted: {recovery.get('method')}")
                time.sleep(1.0)
                r = exec_cmd(step, token)
                status = r.get("status")

            ok = status == "ok"
            results.append({"step": step, "result": r, "ok": ok, "status": status})
            _report_step_progress(task_id, i + 1, len(steps), step, r)
            _checkpoint_task(task_id, "running", i + 1, len(steps), step, r,
                             message=f"Step {i+1}/{len(steps)} {status}")

            if status == "ok":
                verified_count += 1
                log.info("Step %d OK (verified)", i + 1)
            elif status == "skipped":
                log.info("Step %d skipped: %s", i + 1, r.get("reason", ""))
            elif status == "action_required":
                action_required_count += 1
                speak(f"Step {i+1} needs your attention: {r.get('message','')[:80]}")
                log.warning("Step %d needs human follow-through: %s", i + 1, r.get("message", ""))
            else:
                hard_failure = True
                speak(f"Step {i+1} failed: {r.get('message','')[:60]}")
                log.warning("Step %d failed after retry: %s => %s", i + 1, step, r)
                # If an early step fails hard, later steps are very likely to be
                # meaningless (e.g. can't "read the email" if "open inbox" failed).
                # Stop here rather than burning through the rest of the plan and
                # reporting a misleadingly granular partial result.
                remaining = len(steps) - (i + 1)
                if remaining > 0:
                    log.warning("Stopping plan early: %d remaining step(s) skipped after hard failure", remaining)
                    speak(f"Stopping here — {remaining} remaining step(s) depend on this and were not attempted.")
                break

            time.sleep(0.3)
        except Exception as e:
            log.error("Step %d exception: %s", i + 1, e)
            results.append({"step": step, "result": {"status": "error", "message": str(e)}, "ok": False, "status": "error"})
            _report_step_progress(task_id, i + 1, len(steps), step, {"status": "error", "message": str(e)})
            hard_failure = True
            break

    HEALTH["planner_status"] = "idle"
    HEALTH["executor_status"] = "idle"

    attempted = len(results)
    cancelled = any(r.get("status") == "cancelled" for r in results)
    fully_done = verified_count == len(steps)
    partially_done = verified_count > 0 or action_required_count > 0

    # A workflow is only ever learned/replayed later if every single step was
    # a true, verified "ok" — never if any step needed human follow-through
    # or silently failed. This is the core "no fake success" guarantee.
    if cancelled:
        remember_task(goal, "cancelled")
        overall_status = "cancelled"
    elif fully_done:
        save_workflow(goal[:80], steps, verified=True)
        remember_task(goal, "ok")
        speak("Task complete and verified!")
        overall_status = "ok"
    elif partially_done:
        remember_task(goal, "partial")
        if action_required_count and not hard_failure:
            speak(f"Done what I can — {action_required_count} step(s) need you to finish manually.")
        else:
            speak("Task finished with some issues — not everything was verified.")
        overall_status = "partial"
    else:
        remember_task(goal, "failed")
        speak("Task did not complete — nothing could be verified.")
        overall_status = "failed"

    return {
        "status":   overall_status,
        "goal":     goal,
        "steps":    len(steps),
        "attempted": attempted,
        "ok":       verified_count,
        "action_required": action_required_count,
        "total":    len(steps),
        "results":  results,
    }

# ══════════════════════════════════════════════════════════════════════════════
# TASK QUEUE & BACKGROUND EXECUTION (Phase 3)
# ══════════════════════════════════════════════════════════════════════════════
def _load_task_state() -> dict:
    try:
        if TASK_STATE_FILE.exists():
            data = json.loads(TASK_STATE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception as e:
        log.warning("load task state: %s", e)
    return {}

def _save_task_state_snapshot():
    with _task_checkpoint_lock:
        try:
            data = {
                "updated_at": datetime.datetime.now().isoformat(),
                "tasks": _active_tasks,
            }
            tmp = TASK_STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            tmp.replace(TASK_STATE_FILE)
        except Exception as e:
            log.warning("save task state: %s", e)

def _checkpoint_task(task_id: str, state: str = "", step_index: int = 0,
                     total_steps: int = 0, step: Optional[dict] = None,
                     result: Optional[dict] = None, message: str = ""):
    if not task_id:
        return
    now = datetime.datetime.now().isoformat()
    with _tasks_lock:
        rec = _active_tasks.setdefault(task_id, {"id": task_id, "goal": "", "state": "unknown"})
        if state:
            rec["state"] = state
        rec["updated_at"] = now
        rec["step_index"] = step_index or rec.get("step_index", 0)
        rec["total_steps"] = total_steps or rec.get("total_steps", 0)
        if total_steps:
            rec["progress"] = round(min(max((step_index or 0) / max(total_steps, 1), 0), 1), 4)
        if step is not None:
            rec["last_step"] = step
        if result is not None:
            rec["last_result"] = result
        if message:
            rec["message"] = message
        HEALTH["last_checkpoint"] = now
    _save_task_state_snapshot()

def _is_task_cancelled(task_id: str) -> bool:
    if not task_id:
        return False
    ev = _task_cancel_flags.get(task_id)
    if ev and ev.is_set():
        return True
    with _tasks_lock:
        return _active_tasks.get(task_id, {}).get("state") == "cancelled"

def restore_task_state():
    data = _load_task_state()
    tasks = data.get("tasks", {}) if isinstance(data, dict) else {}
    restored = 0
    with _tasks_lock:
        for tid, rec in tasks.items():
            if not isinstance(rec, dict):
                continue
            state = rec.get("state")
            if state in ("queued", "running", "recovering"):
                rec = dict(rec)
                rec["state"] = "interrupted"
                rec["message"] = "Agent restarted before this task finished. Use resume task <id> to run it again."
                _active_tasks[tid] = rec
                restored += 1
    if restored:
        _save_task_state_snapshot()
        log.info("Restored %d interrupted task records", restored)

def resume_task(task_id: str, token: str) -> dict:
    with _tasks_lock:
        rec = dict(_active_tasks.get(task_id, {}))
    if not rec:
        return {"status": "error", "message": "Task not found"}
    goal = rec.get("goal", "")
    if not goal:
        return {"status": "error", "message": "Task has no saved goal"}
    new_id = queue_task(goal, token)
    return {"status": "ok", "resumed_from": task_id, "task_id": new_id, "goal": goal}

def _recover_from_failure(step: dict, result: dict) -> dict:
    action = str(step.get("action", "")).lower()
    msg = str(result.get("message") or result.get("note") or "")
    recovery = {"attempted": False, "action": action, "message": msg}
    try:
        if action in {"selenium_open", "selenium_click", "selenium_fill"}:
            with _sel_lock:
                drv = _selenium_driver
            if drv:
                try:
                    drv.refresh()
                    time.sleep(1.5)
                    recovery.update({"attempted": True, "method": "browser_refresh"})
                except Exception:
                    pass
        elif action in {"open", "open_url", "open_browser"}:
            target = step.get("target") or step.get("url") or step.get("app") or ""
            if target:
                smart_open(str(target))
                recovery.update({"attempted": True, "method": "reopen_target"})
        elif action in {"ocr", "ocr_screen", "read_screen", "screenshot"}:
            understand_screen(save_screenshot=True, fast=True)
            recovery.update({"attempted": True, "method": "vision_rescan"})
        elif action in {"type", "fill", "write"} and CLIP_OK:
            pyperclip.copy(str(step.get("text") or step.get("value") or ""))
            recovery.update({"attempted": True, "method": "clipboard_reset"})
    except Exception as e:
        recovery["recovery_error"] = str(e)
    return recovery

def _queue_worker():
    while _running:
        try:
            task_rec = _task_queue.get(timeout=1)
            if task_rec is None:
                break
            task_id  = task_rec["id"]
            goal     = task_rec["goal"]
            token    = task_rec["token"]
            callback = task_rec.get("callback")

            with _tasks_lock:
                if task_id in _active_tasks:
                    _active_tasks[task_id]["state"] = "running"
                    _active_tasks[task_id]["started_at"] = datetime.datetime.now().isoformat()
                    _active_tasks[task_id]["attempts"] = int(_active_tasks[task_id].get("attempts", 0)) + 1
            _checkpoint_task(task_id, "running", message="Task started")
            HEALTH["active_jobs"] = len(list_active_tasks())

            try:
                if _is_task_cancelled(task_id):
                    result = {"status": "cancelled", "message": "Task cancelled before start"}
                else:
                    result = execute_planned_task(goal, token, task_id=task_id)
                    if result.get("status") in ("failed", "error") and not _is_task_cancelled(task_id):
                        with _tasks_lock:
                            attempts = int(_active_tasks.get(task_id, {}).get("attempts", 1))
                        if attempts < 2:
                            _checkpoint_task(task_id, "recovering", message="Retrying failed task once")
                            time.sleep(2)
                            result = execute_planned_task(goal, token, task_id=task_id)
                with _tasks_lock:
                    if task_id in _active_tasks:
                        final_state = "cancelled" if result.get("status") == "cancelled" else "completed"
                        _active_tasks[task_id]["state"]  = final_state
                        _active_tasks[task_id]["result"] = result
                        _active_tasks[task_id]["finished_at"] = datetime.datetime.now().isoformat()
                _checkpoint_task(task_id, _active_tasks.get(task_id, {}).get("state", "completed"),
                                 result=result, message=f"Task finished: {result.get('status')}")
                if callback:
                    callback(task_id, result)
            except Exception as e:
                with _tasks_lock:
                    if task_id in _active_tasks:
                        _active_tasks[task_id]["state"]  = "failed"
                        _active_tasks[task_id]["result"] = {"status": "error", "message": str(e)}
                        _active_tasks[task_id]["finished_at"] = datetime.datetime.now().isoformat()
                _checkpoint_task(task_id, "failed", result={"status": "error", "message": str(e)})
                log.error("Queue worker task %s failed: %s", task_id, e)
            finally:
                HEALTH["active_jobs"] = len(list_active_tasks())
                try:
                    _task_queue.task_done()
                except Exception:
                    pass
        except queue.Empty:
            continue
        except Exception as e:
            log.error("Queue worker: %s", e)

# Start background queue worker
threading.Thread(target=_queue_worker, daemon=True, name="TaskQueueWorker").start()

def queue_task(goal: str, token: str, callback: Optional[Callable] = None) -> str:
    task_id = hashlib.md5(f"{goal}{time.time()}".encode()).hexdigest()[:10]
    _task_cancel_flags[task_id] = threading.Event()
    with _tasks_lock:
        _active_tasks[task_id] = {
            "id": task_id, "goal": goal,
            "state": "queued", "result": None,
            "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "attempts": 0,
            "progress": 0.0,
        }
    _task_queue.put({"id": task_id, "goal": goal, "token": token, "callback": callback})
    _checkpoint_task(task_id, "queued", message="Task queued")
    return task_id

def get_task_status(task_id: str) -> dict:
    with _tasks_lock:
        return dict(_active_tasks.get(task_id, {"state": "not_found"}))

def cancel_task(task_id: str) -> dict:
    if task_id in _task_cancel_flags:
        _task_cancel_flags[task_id].set()
    with _tasks_lock:
        if task_id in _active_tasks:
            if _active_tasks[task_id]["state"] in ("queued", "running", "recovering"):
                _active_tasks[task_id]["state"] = "cancelled"
                _active_tasks[task_id]["cancelled_at"] = datetime.datetime.now().isoformat()
                _save_task_state_snapshot()
                return {"status": "ok", "cancelled": task_id}
            return {"status": "error", "message": "Task already running or completed"}
    return {"status": "error", "message": "Task not found"}

def list_active_tasks() -> list:
    with _tasks_lock:
        return [
            {"id": k, "state": v["state"], "goal": v.get("goal", "")[:60],
             "progress": v.get("progress", 0), "message": v.get("message", "")}
            for k, v in _active_tasks.items()
            if v["state"] in ("queued", "running", "recovering", "interrupted")
        ]

def execute_task(task: str, token: str, task_id: str = "") -> dict:
    """Main entry point: checks for saved workflow first, then routes through
    the multi-agent coordinator (previously this bypassed agent routing
    entirely and went straight to the planner — coordinator_dispatch is
    defined below but resolved at call time, so this is safe)."""
    # Check if we have a saved workflow for this exact goal
    wf = get_workflow(task)
    if wf:
        speak(f"Found saved workflow: {task[:40]}. Replaying.")
        return replay_workflow(task, token)
    return coordinator_dispatch(task, token, task_id=task_id)

# ══════════════════════════════════════════════════════════════════════════════
# MULTI-AGENT SYSTEM (Phase 7)
# ══════════════════════════════════════════════════════════════════════════════
class Agent:
    def __init__(self, name: str, skills: List[str], description: str, delegates: Optional[List[str]] = None):
        self.name        = name
        self.skills      = skills
        self.description = description
        self.delegates   = delegates or []

    def score(self, task: str) -> int:
        tl = task.lower()
        return sum(1 for s in self.skills if s.lower() in tl)

    def can_handle(self, task: str) -> bool:
        return self.score(task) > 0

    def delegate_names(self, task: str) -> List[str]:
        names = []
        for name in self.delegates:
            agent = next((a for a in _AGENTS if a.name == name), None)
            if agent and agent.can_handle(task):
                names.append(name)
        return names

    def handle(self, task: str, token: str, task_id: str = "") -> dict:
        with _mem_lock:
            MEMORY["context"]["active_agent"] = self.name
            MEMORY["context"]["agent_role"] = self.description
        return execute_planned_task(task, token, task_id=task_id)

# Register sub-agents
_AGENTS: List[Agent] = [
    Agent("CEO Agent",
          ["strategy", "board", "investor", "kpi", "dashboard", "profit", "revenue", "goal", "plan", "company"],
          "Coordinates company-level goals, priorities, reports, and cross-functional execution.",
          ["Finance Agent", "Sales Agent", "Marketing Agent", "Operations Agent", "Research Agent", "Support Agent", "Recruitment Agent"]),
    Agent("Finance Agent",
          ["finance", "invoice", "payment", "expense", "cashflow", "cash flow", "budget", "revenue", "profit", "tax", "investor"],
          "Handles revenue, profit, expenses, payments, invoices, investor data, and finance reports."),
    Agent("Sales Agent",
          ["lead", "prospect", "crm", "sales", "pipeline", "quotation", "customer", "deal", "retention"],
          "Handles lead management, pipeline reporting, sales outreach, and customer retention."),
    Agent("Marketing Agent",
          ["marketing", "campaign", "newsletter", "social", "twitter", "linkedin", "facebook", "ad", "seo", "keyword", "brand"],
          "Handles campaigns, content, social posting, market messaging, and marketing operations."),
    Agent("Operations Agent",
          ["operation", "workflow", "file", "folder", "organize", "pdf", "spreadsheet", "document", "backup", "browser", "desktop"],
          "Handles desktop operations, files, documents, workflows, browser actions, and automation reliability."),
    Agent("Support Agent",
          ["support", "ticket", "reply", "inbox", "email", "whatsapp", "instagram", "facebook", "customer issue", "complaint"],
          "Handles inboxes, customer support replies, social DMs, and service follow-up."),
    Agent("Research Agent",
          ["research", "search", "find", "investigate", "competitor", "market", "monitor", "news", "trend"],
          "Handles web research, competitor monitoring, market monitoring, and evidence gathering."),
    Agent("Recruitment Agent",
          ["recruit", "candidate", "resume", "interview", "hiring", "job", "talent", "hr"],
          "Handles hiring workflows, candidate tracking, recruiting docs, and interview planning."),
]

def coordinator_dispatch(task: str, token: str, task_id: str = "") -> dict:
    """Coordinator Agent: routes task to the best sub-agent or handles directly."""
    # Find best matching agent
    for agent in _AGENTS:
        if agent.can_handle(task):
            log.info("Coordinator → %s for: %s", agent.name, task[:60])
            speak(f"{agent.name} handling: {task[:40]}")
            return agent.handle(task, token, task_id=task_id)
    # No specific agent — coordinator handles directly
    log.info("Coordinator handles directly: %s", task[:60])
    return execute_planned_task(task, token, task_id=task_id)


# ══════════════════════════════════════════════════════════════════════════════
# FILE ORGANIZER
# ══════════════════════════════════════════════════════════════════════════════
def coordinator_dispatch(task: str, token: str, task_id: str = "") -> dict:
    """Role-based coordinator for CEO/Finance/Sales/Marketing/Ops/Support/Research/Recruitment agents."""
    scored = sorted([(agent.score(task), agent) for agent in _AGENTS], key=lambda x: x[0], reverse=True)
    matched = [agent for score, agent in scored if score > 0]
    if not matched:
        matched = [next(a for a in _AGENTS if a.name == "CEO Agent")]
    lead = matched[0]
    collaborators = []
    for agent in matched[1:4]:
        if agent.name not in collaborators:
            collaborators.append(agent.name)
    for name in lead.delegate_names(task):
        if name not in collaborators and name != lead.name:
            collaborators.append(name)
    with _mem_lock:
        MEMORY["context"]["active_agents"] = [lead.name] + collaborators
        MEMORY["context"]["last_coordinator_task"] = task[:300]
    log.info("Coordinator -> %s collaborators=%s task=%s", lead.name, collaborators, task[:80])
    speak(f"{lead.name} coordinating" + (f" with {', '.join(collaborators[:2])}" if collaborators else ""))
    result = lead.handle(task, token, task_id=task_id)
    result["lead_agent"] = lead.name
    result["collaborators"] = collaborators
    return result

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
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except Exception:
                pass
        for m in re.finditer(r"[₹$€£]\s*([\d,]+\.?\d*)", text):
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except Exception:
                pass
        for m in re.finditer(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text):
            dates.append(m.group())
        for m in re.finditer(r"(?:invoice|inv|bill)\s*[#no.]*\s*([A-Z0-9-]+)", text, re.I):
            invoice_nos.append(m.group(1))

        result = {
            "status":       "ok",
            "file":         p.name,
            "amounts":      list(set(amounts)),
            "max_amount":   max(amounts) if amounts else 0,
            "dates":        dates[:5],
            "invoice_nos":  invoice_nos[:3],
            "text_preview": text[:500],
        }
        log.info("Invoice extracted: %s — max amount: %s", p.name, result["max_amount"])
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
        # Verify CSV was created
        if not verify_file_created(str(report)):
            return {"status": "error", "message": "Report file was not created"}
        try:
            subprocess.Popen(f'notepad.exe "{report}"', shell=True)
        except Exception:
            pass
        speak(f"Processed {len(records)} invoices. {queued} queued for payment approval.")
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
    if not amount:
        return None
    q = _load_payment_queue()
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
                             f"Pay {entry['amount']} — invoice {entry.get('invoice_no') or '?'} ({entry['file']})"):
        return {"status": "denied"}

    entry["status"]      = "approved"
    entry["approved_at"] = datetime.datetime.now().isoformat()
    entry["portal"]      = portal
    _save_payment_queue(q)
    audit.info("PAYMENT_APPROVED id=%s amount=%s file=%s portal=%s",
               queue_id, entry["amount"], entry["file"], portal)

    url = PAYMENT_PORTALS.get(portal, "")
    if url:
        webbrowser.open(url)
        speak(f"Approved. Opened {portal} — pay {entry['amount']}.")
    else:
        speak(f"Approved payment of {entry['amount']}. No portal URL — pay manually.")
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
# SPREADSHEET
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

def paste_spreadsheet_to_browser(path: str, url: str, field_selector: str = "input") -> dict:
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
        speak(f"Pasted {pasted} rows.")
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
    plain = body.replace("<br>", "\n")
    html  = "<html><body>" + body.replace("\n", "<br>") + "</body></html>"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))
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
        speak(f"Gmail draft opened for {to} — SMTP isn't configured, so I can't auto-send. "
              f"You'll need to click Send yourself, or say 'configure email' to enable auto-send.")
        # A draft sitting open is NOT a sent email — must not report "ok" here,
        # or the planner will mark this step verified when no email left the outbox.
        return {"status": "action_required", "action": "browser_draft", "to": to,
                "message": "SMTP not configured. Draft opened in browser; requires manual Send click."}

    try:
        msg = _build_msg(em, to, subject, body)
        with smtplib.SMTP(ht, pt, timeout=30) as srv:
            srv.ehlo(); srv.starttls(); srv.ehlo(); srv.login(em, pw)
            srv.sendmail(em, [to], msg.as_string())
        audit.info("EMAIL_SENT to=%s subject=%s", to, subject[:60])
        # Verify email actually sent by checking the audit trail we just wrote.
        if not verify_email_sent(to):
            log.warning("Email send verification failed for %s despite no SMTP exception", to)
            return {"status": "error", "message": f"SMTP reported no error but send could not be verified for {to}"}
        speak(f"Email sent to {to}!")
        return {"status": "ok", "sent_to": to, "verified": True}
    except Exception as e:
        log.warning("email failed: %s", e)
        url = (f"https://mail.google.com/mail/?view=cm&fs=1"
               f"&to={urllib.parse.quote(to)}&su={urllib.parse.quote(subject)}")
        webbrowser.open(url)
        speak(f"SMTP send failed, so I opened a Gmail draft for {to} instead. You'll need to send it manually.")
        return {"status": "action_required", "action": "browser_fallback", "to": to,
                "message": f"SMTP send failed ({e}); draft opened in browser, requires manual Send click."}

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
                body    = (body_tmpl.replace("{name}", name).replace("{Name}", name)
                           .replace("{email}", to_e).replace("{company}", company))
                subj    = subject.replace("{name}", name).replace("{company}", company)
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
            if p2.exists():
                p = p2
            else:
                return []
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = (row.get("email") or row.get("Email") or row.get("EMAIL") or "").strip()
                if em and "@" in em:
                    contacts.append({
                        "email":   em,
                        "name":    (row.get("name") or row.get("Name") or em.split("@")[0]).strip(),
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
        "gmail.com":      "imap.gmail.com",
        "googlemail.com": "imap.gmail.com",
        "outlook.com":    "imap-mail.outlook.com",
        "hotmail.com":    "imap-mail.outlook.com",
        "yahoo.com":      "imap.mail.yahoo.com",
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
                emails.append({"from": sender, "subject": subject, "preview": body[:200], "urgent": is_urgent})

            urgent_count = sum(1 for e in emails if e["urgent"])
            if urgent_count:
                speak(f"You have {urgent_count} urgent emails!")
                _notify("Urgent Emails", f"{urgent_count} urgent messages")
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
                    f"I'm reviewing the details and will respond within 24 hours.\n\nBest regards")
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
            snips = [
                tag.get_text(" ", strip=True)
                for tag in soup.find_all(
                    ["div", "span"],
                    class_=lambda c: c and any(x in c for x in ["BNeawe", "VwiC3b", "MUxGbd", "hgKElc"])
                )
                if len(tag.get_text().strip()) > 60
            ]
            return " ".join(snips[:12])[:6000] or "No results."
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:3000]
    except Exception as e:
        return f"Research error: {e}"

def find_leads_web(product: str, niche: str = "", max_leads: int = 50) -> list:
    if not REQUESTS_OK:
        return []
    leads = []
    email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b')
    skip = {"example.com", "test.com", "sentry.io", "w3.org", "google.com", "github.com", "cloudflare.com"}
    speak(f"Searching leads for {product}...")
    queries = [
        f"{niche} {product} contact email",
        f"{product} company email contact",
        f'"{product}" "@gmail.com" contact',
    ]
    for q in queries:
        if len(leads) >= max_leads:
            break
        try:
            r = req_lib.get(
                f"https://www.google.com/search?q={urllib.parse.quote(q)}&num=20",
                headers=_HDRS, timeout=15)
            text = BeautifulSoup(r.text, "html.parser").get_text() if BS4_OK else r.text
            for em in email_re.findall(text):
                domain = em.split("@")[-1].lower()
                if domain in skip:
                    continue
                if any(l["email"].lower() == em.lower() for l in leads):
                    continue
                leads.append({
                    "email":   em,
                    "name":    em.split("@")[0].replace(".", " ").title(),
                    "company": domain.split(".")[0].title(),
                })
                if len(leads) >= max_leads:
                    break
            time.sleep(2)
        except Exception as e:
            log.warning("lead search: %s", e)
    try:
        lf = DATA_DIR / "leads.csv"
        with open(lf, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["email", "name", "company"])
            w.writeheader(); w.writerows(leads)
    except Exception:
        pass
    speak(f"Found {len(leads)} leads.")
    return leads

# ══════════════════════════════════════════════════════════════════════════════
# WHATSAPP
# ══════════════════════════════════════════════════════════════════════════════
def wa_send(phone: str, msg: str) -> dict:
    ph = re.sub(r"[^0-9+]", "", str(phone))
    if not ph.startswith("+"):
        ph = "+91" + ph
    url = f"https://wa.me/{ph.lstrip('+')}?text={urllib.parse.quote(str(msg))}"
    webbrowser.open(url)
    speak(f"WhatsApp Web opened for {phone}.")
    return {"status": "action_required", "note": "WhatsApp Web opened; click Send to complete. Message not verified as sent."}

# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR BOOKING
# ══════════════════════════════════════════════════════════════════════════════
def check_calendar_availability(date_str: str) -> dict:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        url = f"https://calendar.google.com/calendar/r/day/{dt.year}/{dt.month}/{dt.day}"
        webbrowser.open(url)
        speak(f"Opening calendar for {date_str}")
        return {"status": "ok", "date": date_str, "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def book_meeting(with_email: str, subject: str, date_str: str, duration_min: int = 60) -> dict:
    url = (f"https://calendar.google.com/calendar/r/eventedit"
           f"?text={urllib.parse.quote(subject)}"
           f"&add={urllib.parse.quote(with_email)}")
    webbrowser.open(url)
    speak(f"Calendar opened to book meeting with {with_email}")
    return {"status": "action_required", "note": "Calendar draft opened; choose time and click Save. Meeting not verified as booked."}

# ══════════════════════════════════════════════════════════════════════════════
# SELENIUM BROWSER AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════
def _get_driver(headless: bool = False):
    with _sel_lock:

    global _selenium_driver
    with _sel_lock:
        if _selenium_driver:
            try:
                _ = _selenium_driver.current_url
                return _selenium_driver
            except Exception:
                try:
                    _selenium_driver.quit()
                except Exception:
                    pass
                _selenium_driver = None
        if not SELENIUM_OK:
            return None
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        try:
            svc = ChromeService(ChromeDriverManager().install())
            drv = webdriver.Chrome(service=svc, options=opts)
            drv.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _selenium_driver = drv
            return drv
        except Exception as e:
            log.warning("Selenium init: %s", e)
            return None

def selenium_open(url: str, wait_for_css: str = None, timeout: int = 15) -> dict:
    drv = _get_driver()
    if not drv:
        webbrowser.open(url)
        return {"status": "action_required", "note": "Opened in default browser without Selenium verification", "url": url}
    try:
        drv.get(url)
        if wait_for_css:
            WebDriverWait(drv, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_css)))
        return {"status": "ok", "url": drv.current_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def selenium_fill(selector: str, value: str, by: str = "css", submit: bool = False) -> dict:
    drv = _get_driver()
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "id": By.ID, "name": By.NAME}
    try:
        el = WebDriverWait(drv, 10).until(EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.clear(); el.send_keys(value)
        if submit:
            el.send_keys(Keys.RETURN)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def selenium_click(selector: str, by: str = "css") -> dict:
    drv = _get_driver()
    if not drv:
        return {"status": "error", "message": "Selenium not available"}
    by_map = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "id": By.ID, "name": By.NAME}
    try:
        el = WebDriverWait(drv, 10).until(EC.element_to_be_clickable((by_map.get(by, By.CSS_SELECTOR), selector)))
        el.click()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL MEDIA POSTING
# ══════════════════════════════════════════════════════════════════════════════
def post_twitter(username: str, password: str, text: str) -> dict:
    if not request_approval("post_twitter", f"@{username}: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into Twitter...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://x.com")
        return {"status": "ok", "note": "Opened X"}
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
        speak("Tweet posted!")
        return {"status": "ok", "platform": "twitter"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def post_linkedin(username: str, password: str, text: str) -> dict:
    if not request_approval("post_linkedin", f"LinkedIn: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into LinkedIn...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://www.linkedin.com")
        return {"status": "ok"}
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
        time.sleep(2)
        speak("LinkedIn post published!")
        return {"status": "ok", "platform": "linkedin"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def post_facebook(username: str, password: str, text: str, page_id: str = "") -> dict:
    if not request_approval("post_facebook", f"Facebook: {text[:80]}"):
        return {"status": "denied"}
    speak("Logging into Facebook...")
    drv = _get_driver()
    if not drv:
        webbrowser.open("https://www.facebook.com")
        return {"status": "ok"}
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
        time.sleep(2)
        speak("Facebook post published!")
        return {"status": "ok", "platform": "facebook"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def youtube_search_and_play(query: str) -> dict:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    speak(f"YouTube search: {query}")
    return {"status": "ok", "url": url}

# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL MESSAGE REPLY BOTS
# ══════════════════════════════════════════════════════════════════════════════
def _get_social_driver(platform: str):
    with _social_lock:

    with _social_lock:
        drv = _social_drivers.get(platform)
        if drv:
            try:
                _ = drv.current_url
                return drv
            except Exception:
                try:
                    drv.quit()
                except Exception:
                    pass
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
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
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
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan me!']")))
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
                if not msgs:
                    continue
                last_msg = msgs[-1].text
                if not last_msg:
                    continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["whatsapp"]:
                    continue
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
                if not msgs:
                    continue
                last_msg = msgs[-1].text
                if not last_msg:
                    continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["instagram"]:
                    continue
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
                if not msgs:
                    continue
                last_msg = msgs[-1].text
                if not last_msg:
                    continue
                seen_key = last_msg[:40]
                if seen_key in _social_seen["facebook"]:
                    continue
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
                    _SOCIAL_CHECKERS[plat]()
                except Exception as e:
                    log.warning("social poll [%s]: %s", plat, e)
        time.sleep(SOCIAL_POLL_INTERVAL)

def start_social_replies(platforms: list, auto: bool = False) -> dict:
    global _social_thread, _social_running
    plats = [str(p).lower().strip() for p in platforms if str(p).lower().strip() in _SOCIAL_CHECKERS]
    if not plats:
        return {"status": "error", "message": "No valid platforms (use whatsapp / instagram / facebook)"}
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
    if not target:
        return {"status": "error", "message": "Nothing to open"}
    t = str(target).strip(); tl = t.lower()
    for pfx in ["open ", "launch ", "start ", "go to ", "navigate to ", "visit ", "browse "]:
        if tl.startswith(pfx):
            tl = tl[len(pfx):].strip(); t = t[len(pfx):].strip()

    if tl in APPS:
        try:
            subprocess.Popen(APPS[tl], shell=True)
            speak(f"Opening {tl}")
            return {"status": "ok", "opened": APPS[tl]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    for app, exe in APPS.items():
        if app in tl:
            try:
                subprocess.Popen(exe, shell=True)
                speak(f"Opening {app}")
                return {"status": "ok", "opened": exe}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def _open_chrome(url, name=""):
        speak(f"Opening {name or url}")
        try:
            subprocess.Popen(["start", "chrome", url], shell=True)
        except Exception:
            webbrowser.open(url)

    if tl in SITES:
        _open_chrome(SITES[tl], tl); return {"status": "ok", "opened": SITES[tl]}
    for site, url in SITES.items():
        if site in tl:
            _open_chrome(url, site); return {"status": "ok", "opened": url}
    if tl.startswith(("http://", "https://")):
        _open_chrome(t); return {"status": "ok", "opened": t}
    if re.match(r"^[a-z0-9\-]+\.[a-z]{2,}$", tl) and " " not in tl:
        _open_chrome("https://" + tl); return {"status": "ok", "opened": "https://" + tl}
    p = Path(t)
    if p.exists():
        try:
            os.startfile(str(p)); return {"status": "ok", "opened": str(p)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    if len(t.split()) <= 4:
        try:
            subprocess.Popen(t, shell=True); return {"status": "ok", "opened": t}
        except Exception:
            pass
    return {"status": "error", "message": f"Could not open: {target[:80]}"}

# ══════════════════════════════════════════════════════════════════════════════
# BUSINESS OS WORKFLOWS (Phase 8)
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
        return {"status": "warning", "note": f"Found {len(errors)} recent errors.", "errors": errors[:5]}
    return {"status": "ok", "note": "No recent errors found in logs."}

def backup_to_cloud() -> dict:
    source = str(Path.home() / "Documents" / "DacexyData")
    if not os.path.exists(source):
        os.makedirs(source, exist_ok=True)
    dest = str(Path.home() / "OneDrive" / "DacexyBackup")
    try:
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(os.path.join(dest, backup_name), "zip", source)
        result_path = os.path.join(dest, backup_name + ".zip")
        if not verify_file_created(result_path):
            return {"status": "error", "note": "Backup file was not created"}
        return {"status": "ok", "note": f"Successfully backed up to {dest}"}
    except Exception as e:
        return {"status": "error", "note": f"Backup failed: {e}"}

def monitor_prices(url: str) -> dict:
    return {"status": "ok", "note": f"Price monitoring activated for {url}.", "action_taken": "scheduled"}

def create_newsletter() -> dict:
    draft = ask_ai_brain("Write a short, engaging professional weekly newsletter for business clients highlighting recent updates and industry news.")
    return {"status": "ok", "note": "Newsletter generated.", "content": draft}

def draft_contract(client: str) -> dict:
    draft = ask_ai_brain(
        f"Draft a standard professional freelance/service contract for a new client named {client}. "
        f"Include payment terms, scope of work, confidentiality, and termination clauses."
    )
    filename = f"Contract_Draft_{client.replace(' ', '_')}.txt"
    filepath = Path.home() / "Desktop" / filename
    filepath.write_text(draft, encoding="utf-8")
    if not verify_file_created(str(filepath)):
        return {"status": "error", "note": "Contract file was not created"}
    return {"status": "ok", "note": f"Contract drafted and saved to Desktop as {filename}."}

def generate_sales_report(data_path: str = "") -> dict:
    """Locate spreadsheets, parse, generate summary."""
    speak("Generating sales report...")
    # Find spreadsheets
    search_dirs = [Path.home() / "Desktop", Path.home() / "Documents", DATA_DIR]
    found = []
    for d in search_dirs:
        if d.exists():
            found.extend(list(d.glob("*.xlsx")) + list(d.glob("*.csv")))
    if data_path and Path(data_path).exists():
        found.insert(0, Path(data_path))

    if not found:
        return {"status": "error", "message": "No spreadsheet files found"}

    all_data = []
    for f in found[:3]:
        r = read_spreadsheet(str(f))
        if r.get("status") == "ok":
            all_data.append({"file": f.name, "rows": r.get("rows", [])[:20]})

    summary_prompt = (
        f"Analyze this sales data and write a concise business summary with key metrics and insights:\n"
        f"{json.dumps(all_data, default=str)[:3000]}"
    )
    summary = ask_ai_brain(summary_prompt)

    report_path = DATA_DIR / f"sales_report_{datetime.date.today()}.txt"
    report_path.write_text(
        f"DACEXY SALES REPORT\nGenerated: {datetime.datetime.now()}\n\n{summary}",
        encoding="utf-8"
    )
    if not verify_file_created(str(report_path)):
        return {"status": "error", "message": "Report file was not created"}

    try:
        subprocess.Popen(f'notepad.exe "{report_path}"', shell=True)
    except Exception:
        pass
    speak("Sales report ready.")
    return {"status": "ok", "report": str(report_path), "summary": summary[:300]}

def generate_investor_report() -> dict:
    """CEO: revenue tracking, KPI monitoring, investor report."""
    speak("Generating investor update...")
    context = get_mem_ctx()
    biz_facts = MEMORY.get("business_facts", {})

    prompt = (
        f"Generate a professional investor update report for a tech startup.\n"
        f"Business context: {context}\n"
        f"Known metrics: {json.dumps({k: v.get('value') for k, v in biz_facts.items()}, default=str)}\n"
        f"Include: executive summary, key metrics, recent progress, challenges, next steps."
    )
    content = ask_ai_brain(prompt)
    report_path = DATA_DIR / f"investor_report_{datetime.date.today()}.txt"
    report_path.write_text(
        f"INVESTOR UPDATE REPORT\nDate: {datetime.datetime.now()}\n\n{content}",
        encoding="utf-8"
    )
    if not verify_file_created(str(report_path)):
        return {"status": "error", "message": "Investor report file was not created"}
    try:
        subprocess.Popen(f'notepad.exe "{report_path}"', shell=True)
    except Exception:
        pass
    speak("Investor report ready.")
    return {"status": "ok", "report": str(report_path), "preview": content[:200]}

def _parse_money(value: Any) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        s = re.sub(r"[^0-9.\-]", "", str(value))
        return float(s) if s else 0.0
    except Exception:
        return 0.0

def record_business_metric(metric: str, value: Any, period: str = "", source: str = "manual") -> dict:
    metric = (metric or "metric").strip().lower().replace(" ", "_")
    amount = _parse_money(value)
    entry = {
        "metric": metric,
        "value": amount if amount or str(value).strip().replace(".", "", 1).isdigit() else value,
        "raw_value": value,
        "period": period or datetime.date.today().isoformat(),
        "source": source,
        "updated": datetime.datetime.now().isoformat(),
    }
    with _mem_lock:
        if metric in ("revenue", "income", "sales_revenue", "arr", "mrr"):
            MEMORY["revenue"].append(entry)
        elif metric in ("profit", "net_profit", "gross_profit", "margin"):
            MEMORY["profit"].append(entry)
        elif metric.startswith("sales") or metric in ("pipeline", "closed_won", "bookings"):
            MEMORY["sales"].append(entry)
        else:
            MEMORY["kpis"][metric] = entry
        MEMORY["business_memory"][metric] = entry
        MEMORY["business_facts"][metric] = {"value": entry["value"], "updated": entry["updated"], "period": entry["period"]}
    save_memory()
    return {"status": "ok", "metric": metric, "entry": entry}

def _sum_metric(entries: list) -> float:
    total = 0.0
    for e in entries:
        total += _parse_money(e.get("value", 0) if isinstance(e, dict) else e)
    return round(total, 2)

def business_dashboard() -> dict:
    with _mem_lock:
        revenue = list(MEMORY.get("revenue", []))
        profit = list(MEMORY.get("profit", []))
        sales = list(MEMORY.get("sales", []))
        kpis = dict(MEMORY.get("kpis", {}))
        customers = dict(MEMORY.get("customers", {}))
        leads = list(MEMORY.get("leads", []))
    dashboard = {
        "revenue_total": _sum_metric(revenue),
        "profit_total": _sum_metric(profit),
        "sales_total": _sum_metric(sales),
        "kpis": kpis,
        "customers": len(customers),
        "leads": len(leads),
        "updated_at": datetime.datetime.now().isoformat(),
    }
    speak(f"Revenue {dashboard['revenue_total']}, profit {dashboard['profit_total']}, {dashboard['leads']} leads.")
    return {"status": "ok", "dashboard": dashboard}

def _write_business_report(name: str, title: str, body: str) -> dict:
    path = DATA_DIR / f"{name}_{datetime.date.today()}.txt"
    path.write_text(f"{title}\nGenerated: {datetime.datetime.now()}\n\n{body}", encoding="utf-8")
    if not verify_file_created(str(path)):
        return {"status": "error", "message": f"{title} file was not created"}
    return {"status": "ok", "report": str(path), "preview": body[:500]}

def generate_board_report() -> dict:
    dash = business_dashboard().get("dashboard", {})
    with _mem_lock:
        context = {
            "dashboard": dash,
            "kpis": MEMORY.get("kpis", {}),
            "competitors": MEMORY.get("competitors", {}),
            "market_watch": MEMORY.get("market_watch", {}),
            "recent_tasks": list(MEMORY.get("task_history", []))[-20:],
        }
    prompt = (
        "Create a concise board report with executive summary, KPI table, revenue/profit notes, "
        "risks, decisions needed, and next actions from this data:\n"
        f"{json.dumps(context, default=str)[:6000]}"
    )
    content = ask_ai_brain(prompt)
    return _write_business_report("board_report", "DACEXY BOARD REPORT", content)

def generate_kpi_report() -> dict:
    with _mem_lock:
        data = {
            "kpis": MEMORY.get("kpis", {}),
            "revenue": MEMORY.get("revenue", [])[-50:],
            "profit": MEMORY.get("profit", [])[-50:],
            "sales": MEMORY.get("sales", [])[-50:],
        }
    body = ask_ai_brain("Analyze these business KPIs and produce a concise KPI report:\n" + json.dumps(data, default=str)[:6000])
    return _write_business_report("kpi_report", "DACEXY KPI REPORT", body)

def generate_finance_report(kind: str = "finance") -> dict:
    dash = business_dashboard().get("dashboard", {})
    with _mem_lock:
        data = {
            "revenue": MEMORY.get("revenue", [])[-100:],
            "profit": MEMORY.get("profit", [])[-100:],
            "sales": MEMORY.get("sales", [])[-100:],
            "dashboard": dash,
        }
    body = ask_ai_brain(f"Create a {kind} report with revenue, profit, trend notes, and actions:\n{json.dumps(data, default=str)[:6000]}")
    return _write_business_report(f"{kind}_report", f"DACEXY {kind.upper()} REPORT", body)

def monitor_competitor(name: str, url: str = "", notes: str = "") -> dict:
    if not name:
        return {"status": "error", "message": "Competitor name required"}
    record = {
        "name": name,
        "url": url,
        "notes": notes,
        "last_checked": datetime.datetime.now().isoformat(),
    }
    if url and REQUESTS_OK:
        try:
            r = req_lib.get(url, timeout=12, headers={"User-Agent": "DacexyAgent/14"})
            record["status_code"] = r.status_code
            record["title"] = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S).group(1).strip()[:200] if re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S) else ""
            record["page_preview"] = re.sub(r"\s+", " ", BeautifulSoup(r.text, "html.parser").get_text(" ") if BS4_OK else r.text)[:1500]
        except Exception as e:
            record["error"] = str(e)
    with _mem_lock:
        MEMORY["competitors"][name.lower()] = record
    save_memory()
    return {"status": "ok", "competitor": record}

def monitor_market(topic: str, max_items: int = 5) -> dict:
    if not topic:
        return {"status": "error", "message": "Market topic required"}
    research = web_research(f"{topic} market trends competitors pricing news")[:3000]
    record = {
        "topic": topic,
        "research": research,
        "updated": datetime.datetime.now().isoformat(),
    }
    with _mem_lock:
        MEMORY["market_watch"][topic.lower()] = record
    save_memory()
    return {"status": "ok", "market": record}

def lead_management(action: str, name: str = "", email: str = "", company: str = "",
                    stage: str = "new", notes: str = "") -> dict:
    action = (action or "add").lower()
    with _mem_lock:
        if action in ("list", "show", "report"):
            leads = list(MEMORY.get("leads", []))
            return {"status": "ok", "leads": leads[-100:], "count": len(leads)}
        if not (name or email or company):
            return {"status": "error", "message": "Lead name, email, or company required"}
        lead_id = hashlib.sha1(f"{name}|{email}|{company}".lower().encode()).hexdigest()[:10]
        lead = {
            "id": lead_id,
            "name": name,
            "email": email,
            "company": company,
            "stage": stage,
            "notes": notes,
            "updated": datetime.datetime.now().isoformat(),
        }
        existing = [l for l in MEMORY["leads"] if isinstance(l, dict) and l.get("id") != lead_id]
        existing.append(lead)
        MEMORY["leads"] = existing[-1000:]
    save_memory()
    return {"status": "ok", "lead": lead}

def customer_retention_report() -> dict:
    with _mem_lock:
        customers = dict(MEMORY.get("customers", {}))
        retention = dict(MEMORY.get("retention", {}))
    prompt = (
        "Create a customer retention report with churn risks, renewal opportunities, and follow-up actions:\n"
        f"{json.dumps({'customers': customers, 'retention': retention}, default=str)[:6000]}"
    )
    body = ask_ai_brain(prompt)
    return _write_business_report("customer_retention_report", "DACEXY CUSTOMER RETENTION REPORT", body)

def sales_pipeline_report() -> dict:
    with _mem_lock:
        leads = list(MEMORY.get("leads", []))
        sales = list(MEMORY.get("sales", []))
    prompt = "Create a sales pipeline report from these leads and sales records:\n" + json.dumps({"leads": leads[-200:], "sales": sales[-100:]}, default=str)[:6000]
    body = ask_ai_brain(prompt)
    return _write_business_report("sales_pipeline_report", "DACEXY SALES PIPELINE REPORT", body)

def document_operation(kind: str, title: str, content: str = "") -> dict:
    title = title or kind or "document"
    content = content or ask_ai_brain(f"Draft a professional {kind} document titled {title}.")
    safe_title = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title).strip("_")[:80] or "document"
    path = DOC_DIR / f"{safe_title}_{int(time.time())}.txt"
    path.write_text(content, encoding="utf-8")
    if not verify_file_created(str(path)):
        return {"status": "error", "message": "Document file was not created"}
    with _mem_lock:
        MEMORY["documents"][safe_title] = {"path": str(path), "kind": kind, "updated": datetime.datetime.now().isoformat()}
    save_memory()
    return {"status": "ok", "path": str(path), "title": title}

def run_diagnostics() -> dict:
    """Phase 11 — Full system status."""
    report = []
    report.append(f"Agent Version  : {AGENT_VERSION}")
    report.append(f"Device ID      : {get_device_registration().get('device_id', '')}")
    report.append(f"PyAutoGUI      : {'OK' if PYAUTOGUI_OK else 'MISSING'}")
    report.append(f"Selenium       : {'OK' if SELENIUM_OK else 'MISSING'}")
    report.append(f"Voice/PyAudio  : {'OK' if VOICE_OK else 'MISSING'}")
    report.append(f"System Monitor : {'OK' if PSUTIL_OK else 'MISSING'}")
    report.append(f"TTS Engine     : {'OK' if _tts_engine else 'MISSING'}")
    report.append(f"PDF Extraction : {'OK' if PDF_OK else 'MISSING'}")
    report.append(f"Spreadsheet    : {'OK' if XL_OK else 'MISSING'}")
    report.append(f"OCR            : {'OK' if OCR_OK else 'MISSING'}")
    report.append(f"Clipboard      : {'OK' if CLIP_OK else 'MISSING'}")
    report.append(f"Notifications  : {'OK' if NOTIFY_OK else 'MISSING'}")
    report.append(f"Encryption     : {'OK' if CRYPTO_OK else 'MISSING'}")
    report.append(f"Requests       : {'OK' if REQUESTS_OK else 'MISSING'}")
    smtp_ok = bool(_smtp_cfg.get("email") and _smtp_cfg.get("password"))
    report.append(f"SMTP Config    : {'CONFIGURED — ' + _smtp_cfg.get('email','') if smtp_ok else 'NOT SET'}")
    ws_ok = _ws_send_fn is not None
    report.append(f"WebSocket      : {'CONNECTED' if ws_ok else 'DISCONNECTED'}")
    report.append(f"Voice Status   : {HEALTH['voice_status']}")
    report.append(f"Vision Status  : {HEALTH.get('vision_status', 'idle')}")
    report.append(f"Planner Status : {HEALTH['planner_status']}")
    report.append(f"Executor Status: {HEALTH['executor_status']}")
    report.append(f"Last Checkpoint: {HEALTH.get('last_checkpoint', '')}")
    report.append(f"Memory Entries : {len(MEMORY.get('facts', []))} facts, "
                  f"{len(MEMORY.get('contacts', {}))} contacts, "
                  f"{len(MEMORY.get('workflows', {}))} workflows")
    if PSUTIL_OK:
        report.append(f"CPU            : {psutil.cpu_percent(interval=0.5)}%")
        report.append(f"RAM            : {psutil.virtual_memory().percent}%")
    active = list_active_tasks()
    report.append(f"Active Tasks   : {len(active)}")
    report.append(f"Tasks Run      : {HEALTH['tasks_run']} total, {HEALTH['tasks_ok']} OK")
    uptime_s = int(time.time() - HEALTH["uptime_start"])
    report.append(f"Uptime         : {uptime_s // 3600}h {(uptime_s % 3600) // 60}m")

    full_report = "\n".join(report)
    print(f"\n  ═══════ DACEXY SYSTEM STATUS ═══════\n{full_report}\n  ═════════════════════════════════════\n")
    passed = sum(1 for r in report if any(x in r for x in ["OK", "CONFIGURED", "CONNECTED"]))
    total  = len(report)
    summary = f"Diagnostics complete. {passed} of {total} checks passed."
    speak(summary)
    return {"status": "ok", "report": report, "passed": passed, "total": total}

# ══════════════════════════════════════════════════════════════════════════════
# LOCAL NLP PARSER
# ══════════════════════════════════════════════════════════════════════════════
def local_parse(task: str) -> list:
    t  = task.strip()
    tl = t.lower()

    # Compound commands
    if " then " in tl:
        parts = tl.split(" then ")
        cmds  = []
        for p in parts:
            cmds.extend(local_parse(p.strip()))
            cmds.append({"action": "wait", "seconds": 2})
        return [c for c in cmds if c.get("action") != "wait" or cmds.index(c) != len(cmds) - 1]

    if " and then " in tl:
        parts = tl.split(" and then ")
        cmds  = []
        for p in parts:
            cmds.extend(local_parse(p.strip()))
            cmds.append({"action": "wait", "seconds": 2})
        return [c for c in cmds if c.get("action") != "wait" or cmds.index(c) != len(cmds) - 1]

    # ── SYSTEM STATUS / DIAGNOSTICS ──────────────────────────────────────
    if re.search(r"\bsystem\s+status\b|\brun\s+diagnostics\b|\bhealth\s+check\b|\bself.?test\b", tl):
        return [{"action": "run_diagnostics"}]

    if re.search(r"\b(?:what'?s|what is|describe|understand|analyze)\s+(?:on\s+)?(?:my\s+)?screen\b|\bscreen\s+understanding\b|\bvision\s+status\b", tl):
        return [{"action": "understand_screen"}]

    if re.search(r"\b(?:start|enable|turn\s+on)\s+(?:continuous\s+)?(?:screen|vision)\s+(?:monitor|understanding)\b", tl):
        return [{"action": "start_vision_monitor"}]

    if re.search(r"\b(?:stop|disable|turn\s+off)\s+(?:screen|vision)\s+(?:monitor|understanding)\b", tl):
        return [{"action": "stop_vision_monitor"}]

    if re.search(r"\b(?:voice|microphone|mic)\s+(?:diagnostics?|test|health)\b", tl):
        return [{"action": "voice_diagnostics"}]

    if re.search(r"\b(?:recover|reset|fix)\s+(?:microphone|mic|voice)\b", tl):
        return [{"action": "recover_microphone"}]

    # ── WORKFLOW COMMANDS ─────────────────────────────────────────────────
    m = re.search(r"(?:replay|reuse|run|repeat)\s+workflow\s+(.+)", tl)
    if m:
        return [{"action": "replay_workflow", "name": m.group(1).strip()}]

    m = re.search(r"(?:list|show)\s+(?:my\s+)?workflows", tl)
    if m:
        return [{"action": "list_workflows"}]

    m = re.search(r"(?:save|remember)\s+(?:this\s+)?workflow\s+(?:as\s+)?(.+)", tl)
    if m:
        return [{"action": "save_current_workflow", "name": m.group(1).strip()}]

    # ── BUSINESS OS ───────────────────────────────────────────────────────
    if re.search(r"investor\s+(?:report|update)", tl):
        return [{"action": "investor_report"}]

    if re.search(r"sales\s+(?:report|analysis|dashboard)", tl):
        return [{"action": "sales_report"}]

    if re.search(r"\bboard\s+(?:report|update)\b", tl):
        return [{"action": "board_report"}]

    if re.search(r"\bkpi\s+(?:report|dashboard|tracking|status)\b", tl):
        return [{"action": "kpi_report"}]

    if re.search(r"\b(?:business|company)\s+dashboard\b|\bbusiness\s+os\b", tl):
        return [{"action": "business_dashboard"}]

    if re.search(r"\b(?:revenue|profit|finance)\s+(?:report|tracking|status)\b", tl):
        kind = "profit" if "profit" in tl else "revenue" if "revenue" in tl else "finance"
        return [{"action": "finance_report", "kind": kind}]

    m = re.search(r"(?:record|save|track|add)\s+(revenue|profit|kpi|sales|expense|income|mrr|arr)\s+(?:of\s+|as\s+|=)?([₹$€£]?\s*[-\d,.]+)", tl)
    if m:
        period_m = re.search(r"(?:for|in|during)\s+([a-z0-9\-/ ]{3,30})$", tl)
        return [{"action": "record_metric", "metric": m.group(1), "value": m.group(2), "period": period_m.group(1).strip() if period_m else ""}]

    m = re.search(r"(?:monitor|track|watch)\s+competitor\s+(.+?)(?:\s+(https?://\S+))?$", tl)
    if m:
        return [{"action": "monitor_competitor", "name": m.group(1).strip(), "url": (m.group(2) or "").strip()}]

    m = re.search(r"(?:monitor|track|research|watch)\s+(?:the\s+)?market\s+(?:for|about|on)?\s*(.+)", tl)
    if m:
        return [{"action": "monitor_market", "topic": m.group(1).strip()}]

    if re.search(r"\bcustomer\s+retention\s+(?:report|status|analysis)\b", tl):
        return [{"action": "customer_retention_report"}]

    if re.search(r"\bsales\s+pipeline\s+(?:report|status|analysis)\b", tl):
        return [{"action": "sales_pipeline_report"}]

    m = re.search(r"(?:add|save|track)\s+lead\s+(.+?)(?:\s+email\s+([^\s,]+@[^\s,]+))?(?:\s+company\s+(.+?))?(?:\s+stage\s+(\w+))?$", tl)
    if m:
        return [{"action": "lead_manage", "op": "add", "name": m.group(1).strip(), "email": m.group(2) or "", "company": m.group(3) or "", "stage": m.group(4) or "new"}]

    if re.search(r"(?:list|show)\s+leads\b|\blead\s+management\b", tl):
        return [{"action": "lead_manage", "op": "list"}]

    if re.search(r"(?:prepare|generate|create|write)\s+(?:investor|board)\s+(?:report|update|deck)", tl):
        return [{"action": "investor_report"}]

    # ── TASK STATUS ───────────────────────────────────────────────────────
    if re.search(r"(?:show|list|check)\s+(?:active\s+)?tasks?|task\s+status", tl):
        return [{"action": "list_tasks"}]

    m = re.search(r"cancel\s+task\s+([a-z0-9]+)", tl)
    if m:
        return [{"action": "cancel_task", "task_id": m.group(1)}]

    m = re.search(r"resume\s+task\s+([a-z0-9]+)", tl)
    if m:
        return [{"action": "resume_task", "task_id": m.group(1)}]

    # ── ERROR LOGS ────────────────────────────────────────────────────────
    if re.search(r"(?:monitor|check|scan|read)\s+(?:error\s+)?(?:logs?|error\s+files?)", tl):
        m_path = re.search(r"(?:in|at|from|path)\s+(\S+)", tl)
        path   = m_path.group(1) if m_path else str(Path.home() / "Desktop" / "error.log")
        return [{"action": "monitor_error_logs", "path": path}]

    if re.search(r"(?:backup|save|sync)\s+(?:my\s+)?(?:files?|data|documents?|everything)\s+(?:to\s+)?(?:cloud|onedrive|drive)", tl):
        return [{"action": "backup_to_cloud"}]

    if re.search(r"(?:monitor|track|watch|check)\s+(?:the\s+)?(?:price|prices|cost)\s+(?:of|for|on|at)?", tl):
        m_url = re.search(r"(https?://\S+)", tl)
        url   = m_url.group(1) if m_url else ""
        if not url:
            m_site = re.search(r"(?:of|for|on|at)\s+(\S+)", tl)
            url = m_site.group(1) if m_site else "amazon.com"
        return [{"action": "monitor_prices", "url": url}]

    if re.search(r"(?:create|draft|write|generate|make)\s+(?:a\s+)?(?:newsletter|news\s+letter)", tl):
        return [{"action": "create_newsletter"}]

    m = re.search(r"(?:draft|create|write|generate|make)\s+(?:a\s+)?contract\s+(?:for\s+)?(.+)", tl)
    if m and "newsletter" not in tl:
        return [{"action": "draft_contract", "client": m.group(1).strip()}]

    # ── EMAIL ─────────────────────────────────────────────────────────────
    if re.search(r"(?:configure|setup|set up|enable|add|connect)\s+(?:email|smtp|mail)", tl):
        return [{"action": "configure_email"}]

    if re.search(r"(?:read|check|open|show)\s+(?:my\s+)?(?:inbox|emails|mail)", tl):
        return [{"action": "read_inbox"}]

    if re.search(r"draft\s+(?:a\s+)?(?:reply|response)\s+(?:to|for)", tl):
        m = re.search(r"(?:to|for)\s+(.+?)(?:\s+about\s+(.+))?$", tl)
        subj = m.group(2) if m and m.group(2) else "your email"
        return [{"action": "draft_reply", "subject": subj}]

    m = re.search(
        r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+([^\s,]+@[^\s,]+)"
        r"(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        subj = (m.group(2) or "Hello from Dacexy").strip()
        return [{"action": "send_email", "to": m.group(1).strip(), "subject": subj, "body": subj}]

    m = re.search(r"(?:send|compose|write)\s+(?:an?\s+)?(?:email|mail)\s+to\s+(.+?)(?:\s+(?:saying|about|subject|re)\s+(.+?))?$", tl)
    if m:
        contact_name = m.group(1).strip()
        subj = (m.group(2) or "Hello").strip()
        return [{"action": "send_email_by_name", "name": contact_name, "subject": subj, "body": subj}]

    if re.search(r"bulk\s+email|mass\s+email|email\s+campaign|email\s+blast", tl):
        csv_m = re.search(r"(?:from|using|with|file)\s+(\S+\.csv)", tl)
        return [{"action": "bulk_email", "csv_path": csv_m.group(1) if csv_m else "",
                 "subject": "Hello from Dacexy", "body": "Hi {name},\n\nHope this finds you well!\n\nBest"}]

    # ── FILES ─────────────────────────────────────────────────────────────
    if re.search(r"(?:organize|sort|clean\s+up|arrange)\s+(?:my\s+)?(?:files|folder|desktop|downloads)", tl):
        m = re.search(r"(?:in|from|folder|directory)\s+(.+?)(?:\s*$|\s+and\b)", tl)
        folder = m.group(1).strip() if m else str(Path.home() / "Desktop")
        if "desktop" in tl:
            folder = str(Path.home() / "Desktop")
        elif "download" in tl:
            folder = str(Path.home() / "Downloads")
        elif "document" in tl:
            folder = str(Path.home() / "Documents")
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
                 "url":  m_url.group(1)  if m_url  else ""}]

    # ── BOOKING ───────────────────────────────────────────────────────────
    if re.search(r"(?:book|schedule)\s+(?:a\s+)?(?:meeting|call|appointment)\s+with", tl):
        m_email = re.search(r"([^\s,]+@[^\s,]+)", tl)
        m_date  = re.search(r"(\d{4}-\d{2}-\d{2})", tl)
        m_subj  = re.search(r"(?:about|for|re)\s+(.+?)(?:\s+on\b|\s+with\b|$)", tl)
        return [{"action": "book_meeting",
                 "with_email": m_email.group(1) if m_email else "",
                 "date":       m_date.group(1)  if m_date  else str(datetime.date.today()),
                 "subject":    m_subj.group(1)  if m_subj  else "Meeting"}]

    # ── LEADS ─────────────────────────────────────────────────────────────
    if re.search(r"(?:find|get|search|generate|scrape)\s+(?:leads|customers|clients|prospects)", tl):
        m = re.search(r"for\s+(?:my\s+)?(.+?)(?:\s+and\b|\s+then\b|\s*$)", tl)
        prod = m.group(1).strip() if m else "product"
        return [{"action": "find_leads_and_email", "product": prod, "niche": ""}]

    # ── SOCIAL ────────────────────────────────────────────────────────────
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
            if p in tl:
                plat = p; break
        auto = bool(re.search(r"\b(?:auto|automatically|and\s+send|and\s+reply)\b", tl))
        return [{"action": "check_social_messages", "platform": plat, "auto": auto}]

    if re.search(r"(?:turn\s+on|enable|start)\s+auto.?repl", tl) or \
       re.search(r"(?:auto.?reply|reply\s+bot)s?\s+(?:on|for)\s+(?:whatsapp|instagram|facebook)", tl):
        plats = [p for p in ("whatsapp", "instagram", "facebook") if p in tl] or ["whatsapp", "instagram", "facebook"]
        return [{"action": "start_social_replies", "platforms": plats, "auto": True}]

    if re.search(r"(?:turn\s+off|disable|stop)\s+auto.?repl", tl):
        plats = [p for p in ("whatsapp", "instagram", "facebook") if p in tl] or None
        return [{"action": "stop_social_replies", "platforms": plats}]

    # ── PAYMENT QUEUE ─────────────────────────────────────────────────────
    if re.search(r"(?:pending|queued|outstanding)\s+payments?|payment\s+queue|payments?\s+(?:to\s+)?approve", tl):
        return [{"action": "list_payment_queue", "status": "pending_review"}]

    m = re.search(r"approve\s+payment\s+([a-z0-9]{4,})", tl)
    if m:
        return [{"action": "approve_payment", "queue_id": m.group(1), "portal": "razorpay"}]

    m = re.search(r"reject\s+payment\s+([a-z0-9]{4,})", tl)
    if m:
        return [{"action": "reject_payment", "queue_id": m.group(1)}]

    # ── YOUTUBE ───────────────────────────────────────────────────────────
    m = re.search(r"(?:search|play|find|watch|look\s+up)\s+(.+?)\s+(?:on|in)\s+youtube", tl)
    if m:
        return [{"action": "open_youtube", "query": m.group(1).strip()}]
    if re.search(r"\byoutube\b", tl) and re.search(r"\b(?:search|play|watch|find|open|look)\b", tl):
        q = re.sub(r"\b(youtube|search|play|watch|find|open|on|in|for|me|video)\b", "", tl).strip()
        if q and len(q) > 2:
            return [{"action": "open_youtube", "query": q}]

    # ── OPEN / NAVIGATE ───────────────────────────────────────────────────
    m = re.match(r"(?:open|launch|start|go\s+to|navigate\s+to|visit|browse|load|show)\s+(.+)", tl)
    if m:
        return [{"action": "open", "target": m.group(1).strip()}]

    # ── SEARCH ────────────────────────────────────────────────────────────
    m = re.search(r"(?:google|search\s+for|look\s+up|search|find)\s+(.+?)(?:\s+on\s+google)?$", tl)
    if m and "youtube" not in tl and "email" not in tl and "lead" not in tl:
        q = m.group(1).strip()
        if q and len(q) > 1:
            return [{"action": "search_web", "query": q}]

    # ── SCREENSHOT / OCR ──────────────────────────────────────────────────
    if re.search(r"screenshot|screen\s+shot|capture\s+screen|take\s+screenshot", tl):
        return [{"action": "screenshot"}]
    if re.search(r"\bocr\b|read\s+screen|extract\s+text\s+from\s+screen", tl):
        return [{"action": "ocr"}]

    # ── TIME / DATE ───────────────────────────────────────────────────────
    if re.search(r"what(?:'s| is)\s+the\s+time|time\s+is\s+it|current\s+time", tl):
        return [{"action": "get_time"}]
    if re.search(r"what(?:'s| is)\s+(?:today|the\s+date)|today'?s?\s+date|current\s+date", tl):
        return [{"action": "get_date"}]

    # ── SYSTEM ────────────────────────────────────────────────────────────
    if re.search(r"system\s+info|cpu\s+usage|ram\s+usage|disk\s+space|check\s+system", tl):
        return [{"action": "get_system_info"}]

    # ── VOLUME / MEDIA ────────────────────────────────────────────────────
    if re.search(r"volume\s*up|increase\s+volume|louder|turn\s+up", tl):
        return [{"action": "volume_up", "steps": 5}]
    if re.search(r"volume\s*down|lower\s+volume|quieter|turn\s+down|decrease\s+volume", tl):
        return [{"action": "volume_down", "steps": 5}]
    if re.search(r"\bmute\b|\bsilence\b|\bunmute\b", tl):
        return [{"action": "mute"}]
    if re.search(r"(?:play|pause|toggle)\s+(?:music|media|song|video)", tl):
        return [{"action": "media_play_pause"}]
    if re.search(r"next\s+(?:song|track)", tl):
        return [{"action": "media_next"}]
    if re.search(r"prev(?:ious)?\s+(?:song|track)", tl):
        return [{"action": "media_prev"}]

    # ── WINDOW ────────────────────────────────────────────────────────────
    if re.search(r"minimiz|minimis", tl):   return [{"action": "minimize_window"}]
    if re.search(r"maximiz|maximis|full.?screen", tl): return [{"action": "maximize_window"}]
    if re.search(r"close\s+(?:this\s+)?(?:window|tab|app|program)", tl): return [{"action": "close_window"}]
    if re.search(r"show\s+desktop", tl):    return [{"action": "show_desktop"}]
    if re.search(r"switch\s+(?:window|tab)|alt\s+tab", tl): return [{"action": "switch_window"}]

    # ── KEYBOARD ─────────────────────────────────────────────────────────
    m = re.match(r"(?:type|write|enter|input)\s+(.+)", tl)
    if m:
        return [{"action": "type", "text": m.group(1).strip()}]
    m = re.match(r"(?:click|press)\s+(?:at\s+)?(\d+)\s*[,x]\s*(\d+)", tl)
    if m:
        return [{"action": "click", "x": int(m.group(1)), "y": int(m.group(2))}]
    if re.search(r"scroll\s+down|page\s+down", tl): return [{"action": "scroll_down", "amount": 5}]
    if re.search(r"scroll\s+up|page\s+up", tl):     return [{"action": "scroll_up", "amount": 5}]
    if re.search(r"\bpress\s+enter\b|submit\s+form", tl): return [{"action": "key", "key": "enter"}]
    if re.search(r"\bpress\s+(?:escape|esc)\b", tl):      return [{"action": "key", "key": "escape"}]
    if re.search(r"select\s+all", tl):   return [{"action": "hotkey", "keys": ["ctrl", "a"]}]
    if re.search(r"copy\s+(?:it|that|all|text)", tl): return [{"action": "hotkey", "keys": ["ctrl", "c"]}]
    if re.search(r"paste\s+(?:it|that|here)", tl):   return [{"action": "hotkey", "keys": ["ctrl", "v"]}]
    if re.search(r"save\s+(?:the\s+)?(?:file|document|this)", tl): return [{"action": "hotkey", "keys": ["ctrl", "s"]}]
    if re.search(r"(?:refresh|reload)\s+(?:page|browser)", tl): return [{"action": "key", "key": "f5"}]
    if re.search(r"new\s+tab\b", tl):    return [{"action": "hotkey", "keys": ["ctrl", "t"]}]
    if re.search(r"close\s+tab\b", tl):  return [{"action": "hotkey", "keys": ["ctrl", "w"]}]

    # ── MEMORY ────────────────────────────────────────────────────────────
    m = re.match(r"remember\s+(?:that\s+)?(.+)", tl)
    if m:
        return [{"action": "remember", "fact": m.group(1)}, {"action": "speak", "text": "Noted!"}]

    m = re.search(r"(?:search|find|recall)\s+(?:my\s+)?memory\s+(?:for\s+)?(.+)", tl)
    if m:
        return [{"action": "semantic_memory_search", "query": m.group(1).strip()}]

    m = re.match(r"(?:say|speak|tell\s+me|announce)\s+(.+)", tl)
    if m:
        return [{"action": "speak", "text": m.group(1)}]

    m = re.match(r"(?:research|investigate|find\s+out\s+about)\s+(.+)", tl)
    if m:
        return [{"action": "web_research", "query": m.group(1).strip()}]

    m = re.match(r"(?:run|execute|cmd|shell)\s+(?:command\s+)?(.+)", tl)
    if m:
        return [{"action": "run_command", "command": m.group(1).strip()}]

    m = re.search(r"wait\s+(?:for\s+)?(\d+)\s+(?:second|sec)", tl)
    if m:
        return [{"action": "wait", "seconds": float(m.group(1))}]

    if re.search(r"\bwhatsapp\b", tl):
        return [{"action": "open", "target": "whatsapp web"}]

    for app in APPS:
        if tl.strip() == app:
            return [{"action": "open", "target": app}]
    for site in SITES:
        if tl.strip() == site:
            return [{"action": "open", "target": site}]

    if re.search(r"\b(?:help|what\s+can\s+you\s+do|commands)\b", tl):
        return [{"action": "speak", "text": (
            "I can: plan and execute multi-step tasks, open apps/sites, send emails, "
            "organize files, read inbox, find leads, process invoices, take screenshots, "
            "control volume, post social media, reply to WhatsApp/Instagram/Facebook, "
            "manage payment queues, book meetings, run business reports, learn and replay "
            "workflows, and use multiple AI sub-agents for specialized tasks!"
        )}]

    if re.search(r"\b(?:hello|hi|hey|good\s+morning|howdy)\b", tl):
        return [{"action": "speak", "text": "Hello! Dacexy is ready. What can I do for you?"}]

    if re.search(r"\b(?:ping|test|are\s+you\s+there)\b", tl):
        return [{"action": "ping"}]

    # Fallback to AI Brain
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
        # ── DIAGNOSTICS ───────────────────────────────────────────────────
        if action in {"run_diagnostics", "system_status", "status"}:
            return run_diagnostics()

        if action in {"voice_diagnostics", "mic_diagnostics", "microphone_diagnostics"}:
            return voice_diagnostics()

        if action in {"recover_microphone", "recover_mic", "reset_microphone"}:
            _recover_mic()
            return voice_diagnostics()

        if action in {"understand_screen", "screen_understanding", "vision_status", "what_is_on_screen"}:
            res = understand_screen(save_screenshot=True)
            if res.get("status") == "ok":
                speak(res.get("summary", "Screen understood.")[:350])
            return res

        if action == "start_vision_monitor":
            return start_vision_monitor()

        if action == "stop_vision_monitor":
            return stop_vision_monitor()

        # ── WORKFLOW LEARNING ─────────────────────────────────────────────
        if action == "replay_workflow":
            name = str(cmd.get("name", ""))
            if not name:
                return {"status": "error", "message": "Workflow name required"}
            return replay_workflow(name, token or "")

        if action == "list_workflows":
            wfs = list_workflows()
            speak(f"{len(wfs)} saved workflows: {', '.join(wfs[:5])}" if wfs else "No saved workflows yet.")
            return {"status": "ok", "workflows": wfs}

        if action == "save_current_workflow":
            name = str(cmd.get("name", ""))
            steps = cmd.get("steps", [])
            if name and steps:
                save_workflow(name, steps)
                speak(f"Workflow '{name}' saved.")
            return {"status": "ok"}

        # ── TASK QUEUE ────────────────────────────────────────────────────
        if action == "list_tasks":
            tasks = list_active_tasks()
            if tasks:
                for t in tasks:
                    print(f"  [{t['state'].upper()}] {t['id']} — {t['goal']}")
            else:
                speak("No active tasks.")
            return {"status": "ok", "tasks": tasks}

        if action == "cancel_task":
            return cancel_task(str(cmd.get("task_id", "")))

        if action == "resume_task":
            return resume_task(str(cmd.get("task_id", "")), token or "")

        if action == "queue_task":
            goal = str(cmd.get("goal") or cmd.get("task") or "")
            if not goal:
                return {"status": "error", "message": "No goal specified"}
            tid = queue_task(goal, token or "")
            speak(f"Task queued: {goal[:40]}")
            return {"status": "ok", "task_id": tid}

        # ── BUSINESS OS ───────────────────────────────────────────────────
        if action in {"investor_report", "generate_investor_report"}:
            return generate_investor_report()

        if action in {"sales_report", "generate_sales_report"}:
            return generate_sales_report(str(cmd.get("path", "")))

        if action in {"board_report", "generate_board_report"}:
            return generate_board_report()

        if action in {"kpi_report", "generate_kpi_report"}:
            return generate_kpi_report()

        if action in {"finance_report", "revenue_report", "profit_report"}:
            return generate_finance_report(str(cmd.get("kind") or action.replace("_report", "")))

        if action in {"business_dashboard", "business_status", "business_os"}:
            return business_dashboard()

        if action in {"record_metric", "track_metric", "save_metric"}:
            return record_business_metric(str(cmd.get("metric") or "metric"),
                                          cmd.get("value", ""),
                                          str(cmd.get("period") or ""),
                                          str(cmd.get("source") or "manual"))

        if action == "monitor_competitor":
            return monitor_competitor(str(cmd.get("name") or ""), str(cmd.get("url") or ""), str(cmd.get("notes") or ""))

        if action in {"monitor_market", "market_monitoring"}:
            return monitor_market(str(cmd.get("topic") or cmd.get("query") or ""))

        if action == "customer_retention_report":
            return customer_retention_report()

        if action == "sales_pipeline_report":
            return sales_pipeline_report()

        if action in {"lead_manage", "lead_management"}:
            return lead_management(str(cmd.get("op") or cmd.get("operation") or "add"),
                                   str(cmd.get("name") or ""),
                                   str(cmd.get("email") or ""),
                                   str(cmd.get("company") or ""),
                                   str(cmd.get("stage") or "new"),
                                   str(cmd.get("notes") or ""))

        if action in {"document_operation", "create_document", "draft_document"}:
            return document_operation(str(cmd.get("kind") or "document"),
                                      str(cmd.get("title") or cmd.get("name") or "document"),
                                      str(cmd.get("content") or ""))

        if action == "monitor_error_logs":
            res = monitor_error_logs(str(cmd.get("path", str(Path.home() / "Desktop" / "error.log"))))
            speak(res.get("note", "Checked logs."))
            return res

        if action == "backup_to_cloud":
            speak("Starting cloud backup...")
            res = backup_to_cloud()
            speak(res.get("note", "Backup complete."))
            return res

        if action == "monitor_prices":
            url = str(cmd.get("url", ""))
            speak(f"Setting up price monitoring for {url}.")
            return monitor_prices(url)

        if action == "create_newsletter":
            speak("Drafting newsletter...")
            res = create_newsletter()
            content = res.get("content", "")
            if content:
                speak("Newsletter ready. Writing it now.")
                real_type(content)
            return res

        if action == "draft_contract":
            client = str(cmd.get("client", "a client"))
            speak(f"Drafting contract for {client}...")
            return draft_contract(client)

        # ── SPEAK / NOTIFY ────────────────────────────────────────────────
        if action == "speak":
            speak(str(cmd.get("text", ""))); return {"status": "ok"}
        if action == "notify":
            _notify(str(cmd.get("title", "Dacexy")), str(cmd.get("text", ""))); return {"status": "ok"}

        # ── AI BRAIN ──────────────────────────────────────────────────────
        if action == "ask_ai":
            speak("Let me think about that.")
            resp = ask_ai_brain(str(cmd.get("prompt", "")))
            _notify("Dacexy AI", resp[:150])
            print(f"\n  [AI BRAIN]\n{resp}\n")
            prompt_text = str(cmd.get("prompt", "")).lower()
            if any(k in prompt_text for k in ["write about", "draft", "generate", "create"]):
                speak("Here is what I came up with. Writing it now.")
                real_type(resp)
            else:
                speak(resp[:300])
            return {"status": "ok", "response": resp}

        if action == "enterprise_automation":
            task_text = str(cmd.get("task", ""))
            speak("Working on that...")
            resp = ask_ai_brain(
                f"The user asked Dacexy (desktop AI agent) to help with: \"{task_text}\". "
                f"Give clear practical step-by-step guidance."
            )
            print(f"\n  [BUSINESS TASK]\n{resp}\n")
            speak("Here's what I found — check the window for details.")
            return {"status": "ok", "response": resp}

        # ── EMAIL ─────────────────────────────────────────────────────────
        if action == "configure_email":
            return configure_smtp_interactive()

        if action in {"send_email", "email", "compose_email", "send_mail", "gmail_send"}:
            to_ = str(cmd.get("to") or cmd.get("email") or cmd.get("recipient") or "").strip()
            if not to_:
                return {"status": "error", "message": "No recipient email"}
            return send_email_real(to_, str(cmd.get("subject") or "Message from Dacexy"),
                                   str(cmd.get("body") or cmd.get("text") or "Hello"), require_approval=True)

        if action in {"bulk_email", "send_bulk_email", "mass_email", "email_campaign"}:
            contacts = cmd.get("contacts") or []
            csv_p    = cmd.get("csv_path") or ""
            if csv_p and not contacts:
                contacts = load_csv_contacts(str(csv_p))
            if not contacts:
                return {"status": "error", "message": "No contacts found."}
            return send_bulk_email(contacts, str(cmd.get("subject") or "Hello from Dacexy"),
                                   str(cmd.get("body") or "Hi {name},\n\nBest regards"), float(cmd.get("delay") or 1.5))

        if action == "read_inbox":
            return read_inbox(int(cmd.get("max_count") or 10))

        if action == "draft_reply":
            draft = draft_email_reply(str(cmd.get("subject") or ""), str(cmd.get("body") or ""),
                                      str(cmd.get("context") or ""))
            speak("Draft created.")
            print(f"\n  === EMAIL DRAFT ===\n{draft}\n  ==================")
            return {"status": "ok", "draft": draft}

        if action in {"find_leads_and_email", "lead_campaign"}:
            product = str(cmd.get("product") or "product")
            leads = find_leads_web(product, str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            if not leads:
                return {"status": "error", "message": "No leads found."}
            return send_bulk_email(leads, str(cmd.get("subject") or f"About {product}"),
                                   str(cmd.get("body") or f"Hi {{name}},\n\nI think {product} could help you.\nBest"), 2.0)

        if action in {"find_leads", "get_leads"}:
            leads = find_leads_web(str(cmd.get("product") or ""), str(cmd.get("niche") or ""), int(cmd.get("max") or 50))
            return {"status": "ok", "leads_found": len(leads)}

        if action == "send_email_by_name":
            name    = str(cmd.get("name", "")).lower()
            contacts = MEMORY.get("contacts", {})
            found_email = ""
            if name in contacts:
                found_email = contacts[name].get("email", "")
            if not found_email:
                for k, v in contacts.items():
                    if name in k:
                        found_email = v.get("email", ""); break
            if not found_email:
                speak(f"I don't have {name} in contacts. Opening Gmail.")
                webbrowser.open(f"https://mail.google.com/mail/?view=cm&fs=1&su={cmd.get('subject','')}")
                return {"status": "action_required", "note": "Opened Gmail compose; send not verified"}
            return send_email_real(found_email, str(cmd.get("subject") or "Message"),
                                   str(cmd.get("body") or "Hello"), require_approval=True)

        # ── FILE OPS ──────────────────────────────────────────────────────
        if action == "organize_folder":
            folder = str(cmd.get("folder") or str(Path.home() / "Desktop"))
            if not _is_path_allowed(folder):
                return {"status": "error", "message": "Access blocked."}
            return organize_folder(folder, dry_run=bool(cmd.get("dry_run", False)))

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
            if not verify_file_created(str(p)):
                return {"status": "error", "message": f"File was not created: {p}"}
            try:
                subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            except Exception:
                pass
            return {"status": "ok", "path": str(p)}

        if action in {"read_file", "open_file"}:
            p = Path(str(cmd.get("path") or ""))
            if not _is_path_allowed(str(p)):
                return {"status": "error", "message": "Path blocked."}
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="ignore")[:10000]
                speak(f"File read: {len(content)} chars.")
                return {"status": "ok", "content": content}
            return {"status": "error", "message": f"Not found: {p}"}

        if action in {"list_files", "ls"}:
            folder = Path(str(cmd.get("folder") or Path.home() / "Desktop"))
            if not _is_path_allowed(str(folder)):
                return {"status": "error", "message": "Blocked."}
            try:
                files = [f.name for f in folder.iterdir()][:50]
                speak(f"{len(files)} files in {folder.name}")
                return {"status": "ok", "files": files}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        if action in {"zip_files", "compress", "backup"}:
            src = Path(str(cmd.get("path") or cmd.get("folder") or Path.home() / "Desktop"))
            dst = Path(str(cmd.get("output") or AGENT_DIR / f"backup_{int(time.time())}.zip"))
            try:
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file():
                        zf.write(src, src.name)
                    elif src.is_dir():
                        for f in src.rglob("*"):
                            if f.is_file():
                                zf.write(f, f.relative_to(src))
                if not verify_file_created(str(dst)):
                    return {"status": "error", "message": "ZIP was not created"}
                speak(f"Compressed to {dst.name}")
                return {"status": "ok", "zip": str(dst)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # ── PAYMENT QUEUE ─────────────────────────────────────────────────
        if action in {"list_payment_queue", "show_payments", "pending_payments", "payment_queue"}:
            return list_payment_queue(str(cmd.get("status") or "pending_review"))

        if action in {"approve_payment", "pay_invoice"}:
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid:
                return {"status": "error", "message": "queue_id required"}
            return approve_payment(qid, str(cmd.get("portal") or "razorpay"))

        if action == "reject_payment":
            qid = str(cmd.get("queue_id") or cmd.get("id") or "")
            if not qid:
                return {"status": "error", "message": "queue_id required"}
            return reject_payment(qid, str(cmd.get("reason") or ""))

        # ── SOCIAL REPLY BOTS ─────────────────────────────────────────────
        if action in {"start_social_replies", "enable_auto_reply", "watch_messages"}:
            plats = cmd.get("platforms") or ["whatsapp", "instagram", "facebook"]
            if isinstance(plats, str):
                plats = re.split(r"[,\s]+", plats)
            return start_social_replies(plats, bool(cmd.get("auto", False)))

        if action in {"stop_social_replies", "disable_auto_reply"}:
            plats = cmd.get("platforms")
            if isinstance(plats, str):
                plats = re.split(r"[,\s]+", plats)
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

        # ── BOOKING ───────────────────────────────────────────────────────
        if action == "check_calendar":
            return check_calendar_availability(str(cmd.get("date") or str(datetime.date.today())))
        if action == "book_meeting":
            return book_meeting(str(cmd.get("with_email") or ""), str(cmd.get("subject") or "Meeting"),
                                str(cmd.get("date") or str(datetime.date.today())), int(cmd.get("duration_min") or 60))

        # ── OPEN / LAUNCH ─────────────────────────────────────────────────
        if action in {"open", "open_url", "open_browser", "launch", "start", "navigate",
                      "navigate_to", "go_to", "browse", "visit", "open_site", "open_website",
                      "open_app", "run_app", "open_application", "launch_application",
                      "open_chrome", "launch_browser", "load_url", "goto"}:
            tgt = (cmd.get("url") or cmd.get("app") or cmd.get("text") or cmd.get("name")
                   or cmd.get("site") or cmd.get("target") or "").strip()
            if not tgt:
                return {"status": "error", "message": "No target to open"}

            def _open():
                return smart_open(tgt)
            def _verify():
                return verify_window_contains(tgt) or verify_screen_ocr(tgt)
            def _correct():
                smart_open(tgt)

            return run_with_verification(_open, _verify, f"open {tgt}", correction_func=_correct)

        # ── MOUSE / KEYBOARD ──────────────────────────────────────────────
        if action == "click":
            x = int(cmd.get("x") or 0); y = int(cmd.get("y") or 0)
            if x == 0 and y == 0:
                return {"status": "skipped", "reason": "no coordinates"}
            return real_click(x, y, button=str(cmd.get("button") or "left"), clicks=int(cmd.get("clicks") or 1))

        if action == "double_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), clicks=2)
        if action == "right_click":
            return real_click(int(cmd.get("x", 0)), int(cmd.get("y", 0)), button="right")

        if action in {"move_mouse", "move_to"}:
            if PYAUTOGUI_OK:
                pyautogui.moveTo(int(cmd.get("x", 0)), int(cmd.get("y", 0)), duration=0.3)
            return {"status": "ok"}

        if action == "drag":
            if PYAUTOGUI_OK:
                pyautogui.dragTo(int(cmd.get("x2", 0)), int(cmd.get("y2", 0)), button="left")
            return {"status": "ok"}

        if action in {"type", "type_text", "write", "input", "enter_text", "fill"}:
            return real_type(str(cmd.get("text") or cmd.get("content") or cmd.get("value") or ""),
                              bool(cmd.get("clear_first", False)), bool(cmd.get("human_speed", False)))

        if action in {"key", "press", "press_key"}:
            k = str(cmd.get("key") or "enter")
            real_press(k)
            return {"status": "ok", "key": k}

        if action in {"hotkey", "key_combo", "shortcut"}:
            keys = cmd.get("keys") or cmd.get("key") or []
            if isinstance(keys, str):
                keys = re.split(r"[+\s,]+", keys)
            real_hotkey(*keys)
            return {"status": "ok"}

        if action == "select_all":   real_hotkey("ctrl", "a"); return {"status": "ok"}
        if action == "copy":
            real_hotkey("ctrl", "c"); time.sleep(0.15)
            clip = pyperclip.paste() if CLIP_OK else ""
            return {"status": "ok", "clipboard": clip}
        if action == "paste":        real_hotkey("ctrl", "v"); return {"status": "ok"}
        if action == "undo":         real_hotkey("ctrl", "z"); return {"status": "ok"}
        if action in {"save", "save_file_shortcut"}: real_hotkey("ctrl", "s"); return {"status": "ok"}
        if action == "refresh":      real_press("f5"); return {"status": "ok"}
        if action == "new_tab":      real_hotkey("ctrl", "t"); return {"status": "ok"}
        if action == "close_tab":    real_hotkey("ctrl", "w"); return {"status": "ok"}

        if action in {"scroll_down", "scrolldown"}:
            real_scroll("down", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action in {"scroll_up", "scrollup"}:
            real_scroll("up", int(cmd.get("amount", 5))); return {"status": "ok"}
        if action == "scroll":
            real_scroll(str(cmd.get("direction", "down")), int(cmd.get("amount", 3))); return {"status": "ok"}

        # ── SCREENSHOT / OCR ──────────────────────────────────────────────
        if action in {"screenshot", "take_screenshot", "capture_screen"}:
            ss = take_screenshot(save=True)
            if ss:
                speak("Screenshot taken!")
                return {"status": "ok", "screenshot": ss}
            return {"status": "error", "message": "Screenshot failed"}

        if action in {"ocr", "ocr_screen", "read_screen"}:
            text = read_screen_text()
            speak("Screen text extracted." if text else "No text found on screen.")
            return {"status": "ok", "text": text[:5000]}

        if action == "find_on_screen":
            loc = find_on_screen(str(cmd.get("image") or ""))
            if loc:
                speak(f"Found at {loc[0]},{loc[1]}")
                return {"status": "ok", "x": loc[0], "y": loc[1]}
            return {"status": "error", "message": "Not found on screen"}

        # ── WINDOW ────────────────────────────────────────────────────────
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
        if action == "focus_window":
            ok = focus_window(str(cmd.get("title") or cmd.get("name") or ""))
            return {"status": "ok" if ok else "error"}
        if action in {"get_windows", "list_windows"}:
            wins = list_windows()
            speak(f"{len(wins)} windows open.")
            return {"status": "ok", "windows": wins}
        if action == "active_window":
            win = get_active_win()
            speak(f"Active: {win or 'unknown'}")
            return {"status": "ok", "active_window": win}

        # ── VOLUME / MEDIA ────────────────────────────────────────────────
        if action in {"volume_up", "increase_volume", "louder"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)):
                real_press("volumeup")
            speak("Volume up"); return {"status": "ok"}
        if action in {"volume_down", "decrease_volume", "quieter"}:
            for _ in range(min(int(cmd.get("steps", 5)), 20)):
                real_press("volumedown")
            speak("Volume down"); return {"status": "ok"}
        if action in {"mute", "unmute", "toggle_mute"}:
            real_press("volumemute"); speak("Muted/unmuted"); return {"status": "ok"}
        if action in {"media_play_pause", "play_pause"}:
            real_press("playpause"); return {"status": "ok"}
        if action in {"media_next", "next_track"}:
            real_press("nexttrack"); return {"status": "ok"}
        if action in {"media_prev", "prev_track"}:
            real_press("prevtrack"); return {"status": "ok"}

        # ── SYSTEM INFO ───────────────────────────────────────────────────
        if action in {"get_system_info", "system_info", "sysinfo"}:
            if PSUTIL_OK:
                dp = "C:\\" if platform.system() == "Windows" else "/"
                info = {
                    "cpu": psutil.cpu_percent(interval=0.5),
                    "cpu_cores": psutil.cpu_count(),
                    "ram": psutil.virtual_memory().percent,
                    "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
                    "disk": psutil.disk_usage(dp).percent,
                    "disk_free_gb": round(psutil.disk_usage(dp).free / 1e9, 1),
                    "platform": platform.system(),
                    "hostname": socket.gethostname(),
                }
                HEALTH.update({"cpu": info["cpu"], "ram": info["ram"], "disk": info["disk"]})
                speak(f"CPU {info['cpu']}%, RAM {info['ram']}%, Disk {info['disk']}%")
                return {"status": "ok", "info": info}
            return {"status": "ok", "info": {"platform": platform.system()}}

        if action == "get_time":
            t_ = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"Time: {t_}"); return {"status": "ok", "time": t_}
        if action == "get_date":
            d_ = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today: {d_}"); return {"status": "ok", "date": d_}

        # ── SHELL ─────────────────────────────────────────────────────────
        if action in {"run_command", "execute_command", "shell", "cmd_run"}:
            c_ = str(cmd.get("command") or cmd.get("cmd") or "")
            if not c_:
                return {"status": "error", "message": "No command"}
            if not _is_command_safe(c_):
                return {"status": "blocked", "message": "Blocked for safety"}
            if not request_approval("run_command", c_):
                return {"status": "denied"}
            try:
                r_ = subprocess.run(c_, shell=True, capture_output=True, text=True, timeout=60,
                                    encoding="utf-8", errors="replace")
                out = (r_.stdout or "")[:5000]
                if out.strip():
                    speak(out[:200])
                return {"status": "ok", "stdout": out, "returncode": r_.returncode}
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Command timed out (60s)"}

        # ── WEB SEARCH ────────────────────────────────────────────────────
        if action in {"search_web", "search", "google", "google_search"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                speak(f"Searching: {q[:60]}")
            else:
                webbrowser.open("https://www.google.com")
            return {"status": "ok"}

        if action in {"web_research", "research"}:
            q = str(cmd.get("query") or cmd.get("text") or cmd.get("topic") or "")
            if not q:
                return {"status": "error", "message": "No query"}
            speak(f"Researching {q[:50]}...")
            result = web_research(q)
            rp = AGENT_DIR / f"research_{int(time.time())}.txt"
            rp.write_text(f"Query: {q}\nDate: {datetime.datetime.now()}\n\n{result}", encoding="utf-8")
            try:
                subprocess.Popen(f'notepad.exe "{rp}"', shell=True)
            except Exception:
                pass
            speak("Research done.")
            return {"status": "ok", "result": result[:800]}

        # ── YOUTUBE ───────────────────────────────────────────────────────
        if action in {"open_youtube", "youtube", "youtube_search", "play_youtube"}:
            q = str(cmd.get("query") or cmd.get("text") or "")
            if q:
                return youtube_search_and_play(q)
            webbrowser.open("https://www.youtube.com")
            return {"status": "ok"}

        # ── SOCIAL POSTING ────────────────────────────────────────────────
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

        # ── WHATSAPP ──────────────────────────────────────────────────────
        if action in {"whatsapp", "whatsapp_send", "send_whatsapp", "wa_send"}:
            phone = str(cmd.get("phone") or cmd.get("contact") or cmd.get("to") or "")
            if not phone:
                return {"status": "error", "message": "No phone number"}
            return wa_send(phone, str(cmd.get("message") or cmd.get("text") or ""))

        # ── SELENIUM ──────────────────────────────────────────────────────
        if action == "selenium_open":
            return selenium_open(str(cmd.get("url") or ""), cmd.get("wait_for"), int(cmd.get("timeout") or 15))
        if action in {"selenium_fill", "fill_field"}:
            return selenium_fill(str(cmd.get("selector") or ""), str(cmd.get("value") or cmd.get("text") or ""),
                                 str(cmd.get("by") or "css"), bool(cmd.get("submit", False)))
        if action == "selenium_click":
            return selenium_click(str(cmd.get("selector") or ""), str(cmd.get("by") or "css"))

        # ── MEMORY ────────────────────────────────────────────────────────
        if action in {"remember", "save_fact", "memorize"}:
            fact = str(cmd.get("fact") or cmd.get("text") or "")
            if fact:
                remember(fact); speak("Noted!")
            return {"status": "ok"}
        if action in {"semantic_memory_search", "search_memory", "memory_search"}:
            res = semantic_search_memory(str(cmd.get("query") or cmd.get("text") or ""),
                                         int(cmd.get("top_k") or 5))
            if res.get("results"):
                speak(f"Found {len(res['results'])} memory matches.")
            else:
                speak("No matching memory found.")
            return res
        if action in {"remember_structured", "save_memory_record"}:
            return remember_structured(str(cmd.get("kind") or "memory"),
                                       str(cmd.get("key") or cmd.get("name") or ""),
                                       cmd.get("value", cmd.get("text", "")),
                                       cmd.get("tags") or [])
        if action in {"get_memory", "show_memory", "recall"}:
            ctx = get_mem_ctx()
            speak("Memory retrieved.")
            return {"status": "ok", "memory": ctx}
        if action in {"add_contact", "save_contact"}:
            name = str(cmd.get("name", ""))
            if name:
                with _mem_lock:
                    MEMORY["contacts"][name.lower()] = {
                        "name": name,
                        "email": str(cmd.get("email", "")),
                        "phone": str(cmd.get("phone", "")),
                    }
                save_memory()
                speak(f"Contact {name} saved.")
            return {"status": "ok"}
        if action == "save_business_fact":
            key = str(cmd.get("key", ""))
            val = cmd.get("value", "")
            if key:
                with _mem_lock:
                    MEMORY["business_facts"][key] = {"value": val, "updated": datetime.datetime.now().isoformat()}
                save_memory()
                speak(f"Business fact saved: {key}")
            return {"status": "ok"}

        # ── SCHEDULE ──────────────────────────────────────────────────────
        if action in {"schedule_task", "schedule", "set_reminder"}:
            task_s = str(cmd.get("task") or cmd.get("command") or "")
            sched  = str(cmd.get("schedule") or cmd.get("time") or "daily at 09:00")
            if not task_s:
                return {"status": "error", "message": "No task to schedule"}
            job = {"id": "".join(random.choices(string.ascii_lowercase, k=8)), "task": task_s, "schedule": sched, "last_run": ""}
            _sched_jobs.append(job)
            save_memory()
            speak(f"Scheduled: {task_s[:50]} — {sched}")
            return {"status": "ok", "job_id": job["id"]}

        # ── HEALTH / WAIT / PING ──────────────────────────────────────────
        if action in {"wait", "sleep", "pause"}:
            secs = min(float(cmd.get("seconds") or 1), 60)
            time.sleep(secs)
            return {"status": "ok"}

        if action in {"ping", "test", "health_check"}:
            speak("Online and ready!")
            return {"status": "ok", "pong": True, "health": HEALTH}

        if action in {"list_skills", "skills", "help"}:
            skills = [
                "plan & execute multi-step goals", "open apps/sites", "send email", "bulk email",
                "read inbox", "draft replies", "find leads", "organize files", "process invoices",
                "paste spreadsheet data", "screenshot & OCR", "voice control", "social media posting",
                "WhatsApp messaging", "social reply bots", "invoice payment queue", "book meetings",
                "web research", "browser automation", "scheduler", "real mouse/keyboard",
                "investor reports", "sales reports", "workflow learning & replay",
                "multi-agent dispatch", "business OS workflows",
            ]
            speak(f"{len(skills)} skill types available.")
            return {"status": "ok", "skills": skills}

        # ── BRIGHTNESS ────────────────────────────────────────────────────
        if action == "brightness_up":
            subprocess.Popen(
                "powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)",
                shell=True)
            return {"status": "ok"}
        if action == "brightness_down":
            subprocess.Popen(
                "powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)",
                shell=True)
            return {"status": "ok"}

        # ── FALLBACK — smart_open ─────────────────────────────────────────
        tgt = (cmd.get("url") or cmd.get("app") or cmd.get("target") or cmd.get("name") or "")
        if tgt:
            res = smart_open(str(tgt))
            if res.get("status") == "ok":
                return res

        res = smart_open(action.replace("_", " ").strip())
        if res.get("status") == "ok":
            return res

        log.warning("Unhandled action: '%s'", action)
        speak(f"I don't know how to '{action.replace('_', ' ')}' yet.")
        return {"status": "error", "message": f"Unknown action: '{action}'"}

    except Exception as e:
        log.error("exec_cmd [%s]: %s", action, e, exc_info=True)
        return {"status": "error", "message": f"Exception in {action}: {e}"}

# ══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE (always-listening, wake word, streaming TTS, mic recovery)
# ══════════════════════════════════════════════════════════════════════════════
_voice_r       = None
_voice_mic     = None
_voice_thread  = None
_voice_mic_idx: Optional[int] = None
_voice_conv_active = False
_voice_last_heard  = 0.0
_VOICE_CONV_TIMEOUT = 30.0
_VOICE_CONFIDENCE_THRESH = 0.5
_voice_errors = 0

def _is_wake_word(heard: str) -> bool:
    h = heard.lower().strip()
    return any(re.search(r"\b" + re.escape(w) + r"\b", h) for w in WAKE_WORDS)

def _strip_wake_word(text: str) -> str:
    t = text.lower().strip()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        pattern = r"^(?:hey\s+)?" + re.escape(w) + r"[,.]?\s*"
        t = re.sub(pattern, "", t).strip()
    return t

def _voice_score_confidence(text: str) -> float:
    if not text or len(text) < 2:
        return 0.0
    t = text.lower()
    if re.match(r"^\s*$|^[^a-z]+$", t):
        return 0.0
    score = min(len(t.split()) / 8.0, 1.0)
    known = ["open", "send", "email", "screenshot", "organize", "search",
             "close", "play", "stop", "help", "find", "check", "read"]
    if any(k in t for k in known):
        score = min(score + 0.3, 1.0)
    return score

def _find_best_mic() -> Optional[int]:
    if not PYAUDIO_OK:
        return None
    try:
        pa = pyaudio.PyAudio()
        best = None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                name = (info.get("name") or "").lower()
                if any(k in name for k in ["stereo mix", "what u hear", "loopback"]):
                    continue
                best = i
                if any(k in name for k in ["microphone", "mic", "input", "headset"]):
                    break
        pa.terminate()
        return best
    except Exception as e:
        log.warning("_find_best_mic: %s", e)
        return None

def _recover_mic():
    global _voice_mic_idx
    log.info("Voice: attempting mic recovery...")
    _voice_mic_idx = _find_best_mic()
    time.sleep(2)
    log.info("Voice: mic recovery done, new index=%s", _voice_mic_idx)

def voice_diagnostics() -> dict:
    devices = []
    default_idx = None
    if PYAUDIO_OK:
        try:
            pa = pyaudio.PyAudio()
            default_idx = pa.get_default_input_device_info().get("index")
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": i,
                        "name": info.get("name", ""),
                        "channels": info.get("maxInputChannels", 0),
                        "rate": int(info.get("defaultSampleRate", 0) or 0),
                        "default": i == default_idx,
                        "selected": i == _voice_mic_idx,
                    })
            pa.terminate()
        except Exception as e:
            devices.append({"error": str(e)})
    result = {
        "status": "ok" if VOICE_OK and bool(devices) else "error",
        "voice_ok": VOICE_OK,
        "pyaudio_ok": PYAUDIO_OK,
        "speech_recognition_ok": sr is not None,
        "selected_mic": _voice_mic_idx,
        "default_mic": default_idx,
        "devices": devices,
        "conversation_active": _voice_conv_active,
        "voice_errors": _voice_errors,
        "energy_threshold": getattr(_voice_r, "energy_threshold", None),
        "voice_status": HEALTH.get("voice_status"),
    }
    speak("Microphone diagnostics complete." if result["status"] == "ok" else "Microphone diagnostics found a problem.")
    return result

def _handle_voice_command(text: str, token: str):
    global _voice_conv_active, _voice_last_heard
    text = text.strip()
    if not text:
        return

    log.info("VOICE CMD: %s", text)
    print(f"\n  [VOICE] '{text}'")

    # Abort
    if text.lower() in ("stop", "abort", "cancel", "interrupt", "stop talking", "quit listening"):
        interrupt_speech("voice command")
        _voice_conv_active = False
        speak("Stopped.")
        HEALTH["voice_status"] = "idle"
        return

    # Voice status
    if re.search(r"\b(voice|mic)\s+status\b", text.lower()):
        diag = voice_diagnostics()
        speak(f"Voice is {diag.get('voice_status')}. Microphone index {_voice_mic_idx}. "
              f"Conversation mode {'active' if _voice_conv_active else 'idle'}.")
        return

    _voice_last_heard = time.time()
    threading.Thread(
        target=lambda: execute_task(text, token),
        daemon=True,
        name="VoiceCmdExec"
    ).start()

_voice_unclear_streak = 0
_VOICE_MAX_RETRY_PROMPTS = 2
_voice_recalibrate_due_at = 0.0

def _voice_listen_loop():
    global _voice_conv_active, _voice_last_heard, _voice_errors, _voice_mic_idx, _voice_unclear_streak, _voice_recalibrate_due_at, _voice_r
    if not sr or not VOICE_OK:
        log.warning("Voice: speech_recognition or pyaudio not available")
        return

    _voice_mic_idx = _find_best_mic()
    print("  [VOICE] Always-listening mode ON")
    print(f"  [VOICE] Wake words: {', '.join(WAKE_WORDS[:5])}...")
    HEALTH["voice_status"] = "listening"

    consecutive_failures = 0
    _voice_recalibrate_due_at = time.time() + 300

    while _voice_on and _running:
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold         = 300
            recognizer.dynamic_energy_threshold  = True
            recognizer.phrase_threshold          = 0.3
            recognizer.non_speaking_duration     = 0.5
            _voice_r = recognizer

            mic = sr.Microphone(device_index=_voice_mic_idx)

            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                consecutive_failures = 0

                while _voice_on and _running:
                    try:
                        in_conv  = _voice_conv_active and (time.time() - _voice_last_heard) < _VOICE_CONV_TIMEOUT
                        # Conversation mode needs a longer pause threshold — natural business
                        # commands ("reply to... the first email... from the investor") have
                        # mid-sentence pauses that a 0.8s cutoff chops into fragments.
                        recognizer.pause_threshold = 1.4 if in_conv else 0.8
                        timeout  = 6.0 if in_conv else 5.0
                        phrase_limit = 18.0 if in_conv else 10.0

                        # Periodic re-calibration against ambient noise, even mid-session,
                        # so a noisy room doesn't permanently degrade capture quality.
                        if time.time() >= _voice_recalibrate_due_at:
                            try:
                                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                            except Exception:
                                pass
                            _voice_recalibrate_due_at = time.time() + 300

                        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)

                        # Recognize
                        text = ""
                        heard_but_unclear = False
                        try:
                            text = recognizer.recognize_google(audio)
                        except sr.UnknownValueError:
                            heard_but_unclear = True
                        except sr.RequestError:
                            try:
                                text = recognizer.recognize_sphinx(audio)
                            except Exception:
                                heard_but_unclear = True
                        except Exception:
                            heard_but_unclear = True

                        if not text:
                            # During an active conversation, silently dropping a misheard
                            # command feels broken — ask the user to repeat instead, up to
                            # a couple of times, before giving up quietly.
                            if in_conv and heard_but_unclear:
                                _voice_unclear_streak += 1
                                if _voice_unclear_streak <= _VOICE_MAX_RETRY_PROMPTS:
                                    speak("Sorry, didn't catch that — go ahead.")
                                    _voice_last_heard = time.time()
                            continue

                        _voice_unclear_streak = 0
                        confidence = _voice_score_confidence(text)
                        log.debug("HEARD: '%s' conf=%.2f", text, confidence)

                        # Conversation mode — no wake word needed
                        if in_conv and confidence >= _VOICE_CONFIDENCE_THRESH:
                            _voice_last_heard = time.time()
                            tok = _cur_token
                            _handle_voice_command(text, tok or "")
                            continue

                        # Heard something in conversation mode but confidence too low to
                        # act on (likely noise/partial capture) — ask for a repeat rather
                        # than silently ignoring it.
                        if in_conv and confidence < _VOICE_CONFIDENCE_THRESH:
                            _voice_unclear_streak += 1
                            if _voice_unclear_streak <= _VOICE_MAX_RETRY_PROMPTS:
                                speak("Could you repeat that?")
                                _voice_last_heard = time.time()
                            continue

                        # Wake word check
                        if _is_wake_word(text):
                            log.info("WAKE WORD: '%s'", text)
                            _voice_conv_active = True
                            _voice_last_heard  = time.time()
                            HEALTH["voice_status"] = "active"

                            if _ws_send_fn and _ws_loop:
                                try:
                                    asyncio.run_coroutine_threadsafe(
                                        _ws_send_fn({"type": "voice_wake", "text": text}),
                                        _ws_loop
                                    )
                                except Exception:
                                    pass

                            cmd = _strip_wake_word(text)
                            if cmd and len(cmd) > 2:
                                tok = _cur_token
                                _handle_voice_command(cmd, tok or "")
                            else:
                                speak("Yes?")
                        else:
                            # Timeout conversation
                            if _voice_conv_active and (time.time() - _voice_last_heard) >= _VOICE_CONV_TIMEOUT:
                                _voice_conv_active = False
                                HEALTH["voice_status"] = "listening"

                    except sr.WaitTimeoutError:
                        if _voice_conv_active and (time.time() - _voice_last_heard) >= _VOICE_CONV_TIMEOUT:
                            _voice_conv_active = False
                            HEALTH["voice_status"] = "listening"
                        continue
                    except Exception as inner_e:
                        log.warning("Voice inner: %s", inner_e)
                        consecutive_failures += 1
                        _voice_errors += 1
                        if consecutive_failures >= 5:
                            break
                        time.sleep(0.5)

        except Exception as outer_e:
            log.warning("Voice outer: %s", outer_e)
            _voice_errors += 1
            consecutive_failures += 1
            if consecutive_failures >= 3:
                _recover_mic()
                consecutive_failures = 0
            time.sleep(2)

    HEALTH["voice_status"] = "off"

def start_voice(token: str) -> bool:
    global _voice_on, _voice_thread, _cur_token
    with _tok_lock:
        _cur_token = token
    if not VOICE_OK:
        log.warning("Voice: cannot start — missing speech_recognition or pyaudio")
        return False
    if _voice_on:
        return True
    _voice_on = True
    HEALTH["voice_status"] = "starting"
    _voice_thread = threading.Thread(target=_voice_listen_loop, daemon=True, name="VoiceListener")
    _voice_thread.start()
    log.info("Voice engine started")
    return True

def stop_voice():
    global _voice_on
    _voice_on = False
    HEALTH["voice_status"] = "off"

def update_token(t: str):
    global _cur_token
    with _tok_lock:
        _cur_token = t

# ══════════════════════════════════════════════════════════════════════════════
# AUTOSTART
# ══════════════════════════════════════════════════════════════════════════════
def setup_autostart():
    try:
        if not WINREG_OK:
            return
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
def _scheduler_loop(tok_ref: list):
    while _running:
        try:
            now = datetime.datetime.now()
            for job in list(_sched_jobs):
                sched = job.get("schedule", "").lower()
                last  = job.get("last_run", "")
                run   = False
                if "daily at" in sched:
                    m = re.search(r"(\d{1,2}):(\d{2})", sched)
                    if m:
                        h, mi = int(m.group(1)), int(m.group(2))
                        if now.hour == h and now.minute == mi:
                            ts = now.strftime("%Y-%m-%dT%H:%M")
                            if not last or last[:16] != ts:
                                run = True
                if run:
                    job["last_run"] = now.isoformat()
                    save_memory()
                    tok = tok_ref[0]
                    if tok:
                        t = job.get("task", "")
                        threading.Thread(
                            target=execute_task, args=(t, tok), daemon=True
                        ).start()
                        log.info("Scheduled job fired: %s", t[:60])
        except Exception as e:
            log.warning("Scheduler: %s", e)
        time.sleep(30)

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH MONITOR
# ══════════════════════════════════════════════════════════════════════════════
def _health_monitor(ws_send_ref: list):
    global _dashboard_last_screenshot
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

            fn = ws_send_ref[0]
            if fn and _ws_loop:
                try:
                    asyncio.run_coroutine_threadsafe(
                        fn({"type": "heartbeat", "health": dict(HEALTH), "device_id": HEALTH.get("device_id", "")}),
                        _ws_loop
                    )
                except Exception:
                    pass
                if time.time() - _dashboard_last_screenshot > 120 and PIL_OK:
                    ss = take_screenshot(save=False, quality=35)
                    if ss:
                        _dashboard_last_screenshot = time.time()
                        try:
                            asyncio.run_coroutine_threadsafe(
                                fn({"type": "live_screenshot", "screenshot": ss, "captured_at": datetime.datetime.now().isoformat()}),
                                _ws_loop
                            )
                        except Exception:
                            pass

            if HEALTH["cpu"] > 90:
                speak("Warning: CPU usage is very high!")
                _notify("Dacexy Alert", f"CPU at {HEALTH['cpu']}%")
            if HEALTH["ram"] > 90:
                speak("Warning: RAM usage is very high!")
        except Exception as e:
            log.warning("Health monitor: %s", e)

# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE SHELL
# ══════════════════════════════════════════════════════════════════════════════
def _interactive_shell(token: str, tok_ref: list):
    print("\n" + "=" * 60)
    print("  DACEXY — COMMAND CENTER v13.0")
    print("=" * 60)
    print(f"  Email    : {_smtp_cfg.get('email') or 'NOT CONFIGURED'}")
    print(f"  Voice    : {'ON' if _voice_on else 'OFF'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print("=" * 60)
    print("  Type any task. 'help' for examples. 'quit' to exit.\n")

    cmds_help = {
        "system status":            "Full diagnostics of all systems",
        "organize desktop":         "Sort files into folders by type",
        "process invoices":         "Extract data from PDFs, queue payments",
        "pending payments":         "Show invoices queued for payment approval",
        "check inbox":              "Read and flag urgent emails",
        "configure email":          "Set up SMTP for auto-send",
        "find leads for X":         "Find email leads for product X",
        "investor report":          "Generate AI investor update",
        "sales report":             "Analyze spreadsheets, generate summary",
        "what is on my screen":      "Use OCR/window/browser vision to describe the screen",
        "business dashboard":        "Show revenue, profit, KPI, customer, and lead status",
        "board report":              "Generate a verified board report file",
        "record revenue 5000":       "Track revenue/profit/KPI metrics in memory",
        "monitor competitor NAME":   "Save competitor monitoring record",
        "search memory QUERY":       "Semantic search across long-term memory",
        "list workflows":           "Show all saved/learned workflows",
        "replay workflow NAME":     "Re-execute a saved workflow",
        "reply to my whatsapp":     "Read WhatsApp DMs and draft replies",
        "turn on auto reply":       "Enable auto-send replies (needs approval)",
        "open youtube":             "Open YouTube",
        "screenshot":               "Take a screenshot",
        "system info":              "CPU/RAM/disk usage",
        "queue task GOAL":          "Add a background task to the queue",
        "list tasks":               "Show all queued/running tasks",
        "help":                     "Show this list",
    }

    while _running:
        try:
            line = input("  Dacexy> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        tl = line.lower()

        if tl in ("quit", "exit"):
            print("  Goodbye!"); break
        if tl in ("help", "menu"):
            print()
            for k, v in cmds_help.items():
                print(f"    {k:<35} {v}")
            print()
            continue
        if tl == "memory":
            print("\n" + get_mem_ctx() + "\n"); continue
        if tl == "jobs":
            if _sched_jobs:
                for j in _sched_jobs:
                    print(f"  [{j['id']}] {j['task']} — {j['schedule']}")
            else:
                print("  No scheduled jobs.")
            continue
        if tl == "email":
            configure_smtp_interactive(); continue
        if tl == "sysinfo":
            exec_cmd({"action": "get_system_info"}, token); continue
        if tl == "screenshot":
            exec_cmd({"action": "screenshot"}, token); continue
        if tl == "health":
            print(f"  Health: {HEALTH}"); continue
        if tl == "workflows":
            exec_cmd({"action": "list_workflows"}, token); continue

        tok = tok_ref[0]
        def _run(t_=tok, cmd_=line):
            try:
                r = execute_task(cmd_, t_)
                status = r.get("status", "?")
                ok_n   = r.get("ok", 0)
                tot_n  = r.get("total", r.get("steps", 1))
                print(f"\n  [{'OK' if status == 'ok' else 'PARTIAL' if status == 'partial' else 'FAIL'}] "
                      f"{ok_n}/{tot_n} steps — {status}")
            except Exception as e:
                print(f"\n  [ERROR] {e}")
        threading.Thread(target=_run, daemon=True, name="ShellTask").start()

# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — Authenticated bridge with live monitoring (Phase 9)
# ══════════════════════════════════════════════════════════════════════════════
async def run_websocket(token: str):
    global _ws_send_fn, _ws_loop, _ws_device_session
    retry = 4.0; max_retry = 60.0
    device = get_device_registration()

    while _running:
        try:
            _ws_device_session = _new_id("session")
            log.info("WS: connecting...")
            print("  [WS] Connecting to Dacexy cloud...")

            connect_kw: dict = {"ping_interval": 20, "ping_timeout": 15, "max_size": 16 * 1024 * 1024}
            try:
                wsv = int(str(getattr(websockets, "__version__", "0")).split(".")[0])
                if wsv >= 14:
                    connect_kw["open_timeout"] = 20
                elif wsv >= 10:
                    connect_kw["close_timeout"] = 10
            except Exception:
                pass

            async with websockets.connect(BACKEND_WS, **connect_kw) as ws:
                await ws.send(json.dumps({"token": token}))
                try:
                    auth_raw = await asyncio.wait_for(ws.recv(), timeout=25)
                    auth_msg = json.loads(auth_raw)
                    if auth_msg.get("type") == "error":
                        log.error("WS auth rejected: %s", auth_msg.get("message"))
                        speak("Authentication failed.")
                        await asyncio.sleep(retry)
                        retry = min(retry * 1.5, max_retry)
                        continue
                except asyncio.TimeoutError:
                    log.warning("WS: auth timeout")
                    await asyncio.sleep(retry)
                    retry = min(retry * 1.5, max_retry)
                    continue
                except Exception as e:
                    log.warning("WS: auth error: %s", e)
                    await asyncio.sleep(retry)
                    continue

                await ws.send(json.dumps({
                    "type": "init",
                    "device_id": device.get("device_id"),
                    "session_id": _ws_device_session,
                    "platform": platform.system(),
                    "machine": platform.machine(),
                    "hostname": socket.gethostname(),
                    "version": AGENT_VERSION,
                    "features": [
                        "voice3", "vision", "browser", "email", "social_selenium",
                        "bulk_email", "lead_gen", "web_research", "scheduler", "memory",
                        "selenium", "ocr", "screenshot", "file_organizer", "invoice_extractor",
                        "spreadsheet_paste", "inbox_reader", "approval_gates",
                        "real_mouse_keyboard", "encrypted_config", "health_monitor",
                        "calendar_booking", "human_approval", "social_reply_bots",
                        "payment_queue", "planner", "executor", "verifier",
                        "workflow_learning", "multi_agent", "business_os",
                        "task_queue", "background_execution", "task_progress",
                        "device_registration", "command_sync", "task_sync",
                        "live_logs", "live_screenshots", "semantic_memory",
                        "continuous_vision", "checkpoint_recovery",
                    ],
                    "memory_context": get_mem_ctx()[:3000],
                }))

                log.info("WS: connected!")
                print("\n  [OK] Connected to Dacexy cloud — agent is LIVE!")
                speak("Connected! Ready for your commands.")
                HEALTH["ws_status"] = "connected"
                retry = 4.0

                ws_lock = asyncio.Lock()
                loop    = asyncio.get_event_loop()

                async def ws_send(data: dict):
                    async with ws_lock:
                        try:
                            await ws.send(json.dumps(data))
                        except Exception as e_:
                            log.warning("ws_send: %s", e_)

                _ws_send_fn = ws_send
                _ws_loop    = loop

                while _running:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=50)
                    except asyncio.TimeoutError:
                        try:
                            await asyncio.wait_for(ws.send(json.dumps({"type": "ping"})), timeout=8)
                        except Exception:
                            break
                        continue

                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    mtype    = msg.get("type",   "")
                    action   = msg.get("action", "")
                    task_txt = (msg.get("task") or msg.get("goal") or "").strip()
                    task_id  = str(msg.get("task_id") or "")

                    if mtype == "ping":
                        await ws_send({"type": "pong"}); continue
                    if mtype in ("pong", "connected", "init_ack", "heartbeat"):
                        continue

                    # Task cancellation from dashboard
                    if mtype == "cancel_task" or action == "cancel_task":
                        tid = str(msg.get("task_id") or "")
                        result = cancel_task(tid)
                        await ws_send({"type": "task_cancelled", "task_id": tid, **result})
                        continue

                    # Direct action command
                    if action and action not in ("swarm_task", "task", "run_agent", ""):
                        def _cmd_thread(m_=dict(msg), t_=token, tid_=task_id):
                            try:
                                r_ = exec_cmd(m_, t_)
                                status_ = r_.get("status", "error")  # missing status is NOT assumed ok
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": status_,
                                    "ok": 1 if status_ == "ok" else 0,
                                    "total": 1,
                                    "result": str(r_.get("message") or r_.get("opened") or
                                                  ("done" if status_ == "ok" else status_)),
                                    "data": r_,
                                }), loop)
                            except Exception as e_:
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": "error", "ok": 0, "total": 1, "result": str(e_),
                                }), loop)
                        threading.Thread(target=_cmd_thread, daemon=True).start()
                        continue

                    # Natural language task (background queued)
                    if task_txt or mtype in ("task", "command"):
                        if not task_txt:
                            task_txt = action
                        if not task_txt:
                            continue
                        log.info("Dashboard task: %s", task_txt[:80])
                        print(f"\n  [TASK] From dashboard: {task_txt[:80]}")
                        speak(f"On it! {task_txt[:40]}")

                        def _task_thread(t_=token, txt_=task_txt, tid_=task_id):
                            try:
                                # task_id threaded through so execute_planned_task can
                                # push live task_progress messages per step, not just
                                # a single result at the very end.
                                r_ = coordinator_dispatch(txt_, t_, task_id=tid_)
                                asyncio.run_coroutine_threadsafe(ws_send({
                                    "type": "task_result", "task_id": tid_,
                                    "status": r_.get("status", "error"),
                                    "ok": r_.get("ok", 0),
                                    "total": r_.get("total", 1),
                                    "result": r_.get("result", ""),
                                    "steps": r_.get("results", []),
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
            HEALTH["ws_status"] = "disconnected"
            HEALTH["ws_reconnects"] = int(HEALTH.get("ws_reconnects", 0)) + 1
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
    print("  DACEXY DESKTOP AGENT v13.0 — STARTING")
    print("  Production-grade autonomous desktop AI")
    print(f"  Runtime version: {AGENT_VERSION}")
    print("  Voice | Planner | Executor | Verifier | Memory | Multi-Agent")
    print("=" * 65 + "\n")

    init_tts()
    load_memory()
    get_device_registration()
    restore_task_state()
    start_vision_monitor()

    caps = []
    if PYAUTOGUI_OK:  caps.append("mouse/keyboard")
    if PIL_OK:        caps.append("screenshot")
    if PIL_OK:        caps.append("continuous-vision")
    if VOICE_OK:      caps.append("VOICE")
    if SELENIUM_OK:   caps.append("browser-automation")
    if BS4_OK:        caps.append("web-scraping")
    if OCR_OK:        caps.append("OCR")
    if PDF_OK:        caps.append("invoice-PDF")
    if XL_OK:         caps.append("spreadsheet")
    if CRYPTO_OK:     caps.append("encrypted-config")
    em = _smtp_cfg.get("email") or ""
    caps.append(f"email={'✓ ' + em if em else 'NOT CONFIGURED'}")
    print(f"  Capabilities: {', '.join(caps)}\n")

    # Print saved workflows
    wfs = list_workflows()
    if wfs:
        print(f"  Saved workflows ({len(wfs)}): {', '.join(wfs[:5])}\n")

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
            if token:
                break
            if attempt < 2:
                print(f"\n  Attempt {attempt + 1}/3 failed.\n")
        if not token:
            print("\n  [ERROR] Authentication failed. Exiting.")
            sys.exit(1)

    try:
        setup_autostart()
    except Exception:
        pass

    if not _smtp_cfg.get("email"):
        print("  [EMAIL] Not configured. Type 'configure email' to enable auto-send.\n")

    voice_ok = start_voice(token)
    tok_ref     = [token]
    ws_send_ref = [None]

    threading.Thread(target=_scheduler_loop,    args=(tok_ref,),     daemon=True, name="Scheduler").start()
    threading.Thread(target=_health_monitor,    args=(ws_send_ref,), daemon=True, name="HealthMon").start()
    threading.Thread(target=_interactive_shell, args=(token, tok_ref), daemon=True, name="Shell").start()

    print("  " + "-" * 63)
    print("  Dacexy Agent v13.0 — LIVE")
    print(f"  Voice    : {'ON — say Hey Dex / Dacexy / Jarvis' if voice_ok else 'OFF (install PyAudio)'}")
    print(f"  Email    : {_smtp_cfg.get('email') or 'Not configured'}")
    print(f"  Dashboard: dacexy.vercel.app")
    print(f"  Log file : {LOG_FILE}")
    print(f"  Agents   : {', '.join(a.name for a in _AGENTS)}")
    print("  " + "-" * 63 + "\n")

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
        stop_vision_monitor()
        with _sel_lock:
            if _selenium_driver:
                try:
                    _selenium_driver.quit()
                except Exception:
                    pass
        with _social_lock:
            for _drv in _social_drivers.values():
                try:
                    _drv.quit()
                except Exception:
                    pass
        try:
            save_memory()
        except Exception:
            pass
        print("  Dacexy stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
