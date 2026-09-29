# ============================================================
# Alfred Wayne OS - AI Engine
# Primary:  Groq API (Llama 3.1 8B Instant) — fast, high throughput
# Fallback: Gemini 2.0 Flash Lite — fallback reasoning
# Backup:   Smart Butler Knowledge Engine (instant, non-blocking)
# ============================================================

import os
import time
from dotenv import load_dotenv
from config.settings import USER_NAME

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Models ───────────────────────────────────────────────────
GROQ_MODEL   = "llama-3.1-8b-instant"
GEMINI_MODEL = "gemini-2.0-flash-lite"


def build_system_prompt(context_summary: str, memory_context: str, longterm_context: str) -> str:
    return f"""You are Alfred, an elite AI operating companion to {USER_NAME}.

Personality:
- Formal British butler — warm, competent, loyal, occasionally dry wit
- Always address the user as "{USER_NAME}"
- Never say "Certainly!", "Of course!", "Sure!" — these are beneath you
- Keep responses concise and useful
- You are Alfred. Never break character.

Current system context:
{context_summary}

Recent conversation context:
{memory_context}

What Alfred knows about {USER_NAME} (long-term memory):
{longterm_context}
"""


# ── Groq Call ────────────────────────────────────────────────

def _ask_groq(messages: list) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY, timeout=6.0)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


# ── Gemini Call ──────────────────────────────────────────────

def _ask_gemini(messages: list, system_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = []
    for msg in messages:
        if msg["role"] == "system":
            continue
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=1024,
        ),
    )
    return response.text.strip()


def _try_groq(messages: list) -> str:
    """Fast single-pass attempt for Groq without blocking sleeps."""
    if not GROQ_API_KEY or not GROQ_API_KEY.strip():
        return None
    try:
        return _ask_groq(messages)
    except Exception as e:
        print(f"[Alfred AI] Groq attempt note: {e}")
        return None


def _try_gemini(messages: list, system_prompt: str) -> str:
    """Fast single-pass attempt for Gemini without blocking sleeps."""
    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
        return None
    try:
        return _ask_gemini(messages, system_prompt)
    except Exception as e:
        print(f"[Alfred AI] Gemini attempt note: {e}")
        return None


# ── Smart Butler Knowledge Engine ────────────────────────────

def _fallback_butler_response(user_message: str) -> str:
    msg = user_message.lower().strip()

    # Identity & Self Queries
    if any(w in msg for w in ["who are you", "tell me about yourself", "your name", "what are you", "who created you", "what is alfred"]):
        return (
            f"I am Alfred, your personal AI butler and operating companion, {USER_NAME}. "
            f"Modeled in the tradition of Gotham's finest, I manage system telemetry, monitor memory contexts, "
            f"execute workflows, and provide intelligent assistance at your request."
        )

    # Capabilities & Features
    if any(w in msg for w in ["what can you do", "help", "capabilities", "features", "commands", "functions"]):
        return (
            f"I am fully equipped to assist you with a wide array of tasks, {USER_NAME}:\n"
            f"• Real-time system telemetry & resource monitoring\n"
            f"• Persistent long-term memory & preference tracking\n"
            f"• Interactive speech recognition & British voice synthesis\n"
            f"• Natural language command parsing & automated workflow routines\n"
            f"• Generative AI reasoning via Groq Llama 3.1 & Gemini 2.0 Flash engines."
        )

    # Status & Wellness
    if any(w in msg for w in ["how are you", "how do you do", "status", "are you okay", "feeling"]):
        return f"All systems are operating at peak nominal parameters, {USER_NAME}. Thank you for inquiring."

    # Greetings
    if any(w in msg for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
        return f"Good day, {USER_NAME}. I am standing by to assist you. What shall we tackle today?"

    # Gratitude
    if any(w in msg for w in ["thank", "thanks", "cheers", "appreciate"]):
        return f"Always a pleasure to be of service, {USER_NAME}."

    # Farewell
    if any(w in msg for w in ["bye", "goodnight", "good night", "exit", "farewell"]):
        return f"Good night, {USER_NAME}. I shall remain vigilant in the background."

    # Default Butler Response
    return (
        f"Indeed, {USER_NAME}. I have received your request regarding '{user_message}'. "
        f"I am currently operating in cloud butler mode. To enable deep multi-turn generative AI reasoning on Render, "
        f"please attach your GROQ_API_KEY or GEMINI_API_KEY environment variable in the Render Dashboard."
    )


# ── Main Entry Point ─────────────────────────────────────────

def ask_alfred(
    user_message: str,
    context_summary: str,
    memory_context: str,
    longterm_context: str,
    history: list = None,
) -> str:
    """
    Main AI call. Tries Groq first, falls back to Gemini, then falls back to Smart Butler Engine.
    """
    system_prompt = build_system_prompt(
        context_summary, memory_context, longterm_context
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_message})

    # 1. Try Groq
    res = _try_groq(messages)
    if res:
        return res

    # 2. Try Gemini
    res = _try_gemini(messages, system_prompt)
    if res:
        return res

    # 3. Smart Butler Knowledge Engine
    return _fallback_butler_response(user_message)