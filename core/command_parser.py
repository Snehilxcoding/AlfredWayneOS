# ============================================================
# Alfred Wayne OS - Command Parser
# Fixed: routine check now happens before terminal command check
# so "run morning" triggers routine, not terminal.
# ============================================================

import re


class Intent:
    OPEN_APP       = "open_app"
    OPEN_WEBSITE   = "open_website"
    SEARCH_WEB     = "search_web"
    CREATE_FILE    = "create_file"
    TIME_QUERY     = "time_query"
    SYSTEM_INFO    = "system_info"
    FAREWELL       = "farewell"
    GRATITUDE      = "gratitude"
    RUN_COMMAND    = "run_command"
    READ_FILE      = "read_file"
    SHOW_STRUCTURE = "show_structure"
    RUN_ROUTINE    = "run_routine"
    SAVE_ROUTINE   = "save_routine"
    LIST_ROUTINES  = "list_routines"
    AI_QUERY       = "ai_query"


def _contains(text: str, keyword: str) -> bool:
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def _extract(pattern: str, text: str):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def parse_command(text: str) -> dict:
    # Strip trailing punctuation Whisper adds
    t      = re.sub(r'[.!?,;]+$', '', text.lower().strip())
    result = {"intent": Intent.AI_QUERY, "target": None, "raw": text}

    # ── Farewell ─────────────────────────────────────────────
    if any(_contains(t, k) for k in [
        "goodbye", "good night", "goodnight",
        "farewell", "exit", "close alfred", "quit"
    ]):
        result["intent"] = Intent.FAREWELL
        return result

    # ── Gratitude ────────────────────────────────────────────
    if any(_contains(t, k) for k in [
        "thank you", "thanks", "cheers", "well done", "good job"
    ]):
        result["intent"] = Intent.GRATITUDE
        return result

    # ── Time / Date ──────────────────────────────────────────
    if any(k in t for k in [
        "what time", "what's the time", "what is the time", "tell me the time",
        "time right now", "current time", "what day", "what date", "today's date",
        "what year", "current date", "time is it"
    ]) or t.strip() in ["time", "date", "clock"]:
        result["intent"] = Intent.TIME_QUERY
        return result

    # ── System Info ──────────────────────────────────────────
    if (
        any(k in t for k in ["memory usage", "system info", "computer status", "system status", "status report"])
        or any(_contains(t, k) for k in ["battery", "ram", "cpu", "uptime", "telemetry"])
        or any(k in t for k in [
            "am i online", "internet status", "check internet",
            "internet connection", "are we connected"
        ])
        or t.strip() in ["status", "sysinfo", "stats"]
    ):
        result["intent"] = Intent.SYSTEM_INFO
        return result

    # ── List routines ─────────────────────────────────────────
    if any(k in t for k in [
        "list routines", "show routines", "my routines",
        "what routines", "list my routines", "show my routines"
    ]):
        result["intent"] = Intent.LIST_ROUTINES
        return result

    # ── Save routine ──────────────────────────────────────────
    save_pat = _extract(
        r"(?:save|create|make) (?:a )?routine (?:called |named )?(.+)", t
    )
    if save_pat:
        result["intent"] = Intent.SAVE_ROUTINE
        result["target"] = save_pat
        return result

    # ── Run routine (BEFORE terminal command check) ───────────
    # Check all these trigger phrases for routines
    routine_triggers = [
        r"^(?:run|start|execute|launch) (?:my )?routine (.+)",
        r"^(?:run|start) (?:the )?(.+?) routine$",
        r"^(?:run|start|launch) (.+)",   # broad — checked against saved routines
    ]
    for pat in routine_triggers:
        candidate = _extract(pat, t)
        if candidate:
            # Only treat as routine if it actually exists
            from core.workflow_engine import get_routine
            if get_routine(candidate) is not None:
                result["intent"] = Intent.RUN_ROUTINE
                result["target"] = candidate
                return result

    # ── Run terminal command ──────────────────────────────────
    for pat in [
        r"^run command (.+)",
        r"^terminal (.+)",
        r"^execute command (.+)",
    ]:
        target = _extract(pat, t)
        if target:
            result["intent"] = Intent.RUN_COMMAND
            result["target"] = target
            return result

    # ── Read file ─────────────────────────────────────────────
    for pat in [
        r"^read (?:the )?file (.+)",
        r"^show (?:me )?(?:the )?(?:contents of )?(?:file )?(.+\.\w+)",
        r"^look at (.+\.\w+)",
    ]:
        target = _extract(pat, t)
        if target:
            result["intent"] = Intent.READ_FILE
            result["target"] = target
            return result

    # ── Show project structure ────────────────────────────────
    if any(k in t for k in [
        "project structure", "folder structure", "file structure",
        "show structure", "show files", "list files", "directory structure"
    ]):
        result["intent"] = Intent.SHOW_STRUCTURE
        return result

    # ── Recalibrate mic ───────────────────────────────────────
    if any(k in t for k in [
        "recalibrate", "calibrate mic",
        "calibrate microphone", "fix microphone"
    ]):
        result["intent"] = "recalibrate_mic"
        return result

    # ── Open Website (before app) ─────────────────────────────
    for pat in [
        r"^go to (.+)",
        r"^navigate to (.+)",
        r"^open (.+\.(?:com|org|net|io|co|uk))",
        r"^take me to (.+)",
    ]:
        target = _extract(pat, t)
        if target:
            result["intent"] = Intent.OPEN_WEBSITE
            result["target"] = target
            return result

    # ── Open Application ─────────────────────────────────────
    app_patterns = [
        r"^open (?:the )?(.+?)(?:\s+app|browser|for me)?$",
        r"^launch (.+?)(?:\s+app)?$",
        r"^start (.+?)$",
        r"^can you open (?:the )?(.+?)(?:\s+(?:app|browser|for me))?$",
        r"^please open (?:the )?(.+?)(?:\s+app)?$",
        r"^open up (?:the )?(.+?)(?:\s+app)?$",
        r"^could you open (?:the )?(.+?)(?:\s+(?:app|browser|for me))?$",
        r"^pull up (.+?)(?:\s+app)?$",
        r"^i want to open (.+?)(?:\s+app)?$",
    ]
    for pat in app_patterns:
        target = _extract(pat, t)
        if target and "." not in target and "http" not in target:
            target = re.sub(
                r"\s*(for me|please|now|browser|app)$", "", target
            ).strip()
            if target:
                result["intent"] = Intent.OPEN_APP
                result["target"] = target
                return result

    # ── Web Search ───────────────────────────────────────────
    for pat in [
        r"^search (?:for )?(.+)",
        r"^google (.+)",
        r"^look up (.+)",
        r"^find (?:information (?:about|on) )?(.+)",
    ]:
        target = _extract(pat, t)
        if target:
            result["intent"] = Intent.SEARCH_WEB
            result["target"] = target
            return result

    # ── Create File ──────────────────────────────────────────
    for pat in [
        r"^create (?:a )?(?:new )?(?:text )?file (?:called |named )?(.+)",
        r"^new file (.+)",
        r"^make (?:a )?(?:new )?file (?:called |named )?(.+)",
    ]:
        target = _extract(pat, t)
        if target:
            result["intent"] = Intent.CREATE_FILE
            result["target"] = target
            return result

    return result