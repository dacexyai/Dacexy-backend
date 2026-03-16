from __future__ import annotations
import logging
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider

log = logging.getLogger("website")

SYSTEM_PROMPT = """You are an expert web developer. Generate complete, beautiful, 
production-ready single-page HTML websites. 
Always return ONLY valid HTML with embedded CSS and JavaScript.
Make it visually stunning, mobile-responsive, and modern.
Do not include any explanation — only the HTML code."""


async def generate_website(prompt: str, ai: DeepSeekProvider) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Build a website for: {prompt}\n\nReturn only the complete HTML file."}
    ]
    try:
        html = await ai.chat(messages, model="deepseek-chat", stream=False)
        # Strip markdown code blocks if present
        if "```html" in html:
            html = html.split("```html")[1].split("```")[0].strip()
        elif "```" in html:
            html = html.split("```")[1].split("```")[0].strip()
        return html
    except Exception as e:
        log.error("Website generation failed: %s", e)
        raise
