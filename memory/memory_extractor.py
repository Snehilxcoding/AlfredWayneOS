# ============================================================
# Alfred Wayne OS - Memory Extractor
# Updated: google.generativeai → google.genai (new SDK)
# Uses Groq as primary extractor, Gemini as fallback.
# ============================================================

import os
import json
from dotenv import load_dotenv
from memory.memory_manager import load_memory, save_memory, _now

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ── Extraction prompt ────────────────────────────────────────
EXTRACTION_PROMPT = """You are a memory extraction system for an AI assistant.

Analyze this conversation turn and extract any facts about the user.

User said: "{user_message}"
Assistant replied: "{alfred_reply}"

Extract ONLY concrete facts about the user — things Alfred should remember long-term.
Examples of facts worth extracting:
- Name, age, location, occupation
- Preferences (likes, dislikes, habits)
- Goals and ambitions
- Active projects they are working on
- Personal details they mentioned

Do NOT extract:
- Questions the user asked
- General knowledge statements
- Things Alfred said
- Temporary commands like "open YouTube"

If there are no facts worth storing, return an empty list.

Respond ONLY with a valid JSON array. No explanation. No markdown. No extra text.
Each item must have exactly these fields:
- "category": one of "personal", "preferences", "goals", "projects"
- "key": a short snake_case identifier (e.g. "favorite_language", "current_project")
- "value": the fact as a clear short string

Example output:
[
  {"category": "preferences", "key": "favorite_language", "value": "Python"},
  {"category": "projects", "key": "alfred_os", "value": "Building an AI operating companion called Alfred Wayne OS"}
]

If nothing to extract:
[]
"""


# ── Groq extraction ──────────────────────────────────────────

def _extract_via_groq(prompt: str) -> str:
    """Calls Groq and returns raw text response."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,    # Low temperature for consistent JSON output
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ── Gemini extraction ────────────────────────────────────────

def _extract_via_gemini(prompt: str) -> str:
    """Calls Gemini and returns raw text response."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=512,
        ),
    )
    return response.text.strip()


# ── JSON parser ──────────────────────────────────────────────

def _parse_facts(raw: str) -> list:
    """
    Parses raw LLM response into a validated list of facts.
    Handles markdown fences and malformed output gracefully.
    """
    if not raw or not raw.strip():
        return []

    # Strip markdown fences if present
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:]
            part = part.strip()
            if part.startswith("["):
                raw = part
                break

    raw = raw.strip()

    # Must start with [ to be a valid array
    if not raw.startswith("["):
        return []

    # Must end with ]
    if not raw.endswith("]"):
        # Try to find the last ] and truncate
        idx = raw.rfind("]")
        if idx == -1:
            return []
        raw = raw[:idx + 1]

    try:
        facts = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(facts, list):
        return []

    # Validate each fact
    valid = []
    allowed_categories = {"personal", "preferences", "goals", "projects"}
    for f in facts:
        if not isinstance(f, dict):
            continue
        if "category" not in f or "key" not in f or "value" not in f:
            continue
        if f["category"] not in allowed_categories:
            continue
        if not isinstance(f["key"], str) or not isinstance(f["value"], str):
            continue
        if not f["key"].strip() or not f["value"].strip():
            continue
        valid.append(f)

    return valid

# ── Main extraction ──────────────────────────────────────────

def extract_facts(user_message: str, alfred_reply: str) -> list:
    """
    Extracts facts from a conversation turn.
    Tries Groq first, falls back to Gemini.
    Returns a validated list of fact dicts, or [] if nothing found.
    """
    # Skip trivial inputs — not worth an API call
    trivial_starts = [
        "open ", "go to ", "search for ", "what time",
        "what day", "goodbye", "thank", "thanks",
        "yes", "no", "ok", "okay", "alright", "sure",
    ]
    msg_lower = user_message.lower().strip()
    if any(msg_lower.startswith(t) for t in trivial_starts):
        return []

    # Skip very short messages
    if len(user_message.strip()) < 10:
        return []

    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        alfred_reply=alfred_reply,
    )

    # ── Try Groq first ───────────────────────────────────────
    if GROQ_API_KEY:
        try:
            raw   = _extract_via_groq(prompt)
            facts = _parse_facts(raw)
            return facts
        except json.JSONDecodeError:
            pass
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate" in err or "quota" in err:
                pass   # Fall through to Gemini
            else:
                print(f"[Memory] Groq extraction error: {e}")

    # ── Fall back to Gemini ──────────────────────────────────
    if GEMINI_API_KEY:
        try:
            raw   = _extract_via_gemini(prompt)
            facts = _parse_facts(raw)
            return facts
        except json.JSONDecodeError:
            return []
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "exhausted" in err:
                return []   # Silently skip — quota exhausted
            print(f"[Memory] Gemini extraction error: {e}")
            return []

    return []


# ── Storage ──────────────────────────────────────────────────

def store_facts(facts: list) -> int:
    """
    Stores extracted facts into memory.json.
    Deduplicates by category + key.
    Newer value overwrites older one.
    Returns number of new/updated facts stored.
    """
    if not facts:
        return 0

    memory = load_memory()

    # Ensure long_term structure exists
    if "long_term" not in memory:
        memory["long_term"] = {
            "personal":    {},
            "preferences": {},
            "goals":       {},
            "projects":    {},
        }

    stored = 0
    for fact in facts:
        category = fact["category"]
        key      = fact["key"]
        value    = fact["value"]

        existing = memory["long_term"][category].get(key)
        if existing is None or existing["value"] != value:
            memory["long_term"][category][key] = {
                "value":   value,
                "updated": _now(),
            }
            stored += 1
            print(f"[Memory] Stored: [{category}] {key} = {value}")

    if stored > 0:
        save_memory(memory)

    return stored


# ── Entry point ──────────────────────────────────────────────

def extract_and_store(user_message: str, alfred_reply: str) -> int:
    """
    Main entry point. Call this after every AI conversation turn.
    Extracts facts and stores them. Returns count of stored facts.
    """
    facts = extract_facts(user_message, alfred_reply)
    return store_facts(facts)