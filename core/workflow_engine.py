# ============================================================
# Alfred Wayne OS - Workflow Automation Engine (Phase A)
# Detects repeated action patterns and allows Master Wayne
# to create named routines that chain multiple actions.
# ============================================================

import json
import os
from collections import Counter
from config.settings import USER_NAME

ROUTINES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "memory", "routines.json"
)

# ── Minimum times an action must repeat to suggest automation ─
SUGGESTION_THRESHOLD = 3


def _load_routines() -> dict:
    """Load saved routines from disk."""
    if not os.path.exists(ROUTINES_FILE):
        return {}
    try:
        with open(ROUTINES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_routines(routines: dict):
    """Save routines to disk."""
    os.makedirs(os.path.dirname(ROUTINES_FILE), exist_ok=True)
    with open(ROUTINES_FILE, "w", encoding="utf-8") as f:
        json.dump(routines, f, indent=2)


def save_routine(name: str, actions: list) -> str:
    """
    Save a named routine — a list of actions to execute in sequence.
    Example: "start my day" → ["open chrome", "open vs code"]
    """
    routines = _load_routines()
    routines[name.lower().strip()] = {
        "actions": actions,
        "created": _now(),
        "run_count": 0,
    }
    _save_routines(routines)
    return (
        f"Routine '{name}' saved, {USER_NAME}. "
        f"Say '{name}' anytime to run it."
    )


def get_routine(name: str) -> list:
    """
    Returns the action list for a named routine, or None if not found.
    """
    routines = _load_routines()
    routine  = routines.get(name.lower().strip())
    if routine:
        # Increment run count
        routine["run_count"] += 1
        routine["last_run"]   = _now()
        _save_routines(routines)
        return routine["actions"]
    return None


def list_routines() -> str:
    """Returns a formatted list of all saved routines."""
    routines = _load_routines()
    if not routines:
        return f"No routines saved yet, {USER_NAME}."

    lines = [f"Your saved routines, {USER_NAME}:"]
    for name, data in routines.items():
        actions   = ", ".join(data["actions"])
        run_count = data.get("run_count", 0)
        lines.append(f"  • '{name}' → {actions} (run {run_count}x)")
    return "\n".join(lines)


def delete_routine(name: str) -> str:
    """Deletes a named routine."""
    routines = _load_routines()
    key      = name.lower().strip()
    if key in routines:
        del routines[key]
        _save_routines(routines)
        return f"Routine '{name}' deleted, {USER_NAME}."
    return f"I couldn't find a routine named '{name}', {USER_NAME}."


def analyze_workflow(workflow_history: list) -> str:
    """
    Analyzes workflow_history for repeated action patterns.
    Returns a suggestion string if a pattern is found, or "" if nothing.

    Looks for:
    1. Single actions repeated many times
    2. Pairs of actions that always happen together
    """
    if len(workflow_history) < SUGGESTION_THRESHOLD * 2:
        return ""

    # Extract just the action strings
    actions = [e.get("action", "") for e in workflow_history if e.get("action")]

    # Count single action frequencies
    counts = Counter(actions)
    frequent = [
        action for action, count in counts.items()
        if count >= SUGGESTION_THRESHOLD
        and not _routine_exists_for(action)
    ]

    # Count pairs (consecutive actions)
    pairs = []
    for i in range(len(actions) - 1):
        pair = (actions[i], actions[i + 1])
        pairs.append(pair)

    pair_counts = Counter(pairs)
    frequent_pairs = [
        pair for pair, count in pair_counts.items()
        if count >= SUGGESTION_THRESHOLD
        and not _routine_exists_for(f"{pair[0]}+{pair[1]}")
    ]

    # Generate suggestion
    if frequent_pairs:
        a, b = frequent_pairs[0]
        a_name = a.replace("open_app:", "").replace("open_website:", "")
        b_name = b.replace("open_app:", "").replace("open_website:", "")
        return (
            f"Master Wayne, I've noticed you frequently use "
            f"{a_name} and {b_name} together. "
            f"Shall I create a routine for this? "
            f"Just say 'yes, name it [routine name]'."
        )

    if frequent:
        action = frequent[0]
        name   = action.replace("open_app:", "").replace("open_website:", "")
        return (
            f"Master Wayne, I've noticed you frequently use {name}. "
            f"Shall I add it to a routine?"
        )

    return ""


def _routine_exists_for(action: str) -> bool:
    """Check if a routine already covers this action."""
    routines = _load_routines()
    for data in routines.values():
        if action in data.get("actions", []):
            return True
    return False


def _now() -> str:
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")