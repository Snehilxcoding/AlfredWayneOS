# ============================================================
# Alfred Wayne OS - Command Parser
# Phase B: Added coding assistant intents.
# ============================================================

import re


class Intent:
    OPEN_APP     = "open_app"
    OPEN_WEBSITE = "open_website"
    SEARCH_WEB   = "search_web"
    CREATE_FILE  = "create_file"
    TIME_QUERY   = "time_query"
    SYSTEM_INFO  = "system_info"
    FAREWELL     = "farewell"
    GRATITUDE    = "gratitude"
    # Phase B — coding intents
    RUN_COMMAND  = "run_command"
    READ_FILE    = "read_file"
    SHOW_STRUCTURE = "show_structure"
    AI_QUERY     = "ai_query"
    

def _contains(text: str, keyword: str) -> bool:
    """Whole-word match — prevents 'ram' firing inside 'programming'."""
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def parse_command(text: str) -> dict:
    t      = text.lower().strip()
    result = {"intent": Intent.AI_QUERY, "target": None, "raw": text}

    # ── Farewell ─────────────────────────────────────────────
    farewell_keywords = [
        "goodbye", "good night", "goodnight",
        "farewell", "exit", "close alfred", "quit"
    ]
    if any(_contains(t, k) for k in farewell_keywords):
        result["intent"] = Intent.FAREWELL
        return result

    # ── Gratitude ────────────────────────────────────────────
    gratitude_keywords = [
        "thank you", "thanks", "cheers",
        "well done", "good job"
    ]
    if any(_contains(t, k) for k in gratitude_keywords):
        result["intent"] = Intent.GRATITUDE
        return result

    # ── Time / Date ──────────────────────────────────────────
    time_keywords = [
        "what time", "what's the time", "what day",
        "what date", "today's date", "what year"
    ]
    if any(k in t for k in time_keywords):
        result["intent"] = Intent.TIME_QUERY
        return result

    # ── System Info ──────────────────────────────────────────
    system_multiword  = ["memory usage", "system info", "computer status"]
    system_singleword = ["battery", "ram", "cpu", "uptime"]
    internet_phrases  = [
        "am i online", "are we online", "internet status",
        "check internet", "internet connection", "are we connected"
    ]
    if (
        any(k in t for k in system_multiword)
        or any(_contains(t, k) for k in system_singleword)
        or any(k in t for k in internet_phrases)
    ):
        result["intent"] = Intent.SYSTEM_INFO
        return result

    # ── Phase B: Run terminal command ────────────────────────
    run_patterns = [
        r"^run (.+)",
        r"^execute (.+)",
        r"^terminal (.+)",
        r"^run command (.+)",
        r"^run this[:\s]+(.+)",
    ]
    for pat in run_patterns:
        m = re.search(pat, t)
        if m:
            result["intent"] = Intent.RUN_COMMAND
            result["target"] = m.group(1).strip()
            return result

    # ── Phase B: Read a file ─────────────────────────────────
    read_patterns = [
        r"^read (?:the )?file (.+)",
        r"^open (?:the )?file (.+)",
        r"^show (?:me )?(?:the )?(?:contents of )?(?:file )?(.+\.\w+)",
        r"^look at (.+\.\w+)",
    ]
    for pat in read_patterns:
        m = re.search(pat, t)
        if m:
            result["intent"] = Intent.READ_FILE
            result["target"] = m.group(1).strip()
            return result

    # ── Phase B: Show project structure ──────────────────────
    structure_keywords = [
        "project structure", "folder structure", "file structure",
        "show structure", "show files", "what files",
        "list files", "directory structure"
    ]
    if any(k in t for k in structure_keywords):
        result["intent"] = Intent.SHOW_STRUCTURE
        return result
    
    # ── Recalibrate microphone ────────────────────────────────
    if any(k in t for k in ["recalibrate", "calibrate mic", "calibrate microphone", "fix microphone"]):
        result["intent"] = "recalibrate_mic"
        return result

    # ── Open Application ─────────────────────────────────────
    open_app_patterns = [
        r"^open (?:the )?(.+?)(?:\s+app)?$",
        r"^launch (.+?)(?:\s+app)?$",
        r"^start (.+?)$",
    ]
    for pat in open_app_patterns:
        m = re.search(pat, t)
        if m:
            target = m.group(1).strip()
            if "." not in target and "http" not in target:
                result["intent"] = Intent.OPEN_APP
                result["target"] = target
                return result

    # ── Open Website ─────────────────────────────────────────
    open_site_patterns = [
        r"^go to (.+)",
        r"^navigate to (.+)",
        r"^open (.+\.(?:com|org|net|io|co|uk))",
    ]
    for pat in open_site_patterns:
        m = re.search(pat, t)
        if m:
            result["intent"] = Intent.OPEN_WEBSITE
            result["target"] = m.group(1).strip()
            return result

    # ── Web Search ───────────────────────────────────────────
    search_patterns = [
        r"^search (?:for )?(.+)",
        r"^google (.+)",
        r"^look up (.+)",
    ]
    for pat in search_patterns:
        m = re.search(pat, t)
        if m:
            result["intent"] = Intent.SEARCH_WEB
            result["target"] = m.group(1).strip()
            return result

    # ── Create File ──────────────────────────────────────────
    create_patterns = [
        r"^create (?:a )?(?:new )?(?:text )?file (?:called |named )?(.+)",
        r"^new file (.+)",
        r"^make (?:a )?(?:new )?file (?:called |named )?(.+)",
    ]
    for pat in create_patterns:
        m = re.search(pat, t)
        if m:
            result["intent"] = Intent.CREATE_FILE
            result["target"] = m.group(1).strip()
            return result

    # ── Default: send to Gemini/Groq ─────────────────────────
    return result