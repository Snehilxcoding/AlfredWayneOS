# ============================================================
# Alfred Wayne OS - AI Engine
# Primary:  Groq API (Llama 3.3 70B) — free, fast, generous
# Fallback: Gemini 2.0 Flash — if Groq fails
# Updated:  google.generativeai → google.genai (new SDK)
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


# ── Groq call ────────────────────────────────────────────────

def _ask_groq(messages: list) -> str:
    from groq import Groq
    client   = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


# ── Gemini call ──────────────────────────────────────────────

def _ask_gemini(messages: list, system_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build conversation contents (exclude system message)
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            continue
        # Gemini uses "model" instead of "assistant"
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


# ── Retry wrappers ───────────────────────────────────────────

def _try_groq(messages: list, max_retries: int = 3) -> str:
    """Attempts Groq with retries. Returns text or None."""
    if not GROQ_API_KEY:
        return None

    wait_times = [5, 10, 20]

    for attempt in range(max_retries):
        try:
            return _ask_groq(messages)

        except Exception as e:
            err = str(e).lower()

            if "429" in err or "rate" in err or "quota" in err:
                if attempt < max_retries - 1:
                    wait = wait_times[attempt]
                    print(f"[Alfred] Groq rate limit. Waiting {wait}s "
                          f"(attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                return None

            if "401" in err or "invalid" in err or "api_key" in err:
                print(f"[Alfred] Groq auth error: {e}")
                return None

            print(f"[Alfred] Groq error: {e}")
            return None

    return None


def _try_gemini(messages: list, system_prompt: str, max_retries: int = 3) -> str:
    """Attempts Gemini with retries. Returns text or None."""
    if not GEMINI_API_KEY:
        return None

    wait_times = [10, 20, 30]

    for attempt in range(max_retries):
        try:
            return _ask_gemini(messages, system_prompt)

        except Exception as e:
            err = str(e).lower()

            if "429" in err or "quota" in err or "exhausted" in err:
                if attempt < max_retries - 1:
                    wait = wait_times[attempt]
                    print(f"[Alfred] Gemini quota hit. Waiting {wait}s "
                          f"(attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                return None

            if "api_key" in err or "authentication" in err:
                print(f"[Alfred] Gemini auth error: {e}")
                return None

            print(f"[Alfred] Gemini error: {e}")
            return None

    return None


def _fallback_butler_response(user_message: str) -> str:
    msg = user_message.lower().strip()
    if any(w in msg for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
        return f"Good day, {USER_NAME}. I am standing by to assist you."
    if any(w in msg for w in ["who are you", "your name", "what are you"]):
        return f"I am Alfred, your personal AI butler and operating companion, {USER_NAME}."
    if any(w in msg for w in ["what can you do", "help", "capabilities", "features"]):
        return f"I am equipped to manage system telemetry, monitor memory contexts, execute automated routines, and process complex AI queries, {USER_NAME}."
    if any(w in msg for w in ["how are you", "how do you do"]):
        return f"All systems are functioning nominally, {USER_NAME}. Thank you for asking."
    return f"At your service, {USER_NAME}. I am operating in cloud interface mode. To enable full generative AI reasoning on Render, please attach your GROQ_API_KEY or GEMINI_API_KEY environment variable in the Render Dashboard."


# ── Main entry point ─────────────────────────────────────────

def ask_alfred(
    user_message: str,
    context_summary: str,
    memory_context: str,
    longterm_context: str,
    history: list = None,
) -> str:
    """
    Main AI call. Tries Groq first, falls back to Gemini.
    Both have automatic retry with backoff.
    """
    system_prompt = build_system_prompt(
        context_summary, memory_context, longterm_context
    )

    # Build message list
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_message})

    # ── Try Groq first ───────────────────────────────────────
    if GROQ_API_KEY:
        result = _try_groq(messages)
        if result:
            return result
        print("[Alfred] Groq unavailable. Switching to Gemini...")

    # ── Fall back to Gemini ──────────────────────────────────
    if GEMINI_API_KEY:
        result = _try_gemini(messages, system_prompt)
        if result:
            return result

    # ── Fallback Butler Response ──────────────────────────────
    return _fallback_butler_response(user_message)