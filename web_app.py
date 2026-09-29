import os
import sys
import time
import random
try:
    import psutil
except ImportError:
    psutil = None
from flask import Flask, render_template, request, jsonify

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config.settings as settings
settings.TEXT_ONLY_MODE = True

from core.context import get_full_context, build_context_summary
from core.greeting import get_greeting, get_status_comment
from core.command_parser import parse_command, Intent
from core.ai_engine import ask_alfred
from core.logger import log_action, log_conversation
from memory.memory_manager import (
    load_memory, update_last_seen,
    add_conversation_summary, build_memory_context,
    build_longterm_context, log_workflow
)
from memory.memory_extractor import extract_and_store

app = Flask(__name__, template_folder="templates", static_folder="static")

# Shared in-memory conversation history per session
chat_history = []
start_time = time.time()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "healthy", "service": "AlfredWayneOS", "uptime_seconds": int(time.time() - start_time)})

@app.route("/api/status", methods=["GET"])
def get_status():
    ctx = get_full_context()
    memory = load_memory()
    uptime = int(time.time() - start_time)
    
    return jsonify({
        "status": "online",
        "user_name": settings.USER_NAME,
        "time": ctx["time"],
        "date": ctx["date"],
        "day": ctx["day"],
        "cpu_percent": ctx["system"]["cpu_percent"],
        "ram_percent": ctx["system"]["ram_percent"],
        "ram_used_gb": ctx["system"]["ram_used_gb"],
        "ram_total_gb": ctx["system"]["ram_total_gb"],
        "online": ctx["online"],
        "memory_summaries_count": len(memory.get("summaries", [])),
        "longterm_memories_count": len(memory.get("long_term", {})),
        "uptime_seconds": uptime
    })

@app.route("/api/memory", methods=["GET"])
def get_memory_info():
    memory = load_memory()
    return jsonify({
        "user": memory.get("user", {}),
        "long_term": memory.get("long_term", {}),
        "recent_summaries": memory.get("summaries", [])[-10:],
        "routines": memory.get("routines", {})
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    global chat_history
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    ctx = get_full_context()
    memory = load_memory()
    update_last_seen(memory)

    context_summary = build_context_summary(ctx)
    memory_context = build_memory_context(memory)
    longterm_context = build_longterm_context(memory)

    parsed = parse_command(user_message)
    intent = parsed.get("intent")
    target = parsed.get("target")

    alfred_response = None

    # Specific quick intents
    if intent == Intent.FAREWELL:
        alfred_response = f"Good night, {settings.USER_NAME}. I'll be here whenever you return."
    elif intent == Intent.GRATITUDE:
        alfred_response = random.choice([
            f"Think nothing of it, {settings.USER_NAME}.",
            f"Always a pleasure, {settings.USER_NAME}.",
            f"Happy to be of service, {settings.USER_NAME}.",
        ])
    elif intent == Intent.TIME_QUERY:
        alfred_response = f"It is currently {ctx['time']} on {ctx['day']}, {ctx['date']}, {settings.USER_NAME}."
    elif intent == Intent.SYSTEM_INFO:
        s = ctx["system"]
        alfred_response = (
            f"Cloud Web System Context — CPU: {s['cpu_percent']}%, "
            f"RAM: {s['ram_used_gb']}GB of {s['ram_total_gb']}GB used ({s['ram_percent']}%). "
            f"Network: {'Online' if ctx['online'] else 'Offline'}."
        )

    # General AI processing if no static intent matched
    if not alfred_response:
        chat_history.append({"role": "user", "content": user_message})
        alfred_response = ask_alfred(
            user_message=user_message,
            context_summary=context_summary,
            memory_context=memory_context,
            longterm_context=longterm_context,
            history=chat_history
        )
        chat_history.append({"role": "assistant", "content": alfred_response})
        if len(chat_history) > 30:
            chat_history = chat_history[-30:]

    # Log & extract long term memory in background/inline
    try:
        log_conversation("user", user_message)
        log_conversation("alfred", alfred_response)
        extract_and_store(user_message, alfred_response, memory)
    except Exception as e:
        print(f"[Alfred Web] Memory log warning: {e}")

    return jsonify({
        "response": alfred_response,
        "intent": str(intent),
        "user_name": settings.USER_NAME,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
