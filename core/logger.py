import json
import os
import datetime
from config.settings import LOG_FILE

def _ensure():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_action(action_type, description, success=True, error=None, metadata=None):
    _ensure()
    entry = {
        "timestamp":   datetime.datetime.now().isoformat(timespec="seconds"),
        "type":        action_type,
        "description": description,
        "success":     success,
    }
    if error:    entry["error"]    = error
    if metadata: entry["metadata"] = metadata
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def log_conversation(user_text, alfred_response, intent):
    log_action(
        "conversation",
        f"User: {user_text[:100]}",
        metadata={"intent": intent, "response": alfred_response[:200]}
    )
    