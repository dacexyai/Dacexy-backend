"""
dex_tools.py — Tool Registry + Autonomous Agent Loop for Dex (Dacexy Desktop Agent)
====================================================================================
This module is an ADDITION, not a rewrite. It does not touch exec_cmd, the
parser, the workflow engine, memory, or voice. It sits on top of all of it.

It gives Dex three things it was missing:

1. TOOL_REGISTRY — every real action exec_cmd already supports, described as
   a structured tool with name / description / input_schema (JSON-schema,
   OpenAI/Anthropic tool-calling style). This is built from a direct audit of
   exec_cmd's branches in dacexy_agent.py — every name here is a real,
   already-implemented action. Nothing here is invented.

2. agent_loop() — an explicit Think -> Plan -> Act -> Observe -> Verify loop.
   It reuses the existing decompose_goal_to_graph / execute_planned_workflow /
   exec_cmd / is_verified_step / recover_step / replan_after_failure machinery
   from dacexy_agent.py (passed in via `host` at call time so there is no
   circular import). It just makes the loop explicit, tool-schema-aware, and
   gives you a visible reasoning + observation trace per step, like
   AutoGPT/Devin-style agents show.

3. PAUSE / RESUME control — a threading.Event the loop checks between every
   step, layered on top of the existing cancel_active_workflow/_abort_flag.

Import this from dacexy_agent.py with:
    import dex_tools

and call:
    dex_tools.bind(host=sys.modules[__name__])   # near the bottom of dacexy_agent.py
    dex_tools.agent_loop(goal, token)             # replaces/augments execute_task

See PATCH_NOTES.md for the exact 3-line wiring.
"""
from __future__ import annotations

import json
import re
import threading
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple


# Actions safe to run concurrently because they don't touch the shared
# mouse/keyboard/active-window (GUI automation is inherently single-threaded
# — two real_click/real_type calls racing for the same input device would
# corrupt each other). Everything NOT in this set runs strictly in order,
# exactly as before. This is what lets independent steps like "research X"
# + "research Y" + "draft an invoice" overlap instead of queuing, without
# risking two threads fighting over the mouse.
PARALLEL_SAFE_ACTIONS = frozenset({
    "search_web", "research_to_notepad", "find_leads_and_email",
    "web_research", "browser_search_workflow",  # each opens its own driver/profile
    "create_file", "create_excel", "create_word_document", "create_folder_and_files",
    "save_report", "generate_report", "generate_proposal", "generate_invoice",
    "generate_job_description", "analyze_competitors", "generate_social_content",
    "draft_contract", "create_newsletter", "generate_ad_document", "track_expense",
    "read_file", "read_spreadsheet", "summarize_pdf", "extract_invoice",
    "send_email", "draft_email_in_browser", "read_inbox", "investor_email_report",
    "wa_send", "book_meeting", "check_calendar", "get_system_info", "get_time",
    "get_date", "runtime_status", "voice_status", "speak", "remember", "get_memory",
    "ask_ai", "daily_summary", "monitor_errors", "list_payment_queue",
})



# ══════════════════════════════════════════════════════════════════════════════
# 1. TOOL REGISTRY — real actions, real schemas
# ══════════════════════════════════════════════════════════════════════════════
# Every entry below maps 1:1 to an `if action in {...}` / `if action == "..."`
# branch that already exists in exec_cmd() inside dacexy_agent.py. The
# canonical action name (first alias) is what the planner emits; exec_cmd
# already accepts the aliases listed too, so nothing downstream changes.

TOOL_REGISTRY: List[Dict[str, Any]] = [

    # ── App / window / browser opening ────────────────────────────────────
    {
        "name": "open",
        "aliases": ["open_app", "open_application", "launch", "launch_application",
                    "open_site", "open_website", "open_url", "open_browser",
                    "open_chrome", "load_url", "go_to", "goto", "navigate",
                    "navigate_to", "visit", "browse", "google", "run_app",
                    "launch_browser", "open_file", "start"],
        "description": "Open a website, app, or file by name (e.g. 'chrome', 'notepad', 'youtube', 'gmail', or a URL). Use this for any 'open X' / 'launch X' / 'go to X' / 'start X' request.",
        "input_schema": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "App name, site name, or URL to open"}},
            "required": ["target"],
        },
    },
    {
        "name": "smart_open",
        "aliases": [],
        "description": "Same as open, but performs additional verification that the app/site actually launched (window/URL check). Prefer 'open' first; this is used internally as the verified path.",
        "input_schema": {
            "type": "object",
            "properties": {"target": {"type": "string"}},
            "required": ["target"],
        },
    },
    {
        "name": "open_youtube",
        "aliases": ["youtube", "youtube_search", "play_youtube"],
        "description": "Search YouTube for a query and open/play the top result.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "close_window",
        "aliases": ["close", "close_app", "minimize", "minimize_window",
                    "maximize", "maximize_window", "fullscreen", "show_desktop", "win_d"],
        "description": "Close, minimize, maximize the active window, or show desktop.",
        "input_schema": {
            "type": "object",
            "properties": {"mode": {"type": "string", "enum": ["close", "minimize", "maximize", "show_desktop"]}},
        },
    },
    {
        "name": "switch_window",
        "aliases": ["alt_tab", "focus_window"],
        "description": "Switch focus to a window matching a title pattern, or alt-tab.",
        "input_schema": {
            "type": "object",
            "properties": {"title_pattern": {"type": "string", "description": "Substring of the window title to focus"}},
        },
    },
    {
        "name": "get_windows",
        "aliases": ["list_windows", "active_window"],
        "description": "List all open window titles, or get the currently active window.",
        "input_schema": {"type": "object", "properties": {}},
    },

    # ── GUI automation (pyautogui) ────────────────────────────────────────
    {
        "name": "click",
        "aliases": ["double_click", "right_click", "move_mouse", "move_to"],
        "description": "Click, double-click, right-click, or move the mouse to screen coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"}, "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "clicks": {"type": "integer", "default": 1},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "type_text",
        "aliases": ["enter_text", "input", "fill", "type"],
        "description": "Type text at the current cursor focus.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "clear_first": {"type": "boolean", "default": False},
            },
            "required": ["text"],
        },
    },
    {
        "name": "press_key",
        "aliases": ["key", "press", "hotkey", "key_combo", "shortcut"],
        "description": "Press a key or key combo, e.g. 'enter', 'ctrl+c', 'alt+tab'.",
        "input_schema": {
            "type": "object",
            "properties": {"keys": {"type": "string", "description": "Key or combo, '+' separated for combos"}},
            "required": ["keys"],
        },
    },
    {
        "name": "scroll",
        "aliases": ["scroll_down", "scroll_up", "scrolldown", "scrollup"],
        "description": "Scroll the active window up or down.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
                "amount": {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "screenshot",
        "aliases": ["take_screenshot", "capture_screen"],
        "description": "Capture a screenshot of the current screen and save it to disk.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ocr_screen",
        "aliases": ["ocr", "read_screen"],
        "description": "OCR the current screen (or a region) and return the text found.",
        "input_schema": {"type": "object", "properties": {"target": {"type": "string", "description": "Text to look for / verify is on screen"}}},
    },
    {
        "name": "media_play_pause",
        "aliases": ["play_pause", "pause", "media_next", "next_track",
                    "media_prev", "prev_track", "mute", "unmute", "toggle_mute",
                    "increase_volume", "decrease_volume", "volume_up", "volume_down",
                    "louder", "quieter", "brightness_up", "brightness_down"],
        "description": "Control media playback (play/pause/next/prev), volume, or screen brightness.",
        "input_schema": {"type": "object", "properties": {"action_name": {"type": "string"}}},
    },
    {
        "name": "copy",
        "aliases": ["paste", "select_all", "undo", "refresh", "new_tab", "close_tab"],
        "description": "Common keyboard shortcuts: copy, paste, select all, undo, refresh page, new/close browser tab.",
        "input_schema": {"type": "object", "properties": {}},
    },

    # ── Web research ───────────────────────────────────────────────────────
    {
        "name": "search_web",
        "aliases": ["search", "google_search", "research", "web_research"],
        "description": "Search the web for a query and return a synthesized answer/summary. Does not write to a file (use research_to_notepad for that).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "research_to_notepad",
        "aliases": ["save_research_report"],
        "description": "Research a topic on the web and save the findings into a text file Dex creates on disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filename": {"type": "string", "description": "Optional filename; auto-generated if omitted"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "research_and_write",
        "aliases": [],
        "description": "Research a query on the web and write the findings to a destination (notepad/word/excel).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "destination": {"type": "string", "enum": ["notepad", "word", "excel"], "default": "notepad"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_leads_and_email",
        "aliases": ["find_leads", "get_leads", "lead_campaign"],
        "description": "Find potential business leads for a product/niche on the web. Returns a list; does not email automatically unless instructed via bulk_email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "niche": {"type": "string", "default": ""},
                "max_leads": {"type": "integer", "default": 50},
            },
            "required": ["product"],
        },
    },

    # ── Browser agent (selenium) ───────────────────────────────────────────
    {
        "name": "browser_search_workflow",
        "aliases": [],
        "description": "Open a real browser, search a query, and optionally save the result page content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "save_name": {"type": "string", "default": ""},
            },
            "required": ["query"],
        },
    },
    {
        "name": "browser_read_page",
        "aliases": [],
        "description": "Read the text content of the currently open browser page (selenium session must already be active from a prior browser action).",
        "input_schema": {"type": "object", "properties": {"max_chars": {"type": "integer", "default": 8000}}},
    },
    {
        "name": "browser_extract_and_summarize",
        "aliases": [],
        "description": "Read the current page and produce an AI summary of it, optionally focused on a query.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string", "default": ""}}},
    },
    {
        "name": "selenium_open",
        "aliases": [],
        "description": "Open a specific URL in a controlled (selenium) browser session, with optional wait-for-element.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}, "wait_for_css": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "selenium_fill",
        "aliases": ["fill_field"],
        "description": "Fill a form field on the currently open browser page using a CSS/XPath selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"}, "value": {"type": "string"},
                "by": {"type": "string", "enum": ["css", "xpath", "id", "name"], "default": "css"},
                "submit": {"type": "boolean", "default": False},
            },
            "required": ["selector", "value"],
        },
    },
    {
        "name": "selenium_click",
        "aliases": [],
        "description": "Click an element on the currently open browser page by selector.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}, "by": {"type": "string", "enum": ["css", "xpath", "id", "name"], "default": "css"}},
            "required": ["selector"],
        },
    },

    # ── Email ──────────────────────────────────────────────────────────────
    {
        "name": "send_email",
        "aliases": ["send_mail", "email", "compose_email", "gmail_send", "send_email_by_name"],
        "description": "Send a real email via configured SMTP. Requires human approval before sending (APPROVAL_REQUIRED).",
        "input_schema": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "draft_email_in_browser",
        "aliases": ["draft_email", "gmail_compose"],
        "description": "Open Gmail's compose window pre-filled with a draft (does NOT send — opens for the user to review and click Send).",
        "input_schema": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["subject", "body"],
        },
    },
    {
        "name": "send_bulk_email",
        "aliases": ["bulk_email", "mass_email", "email_campaign"],
        "description": "Send a templated email to a list of contacts (CSV-loaded or provided inline). Requires approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contacts": {"type": "array", "items": {"type": "object"}},
                "subject": {"type": "string"},
                "body_tmpl": {"type": "string"},
                "delay": {"type": "number", "default": 1.5},
            },
            "required": ["contacts", "subject", "body_tmpl"],
        },
    },
    {
        "name": "read_inbox",
        "aliases": ["check_messages"],
        "description": "Read recent emails from the configured inbox.",
        "input_schema": {"type": "object", "properties": {"max_count": {"type": "integer", "default": 10}}},
    },
    {
        "name": "draft_reply",
        "aliases": [],
        "description": "Draft an AI-suggested reply to an email subject/body, without sending it.",
        "input_schema": {
            "type": "object",
            "properties": {"subject": {"type": "string"}, "original_body": {"type": "string", "default": ""}},
            "required": ["subject"],
        },
    },
    {
        "name": "investor_email_report",
        "aliases": ["email_report", "summarize_investor_emails"],
        "description": "Scan the inbox for emails matching a keyword (e.g. 'investor') and produce a summary report.",
        "input_schema": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "default": "investor"}, "max_count": {"type": "integer", "default": 20}},
        },
    },
    {
        "name": "configure_email",
        "aliases": [],
        "description": "Interactively configure SMTP credentials for sending email. Requires user input in terminal.",
        "input_schema": {"type": "object", "properties": {}},
    },

    # ── Social media ───────────────────────────────────────────────────────
    {
        "name": "post_twitter",
        "aliases": ["tweet", "twitter_post"],
        "description": "Post a tweet via browser automation. Requires approval.",
        "input_schema": {
            "type": "object",
            "properties": {"username": {"type": "string"}, "password": {"type": "string"}, "text": {"type": "string"}},
            "required": ["username", "password", "text"],
        },
    },
    {
        "name": "post_linkedin",
        "aliases": ["linkedin_post"],
        "description": "Post a LinkedIn update via browser automation. Requires approval.",
        "input_schema": {
            "type": "object",
            "properties": {"username": {"type": "string"}, "password": {"type": "string"}, "text": {"type": "string"}},
            "required": ["username", "password", "text"],
        },
    },
    {
        "name": "post_facebook",
        "aliases": ["facebook_post"],
        "description": "Post a Facebook update (optionally to a page) via browser automation. Requires approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string"}, "password": {"type": "string"},
                "text": {"type": "string"}, "page_id": {"type": "string", "default": ""},
            },
            "required": ["username", "password", "text"],
        },
    },
    {
        "name": "check_social_messages",
        "aliases": ["check_dms", "watch_messages"],
        "description": "Check DMs/messages across connected social platforms (WhatsApp/Instagram/Facebook), optionally auto-replying.",
        "input_schema": {
            "type": "object",
            "properties": {
                "auto": {"type": "boolean", "default": False},
                "max_chats": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "start_social_replies",
        "aliases": ["enable_auto_reply"],
        "description": "Start an auto-reply polling loop on the given social platforms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms": {"type": "array", "items": {"type": "string"}},
                "auto": {"type": "boolean", "default": False},
            },
            "required": ["platforms"],
        },
    },
    {
        "name": "stop_social_replies",
        "aliases": ["disable_auto_reply"],
        "description": "Stop the auto-reply polling loop.",
        "input_schema": {"type": "object", "properties": {"platforms": {"type": "array", "items": {"type": "string"}}}},
    },
    {
        "name": "wa_send",
        "aliases": ["send_whatsapp", "whatsapp_send", "whatsapp"],
        "description": "Send a WhatsApp message to a phone number via WhatsApp Web automation.",
        "input_schema": {
            "type": "object",
            "properties": {"phone": {"type": "string"}, "msg": {"type": "string"}},
            "required": ["phone", "msg"],
        },
    },

    # ── Calendar ───────────────────────────────────────────────────────────
    {
        "name": "check_calendar",
        "aliases": ["check_calendar_availability"],
        "description": "Check calendar availability on a given date.",
        "input_schema": {"type": "object", "properties": {"date_str": {"type": "string"}}, "required": ["date_str"]},
    },
    {
        "name": "book_meeting",
        "aliases": [],
        "description": "Book a calendar meeting with someone at a given date/time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "with_email": {"type": "string"}, "subject": {"type": "string"},
                "date_str": {"type": "string"}, "duration_min": {"type": "integer", "default": 60},
            },
            "required": ["with_email", "subject", "date_str"],
        },
    },

    # ── Files / documents ──────────────────────────────────────────────────
    {
        "name": "create_file",
        "aliases": ["write_file", "save_file", "write", "save", "save_file_shortcut"],
        "description": "Create a plain text/markdown/csv/json file with given content at a path, or trigger Ctrl+S save in the active app.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "aliases": ["list_files", "ls"],
        "description": "Read a file's content or list files in a folder.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "create_excel",
        "aliases": ["create_excel_sheet", "create_spreadsheet"],
        "description": "Create an Excel workbook with given columns and optional row data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "string"}},
                "rows": {"type": "array", "items": {"type": "array"}},
            },
        },
    },
    {
        "name": "read_spreadsheet",
        "aliases": [],
        "description": "Read an existing spreadsheet file and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "sheet": {"type": "integer", "default": 0}},
            "required": ["path"],
        },
    },
    {
        "name": "create_word_document",
        "aliases": ["create_word_doc", "create_word_report"],
        "description": "Create a Word (.docx) document with a title and body content (AI-generated if only a topic is given).",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["topic"],
        },
    },
    {
        "name": "create_folder_and_files",
        "aliases": ["create_folder_files"],
        "description": "Create a folder and optionally populate it with files.",
        "input_schema": {
            "type": "object",
            "properties": {"folder": {"type": "string"}, "files": {"type": "array", "items": {"type": "object"}}},
            "required": ["folder"],
        },
    },
    {
        "name": "organize_folder",
        "aliases": [],
        "description": "Organize files in a folder into subfolders by type (images/docs/etc).",
        "input_schema": {
            "type": "object",
            "properties": {"folder": {"type": "string"}, "dry_run": {"type": "boolean", "default": False}},
            "required": ["folder"],
        },
    },
    {
        "name": "rename_files",
        "aliases": [],
        "description": "Batch-rename files in a folder matching a pattern.",
        "input_schema": {
            "type": "object",
            "properties": {"folder": {"type": "string"}, "pattern": {"type": "string"}, "replacement": {"type": "string"}},
            "required": ["folder", "pattern", "replacement"],
        },
    },
    {
        "name": "summarize_pdf",
        "aliases": ["summarise_pdf", "pdf_summary"],
        "description": "Summarize the contents of a PDF file.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "extract_invoice",
        "aliases": [],
        "description": "Extract structured invoice data (amount, vendor, date) from a PDF.",
        "input_schema": {"type": "object", "properties": {"pdf_path": {"type": "string"}}, "required": ["pdf_path"]},
    },
    {
        "name": "process_invoices",
        "aliases": [],
        "description": "Process all invoice PDFs in a folder and queue them for payment.",
        "input_schema": {"type": "object", "properties": {"folder": {"type": "string"}}, "required": ["folder"]},
    },
    {
        "name": "save_report",
        "aliases": [],
        "description": "Save given text content as a report file at an optional path.",
        "input_schema": {
            "type": "object",
            "properties": {"content": {"type": "string"}, "filename": {"type": "string"}, "path": {"type": "string"}},
            "required": ["content"],
        },
    },

    # ── Payments ───────────────────────────────────────────────────────────
    {
        "name": "list_payment_queue",
        "aliases": ["payment_queue", "show_payments", "pending_payments"],
        "description": "List invoices/payments currently queued for review or approval.",
        "input_schema": {"type": "object", "properties": {"status": {"type": "string", "default": "pending_review"}}},
    },
    {
        "name": "approve_payment",
        "aliases": ["pay_invoice"],
        "description": "Approve a queued payment and open the relevant payment portal. Requires approval gate.",
        "input_schema": {
            "type": "object",
            "properties": {"queue_id": {"type": "string"}, "portal": {"type": "string", "default": "razorpay"}},
            "required": ["queue_id"],
        },
    },
    {
        "name": "reject_payment",
        "aliases": [],
        "description": "Reject a queued payment with a reason.",
        "input_schema": {
            "type": "object",
            "properties": {"queue_id": {"type": "string"}, "reason": {"type": "string", "default": ""}},
            "required": ["queue_id"],
        },
    },
    {
        "name": "generate_invoice",
        "aliases": [],
        "description": "Generate an invoice document for a client with line items and total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client": {"type": "string"},
                "items": {"type": "array", "items": {"type": "object"}},
                "total": {"type": "number", "default": 0},
            },
            "required": ["client"],
        },
    },
    {
        "name": "track_expense",
        "aliases": [],
        "description": "Record a business expense in the local expense tracker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"}, "amount": {"type": "number"},
                "category": {"type": "string", "default": "General"},
            },
            "required": ["description", "amount"],
        },
    },

    # ── Business document generators ──────────────────────────────────────
    {
        "name": "generate_report",
        "aliases": [],
        "description": "Generate a business report of a given type using available data.",
        "input_schema": {
            "type": "object",
            "properties": {"report_type": {"type": "string"}, "data": {"type": "string", "default": ""}},
            "required": ["report_type"],
        },
    },
    {
        "name": "generate_proposal",
        "aliases": [],
        "description": "Generate a business proposal document for a client and service.",
        "input_schema": {
            "type": "object",
            "properties": {"client": {"type": "string"}, "service": {"type": "string"}},
            "required": ["client", "service"],
        },
    },
    {
        "name": "generate_job_description",
        "aliases": [],
        "description": "Generate a job description for a role at a company.",
        "input_schema": {
            "type": "object",
            "properties": {"role": {"type": "string"}, "company": {"type": "string", "default": ""}},
            "required": ["role"],
        },
    },
    {
        "name": "analyze_competitors",
        "aliases": [],
        "description": "Research and summarize competitors for a given business/industry.",
        "input_schema": {"type": "object", "properties": {"business": {"type": "string"}}, "required": ["business"]},
    },
    {
        "name": "generate_social_content",
        "aliases": [],
        "description": "Generate social media post content on a topic for one or all platforms.",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}, "platform": {"type": "string", "default": "all"}},
            "required": ["topic"],
        },
    },
    {
        "name": "draft_contract",
        "aliases": [],
        "description": "Draft a basic service contract for a named client.",
        "input_schema": {"type": "object", "properties": {"client": {"type": "string"}}, "required": ["client"]},
    },
    {
        "name": "create_newsletter",
        "aliases": [],
        "description": "Generate a newsletter draft for the business.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "generate_ad_document",
        "aliases": [],
        "description": "Generate an advertisement document/copy for a topic or product.",
        "input_schema": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]},
    },
    {
        "name": "daily_summary",
        "aliases": [],
        "description": "Produce a daily business summary (tasks done, payments, messages).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "monitor_errors",
        "aliases": [],
        "description": "Scan a log file for recent error entries.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },

    # ── System / info ──────────────────────────────────────────────────────
    {
        "name": "get_system_info",
        "aliases": ["sysinfo", "system_info"],
        "description": "Get system info (OS, CPU, RAM, disk usage).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_time",
        "aliases": [],
        "description": "Get the current time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_date",
        "aliases": [],
        "description": "Get the current date.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "runtime_status",
        "aliases": ["agent_status", "system_status", "health_check", "status", "runtime_state", "ping", "test"],
        "description": "Get Dex's current runtime state (active app, last action, health counters), or a basic health ping.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "voice_status",
        "aliases": ["voice_health", "mic_status"],
        "description": "Get voice subsystem diagnostics (microphone, wake-word stats).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "speak",
        "aliases": ["notify"],
        "description": "Speak a message out loud via TTS and show a desktop notification.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "remember",
        "aliases": ["memorize", "save_fact"],
        "description": "Save a fact to Dex's long-term memory.",
        "input_schema": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]},
    },
    {
        "name": "get_memory",
        "aliases": ["show_memory", "recall"],
        "description": "Recall Dex's stored memory/context.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_skills",
        "aliases": ["skills", "help"],
        "description": "List everything Dex can do.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "shell",
        "aliases": ["cmd_run", "run_command", "execute_command"],
        "description": "Run a shell command. BLOCKED for destructive commands automatically. Requires approval.",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    },
    {
        "name": "wait",
        "aliases": ["sleep"],
        "description": "Wait for a number of seconds before continuing.",
        "input_schema": {"type": "object", "properties": {"seconds": {"type": "number", "default": 1}}},
    },
    {
        "name": "schedule_task",
        "aliases": ["schedule", "set_reminder"],
        "description": "Schedule a task or reminder for a future time.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}, "when": {"type": "string"}},
            "required": ["task", "when"],
        },
    },
    {
        "name": "add_contact",
        "aliases": ["save_contact"],
        "description": "Save a contact (name/email/phone) to memory.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}, "phone": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "compress",
        "aliases": ["zip_files"],
        "description": "Compress files/folder into a zip archive.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "backup",
        "aliases": [],
        "description": "Back up agent data to cloud storage.",
        "input_schema": {"type": "object", "properties": {}},
    },

    # ── Workflow / task control (meta-tools for the loop itself) ──────────
    {
        "name": "workflow_status",
        "aliases": ["task_progress", "progress"],
        "description": "Get progress of the currently running multi-step workflow.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancel_workflow",
        "aliases": ["cancel_task", "stop_task", "abort_task"],
        "description": "Cancel the currently running workflow.",
        "input_schema": {"type": "object", "properties": {"reason": {"type": "string", "default": "user cancelled"}}},
    },
    {
        "name": "ask_ai",
        "aliases": [],
        "description": "Ask the AI a question for an informational answer only — does not perform a desktop action.",
        "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]},
    },
    {
        "name": "enterprise_automation",
        "aliases": [],
        "description": "Get step-by-step AI guidance for a business task that has no direct tool yet. Advisory only — does not execute anything on the desktop.",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
    },
    {
        "name": "unknown_task",
        "aliases": [],
        "description": "Internal fallback when no tool matches the request. Never plan this intentionally — used by the loop itself when planning fails.",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}},
    },
]

# Flat lookup: alias/name -> canonical tool dict
_TOOL_BY_NAME: Dict[str, Dict[str, Any]] = {}
for _t in TOOL_REGISTRY:
    _TOOL_BY_NAME[_t["name"]] = _t
    for _a in _t.get("aliases", []):
        _TOOL_BY_NAME[_a] = _t

# Names the planner is allowed to emit (canonical + aliases) — supersedes
# the old, much narrower EXECUTABLE_ACTIONS list in dacexy_agent.py.
ALL_TOOL_ACTION_NAMES = frozenset(_TOOL_BY_NAME.keys())

# Actions that require human approval before running (mirrors
# APPROVAL_REQUIRED in dacexy_agent.py — kept in sync manually since that
# set lives in the host module and is enforced there, not here).
SENSITIVE_TOOLS = frozenset({
    "send_email", "send_bulk_email", "approve_payment", "post_twitter",
    "post_linkedin", "post_facebook", "shell", "start_social_replies",
})


def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """Look up a tool definition by canonical name or alias."""
    return _TOOL_BY_NAME.get(str(name).lower().strip())


def is_known_action(name: str) -> bool:
    return str(name).lower().strip() in ALL_TOOL_ACTION_NAMES


def tools_as_openai_schema() -> List[Dict[str, Any]]:
    """Export the registry in OpenAI/Anthropic tool-calling format."""
    out = []
    for t in TOOL_REGISTRY:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        })
    return out


def build_tool_prompt(goal: str, max_steps: int = 8) -> str:
    """
    Build the planner prompt the LLM sees, listing every real tool with its
    schema, instead of the old bare action-name list. This is what fixes the
    planner's blind spot: it previously only knew action NAMES, never their
    PARAMETERS, so it routinely emitted malformed or guessed args.
    """
    lines = [
        "You are Dex, an autonomous desktop agent. Decompose the goal below into "
        "a JSON array of tool calls. Each item MUST be a JSON object with an "
        "'action' field set to one of the tool names listed, plus the fields "
        "from that tool's parameters. Use only the tools listed. Do not invent "
        "tools or parameters. Respond ONLY with a JSON array — no markdown, no "
        f"prose, no explanation. Max {max_steps} steps.",
        "",
        "AVAILABLE TOOLS:",
    ]
    for t in TOOL_REGISTRY:
        props = t["input_schema"].get("properties", {})
        req = t["input_schema"].get("required", [])
        arg_bits = []
        for pname, pschema in props.items():
            mark = "*" if pname in req else ""
            arg_bits.append(f"{pname}{mark}:{pschema.get('type', 'any')}")
        arg_str = ", ".join(arg_bits) if arg_bits else "(no params)"
        lines.append(f"- {t['name']}({arg_str}) — {t['description']}")
    lines.append("")
    lines.append(f"GOAL: {goal}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 2. AGENT LOOP — Think -> Plan -> Act -> Observe -> Verify
# ══════════════════════════════════════════════════════════════════════════════
# This is layered on top of dacexy_agent's existing engine. We don't
# re-implement execution, verification, or recovery — we call the host
# module's already-working functions and add an explicit, visible loop
# structure plus pause/resume control around them.

_host = None  # bound to dacexy_agent module via bind()

_pause_event = threading.Event()  # set() == PAUSED
_resume_event = threading.Event()
_resume_event.set()  # not paused by default

_loop_lock = threading.RLock()
_current_loop_state: Dict[str, Any] = {}


def bind(host) -> None:
    """
    Wire this module to the running dacexy_agent module so agent_loop() can
    call its existing functions (decompose_goal_to_graph, exec_cmd,
    is_verified_step, recover_step, replan_after_failure, speak,
    update_runtime_state, _save_workflow_state, finalize_cmd_result,
    make_execution_result, ask_ai_brain, audit, log, _abort_flag, ...).

    Call once, near the bottom of dacexy_agent.py:
        import dex_tools
        dex_tools.bind(sys.modules[__name__])
    """
    global _host
    _host = host


def pause_loop() -> None:
    """Pause the agent loop before its next step. Current step finishes first."""
    _pause_event.set()
    _resume_event.clear()
    if _host:
        try:
            _host.speak("Pausing after this step.")
        except Exception:
            pass


def resume_loop() -> None:
    """Resume a paused agent loop."""
    _pause_event.clear()
    _resume_event.set()
    if _host:
        try:
            _host.speak("Resuming.")
        except Exception:
            pass


def is_paused() -> bool:
    return _pause_event.is_set()


def loop_state() -> dict:
    with _loop_lock:
        return dict(_current_loop_state)


def _wait_if_paused() -> bool:
    """Block here while paused. Returns False if aborted while waiting."""
    if not _pause_event.is_set():
        return True
    while _pause_event.is_set():
        if _host and getattr(_host, "_abort_flag", None) is not None and _host._abort_flag.is_set():
            return False
        time.sleep(0.25)
    return True


def _think(goal: str, step_num: int, total: int, step: dict, history: List[str]) -> str:
    """
    THINK: produce a one-line natural-language rationale for the upcoming
    step, using the existing AI brain. Falls back to a templated line if the
    brain call fails — the loop must never block on this.
    """
    action = step.get("action", "?")
    params = step.get("params") or {}
    if not _host:
        return f"Step {step_num}/{total}: about to run '{action}'."
    try:
        ctx = " | ".join(history[-3:])
        prompt = (
            f"In one short sentence, explain why running the tool '{action}' "
            f"with args {json.dumps(params)[:200]} is the right next step toward "
            f"the goal: '{goal}'. Prior steps: {ctx or 'none yet'}. "
            f"Reply with the sentence only, no preamble."
        )
        thought = _host.ask_ai_brain(prompt, mem_ctx=False)
        thought = (thought or "").strip().split("\n")[0][:200]
        return thought or f"Running '{action}' to progress the goal."
    except Exception:
        return f"Step {step_num}/{total}: about to run '{action}'."


def _observe(step_result: dict) -> str:
    """OBSERVE: turn a raw exec_cmd/finalize_cmd_result dict into a short readable line."""
    if not isinstance(step_result, dict):
        return str(step_result)[:200]
    bits = []
    msg = step_result.get("result") or step_result.get("message") or step_result.get("response") or ""
    if msg:
        bits.append(str(msg)[:160])
    bits.append(f"verified={step_result.get('verified')}")
    if not step_result.get("verified"):
        fr = step_result.get("failure_reason")
        if fr:
            bits.append(f"reason={str(fr)[:120]}")
    return " | ".join(bits)


def _run_one_step(h, goal: str, step: dict, step_num: int, total: int,
                   token: str, history_ref: List[str], emit) -> dict:
    """
    Run THINK -> ACT -> OBSERVE -> VERIFY (with retry/recovery) for a single
    step. Shared by both the sequential path and the parallel-batch path so
    behavior is identical either way — parallelism only changes WHEN steps
    run relative to each other, never HOW an individual step is executed,
    verified, or recovered.
    """
    action = step.get("action", "?")
    params = step.get("params") or {}
    cmd = {"action": action, **params}

    thought = _think(goal, step_num, total, step, history_ref)
    emit({"phase": "think", "step": step_num, "total": total, "action": action, "thought": thought})
    h.log.info("THINK[%s/%s] %s -> %s", step_num, total, action, thought[:160])
    emit({"phase": "plan", "step": step_num, "total": total, "action": action, "params": params})

    max_attempts = int(step.get("max_attempts") or 3)
    step_result = None
    verified = False
    for attempt in range(1, max_attempts + 1):
        if h._abort_flag.is_set() or not _wait_if_paused():
            break
        step["attempts"] = attempt
        if attempt == 1:
            emit({"phase": "act", "step": step_num, "total": total, "action": action, "attempt": attempt})
            step_result = h.finalize_cmd_result(action, h.exec_cmd(cmd, token))
        else:
            emit({"phase": "act_retry", "step": step_num, "total": total, "action": action, "attempt": attempt})
            step_result = h.recover_step(step, step_result or {}, token, attempt - 1)

        observation = _observe(step_result)
        emit({"phase": "observe", "step": step_num, "total": total, "action": action,
              "attempt": attempt, "observation": observation})

        verified = h.is_verified_step(step_result)
        emit({"phase": "verify", "step": step_num, "total": total, "action": action,
              "attempt": attempt, "verified": verified})
        if verified:
            break
        time.sleep(0.3 + attempt * 0.2)

    step["result"] = step_result
    step["verified"] = verified
    step["status"] = "completed" if verified else "failed"
    return {
        "step": step_num, "action": action, "params": params,
        "thought": thought, "result": step_result, "verified": verified,
    }


def _batch_independent_steps(steps: List[dict]) -> List[List[dict]]:
    """
    Group consecutive steps into batches that can run concurrently.

    A run of consecutive steps all belongs to one batch if every one of
    them uses a PARALLEL_SAFE_ACTIONS action — i.e. none of them touch the
    shared mouse/keyboard/active-window. As soon as a step uses a GUI/desktop
    action, it starts a new batch by itself and breaks the run, since it (and
    anything after it that might depend on screen state) must run alone and
    in order. This is conservative on purpose: when in doubt, steps run
    sequentially exactly like before.
    """
    batches: List[List[dict]] = []
    current: List[dict] = []
    for step in steps:
        action = str(step.get("action", "")).lower().strip()
        if action in PARALLEL_SAFE_ACTIONS:
            current.append(step)
        else:
            if current:
                batches.append(current)
                current = []
            batches.append([step])
    if current:
        batches.append(current)
    return batches


def agent_loop(
    goal: str,
    token: str,
    max_steps: int = 12,
    on_step=None,
) -> dict:
    """
    Explicit Think -> Plan -> Act -> Observe -> Verify loop.

    - PLAN comes from host.decompose_goal_to_graph(goal), which already does
      local_parse-first / AI-planner-fallback decomposition.
    - ACT/OBSERVE/VERIFY reuse host.exec_cmd, host.finalize_cmd_result,
      host.is_verified_step, host.recover_step, host.replan_after_failure —
      the same retry + recovery + replanning engine execute_planned_workflow
      already uses.
    - SPEED: consecutive steps that are all "parallel-safe" (no shared
      mouse/keyboard/active-window — e.g. several research/file/email/report
      steps in a row) run concurrently on a thread pool instead of queuing
      one after another. Any step that touches the GUI (click/type/open/etc)
      always runs alone, in order, exactly as before — this is what makes a
      business task like "research X, research Y, draft an invoice, and
      email me a summary" finish in roughly the time of its slowest single
      step instead of the sum of all of them, without ever risking two
      threads fighting over the same mouse.

    on_step(event: dict) is called after every think/act/observe/verify
    phase if provided — useful for streaming progress to a UI or WebSocket.
    Note: when steps run in a parallel batch, events from different steps
    may interleave; each event always carries its own "step" number so a
    consumer can still separate them correctly.
    """
    if _host is None:
        raise RuntimeError("dex_tools.bind(host) must be called before agent_loop().")

    h = _host
    h._abort_flag.clear()

    def _emit(event: dict):
        if on_step:
            try:
                on_step(event)
            except Exception:
                pass

    graph = h.decompose_goal_to_graph(goal)
    steps = graph.get("steps", [])[:max_steps]
    if not steps:
        unknown = h.exec_cmd({"action": "unknown_task", "task": goal}, token)
        return {"status": "error", "ok": 0, "total": 0, "verified": False,
                "result": unknown.get("failure_reason", "no steps"), "trace": [unknown]}

    with _loop_lock:
        _current_loop_state.clear()
        _current_loop_state.update({
            "goal": goal, "total": len(steps), "done": 0,
            "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "running",
        })

    total = len(steps)
    batches = _batch_independent_steps(steps)
    n_parallel_batches = sum(1 for b in batches if len(b) > 1)
    if n_parallel_batches:
        h.speak(f"Starting agent loop: {total} steps for '{goal[:60]}'. Running {n_parallel_batches} batch(es) in parallel.")
    else:
        h.speak(f"Starting agent loop: {total} steps for '{goal[:60]}'.")

    history: List[str] = []
    trace_by_num: Dict[int, dict] = {}
    ok_count = 0
    step_num_lookup = {id(s): i + 1 for i, s in enumerate(steps)}

    for batch in batches:
        if h._abort_flag.is_set():
            break
        if not _wait_if_paused():
            break

        if len(batch) == 1:
            step = batch[0]
            step_num = step_num_lookup[id(step)]
            result = _run_one_step(h, goal, step, step_num, total, token, history, _emit)
            trace_by_num[step_num] = result
            history.append(f"{result['action']} -> {'ok' if result['verified'] else 'failed'}: {_observe(result['result'])[:100]}")
            if result["verified"]:
                ok_count += 1
            elif not h._abort_flag.is_set():
                h.replan_after_failure(graph, {**step, "failure_reason": (result['result'] or {}).get("failure_reason", "failed")}, token)
            with _loop_lock:
                _current_loop_state["done"] = len(trace_by_num)
                _current_loop_state["last_action"] = result["action"]
                _current_loop_state["last_verified"] = result["verified"]
            h.update_runtime_state(
                last_action=f"agent_loop_step_{step_num}",
                last_result=_observe(result["result"])[:200],
                last_verified=result["verified"],
            )
        else:
            # Parallel-safe batch — run concurrently, same per-step logic.
            local_history = list(history)  # snapshot; parallel steps don't see each other's mid-batch results
            with ThreadPoolExecutor(max_workers=min(8, len(batch)), thread_name_prefix="agent_loop") as pool:
                futures = {}
                for step in batch:
                    step_num = step_num_lookup[id(step)]
                    fut = pool.submit(_run_one_step, h, goal, step, step_num, total, token, local_history, _emit)
                    futures[fut] = (step, step_num)
                for fut in as_completed(futures):
                    step, step_num = futures[fut]
                    try:
                        result = fut.result()
                    except Exception as e:
                        result = {
                            "step": step_num, "action": step.get("action", "?"), "params": step.get("params") or {},
                            "thought": "", "result": {"status": "error", "verified": False, "failure_reason": str(e)},
                            "verified": False,
                        }
                    trace_by_num[step_num] = result
                    history.append(f"{result['action']} -> {'ok' if result['verified'] else 'failed'}: {_observe(result['result'])[:100]}")
                    if result["verified"]:
                        ok_count += 1
                    elif not h._abort_flag.is_set():
                        h.replan_after_failure(graph, {**step, "failure_reason": (result['result'] or {}).get("failure_reason", "failed")}, token)
                    with _loop_lock:
                        _current_loop_state["done"] = len(trace_by_num)
                        _current_loop_state["last_action"] = result["action"]
                        _current_loop_state["last_verified"] = result["verified"]
                    h.update_runtime_state(
                        last_action=f"agent_loop_step_{step_num}",
                        last_result=_observe(result["result"])[:200],
                        last_verified=result["verified"],
                    )

    trace = [trace_by_num[n] for n in sorted(trace_by_num.keys())]
    verified_all = ok_count == total and total > 0
    status = "cancelled" if h._abort_flag.is_set() else ("ok" if verified_all else "partial")
    summary = f"Agent loop {'completed' if verified_all else status}: {ok_count}/{total} — {goal[:60]}"

    with _loop_lock:
        _current_loop_state["status"] = status
        _current_loop_state["summary"] = summary

    if status == "ok":
        h.speak(h.jarvis_done())
    elif status == "cancelled":
        h.speak("Agent loop cancelled.")
    elif ok_count > 0:
        h.speak(f"Completed {ok_count} of {total} steps. Some steps could not be verified.")
    else:
        h.speak("The agent loop could not complete the goal.")

    return {
        "status": "ok" if verified_all else ("cancelled" if status == "cancelled" else "error"),
        "ok": ok_count, "total": total, "verified": verified_all,
        "result": summary, "trace": trace, "workflow": graph,
    }
