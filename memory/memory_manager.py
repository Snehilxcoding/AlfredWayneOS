# ============================================================
# Alfred Wayne OS - Memory Manager
# Phase 2: Now includes long-term memory storage and retrieval.
# ============================================================

import json
import os
import datetime
from config.settings import MEMORY_FILE, USER_NAME


DEFAULT = {
    "profile": {
        "name":     USER_NAME,
        "last_seen": None,
        "created":   None,
    },
    "preferences":      {"voice": True},
    "projects":         [],
    "conversations":    [],
    "workflow_history": [],
    "notes":            {},
    # Phase 2 addition — structured long-term memory
    "long_term": {
        "personal":    {},
        "preferences": {},
        "goals":       {},
        "projects":    {},
    },
}


def _dir():
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)


def load_memory() -> dict:
    """Load memory.json from disk. Creates default if missing."""
    _dir()
    if not os.path.exists(MEMORY_FILE):
        m = _deep_copy_default()
        m["profile"]["created"] = _now()
        save_memory(m)
        print("[Alfred] Memory initialized.")
        return m
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            m = json.load(f)
        # Ensure long_term block exists for older memory files
        if "long_term" not in m:
            m["long_term"] = {
                "personal":    {},
                "preferences": {},
                "goals":       {},
                "projects":    {},
            }
            save_memory(m)
        return m
    except Exception:
        m = _deep_copy_default()
        save_memory(m)
        return m


def save_memory(m: dict):
    """Write memory dict to disk."""
    _dir()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)


def update_last_seen(m: dict) -> dict:
    m["profile"]["last_seen"] = _now()
    save_memory(m)
    return m


def add_conversation_summary(m: dict, user_msg: str, alfred_msg: str) -> dict:
    """Store a short summary of each conversation turn."""
    m["conversations"].append({
        "timestamp": _now(),
        "user":      user_msg[:200],
        "alfred":    alfred_msg[:200],
    })
    m["conversations"] = m["conversations"][-50:]
    save_memory(m)
    return m


def log_workflow(m: dict, action: str) -> dict:
    m["workflow_history"].append({"action": action, "timestamp": _now()})
    m["workflow_history"] = m["workflow_history"][-200:]
    save_memory(m)
    return m


def build_memory_context(m: dict) -> str:
    """
    Builds the short-term memory context string for the AI prompt.
    Includes recent conversation topics.
    """
    recent = m.get("conversations", [])[-3:]
    lines  = [f"User: {m['profile'].get('name', USER_NAME)}"]
    for c in recent:
        lines.append(f"  Previously said: \"{c['user']}\"")
    return "\n".join(lines)


def build_longterm_context(m: dict) -> str:
    """
    Phase 2: Builds a long-term memory summary injected into
    Alfred's system prompt so he remembers facts across sessions.
    """
    lt = m.get("long_term", {})

    sections = []

    personal = lt.get("personal", {})
    if personal:
        facts = [f"{k.replace('_', ' ')}: {v['value']}" for k, v in personal.items()]
        sections.append("Personal: " + ", ".join(facts))

    preferences = lt.get("preferences", {})
    if preferences:
        facts = [f"{k.replace('_', ' ')}: {v['value']}" for k, v in preferences.items()]
        sections.append("Preferences: " + ", ".join(facts))

    goals = lt.get("goals", {})
    if goals:
        facts = [v["value"] for v in goals.values()]
        sections.append("Goals: " + "; ".join(facts))

    projects = lt.get("projects", {})
    if projects:
        facts = [v["value"] for v in projects.values()]
        sections.append("Active projects: " + "; ".join(facts))

    if not sections:
        return "No long-term memories stored yet."

    return "\n".join(sections)


def get_all_longterm_facts(m: dict) -> list:
    """
    Returns all long-term facts as a flat list of dicts.
    Useful for displaying memory to the user.
    """
    lt = m.get("long_term", {})
    facts = []
    for category, entries in lt.items():
        for key, data in entries.items():
            facts.append({
                "category": category,
                "key":      key,
                "value":    data["value"],
                "updated":  data.get("updated", ""),
            })
    return facts


def _deep_copy_default() -> dict:
    """Returns a fresh copy of the default memory structure."""
    import copy
    return copy.deepcopy(DEFAULT)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")