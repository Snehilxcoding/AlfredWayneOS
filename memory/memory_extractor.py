# ============================================================
# Alfred Wayne OS - Memory Extractor
# Uses Groq as primary, Gemini as fallback.
# ============================================================

import os
import json
from dotenv import load_dotenv
from memory.memory_manager import load_memory, save_memory, _now

load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
- "key": a short snake_case identifier
- "value": the fact as a clear short string

Example output:
[
  {"category": "preferences", "key": "favorite_language", "value": "Python"}
]

If nothing to extract:
[]
"""


def _extract_via_groq(prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def _extract_via_gemini(prompt: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=512,
        ),
    )
    return response.text.strip()


def _parse_facts(raw: str) -> list:
    if not raw or not raw.strip():
        return []

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

    if not raw.startswith("["):
        return []

    if not raw.endswith("]"):
        idx = raw.rfind("]")
        if idx == -1:
            return []
        raw = raw[:idx + 1]

    try:
        facts = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []

    if not isinstance(facts, list):
        return []

    valid = []
    allowed = {"personal", "preferences", "goals", "projects"}
    for f in facts:
        if not isinstance(f, dict):
            continue
        if "category" not in f or "key" not in f or "value" not in f:
            continue
        if f["category"] not in allowed:
            continue
        if not isinstance(f["key"], str) or not isinstance(f["value"], str):
            continue
        if not f["key"].strip() or not f["value"].strip():
            continue
        valid.append(f)

    return valid


def extract_facts(user_message: str, alfred_reply: str) -> list:
    trivial = [
        "open ", "go to ", "search for ", "what time", "what day",
        "goodbye", "thank", "thanks", "yes", "no", "ok", "okay",
        "alright", "sure",
    ]
    msg_lower = user_message.lower().strip()
    if any(msg_lower.startswith(t) for t in trivial):
        return []
    if len(user_message.strip()) < 10:
        return []

    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        alfred_reply=alfred_reply,
    )

    if GROQ_API_KEY:
        try:
            raw   = _extract_via_groq(prompt)
            facts = _parse_facts(raw)
            return facts
        except (json.JSONDecodeError, ValueError):
            pass
        except Exception as e:
            err = str(e).lower()
            if "429" not in err and "rate" not in err and "quota" not in err:
                print(f"[Memory] Groq extraction error: {e}")

    if GEMINI_API_KEY:
        try:
            raw   = _extract_via_gemini(prompt)
            facts = _parse_facts(raw)
            return facts
        except (json.JSONDecodeError, ValueError):
            return []
        except Exception as e:
            err = str(e).lower()
            if "429" not in err and "quota" not in err:
                print(f"[Memory] Gemini extraction error: {e}")
            return []

    return []


def store_facts(facts: list) -> int:
    if not facts:
        return 0

    memory = load_memory()

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


def extract_and_store(user_message: str, alfred_reply: str) -> int:
    facts = extract_facts(user_message, alfred_reply)
    return store_facts(facts)